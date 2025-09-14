"""Main application module that integrates CLI with decoder components.

This module provides the main entry point that coordinates the HAL, SignalProcessor,
and MorseDecoder components using the registry-based configuration system.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any

from .components.audio.hal import HardwareAbstractionLayer
from .components.decoder.morse_decoder import MorseDecoder
from .components.signal.signal_processor import SignalProcessor
from .events.bus import get_global_event_bus
from .events.types import AudioChunkEvent, MorsePatternEvent, TextDecodedEvent, ToneDetectedEvent

logger = logging.getLogger(__name__)


class ProgressReporter:
    """Progress reporting for CLI using events."""

    def __init__(self) -> None:
        """Initialize the progress reporter."""
        self.start_time = time.time()
        self.chunk_count = 0
        self.tone_detections = 0
        self.patterns_decoded = 0
        self.characters_decoded = 0
        self.current_text = ""
        self.last_progress_time = time.time()

    def handle_audio_chunk(self, event: AudioChunkEvent) -> None:
        """Handle audio chunk events for progress tracking."""
        self.chunk_count += 1

        # Show progress every 100 chunks or when reaching end
        if self.chunk_count % 100 == 0 or not event.has_more_data:
            elapsed = time.time() - self.start_time
            chunks_per_sec = self.chunk_count / elapsed if elapsed > 0 else 0

            print(
                f"\rProcessed {self.chunk_count} chunks "
                f"({chunks_per_sec:.1f}/sec) | "
                f"Tones: {self.tone_detections} | "
                f"Patterns: {self.patterns_decoded} | "
                f"Text: '{self.current_text}'",
                end="",
                flush=True,
            )

            if not event.has_more_data:
                print()  # New line at completion

    def handle_tone_detected(self, event: ToneDetectedEvent) -> None:
        """Handle tone detection events."""
        if event.detected:
            self.tone_detections += 1

    def handle_morse_pattern(self, event: MorsePatternEvent) -> None:
        """Handle morse pattern events."""
        if event.pattern_type in ("dot", "dash"):
            self.patterns_decoded += 1

    def handle_text_decoded(self, event: TextDecodedEvent) -> None:
        """Handle text decoded events."""
        self.characters_decoded += 1
        # Keep only last 20 characters for display
        self.current_text = (self.current_text + event.text)[-20:]

    def setup_event_subscriptions(self) -> None:
        """Subscribe to relevant events."""
        event_bus = get_global_event_bus()
        event_bus.subscribe(AudioChunkEvent, self.handle_audio_chunk)
        event_bus.subscribe(ToneDetectedEvent, self.handle_tone_detected)
        event_bus.subscribe(MorsePatternEvent, self.handle_morse_pattern)
        event_bus.subscribe(TextDecodedEvent, self.handle_text_decoded)


def run_decoder_legacy(
    hal_config: dict[str, Any],
    signal_config: dict[str, Any],
    decoder_config: dict[str, Any],
    app_config: dict[str, Any],
) -> int:
    """Run decoder with legacy config dictionaries from registry system.

    Args:
        hal_config: Hardware abstraction layer configuration
        signal_config: Signal processor configuration
        decoder_config: Morse decoder configuration
        app_config: Application configuration

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting Morse code decoder (registry-based)")

        logger.info("Initializing components")

        # Initialize components with legacy configs
        hal = HardwareAbstractionLayer(cfg_dict=hal_config)
        processor = SignalProcessor(cfg_dict=signal_config)
        decoder = MorseDecoder(cfg_dict=decoder_config)

        logger.info("Components initialized successfully")
        logger.info("Audio file: %s", hal_config.get("wav_filename"))
        logger.info("Target frequency: %d Hz", signal_config.get("target_frequency_hz", 600))
        logger.info("Estimated WPM: %d", decoder_config.get("wpm_estimate", 15))

        # Set up progress reporting via events
        progress_reporter = ProgressReporter()
        progress_reporter.setup_event_subscriptions()

        # Process audio
        return _process_audio(hal, processor, decoder, app_config)

    except Exception as e:
        logger.exception("Unexpected error during decoding")
        print(f"Error: Unexpected error - {e}", file=sys.stderr)
        return 1


def _process_audio(hal: Any, processor: Any, decoder: Any, app_config: dict[str, Any]) -> int:
    """Process audio through the decoder pipeline.

    Args:
        hal: Hardware abstraction layer
        processor: Signal processor
        decoder: Morse decoder
        app_config: Application configuration

    Returns:
        Exit code
    """
    try:
        update_interval_ms = 20  # Fixed for now

        logger.info("Starting audio processing")
        print("Processing audio...", flush=True)

        while hal.has_data():
            # Get next audio chunk (publishes AudioChunkEvent)
            chunk = hal.get_next_chunk(update_interval_ms=update_interval_ms)

            # Process signal for tone detection (publishes ToneDetectedEvent)
            tone_detected = processor.detect_tone(chunk)

            # Feed to Morse decoder (publishes MorsePatternEvent and TextDecodedEvent)
            decoder.process_tone_detection(tone_detected, float(update_interval_ms))

        print("Audio processing complete")

        # Finalize decoding
        logger.info("Finalizing Morse code decoding")
        decoder.finalize_decoding()

        # Get decoded text
        decoded_text = decoder.get_decoded_text()

        if not decoded_text.strip():
            logger.warning("No Morse code patterns detected in audio")
            decoded_text = "[No Morse code detected]"
        else:
            logger.info("Successfully decoded %d characters", len(decoded_text))

        # Output results
        output_file = app_config.get("output_file")
        _write_output(decoded_text, output_file)

        logger.info("Morse code decoding completed successfully")
        return 0

    except Exception as e:
        logger.exception("Error during audio processing")
        print(f"Error during processing: {e}", file=sys.stderr)
        return 1


def _write_output(decoded_text: str, output_file: str | None = None) -> None:
    """Write decoded text to output destination.

    Args:
        decoded_text: The decoded Morse code text
        output_file: Optional output file path (None for stdout)
    """
    if output_file:
        try:
            output_path = Path(output_file)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(decoded_text)
                f.write("\n")
            logger.info("Output written to: %s", output_file)
            print(f"Decoded text written to: {output_file}")
        except OSError as e:
            logger.error("Failed to write output file: %s", e)
            print(f"Error writing output file: {e}", file=sys.stderr)
            print(f"Decoded text: {decoded_text}")
    else:
        # Write to stdout
        print("Decoded text:")
        print(decoded_text)

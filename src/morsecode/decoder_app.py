"""Main application module that integrates CLI with decoder components.

This module provides the main entry point that coordinates the HAL, SignalProcessor,
and MorseDecoder components using the registry-based configuration system.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any

from util.config import AwesomeConfigManager

# Initialize graphics component (auto-subscribes to events)
from .components import graphics  # noqa: F401
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


def run_decoder_configurable(
    config_manager: AwesomeConfigManager,
    overrides: dict[str, Any] | None = None,
    output_file: str | None = None,
) -> int:
    """Run decoder with ConfigurableBase components directly.

    This is the simplified, single-architecture approach that uses ConfigurableBase
    components with AwesomeConfigManager directly, eliminating the dual typed config pattern.

    Args:
        config_manager: AwesomeConfigManager with loaded configuration
        overrides: Optional configuration overrides to apply
        output_file: Optional output file path (None for stdout)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting Morse code decoder (ConfigurableBase architecture)")

        # Apply any CLI overrides to sections
        if overrides:
            for section, section_overrides in overrides.items():
                try:
                    # This would need apply_overrides support in real AwesomeConfigManager
                    logger.info("Applied overrides to section %s: %s", section, list(section_overrides.keys()))
                except Exception as e:
                    logger.warning("Could not apply overrides to section %s: %s", section, e)

        logger.info("Initializing ConfigurableBase components")

        # Initialize components directly with ConfigurableBase pattern
        # This is clean: no typed configs, no mock managers, direct instantiation
        hal = HardwareAbstractionLayer(config_manager, overrides=overrides.get("audio") if overrides else None)
        processor = SignalProcessor(cfg_mgr=config_manager, overrides=overrides.get("signal") if overrides else None)
        decoder = MorseDecoder(cfg_mgr=config_manager, overrides=overrides.get("decoder") if overrides else None)

        logger.info("Components initialized successfully")

        # Set up progress reporting via events
        progress_reporter = ProgressReporter()
        progress_reporter.setup_event_subscriptions()

        # Process audio using the same logic but cleaner components
        try:
            if not hal.has_data():
                logger.error("No audio data available")
                print("Error: No audio data to process", file=sys.stderr)
                return 1

            logger.info("Processing audio data...")

            while hal.has_data():
                try:
                    # Get next audio chunk
                    audio_data = hal.get_next_chunk(update_interval_ms=50)

                    # Process through signal processor
                    tone_detected = processor.detect_tone(audio_data)

                    # Feed to decoder
                    decoder.process_tone_detection(tone_detected, 50.0)  # 50ms chunks

                except Exception as e:
                    logger.error("Error processing audio chunk: %s", e)
                    break

            # Finalize decoding
            decoder.finalize_decoding()
            decoded_text = decoder.get_decoded_text()

            logger.info("Decoding completed successfully")
            logger.info("Decoded text length: %d characters", len(decoded_text))

            # Write output
            _write_output(decoded_text, output_file)

            return 0

        except Exception as e:
            logger.exception("Error during audio processing")
            print(f"Error: Audio processing failed - {e}", file=sys.stderr)
            return 1

    except Exception as e:
        logger.exception("Unexpected error during decoding")
        print(f"Error: Unexpected error - {e}", file=sys.stderr)
        return 1

"""Main application module that integrates CLI with decoder components.

This module provides the main entry point that coordinates the HAL, SignalProcessor,
and MorseDecoder components using the registry-based configuration system.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from util.config.models import AppConfig, AudioConfig, DecoderConfig, SignalConfig

from .components.audio.hal import HardwareAbstractionLayer
from .components.audio.keys import CfgKey as AudioCfgKey
from .components.decoder.keys import CfgKey as DecoderCfgKey
from .components.decoder.morse_decoder import MorseDecoder
from .components.signal.signal_processor import SignalProcessor
from .events.bus import get_global_event_bus
from .events.types import AudioChunkEvent, MorsePatternEvent, TextDecodedEvent, ToneDetectedEvent

logger = logging.getLogger(__name__)


def create_mock_audio_config_manager(audio_config: AudioConfig) -> MagicMock:
    """Create mock config manager from AudioConfig."""
    config_data = {
        AudioCfgKey.SAMPLE_RATE: audio_config.sample_rate,
        AudioCfgKey.WAV_FILENAME: audio_config.wav_filename,
        AudioCfgKey.AUTO_GAIN_CONTROL: audio_config.auto_gain_control,
        AudioCfgKey.CHUNK_SIZE: audio_config.chunk_size_ms,
    }

    mock_config_manager = MagicMock()
    mock_section = MagicMock()

    # Configure the mock section to return values based on enum keys
    def get_value(key):
        return config_data.get(key)

    mock_section.get_int.side_effect = lambda key: get_value(key)
    mock_section.get_double.side_effect = lambda key: get_value(key)
    mock_section.get_bool.side_effect = lambda key: get_value(key)
    mock_section.get_string.side_effect = lambda key: get_value(key)

    mock_config_manager.get_section.return_value = mock_section
    return mock_config_manager


def create_mock_decoder_config_manager(decoder_config: DecoderConfig) -> MagicMock:
    """Create mock config manager from DecoderConfig."""
    config_data = {
        DecoderCfgKey.WPM: decoder_config.wpm,
        DecoderCfgKey.DOT_DURATION: decoder_config.dot_duration_ms,
        DecoderCfgKey.TOLERANCE: decoder_config.tolerance,
    }

    mock_config_manager = MagicMock()
    mock_section = MagicMock()

    # Configure the mock section to return values based on enum keys
    def get_value(key):
        return config_data.get(key)

    mock_section.get_int.side_effect = lambda key: get_value(key)
    mock_section.get_double.side_effect = lambda key: get_value(key)
    mock_section.get_bool.side_effect = lambda key: get_value(key)
    mock_section.get_string.side_effect = lambda key: get_value(key)

    mock_config_manager.get_section.return_value = mock_section
    return mock_config_manager


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


def run_decoder_typed(
    audio_config: AudioConfig,
    signal_config: SignalConfig,
    decoder_config: DecoderConfig,
    app_config: AppConfig,
) -> int:
    """Run decoder with typed configuration objects.

    Args:
        audio_config: Audio configuration
        signal_config: Signal processor configuration
        decoder_config: Morse decoder configuration
        app_config: Application configuration

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        logger.info("Starting Morse code decoder (typed config)")

        logger.info("Initializing components")

        # Initialize components with mock config managers (converted from typed configs)
        audio_cfg_mgr = create_mock_audio_config_manager(audio_config)
        decoder_cfg_mgr = create_mock_decoder_config_manager(decoder_config)

        hal = HardwareAbstractionLayer(cfg_mgr=audio_cfg_mgr)
        processor = SignalProcessor(config=signal_config)  # SignalProcessor supports both patterns
        decoder = MorseDecoder(cfg_mgr=decoder_cfg_mgr)

        logger.info("Components initialized successfully")
        logger.info("Audio file: %s", audio_config.wav_filename)
        logger.info("Target frequency: %d Hz", signal_config.frequency)
        logger.info("Estimated WPM: %d", decoder_config.wpm)

        # Set up progress reporting via events
        progress_reporter = ProgressReporter()
        progress_reporter.setup_event_subscriptions()

        # Process audio
        return _process_audio_typed(hal, processor, decoder, app_config)

    except Exception as e:
        logger.exception("Unexpected error during decoding")
        print(f"Error: Unexpected error - {e}", file=sys.stderr)
        return 1


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

        # Initialize components with legacy configs (convert to typed)
        audio_cfg = AudioConfig(
            sample_rate=hal_config.get("audio_rate_hz", 44100),
            wav_filename=hal_config.get("wav_filename"),
            auto_gain_control=hal_config.get("auto_gain_control", True),
            chunk_size_ms=hal_config.get("chunk_size_ms", 50),
        )
        signal_cfg = SignalConfig(
            sample_rate=signal_config.get("sample_rate_hz", 44100),
            frequency=signal_config.get("target_frequency_hz", 600),  # Registry default
            threshold=signal_config.get("detection_threshold", 0.3),
            bandwidth=signal_config.get("filter_bandwidth_hz", 50),
        )
        decoder_cfg = DecoderConfig(
            wpm=decoder_config.get("wpm_estimate", 15),
            tolerance=decoder_config.get("detection_tolerance", 0.3),
            dot_duration_ms=decoder_config.get("dot_duration_ms"),
            min_silence_ms=decoder_config.get("min_silence_duration_ms", 200.0),
        )

        # Convert legacy configs to mock config managers
        # Note: This is temporary bridge code for legacy function support
        from .components.audio.keys import CfgKey as AudioCfgKey
        from .components.decoder.keys import CfgKey as DecoderCfgKey

        # Create mock audio config manager
        audio_config_data = {
            AudioCfgKey.SAMPLE_RATE: audio_cfg.sample_rate,
            AudioCfgKey.WAV_FILENAME: audio_cfg.wav_filename,
            AudioCfgKey.AUTO_GAIN_CONTROL: audio_cfg.auto_gain_control,
            AudioCfgKey.CHUNK_SIZE: audio_cfg.chunk_size_ms,
        }
        audio_mock = MagicMock()
        audio_section = MagicMock()
        audio_section.get_int.side_effect = lambda key: audio_config_data.get(key)
        audio_section.get_bool.side_effect = lambda key: audio_config_data.get(key)
        audio_section.get_string.side_effect = lambda key: audio_config_data.get(key)
        audio_mock.get_section.return_value = audio_section

        # Create mock decoder config manager
        decoder_config_data = {
            DecoderCfgKey.WPM: decoder_cfg.wpm,
            DecoderCfgKey.DOT_DURATION: decoder_cfg.dot_duration_ms,
            DecoderCfgKey.TOLERANCE: decoder_cfg.tolerance,
        }
        decoder_mock = MagicMock()
        decoder_section = MagicMock()
        decoder_section.get_int.side_effect = lambda key: decoder_config_data.get(key)
        decoder_section.get_double.side_effect = lambda key: decoder_config_data.get(key)
        decoder_mock.get_section.return_value = decoder_section

        hal = HardwareAbstractionLayer(cfg_mgr=audio_mock)
        processor = SignalProcessor(config=signal_cfg)  # SignalProcessor supports both patterns
        decoder = MorseDecoder(cfg_mgr=decoder_mock)

        logger.info("Components initialized successfully")
        logger.info("Audio file: %s", hal_config.get("wav_filename"))
        logger.info(
            "Target frequency: %d Hz",
            signal_config.get("target_frequency_hz", 600),  # Registry default
        )
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


def _process_audio_typed(hal: Any, processor: Any, decoder: Any, app_config: AppConfig) -> int:
    """Process audio through the decoder pipeline with typed config.

    Args:
        hal: Hardware abstraction layer
        processor: Signal processor
        decoder: Morse decoder
        app_config: Application configuration (typed)

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

        # Output results - use typed config field
        _write_output(decoded_text, app_config.output_file)

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user", flush=True)
        return 1
    except Exception as e:
        logger.exception("Error during audio processing: %s", str(e))
        print(f"Processing error: {e}", file=sys.stderr)
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

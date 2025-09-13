"""Main application module that integrates CLI with decoder components.

This module provides the main entry point that coordinates the HAL, SignalProcessor,
and MorseDecoder components using the registry-based configuration system.
"""

import logging
import sys
from pathlib import Path
from typing import Any

from .hal import HardwareAbstractionLayer
from .morse_decoder import MorseDecoder
from .signal_processor import SignalProcessor

logger = logging.getLogger(__name__)


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
        chunk_count = 0
        update_interval_ms = 20  # Fixed for now

        logger.info("Starting audio processing")

        while hal.has_data():
            # Get next audio chunk
            chunk = hal.get_next_chunk(update_interval_ms=update_interval_ms)

            # Process signal for tone detection
            tone_detected = processor.detect_tone(chunk)

            # Feed to Morse decoder
            decoder.process_tone_detection(tone_detected, float(update_interval_ms))

            chunk_count += 1

            if chunk_count % 100 == 0:
                logger.debug("Processed %d chunks", chunk_count)

        logger.info("Audio processing complete (%d chunks)", chunk_count)

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

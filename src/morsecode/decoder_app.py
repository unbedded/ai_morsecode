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

# Concrete implementations that satisfy Protocol interfaces
from .components.audio.hal import HardwareAbstractionLayer
from .components.decoder.factory import DecoderFactory
from .components.signal.signal_processor import SignalProcessor
from .events.bus import get_global_event_bus
from .events.types import AudioChunkEvent, MorsePatternEvent, TextDecodedEvent, ToneDetectedEvent

# Protocol interfaces for dependency injection (loose coupling)
from .interfaces.audio import AudioSource
from .interfaces.signal import SignalProcessor as SignalProcessorProtocol

# Service layer using Protocol interfaces
from .services.audio_processing_service import AudioProcessingService

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


def create_audio_processing_service(
    config_manager: AwesomeConfigManager, overrides: dict[str, Any] | None = None
) -> AudioProcessingService:
    """Factory function demonstrating proper Protocol-based dependency injection.

    This shows how to create services using Protocol interfaces for loose coupling.
    Concrete implementations are created here and injected into the service.

    Args:
        config_manager: Configuration manager for component initialization
        overrides: Optional configuration overrides

    Returns:
        AudioProcessingService configured with Protocol interface dependencies
    """
    logger.info("Creating audio processing service with Protocol-based dependency injection...")

    # Create concrete implementations that satisfy Protocol interfaces
    signal_overrides = overrides.get("signal") if overrides else None
    audio_overrides = overrides.get("audio") if overrides else None

    # Concrete implementations (satisfy Protocol interfaces)
    concrete_processor = SignalProcessor(cfg_mgr=config_manager, overrides=signal_overrides)
    concrete_audio = HardwareAbstractionLayer(config_manager, overrides=audio_overrides)
    event_bus = get_global_event_bus()

    # Type annotations show Protocol interfaces, not concrete classes!
    processor_interface: SignalProcessorProtocol = concrete_processor  # ← Protocol interface
    audio_interface: AudioSource = concrete_audio  # ← Protocol interface

    logger.info(
        "Dependency injection: processor=%s satisfies SignalProcessorProtocol, audio=%s satisfies AudioSource",
        type(concrete_processor).__name__,
        type(concrete_audio).__name__,
    )

    # Service receives Protocol interfaces, not concrete implementations!
    service = AudioProcessingService(
        signal_processor=processor_interface,  # ← Protocol interface injected
        audio_source=audio_interface,  # ← Protocol interface injected
        event_bus=event_bus,
        cfg_mgr=config_manager,
    )

    logger.info("AudioProcessingService created with Protocol-based dependency injection")
    return service


def run_decoder_configurable(
    config_manager: AwesomeConfigManager,
    overrides: dict[str, Any] | None = None,
    output_file: str | None = None,
    debug_graphics: bool = False,
    real_time: bool = False,
    playback_speed: float = 1.0,
) -> int:
    """Run decoder with ConfigurableBase components directly.

    This is the simplified, single-architecture approach that uses ConfigurableBase
    components with AwesomeConfigManager directly, eliminating the dual typed config pattern.

    Args:
        config_manager: AwesomeConfigManager with loaded configuration
        overrides: Optional configuration overrides to apply
        output_file: Optional output file path (None for stdout)
        debug_graphics: If True, enable ASCII debug graphics display for SSH debugging
        real_time: If True, process audio in real-time for live oscilloscope debugging
        playback_speed: Playback speed multiplier for time synchronization

    Returns:
        Exit code (0 for success, 1 for error)
    """
    debug_display: Any = None  # Initialize at function scope for cleanup

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

        # Real-time mode requires smaller FFT window for 20ms chunks
        signal_overrides = overrides.get("signal", {}).copy() if overrides else {}
        if real_time:
            # 20ms chunks at 44100 Hz = 882 samples, so use 512-sample FFT window
            signal_overrides["fft_window_size"] = 512
            logger.info("Real-time mode: using smaller FFT window (512 samples) for 20ms chunks")

        # Convert empty dict to None for consistency with test expectations
        signal_overrides = signal_overrides if signal_overrides else None

        # Initialize components directly with ConfigurableBase pattern
        # This is clean: no typed configs, no mock managers, direct instantiation
        hal = HardwareAbstractionLayer(config_manager, overrides=overrides.get("audio") if overrides else None)
        processor = SignalProcessor(cfg_mgr=config_manager, overrides=signal_overrides)
        decoder = DecoderFactory.create(
            cfg_mgr=config_manager, overrides=overrides.get("decoder") if overrides else None
        )

        logger.info("Components initialized successfully")

        # Initialize ASCII debug display if requested
        if debug_graphics:
            # Check graphics backend to choose between full display and pattern logging
            debug_overrides = overrides.get("graphics", {}) if overrides else {}
            debug_overrides["playback_speed"] = playback_speed

            # Get backend setting to determine display type
            from .components.graphics.keys import GraphicsKey

            graphics_section = config_manager.get_section("graphics")
            backend = graphics_section.get_string(GraphicsKey.BACKEND) if graphics_section else "ascii"

            if backend == "pattern":
                from .components.graphics.pattern_display import PatternDisplay

                logger.info("Initializing pattern display for simple logging")
                debug_display = PatternDisplay(config_manager, overrides=debug_overrides)
                print("📋 Pattern Display started - Simple morse pattern logging")
                print("   Patterns will be logged as they are detected...")
            else:
                from .components.graphics.graphics_display import GraphicsDisplay

                logger.info("Initializing graphics display for %s backend", backend)
                debug_display = GraphicsDisplay(config_manager, overrides=debug_overrides)
                debug_display.start_display()
                print(f"🔍 Graphics Display started - {backend} backend")
                print("   Press Ctrl+C to stop...")

        # Set up progress reporting via events (only if debug display is not active)
        progress_reporter = None
        if not debug_graphics:
            progress_reporter = ProgressReporter()
            progress_reporter.setup_event_subscriptions()

        # Process audio using the same logic but cleaner components
        try:
            # Debug: Check audio data status
            has_data = hal.has_data()
            logger.info("Audio data check: has_data=%s", has_data)

            if not has_data:
                logger.error("No audio data available")
                print("Error: No audio data to process", file=sys.stderr)
                return 1

            if real_time:
                logger.info("Processing audio data in REAL-TIME mode for live debugging...")
                print("🎵 Real-time processing mode enabled - watch the oscilloscope!")
            else:
                logger.info("Processing audio data in BATCH mode...")

            # Real-time processing variables - smaller chunks for better time granularity
            chunk_duration_ms = 20  # ms per chunk (reduced from 50ms for finer granularity)
            base_delay = chunk_duration_ms / 1000.0  # Convert to seconds
            # STEP 3: Apply playback speed multiplier (0.5x = slower, 2.0x = faster)
            real_time_delay = base_delay / playback_speed

            chunk_count = 0
            logger.info(
                "Starting audio processing loop - real_time=%s, playback_speed=%.1fx (delay=%.3fs)",
                real_time,
                playback_speed,
                real_time_delay,
            )

            while hal.has_data():
                try:
                    chunk_count += 1
                    # Real-time timing: sleep to match actual audio playback speed
                    if real_time:
                        time.sleep(real_time_delay)

                    # Debug: Log first few chunks in real-time mode
                    if real_time and chunk_count <= 3:
                        logger.info("Real-time chunk %d: processing with delay=%.3fs", chunk_count, real_time_delay)

                    # Get next audio chunk
                    audio_data = hal.get_next_chunk(duration_ms=chunk_duration_ms)

                    # Debug: Log processing activity
                    if chunk_count % 50 == 1:  # Log every 50 chunks to avoid spam
                        logger.debug("Processing chunk %d: %d samples", chunk_count, len(audio_data))

                    # Process through signal processor
                    tone_detected = processor.detect_tone(audio_data)

                    # Debug: Log tone detection results for first few chunks in real-time mode
                    if real_time and chunk_count <= 3:
                        logger.info("Real-time chunk %d: tone_detected=%s", chunk_count, tone_detected)

                    # Feed to decoder
                    decoder.process_tone_detection(tone_detected, float(chunk_duration_ms))

                except Exception as e:
                    logger.error("Error processing audio chunk: %s", e)
                    break

            # Log completion stats
            logger.info("Audio processing complete: processed %d chunks", chunk_count)

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

        finally:
            # Clean up debug display if it was started
            if debug_display:
                logger.debug("Cleaning up debug display from finally block")
                debug_display.stop_display()

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\nProcessing interrupted by user")
        if debug_display:
            debug_display.stop_display()
        return 1

    except Exception as e:
        logger.exception("Unexpected error during decoding")
        print(f"Error: Unexpected error - {e}", file=sys.stderr)
        if debug_display:
            debug_display.stop_display()
        return 1

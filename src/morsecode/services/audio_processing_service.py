"""Audio processing service demonstrating proper Protocol interface usage.

This service shows how to use Protocol interfaces for dependency injection
and loose coupling, allowing different implementations to be swapped without
changing the service code.
"""

from typing import Any

import numpy as np

from morsecode.events.bus import EventBus
from morsecode.events.types import AudioChunkEvent, FilteredMagnitudeEvent, ToneDetectedEvent
from morsecode.interfaces.audio import AudioSource
from morsecode.interfaces.signal import SignalProcessor
from util.logging import ComponentLogger


class AudioProcessingService:
    """Service that processes audio using Protocol interfaces.

    This demonstrates proper dependency injection using Protocol interfaces.
    The service depends on abstractions (Protocols), not concrete implementations.

    Example:
        ```python
        # Service uses Protocol interfaces - loose coupling
        from morsecode.interfaces.signal import SignalProcessor
        from morsecode.interfaces.audio import AudioSource

        # Concrete implementations satisfy Protocols
        from morsecode.components.signal.signal_processor import SignalProcessor as ConcreteProcessor
        from morsecode.components.audio.hal import HardwareAbstractionLayer as ConcreteAudio

        # Dependency injection with Protocol interfaces
        processor: SignalProcessor = ConcreteProcessor(config)
        audio_source: AudioSource = ConcreteAudio(config)
        service = AudioProcessingService(processor, audio_source, event_bus)
        ```
    """

    def __init__(
        self,
        signal_processor: SignalProcessor,  # ← Protocol interface, not concrete class!
        audio_source: AudioSource,  # ← Protocol interface, not concrete class!
        event_bus: EventBus,
        cfg_mgr=None,
    ):
        """Initialize audio processing service with injected dependencies.

        Args:
            signal_processor: Signal processing implementation (satisfies Protocol)
            audio_source: Audio source implementation (satisfies Protocol)
            event_bus: Event bus for publishing processing results
            cfg_mgr: Configuration manager for logging setup
        """
        # Initialize logger first
        if cfg_mgr is None:
            raise ValueError("cfg_mgr is required for AudioProcessingService")
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("AudioProcessingService initializing with dependency injection...")

        # Store Protocol interface references (not concrete classes!)
        self._signal_processor = signal_processor
        self._audio_source = audio_source
        self._event_bus = event_bus

        # Service state
        self._is_running = False
        self._chunks_processed = 0
        self._tones_detected = 0

        self.logger.info(
            "AudioProcessingService initialized - processor: %s, audio: %s",
            type(signal_processor).__name__,
            type(audio_source).__name__,
        )

    def start_processing(self) -> None:
        """Start audio processing using Protocol interfaces.

        This method demonstrates how service code only depends on Protocol
        interfaces, making it testable and flexible.
        """
        if self._is_running:
            self.logger.warning("Audio processing already running")
            return

        self._is_running = True
        self._chunks_processed = 0
        self._tones_detected = 0

        self.logger.info("Starting audio processing service...")

        try:
            # Use Protocol interfaces - service doesn't know concrete implementations!
            target_freq = self._signal_processor.get_target_frequency()
            self.logger.info("Processing audio for target frequency: %.1f Hz", target_freq)

            while self._is_running:
                # Get audio chunk using Protocol interface
                audio_chunk = self._get_next_audio_chunk()
                if audio_chunk is None:
                    break  # No more audio data

                # Process chunk using Protocol interface
                self._process_audio_chunk(audio_chunk)
                self._chunks_processed += 1

        except Exception as e:
            self.logger.exception("Error during audio processing: %s", str(e))
            raise
        finally:
            self._is_running = False
            self.logger.info(
                "Audio processing completed: %d chunks processed, %d tones detected",
                self._chunks_processed,
                self._tones_detected,
            )

    def stop_processing(self) -> None:
        """Stop audio processing."""
        if self._is_running:
            self.logger.info("Stopping audio processing service...")
            self._is_running = False

    def get_processing_stats(self) -> dict[str, Any]:
        """Get processing statistics.

        Returns:
            Dictionary with processing metrics
        """
        return {
            "chunks_processed": self._chunks_processed,
            "tones_detected": self._tones_detected,
            "is_running": self._is_running,
            "target_frequency": self._signal_processor.get_target_frequency(),
        }

    def _get_next_audio_chunk(self) -> np.ndarray | None:
        """Get next audio chunk using Protocol interface.

        Returns:
            Audio data array or None if no more data
        """
        try:
            # Service uses Protocol interface - doesn't know concrete implementation!
            if hasattr(self._audio_source, "get_next_chunk"):
                # Use standard 20ms chunks for real-time processing
                return self._audio_source.get_next_chunk(duration_ms=20)
            else:
                # Fallback for audio sources that don't implement streaming
                self.logger.debug("Audio source doesn't support streaming, stopping")
                return None

        except Exception as e:
            self.logger.exception("Error getting audio chunk: %s", str(e))
            return None

    def _process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """Process single audio chunk using Protocol interfaces.

        Args:
            audio_data: Audio samples to process
        """
        try:
            # Use Protocol interface methods - service doesn't know concrete implementation!
            tone_detected = self._signal_processor.detect_tone(audio_data)
            signal_strength = self._signal_processor.get_signal_strength(audio_data)
            dominant_freq = self._signal_processor.get_dominant_frequency(audio_data)
            confidence = self._signal_processor.get_detection_confidence(audio_data)

            if tone_detected:
                self._tones_detected += 1

            # Publish events with processing results
            self._publish_processing_events(audio_data, tone_detected, signal_strength, dominant_freq, confidence)

            # Debug logging every 100 chunks
            if self._chunks_processed % 100 == 0:
                self.logger.debug(
                    "Processed chunk %d: tone=%s, strength=%.3f, freq=%.1f Hz, confidence=%.3f",
                    self._chunks_processed,
                    tone_detected,
                    signal_strength,
                    dominant_freq,
                    confidence,
                )

        except Exception as e:
            self.logger.exception("Error processing audio chunk: %s", str(e))

    def _publish_processing_events(
        self,
        audio_data: np.ndarray,
        tone_detected: bool,
        signal_strength: float,
        dominant_freq: float,
        confidence: float,
    ) -> None:
        """Publish processing results as events.

        Args:
            audio_data: Processed audio data
            tone_detected: Whether tone was detected
            signal_strength: Signal strength (0-1)
            dominant_freq: Dominant frequency in Hz
            confidence: Detection confidence (0-1)
        """
        try:
            # Publish tone detection event
            tone_event = ToneDetectedEvent(
                detected=tone_detected,
                frequency=dominant_freq,
                confidence=confidence,
                snr_db=0.0,  # Could be enhanced with actual SNR calculation
                chunk_number=0,  # Could be enhanced with actual chunk counter
                detection_threshold=0.3,  # Standard threshold
            )
            self._event_bus.publish(tone_event)

            # Publish magnitude event for graphics
            magnitude_event = FilteredMagnitudeEvent(
                magnitude_norm=signal_strength,  # Normalized signal strength
                threshold_norm=0.25,  # Standard threshold
            )
            self._event_bus.publish(magnitude_event)

            # Publish audio chunk event
            chunk_event = AudioChunkEvent(
                chunk_data=audio_data,
                chunk_size_ms=20,  # Standard 20ms chunks
                sample_rate=44100,  # Could be made configurable
                chunk_number=0,  # Could be enhanced with actual counter
                has_more_data=self._is_running,
            )
            self._event_bus.publish(chunk_event)

        except Exception as e:
            self.logger.exception("Error publishing processing events: %s", str(e))

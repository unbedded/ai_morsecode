"""Component factory for creating configured instances.

This module provides a factory class that creates concrete implementations
of the protocol interfaces using configuration data. It serves as the bridge
between the configuration system and the component implementations.
"""

import logging
from typing import Any

from ..interfaces.audio import AudioSource
from ..interfaces.decoder import MorseDecoder
from ..interfaces.signal import SignalProcessor

logger = logging.getLogger(__name__)


class ComponentFactory:
    """Factory for creating configured component instances.

    This factory creates concrete implementations of the protocol interfaces
    using configuration dictionaries. It abstracts the creation process and
    allows for easy swapping of implementations.

    The factory uses the existing concrete classes from the legacy system
    but wraps them to work with the new protocol-based architecture.
    """

    def __init__(self) -> None:
        """Initialize the component factory."""
        self.logger = logging.getLogger(__name__)

    def create_audio_source(self, config: dict[str, Any]) -> AudioSource:
        """Create an audio source from configuration.

        Args:
            config: Audio configuration dictionary containing:
                - wav_filename: Path to WAV file (optional)
                - sample_rate_hz: Sample rate in Hz
                - chunk_size_ms: Chunk size in milliseconds

        Returns:
            AudioSource implementation configured with the given parameters.

        Raises:
            ValueError: If required configuration is missing or invalid.

        Example:
            ```python
            factory = ComponentFactory()
            config = {
                "wav_filename": "audio.wav",
                "sample_rate_hz": 44100,
                "chunk_size_ms": 20
            }
            audio_source = factory.create_audio_source(config)
            ```
        """
        try:
            # Import here to avoid circular imports
            from .audio.hal import HardwareAbstractionLayer

            self.logger.debug("Creating audio source with config: %s", config)

            # Create HAL instance with legacy config format
            hal_instance = HardwareAbstractionLayer(cfg_dict=config)

            # Wrap in adapter if needed (for now, return directly since HAL matches protocol)
            return AudioSourceAdapter(hal_instance)

        except Exception as e:
            self.logger.error("Failed to create audio source: %s", e)
            raise ValueError(f"Cannot create audio source: {e}") from e

    def create_signal_processor(self, config: dict[str, Any]) -> SignalProcessor:
        """Create a signal processor from configuration.

        Args:
            config: Signal processing configuration dictionary containing:
                - target_frequency_hz: Target frequency in Hz
                - detection_threshold: Detection threshold (0.0-1.0)
                - filter_bandwidth_hz: Filter bandwidth in Hz
                - sample_rate_hz: Sample rate in Hz

        Returns:
            SignalProcessor implementation configured with the given parameters.

        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        try:
            # Import here to avoid circular imports
            from .signal.signal_processor import SignalProcessor as LegacySignalProcessor

            self.logger.debug("Creating signal processor with config: %s", config)

            # Create processor instance with legacy config format
            processor_instance = LegacySignalProcessor(cfg_dict=config)

            # Wrap in adapter
            return SignalProcessorAdapter(processor_instance)

        except Exception as e:
            self.logger.error("Failed to create signal processor: %s", e)
            raise ValueError(f"Cannot create signal processor: {e}") from e

    def create_decoder(self, config: dict[str, Any]) -> MorseDecoder:
        """Create a Morse decoder from configuration.

        Args:
            config: Decoder configuration dictionary containing:
                - wpm_estimate: Initial WPM estimate
                - detection_tolerance: Timing tolerance (0.0-1.0)
                - dot_duration_ms: Dot duration override (optional)
                - min_silence_duration_ms: Minimum silence for word separation

        Returns:
            MorseDecoder implementation configured with the given parameters.

        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        try:
            # Import here to avoid circular imports
            from .decoder.morse_decoder import MorseDecoder as LegacyMorseDecoder

            self.logger.debug("Creating Morse decoder with config: %s", config)

            # Create decoder instance with legacy config format
            decoder_instance = LegacyMorseDecoder(cfg_dict=config)

            # Wrap in adapter
            return MorseDecoderAdapter(decoder_instance)

        except Exception as e:
            self.logger.error("Failed to create Morse decoder: %s", e)
            raise ValueError(f"Cannot create Morse decoder: {e}") from e


# Adapter classes to bridge legacy implementations with new protocols


class AudioSourceAdapter:
    """Adapter to make HardwareAbstractionLayer work with AudioSource protocol."""

    def __init__(self, hal_instance: Any) -> None:
        """Initialize adapter with HAL instance."""
        self._hal = hal_instance

    def has_data(self) -> bool:
        """Check if more audio data is available."""
        return self._hal.has_data()  # type: ignore[no-any-return]

    def get_next_chunk(self, duration_ms: int) -> Any:
        """Get next audio chunk."""
        return self._hal.get_next_chunk(update_interval_ms=duration_ms)

    def get_sample_rate(self) -> int:
        """Get sample rate."""
        # HAL doesn't expose this directly, so we'll use a reasonable default
        # In a full implementation, this should be exposed by HAL
        return getattr(self._hal, "sample_rate_hz", 44100)

    def get_total_duration_ms(self) -> float | None:
        """Get total duration if available."""
        # HAL doesn't expose this, return None for unknown duration
        return None


class SignalProcessorAdapter:
    """Adapter to make SignalProcessor work with new protocol."""

    def __init__(self, processor_instance: Any) -> None:
        """Initialize adapter with processor instance."""
        self._processor = processor_instance

    def detect_tone(self, audio_data: Any) -> bool:
        """Detect tone in audio data."""
        return self._processor.detect_tone(audio_data)  # type: ignore[no-any-return]

    def get_dominant_frequency(self, audio_data: Any) -> float:
        """Get dominant frequency."""
        # Legacy processor doesn't expose this, implement basic version
        return getattr(self._processor, "target_frequency_hz", 0.0)

    def get_signal_strength(self, audio_data: Any) -> float:
        """Get signal strength."""
        # Legacy processor doesn't expose this, return fixed value for now
        return 0.5

    def get_detection_confidence(self, audio_data: Any) -> float:
        """Get detection confidence."""
        # Legacy processor doesn't expose this, return fixed value for now
        return 0.8

    def get_target_frequency(self) -> float:
        """Get target frequency."""
        return getattr(self._processor, "target_frequency_hz", 600.0)


class MorseDecoderAdapter:
    """Adapter to make MorseDecoder work with new protocol."""

    def __init__(self, decoder_instance: Any) -> None:
        """Initialize adapter with decoder instance."""
        self._decoder = decoder_instance

    def process_detection(self, tone_detected: bool, duration_ms: float) -> None:
        """Process tone detection event."""
        self._decoder.process_tone_detection(tone_detected, duration_ms)

    def get_decoded_text(self) -> str:
        """Get decoded text."""
        return self._decoder.get_decoded_text()  # type: ignore[no-any-return]

    def finalize(self) -> None:
        """Finalize decoding."""
        self._decoder.finalize_decoding()

    def reset(self) -> None:
        """Reset decoder state."""
        # Legacy decoder doesn't have reset, would need to be added
        pass

    def get_statistics(self) -> dict[str, int | float]:
        """Get decoding statistics."""
        return {
            "characters_decoded": getattr(self._decoder, "_total_characters_decoded", 0),
            "dots_detected": getattr(self._decoder, "_total_dots_decoded", 0),
            "dashes_detected": getattr(self._decoder, "_total_dashes_decoded", 0),
            "words_decoded": 0,  # Not tracked by legacy decoder
            "estimated_wpm": getattr(self._decoder, "wpm_estimate", 15),
        }

    def set_wpm_estimate(self, wpm: float) -> None:
        """Set WPM estimate."""
        if wpm <= 0:
            raise ValueError(f"WPM must be positive, got {wpm}")
        self._decoder.wpm_estimate = int(wpm)  # Legacy decoder uses int
        # Recalculate dot duration if needed
        if hasattr(self._decoder, "dot_duration_ms"):
            self._decoder.dot_duration_ms = 1200.0 / wpm

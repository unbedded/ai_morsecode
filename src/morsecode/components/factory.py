"""Component factory for creating configured instances.

This module provides a factory class that creates concrete implementations
of the protocol interfaces using typed configuration objects. It serves as the bridge
between the configuration system and the component implementations.
"""

import logging
from typing import Any
from unittest.mock import MagicMock

from util.config.models import AudioConfig, DecoderConfig, SignalConfig

from ..interfaces.audio import AudioSource
from ..interfaces.decoder import MorseDecoder
from ..interfaces.signal import SignalProcessor

logger = logging.getLogger(__name__)


def create_mock_signal_config_manager(signal_config: SignalConfig) -> MagicMock:
    """Create mock config manager from SignalConfig."""
    from .signal.signal_config_keys import SignalCfgKey

    config_data = {
        SignalCfgKey.FREQUENCY: signal_config.frequency,
        SignalCfgKey.THRESHOLD: signal_config.threshold,
        SignalCfgKey.BANDWIDTH: signal_config.bandwidth,
        SignalCfgKey.SAMPLE_RATE: signal_config.sample_rate,
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
    mock_config_manager.register_enum_config = MagicMock()
    mock_config_manager.register_logging_config = MagicMock()
    return mock_config_manager


def create_mock_audio_config_manager(audio_config: AudioConfig) -> MagicMock:
    """Create mock config manager from AudioConfig."""
    from .audio.keys import CfgKey as AudioCfgKey

    config_data = {
        AudioCfgKey.SAMPLE_RATE: audio_config.sample_rate,
        AudioCfgKey.WAV_FILENAME: audio_config.wav_filename,
        AudioCfgKey.AUTO_GAIN_CONTROL: audio_config.auto_gain_control,
        AudioCfgKey.CHUNK_SIZE: audio_config.chunk_size_ms,
    }

    mock_config_manager = MagicMock()
    mock_section = MagicMock()

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
    from .decoder.keys import CfgKey as DecoderCfgKey

    config_data = {
        DecoderCfgKey.WPM: decoder_config.wpm,
        DecoderCfgKey.DOT_DURATION: decoder_config.dot_duration_ms,
        DecoderCfgKey.TOLERANCE: decoder_config.tolerance,
    }

    mock_config_manager = MagicMock()
    mock_section = MagicMock()

    def get_value(key):
        return config_data.get(key)

    mock_section.get_int.side_effect = lambda key: get_value(key)
    mock_section.get_double.side_effect = lambda key: get_value(key)
    mock_section.get_bool.side_effect = lambda key: get_value(key)
    mock_section.get_string.side_effect = lambda key: get_value(key)

    mock_config_manager.get_section.return_value = mock_section
    return mock_config_manager


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

    def create_audio_source(self, config: AudioConfig) -> AudioSource:
        """Create an audio source from configuration.

        Args:
            config: AudioConfig object with typed configuration parameters.

        Returns:
            AudioSource implementation configured with the given parameters.

        Raises:
            ValueError: If required configuration is missing or invalid.

        Example:
            ```python
            factory = ComponentFactory()
            config = AudioConfig(
                wav_filename="audio.wav",
                sample_rate=44100,
                chunk_size_ms=20
            )
            audio_source = factory.create_audio_source(config)
            ```
        """
        try:
            # Import here to avoid circular imports
            from .audio.hal import HardwareAbstractionLayer

            self.logger.debug("Creating audio source with typed config")

            # Create HAL instance with mock config manager (converted from typed config)
            audio_cfg_mgr = create_mock_audio_config_manager(config)
            hal_instance = HardwareAbstractionLayer(cfg_mgr=audio_cfg_mgr)

            # Wrap in adapter to match protocol interface
            return AudioSourceAdapter(hal_instance)

        except Exception as e:
            self.logger.error("Failed to create audio source: %s", e)
            raise ValueError(f"Cannot create audio source: {e}") from e

    def create_signal_processor(self, config: SignalConfig) -> SignalProcessor:
        """Create a signal processor from configuration.

        Args:
            config: SignalConfig object with typed configuration parameters.

        Returns:
            SignalProcessor implementation configured with the given parameters.

        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        try:
            # Import here to avoid circular imports
            from .signal.signal_processor import SignalProcessor as LegacySignalProcessor

            self.logger.debug("Creating signal processor with typed config")

            # Create mock config manager and use new unified constructor
            signal_cfg_mgr = create_mock_signal_config_manager(config)
            processor_instance = LegacySignalProcessor(cfg_mgr=signal_cfg_mgr)

            # Wrap in adapter
            return SignalProcessorAdapter(processor_instance)

        except Exception as e:
            self.logger.error("Failed to create signal processor: %s", e)
            raise ValueError(f"Cannot create signal processor: {e}") from e

    def create_decoder(self, config: DecoderConfig) -> MorseDecoder:
        """Create a Morse decoder from configuration.

        Args:
            config: DecoderConfig object with typed configuration parameters.

        Returns:
            MorseDecoder implementation configured with the given parameters.

        Raises:
            ValueError: If required configuration is missing or invalid.
        """
        try:
            # Import here to avoid circular imports
            from .decoder.morse_decoder import MorseDecoder as LegacyMorseDecoder

            self.logger.debug("Creating Morse decoder with typed config")

            # Create decoder instance with mock config manager (converted from typed config)
            decoder_cfg_mgr = create_mock_decoder_config_manager(config)
            decoder_instance = LegacyMorseDecoder(cfg_mgr=decoder_cfg_mgr)

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
        return float(getattr(self._processor, "target_frequency_hz", 0))

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
        return float(getattr(self._processor, "target_frequency_hz", 600))


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

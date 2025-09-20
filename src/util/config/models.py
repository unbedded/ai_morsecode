"""Pydantic-like configuration models for type-safe config access.

These models provide a typed interface to the AwesomeConfigManager system,
combining the benefits of YAML configuration with type safety and validation.
"""

import logging
from dataclasses import dataclass

from .config_manager import AwesomeConfigManager

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application-level configuration."""

    debug: bool = False
    log_level: str = "WARNING"
    output_file: str | None = None
    real_time: bool = False

    @classmethod
    def from_config_manager(cls, config_manager: AwesomeConfigManager) -> "AppConfig":
        """Create AppConfig from AwesomeConfigManager."""
        config_data = config_manager.get_config("app")
        return cls(**{k: v for k, v in config_data.items() if hasattr(cls, k)})


@dataclass
class AudioConfig:
    """Audio processing configuration."""

    sample_rate: int = 44100
    wav_filename: str | None = None
    auto_gain_control: bool = True
    chunk_size_ms: int = 50

    @classmethod
    def from_config_manager(cls, config_manager: AwesomeConfigManager) -> "AudioConfig":
        """Create AudioConfig from AwesomeConfigManager."""
        config_data = config_manager.get_config("audio")
        return cls(**{k: v for k, v in config_data.items() if hasattr(cls, k)})


@dataclass
class SignalConfig:
    """Signal processing configuration."""

    frequency_hz: int = 600  # Registry provides defaults, this is fallback only
    signal_threshold_norm: float = 0.25  # Optimized for real-world signals
    bandwidth_hz: int = 50
    sample_rate_hz: int = 44100
    adaptive_frequency: bool = True

    @classmethod
    def from_config_manager(cls, config_manager: AwesomeConfigManager) -> "SignalConfig":
        """Create SignalConfig from AwesomeConfigManager."""
        config_data = config_manager.get_config("signal")
        return cls(**{k: v for k, v in config_data.items() if hasattr(cls, k)})


@dataclass
class DecoderConfig:
    """Morse decoder configuration."""

    wpm: int = 20  # PARIS standard
    timing_tolerance_norm: float = 0.7  # Optimized for real-world timing variations
    dot_duration_ms: float | None = None
    min_silence_ms: float = 200.0

    @classmethod
    def from_config_manager(cls, config_manager: AwesomeConfigManager) -> "DecoderConfig":
        """Create DecoderConfig from AwesomeConfigManager."""
        config_data = config_manager.get_config("decoder")
        return cls(**{k: v for k, v in config_data.items() if hasattr(cls, k)})


@dataclass
class MorseConfig:
    """Complete Morse code decoder configuration."""

    app: AppConfig
    audio: AudioConfig
    signal: SignalConfig
    decoder: DecoderConfig

    @classmethod
    def from_config_manager(cls, config_manager: AwesomeConfigManager) -> "MorseConfig":
        """Create complete MorseConfig from AwesomeConfigManager."""
        return cls(
            app=AppConfig.from_config_manager(config_manager),
            audio=AudioConfig.from_config_manager(config_manager),
            signal=SignalConfig.from_config_manager(config_manager),
            decoder=DecoderConfig.from_config_manager(config_manager),
        )

    @classmethod
    def from_file(cls, config_file: str | None = None, profile: str | None = None) -> "MorseConfig":
        """Create MorseConfig directly from file."""
        config_manager = AwesomeConfigManager(config_file, profile)
        return cls.from_config_manager(config_manager)

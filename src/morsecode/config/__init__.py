"""Configuration package for Morse code decoder.

This package provides:
- AwesomeConfigManager: YAML-based configuration with JSON schema validation
- ConfigRegistry: Auto-discovery and schema generation
- Pydantic-like models for type-safe configuration access
"""

from .manager import AwesomeConfigManager, ConfigValidationError
from .models import AppConfig, AudioConfig, DecoderConfig, MorseConfig, SignalConfig
from .registry import ConfigRegistry

__all__ = [
    "AwesomeConfigManager",
    "ConfigValidationError",
    "ConfigRegistry",
    "AppConfig",
    "AudioConfig",
    "SignalConfig",
    "DecoderConfig",
    "MorseConfig",
]

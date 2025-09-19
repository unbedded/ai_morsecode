"""Universal Configuration System - Standalone utility package.

This package provides a reusable, type-safe configuration framework:
- AwesomeConfigManager: YAML-based configuration with enum-driven validation
- ConfigRegistry: Type-safe schema registration and validation
- CfgField/CfgType: Unit-aware field validation system
- Enum-based configuration keys for compile-time safety

Originally developed for Morse code decoder, but designed for universal use.
"""

from .config_manager import AwesomeConfigManager, ConfigValidationError
from .models import AppConfig, AudioConfig, DecoderConfig, MorseConfig, SignalConfig
from .registry import ConfigRegistry
from .types import CfgField, CfgType, enum_field

__all__ = [
    "AwesomeConfigManager",
    "ConfigValidationError",
    "ConfigRegistry",
    "AppConfig",
    "AudioConfig",
    "SignalConfig",
    "DecoderConfig",
    "MorseConfig",
    "CfgType",
    "CfgField",
    "enum_field",
]

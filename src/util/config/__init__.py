"""Universal Configuration System - Standalone utility package.

This package provides a reusable, type-safe configuration framework:
- AwesomeConfigManager: YAML-based configuration with enum-driven validation
- CfgField/CfgType: Unit-aware field validation system
- Enum-based configuration keys for compile-time safety
- ConfigurableBase: Inheritance pattern for components with runtime reconfiguration
- Components self-register their schemas - no central registry needed

Originally developed for Morse code decoder, but designed for universal use.
"""

from .config_manager import AwesomeConfigManager, ConfigValidationError
from .configurable_base import ConfigurableBase, IConfigurable
from .types import CfgField, CfgType, enum_field

__all__ = [
    "AwesomeConfigManager",
    "ConfigValidationError",
    "CfgType",
    "CfgField",
    "enum_field",
    "ConfigurableBase",
    "IConfigurable",
]

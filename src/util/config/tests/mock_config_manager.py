"""Mock AwesomeConfigManager for testing purposes.

This module provides a mock implementation of AwesomeConfigManager that can be used
in unit tests to avoid complex configuration setup while testing component behavior.
"""

from enum import Enum
from typing import Any


class MockConfigSection:
    """Mock configuration section that provides typed access methods."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    def get_int(self, key) -> int:
        """Get integer value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, 0)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return int(value)

    def get_double(self, key) -> float:
        """Get float value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, 0.0)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return float(value)

    def get_string(self, key) -> str:
        """Get string value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, "")
        return str(value)

    def get_bool(self, key) -> bool:
        """Get boolean value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str, False)
        return bool(value)

    def get_enum(self, key, enum_class):
        """Get enum value from config."""
        key_str = key.value if isinstance(key, Enum) else str(key)
        value = self.data.get(key_str)
        if isinstance(value, enum_class):
            return value
        # Try to convert string to enum
        if isinstance(value, str):
            try:
                return enum_class(value)
            except ValueError:
                return list(enum_class)[0]  # Return first enum value as default
        return list(enum_class)[0]  # Default to first enum value

    def get(self, key: str, default=None):
        """Get raw value from config."""
        return self.data.get(key, default)

    def apply_overrides(self, overrides: dict[str, Any]):
        """Apply configuration overrides to this section."""
        self.data.update(overrides)


class MockAwesomeConfigManager:
    """Mock implementation of AwesomeConfigManager for testing."""

    def __init__(self, configs: dict[str, dict[str, Any]] = None):
        """Initialize with optional predefined configurations."""
        self.configs = configs or {}
        self.schemas = {}

    def register_enum_config(self, section_name, schema):
        """Register an enum-based configuration schema."""
        section_key = section_name.value if isinstance(section_name, Enum) else str(section_name)
        self.schemas[section_key] = schema
        # Create default config if not provided
        if section_key not in self.configs:
            self.configs[section_key] = {}

    def register_logging_config(self, module_name: str, default_level: str = "INFO"):
        """Register logging configuration for a module."""
        # For testing, we just store this - real implementation would create schema
        logging_key = f"application.logging.{module_name}"
        if logging_key not in self.configs:
            self.configs[logging_key] = {"level": default_level}

    def get_section(self, section_name) -> MockConfigSection:
        """Get a config section."""
        section_key = section_name.value if isinstance(section_name, Enum) else str(section_name)
        config_data = self.configs.get(section_key, {})
        return MockConfigSection(config_data)



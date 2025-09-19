"""Registry-Based Configuration Manager with YAML + JSON Schema validation.

This module provides a simple, powerful config system that:
- Uses ConfigRegistry to auto-discover module requirements
- Uses single YAML file for all configuration
- Auto-creates default config if none exists
- Searches multiple default locations
- Validates against JSON schemas from registry
- Supports profile postfix overrides (e.g., setting_debug, setting_production)
- Provides excellent error handling and logging integration
"""

import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class AwesomeConfigManager:
    """Registry-based configuration manager with YAML files and JSON Schema validation."""

    def __init__(self, config_file: str | None = None, profile: str | None = None):
        """Initialize the registry-based configuration manager.

        Args:
            config_file: Path to YAML config file (searches default locations if None)
            profile: Profile name for postfix overrides (e.g., 'debug', 'production')
        """
        self.logger = logging.getLogger(__name__)
        self.config_file: Path
        self.was_created: bool = False  # Track if config was auto-created

        # Initialize ConfigRegistry for module discovery
        from .registry import ConfigRegistry

        self._registry = ConfigRegistry()

        self.config_file = self._resolve_config_file(config_file)
        self.profile = profile
        self._config_data: dict[str, Any] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

        # Load configuration
        self._load_config()

    def _resolve_config_file(self, config_file: str | None = None) -> Path:
        """Resolve configuration file path with fallback locations.

        Args:
            config_file: Explicit config file path, if provided

        Returns:
            Path to configuration file (creates default if none found)
        """
        if config_file:
            return Path(config_file)

        # Default search locations in priority order
        search_paths = [
            Path("morse.yaml"),  # Current directory (project-specific)
            Path.home() / ".config" / "morsecode" / "config.yaml",  # User config dir
            Path.home() / ".morse.yaml",  # User home (fallback)
        ]

        # Check if any existing config exists
        for path in search_paths:
            if path.exists():
                self.logger.debug("Found existing config at: %s", path)
                return path

        # No config found - create default in user config directory
        default_path = search_paths[1]  # ~/.config/morsecode/config.yaml
        self.logger.info("No configuration found, creating default at: %s", default_path)

        # Create directory if it doesn't exist
        default_path.parent.mkdir(parents=True, exist_ok=True)

        # Create sample config
        self._create_initial_config(default_path)
        self.was_created = True

        return default_path

    def _create_initial_config(self, config_path: Path) -> None:
        """Create an initial configuration file with registry-discovered defaults.

        Args:
            config_path: Path where to create the config file
        """
        # Use registry to create documented config file
        self._registry.create_sample_config(str(config_path))

        self.logger.info("Created initial configuration at: %s", config_path)

    def create_sample_config(self, output_file: str = "morse.yaml") -> None:
        """Create a comprehensive sample configuration with registry-discovered modules.

        Args:
            output_file: Path to output YAML file
        """
        # Delegate to registry for consistency
        self._registry.create_sample_config(output_file)
        self.logger.info("Sample configuration created: %s", output_file)

    def _load_config(self) -> None:
        """Load configuration from YAML file with error handling."""
        try:
            if self.config_file.exists():
                with open(self.config_file, encoding="utf-8") as f:
                    self._config_data = yaml.safe_load(f) or {}
                self.logger.info("Configuration loaded from: %s", self.config_file)
            else:
                self.logger.info("Config file not found, using defaults: %s", self.config_file)
                self._config_data = {}
        except Exception as e:
            self.logger.error("Failed to load config file %s: %s", self.config_file, e)
            self._config_data = {}

    def _load_schema(self, module_name: str) -> dict[str, Any]:
        """Load JSON schema for a module from ConfigRegistry.

        Args:
            module_name: Name of module (e.g., 'audio', 'signal', 'decoder', 'app')

        Returns:
            JSON schema as dictionary from registry
        """
        if module_name in self._schemas:
            return self._schemas[module_name]

        # Get schema from registry
        if (
            hasattr(self._registry, "_module_configs")
            and module_name in self._registry._module_configs
        ):
            schema = self._registry._module_configs[module_name]["schema"]
            self._schemas[module_name] = schema
            return schema
        else:
            # Handle app config (not in module registry)
            if module_name == "app":
                schema = {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "title": "App Configuration",
                    "type": "object",
                    "properties": {
                        "debug": {"type": "boolean"},
                        "log_level": {"type": "string"},
                        "output_file": {"type": ["string", "null"]},
                    },
                }
                self._schemas[module_name] = schema
                return schema

            self.logger.warning("No schema found for module: %s", module_name)
            return {}

    def _validate_against_schema(self, module_name: str, config: dict[str, Any]) -> None:
        """Validate configuration against JSON schema.

        Args:
            module_name: Module name for schema lookup
            config: Configuration dictionary to validate

        Raises:
            ConfigValidationError: If validation fails
        """
        schema = self._load_schema(module_name)
        if not schema:
            return  # Skip validation if schema not found

        # Simple validation - check types and ranges
        properties = schema.get("properties", {})
        for key, value in config.items():
            if key not in properties:
                continue

            prop_schema = properties[key]
            expected_type = prop_schema.get("type")

            # Type validation
            if expected_type:
                if isinstance(expected_type, list):
                    # Handle union types like ["string", "null"]
                    valid_types: list[type | tuple[type, ...]] = []
                    for t in expected_type:
                        if t == "string":
                            valid_types.append(str)
                        elif t == "integer":
                            valid_types.append(int)
                        elif t == "number":
                            valid_types.append((int, float))
                        elif t == "boolean":
                            valid_types.append(bool)
                        elif t == "null":
                            valid_types.append(type(None))

                    if not any(isinstance(value, vt) for vt in valid_types):
                        raise ConfigValidationError(
                            f"{module_name}.{key}: Expected {expected_type}, "
                            f"got {type(value).__name__}"
                        )
                else:
                    # Single type
                    if expected_type == "string" and not isinstance(value, str):
                        raise ConfigValidationError(
                            f"{module_name}.{key}: Expected string, got {type(value).__name__}"
                        )
                    elif expected_type == "integer" and not isinstance(value, int):
                        raise ConfigValidationError(
                            f"{module_name}.{key}: Expected integer, got {type(value).__name__}"
                        )
                    elif expected_type == "number" and not isinstance(value, int | float):
                        raise ConfigValidationError(
                            f"{module_name}.{key}: Expected number, got {type(value).__name__}"
                        )
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        raise ConfigValidationError(
                            f"{module_name}.{key}: Expected boolean, got {type(value).__name__}"
                        )

            # Range validation
            if isinstance(value, int | float):
                minimum = prop_schema.get("minimum")
                maximum = prop_schema.get("maximum")
                if minimum is not None and value < minimum:
                    raise ConfigValidationError(
                        f"{module_name}.{key}: Value {value} below minimum {minimum}"
                    )
                if maximum is not None and value > maximum:
                    raise ConfigValidationError(
                        f"{module_name}.{key}: Value {value} above maximum {maximum}"
                    )

            # Pattern validation (regex)
            if isinstance(value, str):
                pattern = prop_schema.get("pattern")
                if pattern and not re.match(pattern, value):
                    raise ConfigValidationError(
                        f"{module_name}.{key}: Value '{value}' doesn't match pattern '{pattern}'"
                    )

    def _get_defaults(self, module_name: str) -> dict[str, Any]:
        """Extract default values from schema.

        Args:
            module_name: Module name for schema lookup

        Returns:
            Dictionary of default values
        """
        schema = self._load_schema(module_name)
        defaults = {}

        properties = schema.get("properties", {})
        for key, prop_schema in properties.items():
            if "default" in prop_schema:
                defaults[key] = prop_schema["default"]

        return defaults

    def _apply_profile_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """Apply profile-specific overrides using postfix pattern.

        Args:
            config: Base configuration dictionary

        Returns:
            Configuration with profile overrides applied
        """
        if not self.profile:
            return config

        result = config.copy()
        postfix = f"_{self.profile}"

        # Look for keys with profile postfix
        for key, value in config.items():
            if key.endswith(postfix):
                # Remove postfix to get base key name
                base_key = key[: -len(postfix)]
                result[base_key] = value
                self.logger.debug("Applied profile override: %s = %s", base_key, value)
                # Remove the postfix key from result
                if key in result:
                    del result[key]

        return result

    def get_config(self, module_name: str) -> dict[str, Any]:
        """Get validated configuration for a module.

        Args:
            module_name: Name of module (e.g., 'audio', 'signal', 'decoder', 'app')

        Returns:
            Complete configuration dictionary with defaults + user overrides + profile overrides

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        try:
            # Start with defaults from schema
            config = self._get_defaults(module_name)

            # Apply user configuration from YAML file
            user_config = self._config_data.get(module_name, {})
            config.update(user_config)

            # Apply profile overrides (Phase 2)
            config = self._apply_profile_overrides(config)

            # Validate the final configuration
            self._validate_against_schema(module_name, config)

            self.logger.debug("Configuration for %s: %s", module_name, config)
            return config

        except ConfigValidationError:
            raise
        except Exception as e:
            self.logger.error("Unexpected error getting config for %s: %s", module_name, e)
            # Return defaults as fallback
            return self._get_defaults(module_name)

    def register_schema(self, section_name, schema_obj) -> None:
        """Register a schema for enum-based configuration.

        Args:
            section_name: Section name (enum or string)
            schema_obj: Schema dataclass with CfgField definitions
        """
        # Convert enum to string if needed
        section_str = section_name.value if hasattr(section_name, 'value') else str(section_name)

        # For now, just log the registration - full implementation would convert
        # the schema_obj to JSON schema and store it
        self.logger.debug("Schema registered for section '%s': %s", section_str, schema_obj)

        # Store the schema object for future use
        if not hasattr(self, '_enum_schemas'):
            self._enum_schemas = {}
        self._enum_schemas[section_str] = schema_obj

    def get_section(self, section_name):
        """Get a config section with enum-friendly access.

        Args:
            section_name: Section name (enum or string)

        Returns:
            ConfigSection object with get_int, get_double, get_enum methods
        """
        # Convert enum to string if needed
        section_str = section_name.value if hasattr(section_name, 'value') else str(section_name)

        # Get config data using existing method
        config_data = self.get_config(section_str)

        # Return wrapped section for enum-friendly access
        return ConfigSection(config_data, section_str, self.logger)


class ConfigSection:
    """Wrapper for config section data with type-safe access methods."""

    def __init__(self, config_data: dict, section_name: str, logger):
        """Initialize config section wrapper with data and logger."""
        self.config_data = config_data
        self.section_name = section_name
        self.logger = logger

    def get_int(self, key) -> int:
        """Get integer value using enum key."""
        key_str = key.value if hasattr(key, 'value') else str(key)
        value = self.config_data.get(key_str, 0)
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to convert %s.%s to int: %s", self.section_name, key_str, e)
            return 0

    def get_double(self, key) -> float:
        """Get double/float value using enum key."""
        key_str = key.value if hasattr(key, 'value') else str(key)
        value = self.config_data.get(key_str, 0.0)
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            self.logger.error("Failed to convert %s.%s to float: %s", self.section_name, key_str, e)
            return 0.0

    def get_string(self, key) -> str:
        """Get string value using enum key."""
        key_str = key.value if hasattr(key, 'value') else str(key)
        value = self.config_data.get(key_str, "")
        return str(value)

    def get_bool(self, key) -> bool:
        """Get boolean value using enum key."""
        key_str = key.value if hasattr(key, 'value') else str(key)
        value = self.config_data.get(key_str, False)
        if isinstance(value, bool):
            return value
        # Handle string representations
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', 'on', '1')
        return bool(value)

    def get_enum(self, key, enum_class):
        """Get enum value using enum key."""
        key_str = key.value if hasattr(key, 'value') else str(key)
        value_str = self.config_data.get(key_str, "")

        # Convert string to enum
        for enum_val in enum_class:
            if enum_val.value == value_str:
                return enum_val

        # Default to first enum value if not found
        default_val = list(enum_class)[0]
        self.logger.warning("Unknown enum value '%s' for %s.%s, using default: %s",
                           value_str, self.section_name, key_str, default_val.value)
        return default_val

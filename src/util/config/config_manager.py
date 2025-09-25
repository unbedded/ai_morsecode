"""YAML Configuration Manager with enum-based validation.

This module provides a clean, simple config system that:
- Uses XDG standard location: ~/.config/morsecode/config.yaml
- Auto-creates default config if none exists
- Override with --cfg-file for custom locations
- Validates against enum-based CfgField definitions
- Supports profile postfix overrides (e.g., setting_debug, setting_production)
- Provides excellent error handling and logging integration
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigSection:
    """Type-safe wrapper for configuration sections with enum-based access."""

    def __init__(self, config_data: dict[str, Any], section_name: str, schema_obj: Any = None):
        """Initialize configuration section wrapper.

        Args:
            config_data: Raw configuration dictionary
            section_name: Name of the configuration section
            schema_obj: Schema object with CfgField definitions for defaults
        """
        self._config_data = config_data.copy()
        self._section_name = section_name
        self._schema_obj = schema_obj
        self._logger = logging.getLogger(__name__)

    def get_int(self, key: Any) -> int:
        """Get integer value for configuration key.

        Args:
            key: Configuration key (enum or string)

        Returns:
            Integer configuration value

        Raises:
            ValueError: If value cannot be converted to int
            KeyError: If key doesn't exist and no schema default available
        """
        key_str = key.value if hasattr(key, "value") else str(key)

        # Try to get value from config data first
        value = None
        if key_str in self._config_data:
            value = self._config_data[key_str]
            # If value is explicitly None/null, treat as missing and use schema default
            if value is None:
                value = self._get_schema_default(key_str)
        else:
            # Fall back to schema default if available
            value = self._get_schema_default(key_str)

        if value is None:
            raise KeyError(
                f"Configuration key '{self._section_name}.{key_str}' not found and no schema default available"
            )

        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert {self._section_name}.{key_str}={value} to int") from e

    def get_double(self, key: Any) -> float:
        """Get float value for configuration key.

        Args:
            key: Configuration key (enum or string)

        Returns:
            Float configuration value

        Raises:
            ValueError: If value cannot be converted to float
            KeyError: If key doesn't exist and no schema default available
        """
        key_str = key.value if hasattr(key, "value") else str(key)

        # Try to get value from config data first
        value = None
        if key_str in self._config_data:
            value = self._config_data[key_str]
            # If value is explicitly None/null, treat as missing and use schema default
            if value is None:
                value = self._get_schema_default(key_str)
        else:
            # Fall back to schema default if available
            value = self._get_schema_default(key_str)

        if value is None:
            raise KeyError(
                f"Configuration key '{self._section_name}.{key_str}' not found and no schema default available"
            )

        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert {self._section_name}.{key_str}={value} to float") from e

    def get_float(self, key: Any) -> float:
        """Alias for get_double() for consistency with Python conventions."""
        return self.get_double(key)

    def get_string(self, key: Any) -> str:
        """Get string value for configuration key.

        Args:
            key: Configuration key (enum or string)

        Returns:
            String configuration value

        Raises:
            KeyError: If key doesn't exist and no schema default available
        """
        key_str = key.value if hasattr(key, "value") else str(key)

        # Try to get value from config data first
        if key_str in self._config_data:
            value = self._config_data[key_str]
        else:
            # Fall back to schema default if available
            value = self._get_schema_default(key_str)
            # Check if we have a schema but key is not found (different from None default)
            if value is None and self._schema_obj and not hasattr(self._schema_obj, key_str):
                raise KeyError(
                    f"Configuration key '{self._section_name}.{key_str}' not found and no schema default available"
                )

        return str(value) if value is not None else None

    def get_bool(self, key: Any) -> bool:
        """Get boolean value for configuration key.

        Args:
            key: Configuration key (enum or string)

        Returns:
            Boolean configuration value

        Raises:
            KeyError: If key doesn't exist and no schema default available
        """
        key_str = key.value if hasattr(key, "value") else str(key)

        # Try to get value from config data first
        value = None
        if key_str in self._config_data:
            value = self._config_data[key_str]
            # If value is explicitly None/null, treat as missing and use schema default
            if value is None:
                value = self._get_schema_default(key_str)
        else:
            # Fall back to schema default if available
            value = self._get_schema_default(key_str)

        if value is None:
            raise KeyError(
                f"Configuration key '{self._section_name}.{key_str}' not found and no schema default available"
            )

        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def get_enum(self, key: Any, enum_class: type) -> Any:
        """Get enum value for configuration key.

        Args:
            key: Configuration key (enum or string)
            enum_class: Enum class to convert string value to

        Returns:
            Enum value

        Raises:
            ValueError: If value is not a valid enum value
            KeyError: If key doesn't exist and no schema default available
        """
        key_str = key.value if hasattr(key, "value") else str(key)

        # Try to get value from config data first
        if key_str in self._config_data:
            value = self._config_data[key_str]
        else:
            # Fall back to schema default if available
            value = self._get_schema_default(key_str)
            # Check if we have a schema but key is not found (different from None default)
            if value is None and self._schema_obj and not hasattr(self._schema_obj, key_str):
                raise KeyError(
                    f"Configuration key '{self._section_name}.{key_str}' not found and no schema default available"
                )

        # Convert string value to enum
        if isinstance(value, enum_class):
            return value
        if isinstance(value, str):
            try:
                return enum_class(value)
            except ValueError as e:
                valid_values = [e.value for e in enum_class]
                raise ValueError(
                    f"Invalid enum value '{value}' for {self._section_name}.{key_str}. Valid values: {valid_values}"
                ) from e

        raise ValueError(f"Cannot convert {self._section_name}.{key_str}={value} to {enum_class.__name__}")

    def apply_overrides(self, overrides: dict[str, Any]) -> None:
        """Apply configuration overrides to this section.

        Args:
            overrides: Dictionary of configuration overrides
        """
        for key, value in overrides.items():
            self._config_data[key] = value
            self._logger.debug("Applied override: %s.%s = %s", self._section_name, key, value)

    def get_raw_dict(self) -> dict[str, Any]:
        """Get the raw configuration dictionary.

        Returns:
            Copy of the raw configuration data
        """
        return self._config_data.copy()

    def _get_schema_default(self, key_str: str) -> Any:
        """Get default value from schema for given key.

        Args:
            key_str: Configuration key string

        Returns:
            Default value from schema or None if not found
        """
        if not self._schema_obj:
            return None

        # Check if schema has this field with a default
        if hasattr(self._schema_obj, key_str):
            field_obj = getattr(self._schema_obj, key_str)
            if hasattr(field_obj, "default"):
                self._logger.debug(
                    "Using schema default for %s.%s = %s", self._section_name, key_str, field_obj.default
                )
                return field_obj.default

        return None


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class AwesomeConfigManager:
    """YAML configuration manager with enum-based field validation."""

    def __init__(self, config_file: str | None = None, profile: str | None = None):
        """Initialize configuration manager with automatic config discovery.

        Args:
            config_file: Optional path to config file (auto-detects if not provided)
            profile: Optional profile name for profile-specific overrides
        """
        self.logger = logging.getLogger(__name__)
        self.profile = profile
        self.was_created = False
        self._config_cache: dict[str, dict[str, Any]] = {}
        self._field_configs: dict[str, Any] = {}

        # No registry needed - components self-register their schemas

        # Find or create config file
        self.config_file = self._find_or_create_config(config_file)
        self.logger.debug("Using config file: %s", self.config_file)

        # Load the YAML config
        self._load_config()

    def _find_or_create_config(self, config_file: str | None) -> Path:
        """Find existing config with development/production mode selection."""
        if config_file:
            return Path(config_file)

        # Check for development mode setting to choose config location
        # Priority: project-local config (development) > XDG user config (production)
        project_config = Path("config/morse.yaml")
        user_config = Path.home() / ".config" / "morsecode" / "config.yaml"

        # If project-local config exists, use it (development mode)
        if project_config.exists():
            return project_config

        # Otherwise, use/create XDG user config (production mode)
        if not user_config.exists():
            self._create_initial_config(user_config)

        return user_config

    def _create_initial_config(self, config_path: Path) -> None:
        """Create initial configuration file and directory structure."""
        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create minimal application config template
        self._create_minimal_config(config_path)

        self.logger.info("Created initial configuration at: %s", config_path)

    def _create_minimal_config(self, config_path: Path) -> None:
        """Create minimal application config template."""
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("# Application Configuration\n")
            f.write("# Components will auto-register their schemas on first run\n")
            f.write("\n")
            f.write("application:\n")
            f.write("  debug: false\n")
            f.write('  log_level: "INFO"\n')
            f.write("  output_file: null\n")
            f.write("  \n")
            f.write("  # Development vs Production mode\n")
            f.write("  development_mode: true  # Set to false for embedded/production deployment\n")
            f.write("  \n")
            f.write("  # Embedded system logging (performance monitoring)\n")
            f.write("  log_to_file: true\n")
            f.write('  log_directory: "/var/log/morsecode"  # Falls back to ~/.local/share/morsecode/logs\n')
            f.write("  log_max_files: 10\n")
            f.write("  log_max_size_mb: 100\n")
            f.write("  \n")
            f.write("  # Per-component log level overrides\n")
            f.write("  logging: {}\n")
            f.write("\n")

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_file, encoding="utf-8") as f:
                self._raw_config = yaml.safe_load(f) or {}
                self.logger.debug("Loaded config from: %s", self.config_file)
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.logger.error("Failed to load config from %s: %s", self.config_file, e)
            self._raw_config = {}

    def get_config(self, module_name: str) -> dict[str, Any]:
        """Get configuration for a specific module with profile override support.

        Args:
            module_name: Name of the module/section

        Returns:
            Configuration dictionary for the module
        """
        if module_name in self._config_cache:
            return self._config_cache[module_name]

        # Get base config for module
        base_config: dict[str, Any] = self._raw_config.get(module_name, {}).copy()

        # Apply profile overrides if profile is specified
        if self.profile:
            self._apply_profile_overrides(module_name, base_config)

        # Cache and return
        self._config_cache[module_name] = base_config
        return base_config

    def get_section(self, section_name: str) -> ConfigSection:
        """Get configuration section wrapped in type-safe ConfigSection object.

        Args:
            section_name: Name of the section

        Returns:
            ConfigSection instance with typed access methods
        """
        config_data = self.get_config(section_name)
        schema_obj = self._field_configs.get(section_name)
        return ConfigSection(config_data, section_name, schema_obj)

    def register_logging_config(self, module_name: str, default_level: str = "INFO") -> None:
        """Register logging configuration for a module - does all the work automatically.

        This creates the schema and registers it so ComponentLogger can find it.

        Args:
            module_name: Full module name (typically __name__)
            default_level: Default log level for this module
        """
        from dataclasses import dataclass

        from util.config.types import CfgField, CfgType

        @dataclass
        class LoggingSchema:
            level = CfgField(
                type=CfgType.STRING, default=default_level, description=f"Log level for {module_name} module"
            )

        # Register under the path ComponentLogger expects: application.logging.module.name
        config_path = f"application.logging.{module_name}"
        self.register_enum_config(config_path, LoggingSchema)

    def create_sample_config(self, output_file: str) -> None:
        """Create a sample configuration file with default values.

        Args:
            output_file: Path where the sample config file should be created
        """
        from pathlib import Path

        # Ensure directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # TODO: Replace with schema-driven config generation
        # This hardcoded template was identified as technical debt during debugging sessions.
        # The new static registration architecture will generate config from component schemas.

        # For now, create a minimal config that will be replaced by schema-driven generation
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sample_config = f"""# Morse Code Decoder Configuration
# Generated: {timestamp}
# TODO: This will be replaced with schema-driven generation
#
# This file uses clear parameter names with unit suffixes for safety.
# All defaults are optimized for real-world morse code audio.
#
# Unit naming conventions:
#   *_hz = frequency units
#   *_norm = normalized values [0.0-1.0]
#   *_ms, *_sec = time units
#

application:
  debug: false              # Enable debug mode and verbose logging
  log_level: "INFO"         # Global log level
  output_file: null         # Output file path for decoded text

  # Per-component log level overrides for debugging
  logging: {{}}

# NOTE: Component-specific configurations will be generated from schemas
# when the new static registration architecture is implemented.
# For now, delete this file and let the system auto-create it from defaults.
"""

        # Write the sample config
        with open(output_file, "w") as f:
            f.write(sample_config)

    def _apply_profile_overrides(self, module_name: str, config: dict[str, Any]) -> None:
        """Apply profile-specific overrides to config.

        Args:
            module_name: Name of the module
            config: Base configuration to modify
        """
        module_config = self._raw_config.get(module_name, {})

        # Look for keys ending with profile suffix
        profile_suffix = f"_{self.profile}"
        for key, value in module_config.items():
            if key.endswith(profile_suffix):
                # Remove suffix to get base key name
                base_key = key[: -len(profile_suffix)]
                config[base_key] = value
                self.logger.debug("Applied profile override: %s.%s = %s", module_name, base_key, value)

    def register_enum_config(self, section_name: str, schema_obj: Any) -> None:
        """Register an enum-based configuration schema.

        Args:
            section_name: Configuration section name
            schema_obj: Schema dataclass with CfgField definitions
        """
        self.logger.debug("Enum config registered for section '%s'", section_name)
        self._field_configs[section_name] = schema_obj

    def validate_config(self) -> bool:
        """Validate the loaded configuration against registered field schemas.

        Returns:
            True if validation passes

        Raises:
            ConfigValidationError: If validation fails
        """
        errors = []

        for section_name, schema_obj in self._field_configs.items():
            section_config = self.get_config(section_name)

            # Basic validation - check required fields exist
            if hasattr(schema_obj, "__dataclass_fields__"):
                for field_name, _field_info in schema_obj.__dataclass_fields__.items():
                    if field_name not in section_config:
                        # Check if field has default or is nullable
                        field_obj = getattr(schema_obj, field_name, None)
                        if field_obj is not None and hasattr(field_obj, "default") and field_obj.default is not None:
                            continue  # Has default, OK
                        if field_obj is not None and hasattr(field_obj, "nullable") and field_obj.nullable:
                            continue  # Nullable, OK
                        errors.append(f"Missing required field: {section_name}.{field_name}")

        if errors:
            raise ConfigValidationError(f"Config validation failed: {'; '.join(errors)}")

        return True

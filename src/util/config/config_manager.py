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
            # Try to fall back to schema default for invalid values
            default_value = self._get_schema_default(key_str)
            if default_value is not None:
                self._logger.warning(
                    "Invalid value for %s.%s=%s, using schema default: %s",
                    self._section_name,
                    key_str,
                    value,
                    default_value,
                )
                return int(default_value)
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
            # Try to fall back to schema default for invalid values
            default_value = self._get_schema_default(key_str)
            if default_value is not None:
                self._logger.warning(
                    "Invalid value for %s.%s=%s, using schema default: %s",
                    self._section_name,
                    key_str,
                    value,
                    default_value,
                )
                return float(default_value)
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

        return str(value)

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
            lower_val = value.lower()
            if lower_val in ("true", "1", "yes", "on"):
                return True
            elif lower_val in ("false", "0", "no", "off"):
                return False
            else:
                # Invalid boolean string - try to fall back to schema default
                default_value = self._get_schema_default(key_str)
                if default_value is not None:
                    self._logger.warning(
                        "Invalid boolean value for %s.%s=%s, using schema default: %s",
                        self._section_name,
                        key_str,
                        value,
                        default_value,
                    )
                    return bool(default_value)
                # No schema default available, raise error
                raise ValueError(f"Cannot convert {self._section_name}.{key_str}={value} to bool")
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

        # Check if schema is a Pydantic BaseModel
        if hasattr(self._schema_obj, "model_fields"):
            model_fields = self._schema_obj.model_fields
            if key_str in model_fields:
                field_info = model_fields[key_str]
                # The default is a CfgField object in Pydantic models
                if hasattr(field_info, "default") and hasattr(field_info.default, "default"):
                    cfg_field = field_info.default
                    self._logger.debug(
                        "Using schema default for %s.%s = %s", self._section_name, key_str, cfg_field.default
                    )
                    return cfg_field.default

        # Check if schema has this field with a default (Pydantic dataclass style)
        if hasattr(self._schema_obj, "__dataclass_fields__"):
            dataclass_fields = self._schema_obj.__dataclass_fields__
            if key_str in dataclass_fields:
                field_info = dataclass_fields[key_str]
                # Get the actual CfgField from the schema class attribute
                cfg_field = getattr(self._schema_obj, key_str, None)
                if cfg_field and hasattr(cfg_field, "default"):
                    self._logger.debug(
                        "Using schema default for %s.%s = %s", self._section_name, key_str, cfg_field.default
                    )
                    return cfg_field.default

        # Fallback: Check if schema has this field as a direct attribute
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
        """Create minimal application config template with basic schema if available."""
        # If we have schemas registered, use them for a richer initial config
        if self._field_configs:
            self.logger.debug("Creating initial config from registered schemas")
            self.create_sample_config(str(config_path))
            return

        # Fallback to truly minimal config if no schemas are registered yet
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("# Application Configuration\n")
            f.write("# Components will auto-register their schemas on first run\n")
            f.write("# Run 'update_config_file_from_schemas()' to generate full config\n")
            f.write("\n")
            f.write("application:\n")
            f.write("  debug: false\n")
            f.write('  log_level: "INFO"\n')
            f.write("  output_file: null\n")
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

    def _format_field_comment(self, cfg_field, field_name: str) -> str:
        """Generate rich inline comment from CfgField metadata.

        Args:
            cfg_field: CfgField object with metadata
            field_name: Name of the field (for context)

        Returns:
            Formatted comment string with type, constraints, and default
        """
        parts = []

        # Description
        if cfg_field.description:
            parts.append(cfg_field.description)

        # Type info
        type_str = cfg_field.type.value.upper()
        parts.append(type_str)

        # Choices/Constraints
        if cfg_field.choices:
            if len(cfg_field.choices) <= 6:  # Short lists inline
                choices_str = ",".join(str(c) for c in cfg_field.choices)
                parts.append(f"{{{choices_str}}}")
            else:
                parts.append("multiple options")
        elif cfg_field.min is not None and cfg_field.max is not None:
            unit = f" {cfg_field.unit}" if cfg_field.unit else ""
            parts.append(f"{cfg_field.min}-{cfg_field.max}{unit}")
        elif cfg_field.unit:
            parts.append(cfg_field.unit)

        # Default value
        default_val = cfg_field.default
        if hasattr(default_val, "value"):  # Enum
            default_val = default_val.value
        elif default_val is None:
            default_val = "null"
        elif isinstance(default_val, str):
            default_val = f'"{default_val}"'

        parts.append(f"default: {default_val}")

        return " | ".join(parts)

    def _format_yaml_value(self, value) -> str:
        """Format a value for YAML output with proper quoting."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            # Quote strings that need it
            if value in ("true", "false", "null") or value.isdigit():
                return f'"{value}"'
            return value
        elif hasattr(value, "value"):  # Enum
            return f'"{value.value}"'
        else:
            return str(value)

    def _write_schema_driven_config(self, file_handle, complete_config: dict) -> None:
        """Write config with rich inline comments from schema metadata."""
        from datetime import datetime

        # Header
        file_handle.write("# Morse Code Decoder Configuration\n")
        file_handle.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file_handle.write("#\n")
        file_handle.write("# This file uses clear parameter names with unit suffixes for safety.\n")
        file_handle.write("# All defaults are optimized for real-world morse code audio.\n")
        file_handle.write("#\n")
        file_handle.write("# Unit naming conventions:\n")
        file_handle.write("#   *_hz = frequency units\n")
        file_handle.write("#   *_norm = normalized values [0.0-1.0]\n")
        file_handle.write("#   *_ms, *_sec = time units\n")
        file_handle.write("#\n\n")

        # Write each section with rich comments
        for section_name, section_data in complete_config.items():
            file_handle.write(f"{section_name}:\n")

            schema_class = self._field_configs.get(section_name)
            if not schema_class:
                # Fallback for sections without schemas
                for key, value in section_data.items():
                    formatted_value = self._format_yaml_value(value)
                    file_handle.write(f"  {key}: {formatted_value}\n")
                file_handle.write("\n")
                continue

            # Get schema fields for rich comments
            schema_fields = {}
            for attr_name in dir(schema_class):
                if not attr_name.startswith("_"):
                    attr_value = getattr(schema_class, attr_name, None)
                    if hasattr(attr_value, "default") and hasattr(attr_value, "type"):
                        schema_fields[attr_name] = attr_value

            # Write each field with comment
            for key, value in section_data.items():
                formatted_value = self._format_yaml_value(value)

                # Generate rich comment if we have schema info
                if key in schema_fields:
                    comment = self._format_field_comment(schema_fields[key], key)
                    # Format with proper spacing for readability
                    key_value = f"{key}: {formatted_value}"
                    padding = max(25 - len(key_value), 1)
                    file_handle.write(f"  {key_value}{' ' * padding}# {comment}\n")
                else:
                    # Fallback without comment
                    file_handle.write(f"  {key}: {formatted_value}\n")

            file_handle.write("\n")

    def update_config_file_from_schemas(self) -> None:
        """Update config file with all registered schemas and their defaults.

        This regenerates the YAML file to include any new fields added to schemas.
        Creates a backup of the existing config before updating.
        Uses rich inline comments from schema metadata.
        """
        from datetime import datetime
        from pathlib import Path

        # Create backup of existing config
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = Path(f"{self.config_file}.backup-{timestamp}")

        if Path(self.config_file).exists():
            import shutil

            shutil.copy(self.config_file, backup_path)
            self.logger.info("Created config backup: %s", backup_path)

        # Build complete config from all registered schemas
        complete_config = {}

        for section_name, schema_class in self._field_configs.items():
            section_config = {}

            # Get current values (preserves user customizations)
            current_section = self.get_config(section_name)

            # Iterate over class attributes to find CfgField objects
            for attr_name in dir(schema_class):
                # Skip private attributes and methods
                if attr_name.startswith("_"):
                    continue

                attr_value = getattr(schema_class, attr_name, None)

                # Check if this is a CfgField
                if hasattr(attr_value, "default") and hasattr(attr_value, "type"):
                    # Use current value if exists, otherwise use schema default
                    if attr_name in current_section:
                        value = current_section[attr_name]
                    else:
                        value = attr_value.default

                    # Convert enum values to their string representation for YAML
                    if hasattr(value, "value"):  # Enum objects have .value
                        value = value.value

                    section_config[attr_name] = value

            if section_config:
                complete_config[section_name] = section_config

        # Write updated config file with rich comments
        with open(self.config_file, "w", encoding="utf-8") as f:
            self._write_schema_driven_config(f, complete_config)

        self.logger.info("Updated config file with all registered schemas: %s", self.config_file)

        # Reload the updated config
        self._load_config()

    def create_sample_config(self, output_file: str) -> None:
        """Create a sample configuration file with default values from registered schemas.

        Args:
            output_file: Path where the sample config file should be created
        """
        from pathlib import Path

        # Ensure directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build complete config from all registered schemas
        complete_config = {}

        for section_name, schema_class in self._field_configs.items():
            section_config = {}

            # Iterate over class attributes to find CfgField objects
            for attr_name in dir(schema_class):
                # Skip private attributes and methods
                if attr_name.startswith("_"):
                    continue

                attr_value = getattr(schema_class, attr_name, None)

                # Check if this is a CfgField
                if hasattr(attr_value, "default") and hasattr(attr_value, "type"):
                    value = attr_value.default

                    # Convert enum values to their string representation for YAML
                    if hasattr(value, "value"):  # Enum objects have .value
                        value = value.value

                    section_config[attr_name] = value

            if section_config:
                complete_config[section_name] = section_config

        # Write sample config file with rich comments
        with open(output_file, "w", encoding="utf-8") as f:
            self._write_schema_driven_config(f, complete_config)

        self.logger.info("Created sample config with schema-driven generation: %s", output_file)

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
        """Register an enum-based configuration schema with automatic cleanup.

        Args:
            section_name: Configuration section name
            schema_obj: Schema dataclass with CfgField definitions

        This method automatically cleans stale/orphaned entries when schema is registered.
        Perfect timing: we have schema in hand and are touching the config anyway.
        """
        self.logger.debug("Enum config registered for section '%s'", section_name)
        self._field_configs[section_name] = schema_obj

        # 🧹 AUTOMATIC CLEANUP: Clean this section now that we have schema
        self._auto_clean_config_section(section_name, schema_obj)

    def apply_cli_overrides(self, cli_overrides: list[str]) -> dict[str, dict[str, Any]]:
        """Parse and apply CLI-style configuration overrides with flexible formats.

        Args:
            cli_overrides: List of CLI override strings in various formats

        Returns:
            Dictionary of parsed overrides in format {section: {key: value}}

        Raises:
            ValueError: If override format is invalid

        Supported formats:
            1. Single override per argument: ["signal-frequency-hz=800", "decoder-wpm=20"]
            2. Comma-separated: ["signal-frequency-hz=800,decoder-wpm=20"]
            3. Mixed formats: ["signal-frequency-hz=800", "decoder-wpm=20,application-debug=true"]

        Example usage:
            # Instead of: --cfg-override signal-frequency-hz=800 --cfg-override decoder-wpm=20
            # You can use: --cfg-override signal-frequency-hz=800,decoder-wpm=20
        """
        overrides: dict[str, dict[str, Any]] = {}

        # First, expand any comma-separated override strings
        expanded_overrides = []
        for override_str in cli_overrides:
            override_str = override_str.strip()
            if not override_str:
                continue

            # Support comma-separated overrides for convenience
            if "," in override_str and "=" in override_str:
                # Split by comma, but be careful not to split values that contain commas in quotes
                parts = []
                current_part = ""
                in_quotes = False
                quote_char = None

                for i, char in enumerate(override_str):
                    if char in ('"', "'") and (i == 0 or override_str[i - 1] != "\\"):
                        if not in_quotes:
                            in_quotes = True
                            quote_char = char
                        elif char == quote_char:
                            in_quotes = False
                            quote_char = None
                    elif char == "," and not in_quotes:
                        if current_part.strip():
                            parts.append(current_part.strip())
                        current_part = ""
                        continue
                    current_part += char

                if current_part.strip():
                    parts.append(current_part.strip())
                expanded_overrides.extend(parts)
            else:
                expanded_overrides.append(override_str)

        # Now process each individual override
        for override_str in expanded_overrides:
            override_str = override_str.strip()
            if not override_str:
                continue

            try:
                # Parse section-key=value format
                if "=" not in override_str:
                    raise ValueError(f"Invalid override format: {override_str} (expected: section-key=value)")

                section_key, value = override_str.split("=", 1)

                # Split section and key, handling multi-dash keys
                if "-" not in section_key:
                    raise ValueError(f"Invalid override format: {override_str} (expected: section-key=value)")

                parts = section_key.split("-")
                section = parts[0]
                key = "-".join(parts[1:]).replace("-", "_")  # Convert kebab-case to snake_case

                # Auto-convert common value types
                converted_value: Any = value
                if value.lower() in ("true", "false"):
                    converted_value = value.lower() == "true"
                elif value.lower() == "null":
                    converted_value = None
                else:
                    # Try to convert to number if possible
                    try:
                        if "." in value:
                            converted_value = float(value)
                        else:
                            converted_value = int(value)
                    except ValueError:
                        # Keep as string if not a number
                        converted_value = value

                # Store parsed override
                overrides.setdefault(section, {})[key] = converted_value

                # Log if logger is available (may not be in mocked tests)
                if hasattr(self, "logger") and self.logger:
                    self.logger.info(
                        "Parsed CLI override: %s.%s = %s (%s)",
                        section,
                        key,
                        converted_value,
                        type(converted_value).__name__,
                    )

            except Exception as e:
                raise ValueError(f"Failed to parse override '{override_str}': {e}") from e

        return overrides

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

    def _auto_clean_config_section(self, section_name: str, schema_obj: Any) -> None:
        """Automatically clean stale/orphaned entries from config section.

        This method removes:
        1. Stale fields: Keys that exist in config but not in current schema
        2. Orphaned profiles: Profile overrides for fields that no longer exist
        3. Invalid values: Values that don't match schema types (future enhancement)

        Args:
            section_name: Name of config section to clean
            schema_obj: Schema object with current field definitions
        """
        if section_name not in self._raw_config:
            self.logger.debug("No config section '%s' to clean", section_name)
            return

        current_section = self._raw_config[section_name].copy()
        valid_base_fields = set()

        # Extract valid field names from schema
        if hasattr(schema_obj, "__dataclass_fields__") and schema_obj.__dataclass_fields__:
            # Standard dataclass with populated fields
            valid_base_fields = set(schema_obj.__dataclass_fields__.keys())
        elif hasattr(schema_obj, "model_fields"):  # Pydantic models
            valid_base_fields = set(schema_obj.model_fields.keys())
        else:
            # Handle CfgField-based schemas (common pattern in this codebase)
            # These use @dataclass but with CfgField objects that don't populate __dataclass_fields__
            valid_base_fields = set()
            for attr_name in dir(schema_obj):
                if not attr_name.startswith("_"):
                    attr_value = getattr(schema_obj, attr_name)
                    # Check if it's a CfgField by looking for the 'type' attribute
                    if hasattr(attr_value, "type") and hasattr(attr_value, "default"):
                        valid_base_fields.add(attr_name)

            if not valid_base_fields:
                self.logger.warning("Cannot determine schema fields for section '%s'", section_name)
                return

        # Track what gets cleaned
        stale_fields = []
        orphaned_profiles = []

        # Check each key in current config
        for config_key in list(current_section.keys()):
            # First check if this is a regular schema field
            if config_key in valid_base_fields:
                continue  # Keep valid schema field

            # Check if this might be a profile override (contains underscore)
            if "_" in config_key:
                # Extract base field name (everything before last underscore)
                parts = config_key.split("_")
                base_field = "_".join(parts[:-1])

                # Valid profile override if base field exists in schema
                if base_field in valid_base_fields:
                    continue  # Keep valid profile override
                else:
                    # Orphaned profile override - base field removed from schema
                    orphaned_profiles.append(config_key)
                    del self._raw_config[section_name][config_key]
            else:
                # Regular field not in schema - stale entry
                stale_fields.append(config_key)
                del self._raw_config[section_name][config_key]

        # Log cleanup actions (ERROR level as requested by user)
        if stale_fields:
            self.logger.error(
                "🧹 Auto-cleanup removed %d stale fields from [%s]: %s",
                len(stale_fields),
                section_name,
                ", ".join(stale_fields),
            )

        if orphaned_profiles:
            self.logger.error(
                "🧹 Auto-cleanup removed %d orphaned profile overrides from [%s]: %s",
                len(orphaned_profiles),
                section_name,
                ", ".join(orphaned_profiles),
            )

        # Save cleaned config back to file if anything was removed
        if stale_fields or orphaned_profiles:
            self._save_config()
            self.logger.info("🧹 Auto-cleanup completed for [%s] - config file updated", section_name)

    def _save_config(self) -> None:
        """Save current config back to YAML file."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(self._raw_config, f, default_flow_style=False, sort_keys=False)
            self.logger.debug("Config saved to: %s", self.config_file)
        except Exception as e:
            self.logger.error("Failed to save config file %s: %s", self.config_file, e)

    def smart_reset_config(self) -> tuple[int, int]:
        """Reset configuration to schema defaults (true reset).

        This method:
        1. Resets ALL values to schema defaults
        2. Removes ALL profile overrides
        3. Creates a backup of the current config
        4. Behaves like deleting morse.yaml and starting fresh

        Returns:
            Tuple of (sections_reset, total_fields_reset)
        """
        import shutil
        from datetime import datetime

        self.logger.info("🔄 Resetting configuration to schema defaults...")

        # Create backup before reset
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = f"{self.config_file}.backup-{timestamp}"

        try:
            shutil.copy2(self.config_file, backup_file)
            self.logger.info("📁 Backup created: %s", backup_file)
        except Exception as e:
            self.logger.warning("Failed to create backup: %s", e)

        sections_reset = 0
        total_fields_reset = 0

        # Import and register all available schemas to get complete defaults
        self._register_all_schemas()

        # Reset each registered section to schema defaults
        for section_name, schema_obj in self._field_configs.items():
            section_defaults = self._extract_schema_defaults(schema_obj)

            if section_defaults:
                self._raw_config[section_name] = section_defaults.copy()
                sections_reset += 1
                total_fields_reset += len(section_defaults)
                self.logger.info("✅ Reset [%s] section: %d fields to defaults", section_name, len(section_defaults))

        # Remove any sections not covered by schemas
        schema_sections = set(self._field_configs.keys())
        config_sections = set(self._raw_config.keys())
        orphaned_sections = config_sections - schema_sections

        for section_name in orphaned_sections:
            del self._raw_config[section_name]
            self.logger.info("🗑️ Removed orphaned section: [%s]", section_name)

        # Save the reset configuration
        self._save_config()

        self.logger.info(
            "✅ Configuration reset complete: %d sections reset, %d total fields", sections_reset, total_fields_reset
        )
        return sections_reset, total_fields_reset

    def _register_all_schemas(self):
        """Register all available component schemas to ensure complete defaults."""
        try:
            # Import all component schemas to register them
            import importlib

            from morsecode.components.audio.schema import AudioSchema
            from morsecode.components.decoder.schema import DecoderSchema
            from morsecode.components.graphics.schema import GraphicsSchema
            from morsecode.components.signal.signal_config_schema import SignalConfigSchema as SignalSchema

            GlobalSchema = importlib.import_module("morsecode.components.global.schema").GlobalSchema

            # Register schemas if not already registered
            if "audio" not in self._field_configs:
                self.register_enum_config("audio", AudioSchema)
            if "signal" not in self._field_configs:
                self.register_enum_config("signal", SignalSchema)
            if "decoder" not in self._field_configs:
                self.register_enum_config("decoder", DecoderSchema)
            if "graphics" not in self._field_configs:
                self.register_enum_config("graphics", GraphicsSchema)
            if "global" not in self._field_configs:
                self.register_enum_config("global", GlobalSchema)

        except ImportError as e:
            self.logger.warning("Could not import all schemas for reset: %s", e)

    def _extract_schema_defaults(self, schema_obj) -> dict:
        """Extract default values from a schema object."""
        defaults = {}

        # Handle CfgField-based schemas (same detection logic as auto-cleanup)
        for attr_name in dir(schema_obj):
            if not attr_name.startswith("_"):
                attr_value = getattr(schema_obj, attr_name)
                # Check if it's a CfgField
                if hasattr(attr_value, "type") and hasattr(attr_value, "default"):
                    defaults[attr_name] = attr_value.default

        return defaults

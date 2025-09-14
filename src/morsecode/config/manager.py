"""Awesome Configuration Manager with YAML + JSON Schema validation.

This module provides a simple, powerful config system that:
- Uses single YAML file for all configuration
- Validates against JSON schemas
- Supports profile postfix overrides (e.g., setting_debug, setting_production)
- Provides excellent error handling and logging integration
"""

import json
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
    """Manages configuration with YAML files and JSON Schema validation."""

    def __init__(self, config_file: str | None = None, profile: str | None = None):
        """Initialize the configuration manager.

        Args:
            config_file: Path to YAML config file (default: ./morse.yaml)
            profile: Profile name for postfix overrides (e.g., 'debug', 'production')
        """
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file or "morse.yaml")
        self.profile = profile
        self._config_data: dict[str, Any] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

        # Load configuration
        self._load_config()

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
        """Load JSON schema for a module.

        Args:
            module_name: Name of module (e.g., 'audio', 'signal', 'decoder', 'app')

        Returns:
            JSON schema as dictionary
        """
        if module_name in self._schemas:
            return self._schemas[module_name]

        schema_path = Path(__file__).parent / module_name / "config.schema.json"
        try:
            with open(schema_path, encoding="utf-8") as f:
                schema: dict[str, Any] = json.load(f)
                self._schemas[module_name] = schema
                return schema
        except Exception as e:
            self.logger.error("Failed to load schema for %s: %s", module_name, e)
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

    def create_sample_config(self, output_file: str = "morse.yaml") -> None:
        """Create a sample configuration file with all defaults and documentation.

        Args:
            output_file: Path to output YAML file
        """
        sample_config = {}

        for module_name in ["app", "audio", "signal", "decoder"]:
            schema = self._load_schema(module_name)
            if not schema:
                continue

            module_config = {}
            properties = schema.get("properties", {})

            for key, prop_schema in properties.items():
                default_value = prop_schema.get("default")

                # Add the default value
                if default_value is not None:
                    module_config[key] = default_value

                # Add commented description (for documentation)
                # This is a simplified version - full implementation would need
                # a YAML library that preserves comments

            sample_config[module_name] = module_config

        # Write sample config
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False)

        self.logger.info("Sample configuration created: %s", output_file)

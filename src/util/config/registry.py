"""Configuration Registry - Auto-discovers and generates schemas from existing modules.

This module implements the registry pattern to automatically discover configuration
requirements from existing modules and generate schemas with proper documentation.
"""

import logging
from typing import Any

# NOTE: This registry implementation is legacy for schema generation
# In the new enum-based system, component schemas are defined declaratively
# in component-specific schema.py files.
from .config_manager import AwesomeConfigManager

logger = logging.getLogger(__name__)


class ConfigRegistry:
    """Registry that auto-discovers module config requirements and generates schemas."""

    def __init__(self) -> None:
        """Initialize the configuration registry."""
        self.logger = logging.getLogger(__name__)
        self._module_configs: dict[str, dict[str, Any]] = {}
        self._discover_modules()

    def _discover_modules(self) -> None:
        """Placeholder for legacy schema discovery.

        In the new enum-based config system, schemas are defined declaratively
        in component-specific schema.py files using CfgField definitions.
        This method is retained for backward compatibility.
        """
        # Legacy implementation disabled - components now use enum-based schemas
        self.logger.info("Legacy schema discovery disabled - using enum-based component schemas")

    def _infer_type_and_range(self, param_name: str, legacy_key: str) -> dict[str, Any]:
        """Infer JSON Schema type and range from parameter name and usage patterns.

        Args:
            param_name: New parameter name
            legacy_key: Legacy parameter name for context

        Returns:
            JSON Schema property definition with unit metadata
        """
        # Common patterns and their schemas with unit metadata
        if "bandwidth" in param_name.lower():
            return {"type": "integer", "minimum": 10, "maximum": 500, "default": 50, "unit": "Hz"}
        elif "frequency" in param_name.lower() or "hz" in legacy_key.lower():
            if "sample" in param_name.lower():
                return {"type": "integer", "minimum": 8000, "maximum": 96000, "default": 44100, "unit": "Hz"}
            else:  # CW frequency - registry owns this value, no external constants
                return {
                    "type": "integer",
                    "minimum": 200,
                    "maximum": 2000,
                    "default": 600,  # Registry as single source of truth
                    "unit": "Hz"
                }

        elif "threshold" in param_name.lower():
            return {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.3, "unit": "norm"}

        elif "wpm" in param_name.lower():
            return {"type": "integer", "minimum": 5, "maximum": 60, "default": 15, "unit": "wpm"}

        elif "tolerance" in param_name.lower():
            return {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.3, "unit": "norm"}

        elif "duration" in param_name.lower() or "ms" in param_name.lower():
            if "chunk" in param_name.lower():
                return {"type": "integer", "minimum": 10, "maximum": 1000, "default": 50, "unit": "ms"}
            elif "silence" in param_name.lower():
                return {"type": "number", "minimum": 50, "maximum": 2000, "default": 200, "unit": "ms"}
            else:  # dot duration
                return {"type": ["number", "null"], "minimum": 10, "maximum": 1000, "default": None, "unit": "ms"}

        elif "filename" in param_name.lower() or "file" in param_name.lower():
            return {"type": ["string", "null"], "default": None}

        elif "control" in param_name.lower() or param_name.startswith("auto_"):
            return {"type": "boolean", "default": True}

        else:
            # Generic fallback
            return {"type": "string", "default": ""}

    def _generate_schema(self, module_name: str, module_info: dict[str, Any]) -> None:
        """Generate JSON schema for a module.

        Args:
            module_name: Name of the module
            module_info: Module configuration information
        """
        properties = {}

        for param_name, (_yaml_key, legacy_key, description) in module_info[
            "config_mapping"
        ].items():
            # Infer type and constraints
            property_schema = self._infer_type_and_range(param_name, legacy_key)
            property_schema["description"] = description

            properties[param_name] = property_schema

        # Generate complete schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": f"{module_name.title()} Module Configuration",
            "description": module_info["description"],
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }

        self._module_configs[module_name] = {
            "schema": schema,
            "config_mapping": module_info["config_mapping"],
        }

        # Schema generation disabled - enum-based system uses component-specific schema.py files
        self.logger.debug("Legacy schema generation disabled for module: %s", module_name)

    def get_config_manager(
        self, config_file: str | None = None, profile: str | None = None
    ) -> AwesomeConfigManager:
        """Get a configured AwesomeConfigManager instance.

        Args:
            config_file: Path to configuration file
            profile: Profile name for overrides

        Returns:
            Configured AwesomeConfigManager instance
        """
        return AwesomeConfigManager(config_file, profile)

    def create_sample_config(self, output_file: str = "morse.yaml") -> None:
        """Create a comprehensive sample configuration with all discovered modules.

        Args:
            output_file: Path to output YAML file
        """
        self._write_documented_yaml(output_file)
        self.logger.info("Sample configuration created: %s", output_file)

    def _extract_unit_from_schema(self, schema_obj, field_name: str) -> str | None:
        """Extract unit metadata from CfgField schema object."""
        if hasattr(schema_obj, '__dataclass_fields__'):
            # Get the field from the dataclass
            field = getattr(schema_obj, field_name, None)
            if hasattr(field, 'unit'):
                return field.unit
        return None

    def _write_documented_yaml(self, output_file: str) -> None:
        """Write a self-documenting YAML configuration file with unit metadata."""
        from datetime import datetime

        with open(output_file, "w", encoding="utf-8") as f:
            # Header with timestamp
            f.write("# Morse Code Decoder Configuration\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# \n")
            f.write("# This file was auto-generated with comprehensive documentation.\n")
            f.write("# Edit values as needed - comments show valid ranges, units, and options.\n")
            f.write("# \n")
            f.write("# Unit naming conventions (enforced via unit metadata):\n")
            f.write("#   *_ms, *_sec, *_us = time units\n")
            f.write("#   *_hz = frequency units\n")
            f.write("#   *_norm = normalized values [0.0-1.0]\n")
            f.write("#   *_pct = percentage values [0-100]\n")
            f.write("# \n\n")

            # App config (hardcoded)
            f.write("app:\n")
            app_config = [
                ("debug", False, "Enable debug mode and verbose logging", "boolean"),
                ("log_level", "INFO", "Log level", "{DEBUG, INFO, WARNING, ERROR, CRITICAL}"),
                (
                    "output_file",
                    None,
                    "Output file path for decoded text (null = stdout)",
                    "string|null",
                ),
            ]

            for key, value, help_text, type_info in app_config:
                formatted_value = (
                    "null"
                    if value is None
                    else str(value).lower()
                    if isinstance(value, bool)
                    else f'"{value}"'
                    if isinstance(value, str)
                    else str(value)
                )
                if type_info.startswith("{"):
                    f.write(
                        f"  {key}: {formatted_value:<11} # {help_text} | Options: {type_info}\n"
                    )
                else:
                    f.write(f"  {key}: {formatted_value:<11} # {help_text} | Type: {type_info}\n")
            f.write("\n")

            # Add discovered module configs
            for module_name, module_info in self._module_configs.items():
                f.write(f"{module_name}:\n")
                schema_props = module_info["schema"]["properties"]

                for prop_name, prop_schema in schema_props.items():
                    default_value = prop_schema.get("default")
                    description = prop_schema.get("description", "")

                    # Format value
                    if default_value is None:
                        formatted_value = "null"
                    elif isinstance(default_value, bool):
                        formatted_value = str(default_value).lower()
                    elif isinstance(default_value, str):
                        formatted_value = f'"{default_value}"'
                    else:
                        formatted_value = str(default_value)

                    # Build help comment
                    help_parts = []
                    if description:
                        help_parts.append(description)

                    # Add type information (terse, all caps)
                    prop_type = prop_schema.get("type")
                    if isinstance(prop_type, list):
                        # Convert list types like ["string", "null"] to "STR|NULL"
                        type_parts = []
                        for t in prop_type:
                            if t == "integer":
                                type_parts.append("INT")
                            elif t == "number":
                                type_parts.append("FLOAT")
                            elif t == "string":
                                type_parts.append("STR")
                            elif t == "boolean":
                                type_parts.append("BOOL")
                            elif t == "null":
                                type_parts.append("NULL")
                            else:
                                type_parts.append(t.upper())
                        type_str = "|".join(type_parts)
                    else:
                        # Single type mapping
                        if prop_type == "integer":
                            type_str = "INT"
                        elif prop_type == "number":
                            type_str = "FLOAT"
                        elif prop_type == "string":
                            type_str = "STR"
                        elif prop_type == "boolean":
                            type_str = "BOOL"
                        else:
                            type_str = prop_type.upper() if prop_type else None

                    if type_str:
                        help_parts.append(type_str)

                    # Add unit metadata if available from schema objects
                    unit_info = prop_schema.get("unit")
                    if unit_info:
                        help_parts.append(f"({unit_info})")

                    # Add range info (terse) or regex for strings
                    if "pattern" in prop_schema:
                        # For strings with regex pattern
                        regex_pattern = prop_schema["pattern"]
                        help_parts.append(f"/{regex_pattern}/")
                    elif "minimum" in prop_schema and "maximum" in prop_schema:
                        # For numeric types with range
                        min_val = prop_schema["minimum"]
                        max_val = prop_schema["maximum"]
                        help_parts.append(f"[{min_val}-{max_val}]")

                    # Add enum choices (terse, quoted, all caps)
                    if "enum" in prop_schema:
                        enum_values = prop_schema["enum"]
                        quoted_values = [f'"{val}"' for val in enum_values]
                        choices_str = ", ".join(quoted_values)
                        help_parts.append(f"OPTION | {{{choices_str}}}")

                    help_text = " | ".join(help_parts) if help_parts else ""

                    f.write(f"  {prop_name}: {formatted_value:<7} # {help_text}\n")

                f.write("\n")

            # Add profile examples
            f.write("# Profile Examples:\n")
            f.write("# Use --profile debug to activate debug-specific overrides:\n")
            f.write("#   app:\n")
            f.write('#     log_level_debug: "DEBUG"     # Override for debug profile\n')
            f.write("#     debug_debug: true            # Enable debug mode in debug profile\n")
            f.write("# \n")
            f.write("# Use --profile production:\n")
            f.write("#   signal:\n")
            f.write("#     frequency_hz_production: 800 # Production frequency override\n")
            f.write("#     threshold_norm_production: 0.2 # Stricter threshold for production\n")
            f.write("\n")

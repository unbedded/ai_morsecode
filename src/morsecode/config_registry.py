"""Configuration Registry - Auto-discovers and generates schemas from existing modules.

This module implements the registry pattern to automatically discover configuration
requirements from existing modules and generate schemas with proper documentation.
"""

import logging
from pathlib import Path
from typing import Any

from .awesome_config import AwesomeConfigManager
from .hal import HardwareAbstractionLayer
from .morse_decoder import MorseDecoder
from .signal_processor import SignalProcessor

logger = logging.getLogger(__name__)


class ConfigRegistry:
    """Registry that auto-discovers module config requirements and generates schemas."""

    def __init__(self) -> None:
        """Initialize the configuration registry."""
        self.logger = logging.getLogger(__name__)
        self._module_configs: dict[str, dict[str, Any]] = {}
        self._discover_modules()

    def _discover_modules(self) -> None:
        """Automatically discover module configuration requirements."""
        # Map of module classes to their config keys and descriptions
        modules = {
            "audio": {
                "class": HardwareAbstractionLayer,
                "description": "Audio processing and hardware abstraction layer configuration",
                "config_mapping": {
                    "sample_rate": ("audio_rate_hz", "sample_rate_hz", "Audio sample rate in Hz"),
                    "wav_filename": ("wav_filename", "wav_filename", "Path to WAV audio file"),
                    "auto_gain_control": (
                        "auto_gain_control",
                        "auto_gain_control",
                        "Enable automatic gain control",
                    ),
                    "chunk_size_ms": (
                        "chunk_size_ms",
                        "chunk_size_ms",
                        "Audio chunk size in milliseconds",
                    ),
                },
            },
            "signal": {
                "class": SignalProcessor,
                "description": "Signal processing and tone detection configuration",
                "config_mapping": {
                    "frequency": (
                        "target_frequency_hz",
                        "target_frequency_hz",
                        "Target CW frequency in Hz for tone detection",
                    ),
                    "threshold": (
                        "detection_threshold",
                        "detection_threshold",
                        "Tone detection threshold (0.0-1.0)",
                    ),
                    "bandwidth": (
                        "filter_bandwidth_hz",
                        "filter_bandwidth_hz",
                        "Filter bandwidth in Hz",
                    ),
                    "sample_rate": ("sample_rate_hz", "sample_rate_hz", "Audio sample rate in Hz"),
                },
            },
            "decoder": {
                "class": MorseDecoder,
                "description": "Morse code pattern recognition and decoding configuration",
                "config_mapping": {
                    "wpm": (
                        "wpm_estimate",
                        "wpm_estimate",
                        "Initial WPM estimate for timing analysis",
                    ),
                    "tolerance": (
                        "detection_tolerance",
                        "detection_tolerance",
                        "Timing tolerance for pattern recognition",
                    ),
                    "dot_duration_ms": (
                        "dot_duration_ms",
                        "dot_duration_ms",
                        "Override dot duration in milliseconds",
                    ),
                    "min_silence_ms": (
                        "min_silence_duration_ms",
                        "min_silence_duration_ms",
                        "Minimum silence for word separation",
                    ),
                },
            },
        }

        for module_name, module_info in modules.items():
            self._generate_schema(module_name, module_info)

    def _infer_type_and_range(self, param_name: str, legacy_key: str) -> dict[str, Any]:
        """Infer JSON Schema type and range from parameter name and usage patterns.

        Args:
            param_name: New parameter name
            legacy_key: Legacy parameter name for context

        Returns:
            JSON Schema property definition
        """
        # Common patterns and their schemas
        if "bandwidth" in param_name.lower():
            return {"type": "integer", "minimum": 10, "maximum": 500, "default": 50}
        elif "frequency" in param_name.lower() or "hz" in legacy_key.lower():
            if "sample" in param_name.lower():
                return {"type": "integer", "minimum": 8000, "maximum": 96000, "default": 44100}
            else:  # CW frequency
                return {"type": "integer", "minimum": 200, "maximum": 2000, "default": 600}

        elif "threshold" in param_name.lower():
            return {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.3}

        elif "wpm" in param_name.lower():
            return {"type": "integer", "minimum": 5, "maximum": 60, "default": 15}

        elif "tolerance" in param_name.lower():
            return {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.3}

        elif "duration" in param_name.lower() or "ms" in param_name.lower():
            if "chunk" in param_name.lower():
                return {"type": "integer", "minimum": 10, "maximum": 1000, "default": 50}
            elif "silence" in param_name.lower():
                return {"type": "number", "minimum": 50, "maximum": 2000, "default": 200}
            else:  # dot duration
                return {"type": ["number", "null"], "minimum": 10, "maximum": 1000, "default": None}

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

        # Write schema to file
        schema_dir = Path(__file__).parent / module_name
        schema_dir.mkdir(exist_ok=True)
        schema_file = schema_dir / "config.schema.json"

        import json

        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)

        self.logger.debug("Generated schema for %s: %s", module_name, schema_file)

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

    def get_legacy_config(
        self, module_name: str, config_manager: AwesomeConfigManager, **overrides: Any
    ) -> dict[str, Any]:
        """Convert YAML config to legacy format for existing modules.

        Args:
            module_name: Name of module ('audio', 'signal', 'decoder')
            config_manager: Configured manager instance
            **overrides: Additional config overrides

        Returns:
            Dictionary in legacy format for existing modules
        """
        if module_name not in self._module_configs:
            raise ValueError(f"Unknown module: {module_name}")

        # Get YAML config
        yaml_config = config_manager.get_config(module_name)

        # Apply any overrides
        yaml_config.update(overrides)

        # Convert to legacy format using mapping
        legacy_config = {}
        mapping = self._module_configs[module_name]["config_mapping"]

        for yaml_key, (_, legacy_key, _) in mapping.items():
            if yaml_key in yaml_config:
                legacy_config[legacy_key] = yaml_config[yaml_key]

        return legacy_config

    def create_sample_config(self, output_file: str = "morse.yaml") -> None:
        """Create a comprehensive sample configuration with all discovered modules.

        Args:
            output_file: Path to output YAML file
        """
        import yaml

        sample_config = {}

        # Add app config (hardcoded for now)
        sample_config["app"] = {
            "debug": False,
            "log_level": "WARNING",
            "output_file": None,
            "real_time": False,
        }

        # Add discovered module configs
        for module_name, module_info in self._module_configs.items():
            module_config = {}
            schema_props = module_info["schema"]["properties"]

            for prop_name, prop_schema in schema_props.items():
                default_value = prop_schema.get("default")
                if default_value is not None:
                    module_config[prop_name] = default_value

            sample_config[module_name] = module_config

        # Write YAML file with comments
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Morse Code Decoder Configuration\n")
            f.write("# Auto-generated from module registry\n\n")

            for module_name, module_config in sample_config.items():
                f.write(f"# {module_name.title()} Configuration\n")
                if module_name in self._module_configs:
                    f.write(f"# {self._module_configs[module_name]['schema']['description']}\n")
                f.write(f"{module_name}:\n")

                for key, value in module_config.items():
                    # Add description as comment
                    if module_name in self._module_configs:
                        props = self._module_configs[module_name]["schema"]["properties"]
                        if key in props:
                            desc = props[key].get("description", "")
                            if desc:
                                f.write(f"  # {desc}\n")

                    f.write(f"  {key}: {yaml.dump(value).strip()}\n")
                f.write("\n")

        self.logger.info("Sample configuration created: %s", output_file)

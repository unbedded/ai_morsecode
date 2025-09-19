"""YAML Configuration Manager with enum-based validation.

This module provides a clean, simple config system that:
- Uses ConfigRegistry for config file generation
- Uses single YAML file for all configuration
- Auto-creates default config if none exists
- Searches multiple default locations
- Validates against enum-based CfgField definitions
- Supports profile postfix overrides (e.g., setting_debug, setting_production)
- Provides excellent error handling and logging integration
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


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
        """Find existing config or create new one in appropriate location."""
        if config_file:
            return Path(config_file)

        # Default search locations in priority order
        search_paths = [
            Path("config/config.yaml"),  # Current directory (project-specific)
            Path.home() / ".config" / "app" / "config.yaml",  # User config dir
            Path.home() / ".config.yaml",  # User home (fallback)
        ]

        # Check if any existing config exists
        for path in search_paths:
            if path.exists():
                return path

        # No config found - create new one in first location
        config_path = search_paths[0]
        self._create_initial_config(config_path)
        return config_path

    def _create_initial_config(self, config_path: Path) -> None:
        """Create initial configuration file using registry."""
        # Ensure directory exists
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

    def get_section(self, section_name: str) -> dict[str, Any]:
        """Get configuration section (alias for get_config for backward compatibility).

        Args:
            section_name: Name of the section

        Returns:
            Configuration dictionary for the section
        """
        return self.get_config(section_name)

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

        # Create a basic sample configuration
        sample_config = """# Morse Code Decoder Configuration
# Generated sample configuration - edit as needed

# Signal processing configuration
signal:
  frequency: 600          # Target CW frequency in Hz [200-2000]
  threshold: 0.3          # Detection threshold [0.0-1.0]
  bandwidth: 50           # Filter bandwidth in Hz [10-500]
  sample_rate: 44100      # Audio sample rate in Hz [8000-96000]
  mode: "AUTO"           # Processing mode ["AUTO", "MANUAL", "ADAPTIVE"]

# Audio input configuration
audio:
  sample_rate: 44100      # Audio sample rate in Hz [8000-96000]
  wav_filename: null      # WAV file path (null for microphone input)
  auto_gain_control: false # Enable automatic gain control
  chunk_size: 50          # Audio chunk size in ms [10-1000]

# Morse decoder configuration
decoder:
  wpm: 20                 # Words per minute estimate [5-50]
  dot_duration: 60.0      # Dot duration in ms [10.0-500.0]
  tolerance: 0.3          # Timing tolerance [0.0-1.0]

# Global application settings
global:
  debug: false            # Enable debug mode
  log_level: "INFO"       # Logging level ["DEBUG", "INFO", "WARN", "ERROR"]
  output_file: null       # Output file path (null for stdout)
  profile: "default"      # Configuration profile name

# Application logging (per-module log levels)
application:
  logging:
    # Example: Set specific modules to DEBUG
    # morsecode.components.signal.signal_processor: "DEBUG"
    # morsecode.components.decoder.morse_decoder: "DEBUG"
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

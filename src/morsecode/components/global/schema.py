"""Global application configuration schema."""

from dataclasses import dataclass

from util.config.types import CfgField, CfgType, string_choices_field


@dataclass
class ConfigSchema:
    """Global application configuration schema."""

    debug = CfgField(type=CfgType.BOOL, default=False, description="Enable debug mode and verbose logging")

    log_level = string_choices_field(
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        description_prefix="Global application log level",
    )

    output_file = CfgField(
        type=CfgType.STRING, default=None, description="Output file for decoded text (None = stdout)"
    )

    profile = CfgField(
        type=CfgType.STRING, default=None, description="Configuration profile name for environment-specific settings"
    )

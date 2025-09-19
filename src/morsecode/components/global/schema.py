"""Global application configuration schema."""

from dataclasses import dataclass

from util.config.types import CfgField, CfgType


@dataclass
class ConfigSchema:
    """Global application configuration schema."""

    debug = CfgField(type=CfgType.BOOL, default=False, description="Enable debug mode and verbose logging")

    log_level = CfgField(
        type=CfgType.STRING,
        default="INFO",
        regex=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level for the application",
    )

    output_file = CfgField(
        type=CfgType.STRING, default=None, description="Output file for decoded text (None = stdout)"
    )

    profile = CfgField(
        type=CfgType.STRING, default=None, description="Configuration profile name for environment-specific settings"
    )

"""Audio component configuration schema with enum-based auto-descriptions."""

from dataclasses import dataclass

from util.config.types import CfgField, CfgType


@dataclass
class ConfigSchema:
    """Clean struct-like schema for Audio component configuration."""

    sample_hz = CfgField(
        type=CfgType.INT, default=44100, min=8000, max=96000, unit="Hz", description="Audio sample rate"
    )

    wav_filename = CfgField(
        type=CfgType.STRING, default=None, nullable=True, regex=r".*\.(wav|mp3|flac)$", description="Audio file path"
    )

    auto_gain_control = CfgField(type=CfgType.BOOL, default=True, description="Enable automatic gain control")

    chunk_size = CfgField(type=CfgType.INT, default=50, min=10, max=1000, unit="ms", description="Audio chunk size")

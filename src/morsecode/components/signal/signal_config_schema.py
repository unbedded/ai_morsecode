"""Signal processor configuration schema with enum-based auto-descriptions."""

from dataclasses import dataclass
from enum import Enum

from util.config.types import CfgField, CfgType, enum_field


class SignalMode(Enum):
    """Signal processing modes."""

    AUTO = "AUTO"
    MANUAL = "MANUAL"
    ADAPTIVE = "ADAPTIVE"


@dataclass
class SignalConfigSchema:
    """Clean struct-like schema for SignalProcessor configuration."""

    frequency = CfgField(
        type=CfgType.INT,
        default=600,
        min=200,
        max=2000,
        unit="Hz",
        description="Target CW frequency for tone detection",
    )

    threshold = CfgField(
        type=CfgType.DOUBLE,
        default=0.3,
        min=0.0,
        max=1.0,
        unit="norm",
        description="Tone detection threshold (0.0-1.0)",
    )

    bandwidth = CfgField(type=CfgType.INT, default=50, min=10, max=500, unit="Hz", description="Filter bandwidth")

    sample_hz = CfgField(
        type=CfgType.INT, default=44100, min=8000, max=96000, unit="Hz", description="Audio sample rate"
    )

    # Auto-generated description from enum values!
    mode = enum_field(SignalMode, SignalMode.AUTO, prefix="Signal processing mode")
    # Result: "Signal processing mode: AUTO, MANUAL, ADAPTIVE"

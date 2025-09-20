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

    frequency_hz = CfgField(
        type=CfgType.INT,
        default=600,
        min=200,
        max=2000,
        unit="Hz",
        description="Target CW frequency for tone detection",
    )

    signal_threshold_norm = CfgField(
        type=CfgType.DOUBLE,
        default=0.25,
        min=0.0,
        max=1.0,
        unit="norm",
        description="Signal detection threshold: minimum energy level to detect CW tone presence",
    )

    bandwidth_hz = CfgField(type=CfgType.INT, default=50, min=10, max=500, unit="Hz", description="Filter bandwidth")

    sample_rate_hz = CfgField(
        type=CfgType.INT, default=44100, min=8000, max=96000, unit="Hz", description="Audio sample rate"
    )

    # Auto-generated description from enum values!
    mode = enum_field(SignalMode, SignalMode.AUTO, prefix="Signal processing mode")
    # Result: "Signal processing mode: AUTO, MANUAL, ADAPTIVE"

    adaptive_frequency = CfgField(
        type=CfgType.BOOL,
        default=True,
        description="Enable adaptive frequency detection (auto-detect strongest frequency peak)",
    )

    # Critical missing parameters from old config
    cutoff_hz = CfgField(
        type=CfgType.DOUBLE,
        default=15.0,
        min=1.0,
        max=100.0,
        unit="Hz",
        description="Lowpass filter cutoff frequency for timing smoothing (critical for real-world audio)",
    )

    cw_mag_thresh_seconds = CfgField(
        type=CfgType.DOUBLE,
        default=0.1,
        min=0.01,
        max=1.0,
        unit="seconds",
        description="Minimum signal duration to count as valid tone (prevents noise spikes)",
    )

    cw_peak_ratio_threshold = CfgField(
        type=CfgType.INT,
        default=4,
        min=2,
        max=20,
        unit="ratio",
        description="Signal-to-noise ratio threshold for tone detection",
    )

    n_move_avg_elements = CfgField(
        type=CfgType.INT,
        default=6,
        min=1,
        max=20,
        unit="count",
        description="Moving average smoothing window size for signal processing",
    )

    rolling_buffer_seconds = CfgField(
        type=CfgType.DOUBLE,
        default=3.0,
        min=0.5,
        max=10.0,
        unit="seconds",
        description="Signal analysis buffer duration for statistics",
    )

    freq_range_min = CfgField(
        type=CfgType.INT,
        default=200,
        min=50,
        max=1000,
        unit="Hz",
        description="Minimum frequency for signal detection range",
    )

    freq_range_max = CfgField(
        type=CfgType.INT,
        default=1000,
        min=500,
        max=3000,
        unit="Hz",
        description="Maximum frequency for signal detection range",
    )

    fft_window_size = CfgField(
        type=CfgType.INT,
        default=1024,
        min=256,
        max=4096,
        unit="samples",
        description="FFT window size for frequency analysis (power of 2)",
    )

    noise_floor_db = CfgField(
        type=CfgType.INT,
        default=-40,
        min=-80,
        max=-10,
        unit="dB",
        description="Noise floor threshold for signal detection",
    )

"""Signal processor configuration keys - enum-based for auto-complete and type safety."""

from enum import Enum


class SignalCfgKey(Enum):
    """Config keys for SignalProcessor - auto-complete friendly!"""

    FREQUENCY_HZ = "frequency_hz"
    SIGNAL_THRESHOLD_NORM = "signal_threshold_norm"
    BANDWIDTH_HZ = "bandwidth_hz"
    SAMPLE_RATE_HZ = "sample_rate_hz"
    MODE = "mode"
    ADAPTIVE_FREQUENCY = "adaptive_frequency"

    # Critical missing parameters from old config
    CUTOFF_HZ = "cutoff_hz"
    CW_MAG_THRESH_SECONDS = "cw_mag_thresh_seconds"
    CW_PEAK_RATIO_THRESHOLD = "cw_peak_ratio_threshold"
    N_MOVE_AVG_ELEMENTS = "n_move_avg_elements"
    ROLLING_BUFFER_SECONDS = "rolling_buffer_seconds"
    FREQ_RANGE_MIN = "freq_range_min"
    FREQ_RANGE_MAX = "freq_range_max"


class SignalCfgSection(Enum):
    """Section names for signal configuration."""

    SIGNAL = "signal"

"""Signal processor configuration keys - enum-based for auto-complete and type safety."""

from enum import Enum


class SignalCfgKey(Enum):
    """Config keys for SignalProcessor - auto-complete friendly!"""
    FREQUENCY = "frequency"
    THRESHOLD = "threshold"
    BANDWIDTH = "bandwidth"
    SAMPLE_RATE = "sample_rate"
    MODE = "mode"


class SignalCfgSection(Enum):
    """Section names for signal configuration."""
    SIGNAL = "signal"

"""Time axis configuration for sample-based data plotting.

Ported from util/graphics/ascii_axes.py with enhanced features for UILT.
Handles conversion from sample indices to time values for X-axis display.
Designed for efficiency and C++ porting compatibility.
"""


class TimeAxis:
    """Time axis configuration for sample-based data plotting.

    Handles conversion from sample indices to time values for X-axis display.
    Designed for efficiency and C++ porting compatibility.
    """

    def __init__(self, sample_period_sec: float, start_time_sec: float = 0.0):
        """Initialize time axis configuration.

        Args:
            sample_period_sec: Time between samples in seconds (1/sample_rate_hz)
            start_time_sec: Starting time offset in seconds
        """
        self.sample_period_sec = sample_period_sec
        self.start_time_sec = start_time_sec
        self.sample_rate_hz = 1.0 / sample_period_sec

    def sample_to_time(self, sample_index: int) -> float:
        """Convert sample index to time value.

        Args:
            sample_index: Zero-based sample index

        Returns:
            Time in seconds
        """
        return self.start_time_sec + (sample_index * self.sample_period_sec)

    def time_to_sample(self, time_sec: float) -> int:
        """Convert time value to sample index.

        Args:
            time_sec: Time in seconds

        Returns:
            Sample index (rounded to nearest integer)
        """
        return int(round((time_sec - self.start_time_sec) / self.sample_period_sec))

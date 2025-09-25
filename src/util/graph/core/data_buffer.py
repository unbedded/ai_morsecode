"""Efficient data buffer optimized for different data types and C++ porting.

Ported from util/graphics/ascii_axes.py with enhancements for UILT architecture.
Performance characteristics:
- list[float]: Fast for <1K points, no dependencies, C++-friendly
- numpy arrays: Better for >1K points, vectorized operations
- deque: Good for streaming/real-time data with fixed size

C++ Porting Notes:
- list[float] maps directly to std::vector<double>
- numpy arrays require additional conversion layer
- Time-axis abstraction separates data from timing concerns
"""

from collections import deque
from typing import Union

from .time_axis import TimeAxis

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


class DataBuffer:
    """Efficient data buffer optimized for different data types and C++ porting.

    Performance characteristics:
    - list[float]: Fast for <1K points, no dependencies, C++-friendly
    - numpy arrays: Better for >1K points, vectorized operations
    - deque: Good for streaming/real-time data with fixed size

    C++ Porting Notes:
    - list[float] maps directly to std::vector<double>
    - numpy arrays require additional conversion layer
    - Time-axis abstraction separates data from timing concerns
    """

    def __init__(self, data: Union[list[float], deque, "np.ndarray"], time_axis: TimeAxis | None = None):
        """Initialize data buffer with type auto-detection.

        Args:
            data: Raw data values
            time_axis: Optional time axis for sample-to-time conversion
        """
        self.data = data
        self.time_axis = time_axis
        self._data_type = self._detect_data_type(data)

    def _detect_data_type(self, data) -> str:
        """Auto-detect data type for optimal processing."""
        if isinstance(data, list):
            return "list"
        elif isinstance(data, deque):
            return "deque"
        elif HAS_NUMPY and isinstance(data, np.ndarray):
            return "numpy"
        else:
            return "unknown"

    def get_values(self) -> list[float]:
        """Get data values as list[float] for consistent interface.

        This method ensures C++ compatibility by always returning
        a simple list that maps directly to std::vector<double>.
        """
        if self._data_type == "list":
            return self.data
        elif self._data_type == "deque":
            return list(self.data)
        elif self._data_type == "numpy":
            return self.data.tolist()
        else:
            # Fallback: try to convert to list
            return list(self.data)

    def get_time_axis(self) -> TimeAxis | None:
        """Get the time axis associated with this buffer.

        Returns:
            TimeAxis object or None if no time axis is set
        """
        return self.time_axis

    def get_time_values(self, max_points: int | None = None) -> list[float]:
        """Get time values for X-axis display.

        Args:
            max_points: Optional limit for downsampling

        Returns:
            List of time values in seconds
        """
        if not self.time_axis:
            # No time axis: use sample indices
            values = self.get_values()
            if max_points and len(values) > max_points:
                # Simple downsampling for display
                step = len(values) // max_points
                return [float(i) for i in range(0, len(values), step)]
            else:
                return [float(i) for i in range(len(values))]

        # Convert sample indices to time values
        values = self.get_values()
        if max_points and len(values) > max_points:
            # Downsample while preserving time accuracy
            step = len(values) // max_points
            return [self.time_axis.sample_to_time(i) for i in range(0, len(values), step)]
        else:
            return [self.time_axis.sample_to_time(i) for i in range(len(values))]

    def downsample_for_display(self, target_width: int) -> tuple[list[float], list[float]]:
        """Downsample data for ASCII display width.

        Args:
            target_width: Target width in characters

        Returns:
            Tuple of (time_values, data_values) downsampled to target_width
        """
        values = self.get_values()
        if len(values) <= target_width:
            # No downsampling needed
            return self.get_time_values(), values

        # Simple decimation for now (could be improved with anti-aliasing)
        step = len(values) // target_width
        downsampled_data = [values[i] for i in range(0, len(values), step)]
        downsampled_time = self.get_time_values(target_width)

        return downsampled_time[: len(downsampled_data)], downsampled_data

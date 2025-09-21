"""Pure ASCII backend implementation with matplotlib-like interface.

Enhanced from util/graphics/ascii_axes.py with UILT backend abstraction.
Provides efficient data interface with considerations for:
- C++ porting compatibility
- Performance optimization based on data size
- Time-axis abstraction for sample-based data
- Backend-aware decimation
"""

from collections import deque
from typing import Union

from ..core.data_buffer import DataBuffer
from ..core.time_axis import TimeAxis
from ..utils.decimation import SmartDecimation, Backend

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


class ASCIIBackend:
    """Pure ASCII backend for matplotlib-like plotting interface.

    Provides efficient data interface with considerations for:
    - C++ porting compatibility
    - Performance optimization based on data size
    - Time-axis abstraction for sample-based data
    - Backend-aware decimation for optimal resolution
    """

    # Sparkline characters: 8 levels of resolution
    SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"

    def __init__(self, width: int, height: int, title: str = ""):
        """Initialize ASCII backend.

        Args:
            width: Width in characters
            height: Height in rows
            title: Optional title for the plot
        """
        self.width = width
        self.height = height
        self.title = title
        self.data_buffers: list[DataBuffer] = []

        # Auto-scaling parameters
        self.y_min: float | None = None
        self.y_max: float | None = None
        self.auto_scale = True

    def add_data_buffer(self, buffer: DataBuffer) -> None:
        """Add a data buffer to this backend.

        Args:
            buffer: DataBuffer containing data and optional time axis
        """
        self.data_buffers.append(buffer)

        # Update auto-scaling if enabled
        if self.auto_scale:
            self._update_auto_scale(buffer.get_values())

    def plot(
        self,
        data: Union[list[float], deque, "np.ndarray"],
        sample_rate_hz: float | None = None,
        start_time_sec: float = 0.0,
        label: str = "",
    ) -> None:
        """Plot data with automatic time-axis handling.

        This is the main plotting interface that handles:
        - Efficient data type detection
        - Optional time-axis creation from sample rate
        - C++ porting considerations

        Args:
            data: Raw data values (optimized for list[float])
            sample_rate_hz: Optional sample rate for time-axis conversion
            start_time_sec: Starting time offset in seconds
            label: Optional label for the data series

        Performance Notes:
            - list[float]: Optimal for <1K points, C++-friendly
            - numpy arrays: Better for >1K points if available
            - Automatic backend-aware downsampling for display width

        C++ Porting Notes:
            - This interface maps cleanly to plot(std::vector<double>, double, double, std::string)
            - TimeAxis abstraction separates timing from data storage
            - No numpy dependencies in core interface
        """
        # Create time axis if sample rate provided
        time_axis = None
        if sample_rate_hz:
            sample_period_sec = 1.0 / sample_rate_hz
            time_axis = TimeAxis(sample_period_sec, start_time_sec)

        # Create data buffer with type auto-detection
        buffer = DataBuffer(data, time_axis)
        self.add_data_buffer(buffer)

    def plot_samples(
        self,
        samples: Union[list[float], deque, "np.ndarray"],
        sample_period_sec: float,
        start_time_sec: float = 0.0,
        label: str = "",
    ) -> None:
        """Plot samples with explicit sample period (alternative interface).

        This method directly accepts sample period instead of sample rate,
        which can be more natural for some use cases.

        Args:
            samples: Raw sample values
            sample_period_sec: Time between samples in seconds
            start_time_sec: Starting time offset in seconds
            label: Optional label for the data series
        """
        time_axis = TimeAxis(sample_period_sec, start_time_sec)
        buffer = DataBuffer(samples, time_axis)
        self.add_data_buffer(buffer)

    def set_ylim(self, y_min: float, y_max: float) -> None:
        """Set Y-axis limits manually (disables auto-scaling).

        Args:
            y_min: Minimum Y value
            y_max: Maximum Y value
        """
        self.y_min = y_min
        self.y_max = y_max
        self.auto_scale = False

    def clear(self) -> None:
        """Clear all data buffers."""
        self.data_buffers.clear()
        if self.auto_scale:
            self.y_min = None
            self.y_max = None

    def _update_auto_scale(self, values: list[float]) -> None:
        """Update auto-scaling based on new data values."""
        if not values:
            return

        data_min = min(values)
        data_max = max(values)

        if self.y_min is None or data_min < self.y_min:
            self.y_min = data_min
        if self.y_max is None or data_max > self.y_max:
            self.y_max = data_max

    def render_sparkline(self) -> list[str]:
        """Render plot as sparkline characters with backend-aware decimation.

        Returns:
            List of strings, one per row of the plot
        """
        if not self.data_buffers or self.y_min is None or self.y_max is None:
            # Return empty plot
            return [" " * self.width for _ in range(self.height)]

        # For now, render only the first data buffer
        # (Multi-series support can be added later)
        buffer = self.data_buffers[0]

        # Get raw data
        raw_data = buffer.get_values()

        # Apply backend-aware decimation
        decimated_data = SmartDecimation.decimate(raw_data, Backend.ASCII, self.width, self.height)

        # Normalize data to sparkline levels
        y_range = self.y_max - self.y_min
        if y_range == 0:
            # All values are the same
            normalized_values = [4] * len(decimated_data)  # Middle level
        else:
            total_levels = self.height * 8  # 8 sparkline levels per row
            normalized_values = []
            for value in decimated_data:
                # Normalize to [0, 1] then scale to levels
                norm = (value - self.y_min) / y_range
                level = int(norm * (total_levels - 1))
                level = max(0, min(total_levels - 1, level))  # Clamp
                normalized_values.append(level)

        # Convert levels to sparkline characters arranged in rows
        rows = []
        for row_idx in range(self.height):
            row_chars = []
            for col_idx in range(min(len(normalized_values), self.width)):
                level = normalized_values[col_idx]
                # Determine which row this level belongs to (bottom-up)
                row_level = level // 8
                char_level = level % 8

                if row_level == (self.height - 1 - row_idx):
                    # This level belongs to this row
                    row_chars.append(self.SPARKLINE_CHARS[char_level])
                elif row_level > (self.height - 1 - row_idx):
                    # This level is above this row (should be filled)
                    row_chars.append(self.SPARKLINE_CHARS[7])  # Full block
                else:
                    # This level is below this row (should be empty)
                    row_chars.append(" ")

            # Pad row to full width
            while len(row_chars) < self.width:
                row_chars.append(" ")

            rows.append("".join(row_chars))

        return rows

    def get_performance_info(self) -> dict:
        """Get performance information about current data buffers.

        Useful for debugging and optimization decisions.
        """
        info = {
            "backend": "ASCII",
            "num_buffers": len(self.data_buffers),
            "total_points": 0,
            "data_types": [],
            "has_time_axis": [],
            "memory_efficient": True,
            "effective_resolution": SmartDecimation.calculate_effective_resolution(
                Backend.ASCII, self.width, self.height
            ),
        }

        for buffer in self.data_buffers:
            values = buffer.get_values()
            info["total_points"] += len(values)
            info["data_types"].append(buffer._data_type)
            info["has_time_axis"].append(buffer.time_axis is not None)

            # Check if data size suggests numpy would be more efficient
            if len(values) > 1000 and buffer._data_type == "list":
                info["memory_efficient"] = False

        return info
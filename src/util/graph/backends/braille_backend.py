"""Braille backend implementation with 2x horizontal resolution.

This module provides Braille-based plotting with correct Unicode character mapping
and support for positive/negative value orientation. Each Braille character encodes
two data points (left + right columns) for double horizontal resolution.
"""

from collections import deque
from typing import Union

from ..core.data_buffer import DataBuffer
from ..core.time_axis import TimeAxis
from ..utils.decimation import Backend, SmartDecimation

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None


class BrailleBackend:
    """Braille backend for high-density plotting with 2x horizontal resolution.

    Each Braille character encodes two data points (left + right columns).
    Supports proper positive/negative orientation:
    - Positive values: dots fill from top down
    - Negative values: dots fill from bottom up
    """

    def __init__(self, width: int, height: int, title: str = "", display_time_span_sec: float = 4.0):
        """Initialize Braille backend.

        Args:
            width: Width in characters
            height: Height in rows
            title: Optional title for the plot
            display_time_span_sec: Time duration that maps to full display width
        """
        self.width = width
        self.height = height
        self.title = title
        self.display_time_span_sec = display_time_span_sec  # Configurable time span
        self.data_buffers: list[DataBuffer] = []

        # Auto-scaling parameters
        self.y_min: float | None = None
        self.y_max: float | None = None
        self.auto_scale = True

        # Create Braille lookup tables
        self._positive_lookup = self._create_positive_braille_lookup()
        self._negative_lookup = self._create_negative_braille_lookup()

    def _make_braille_char(self, left_dots: int, right_dots: int, positive: bool = True) -> str:
        """Create correct Braille character from dot counts.

        Args:
            left_dots: Number of dots in left column (0-4)
            right_dots: Number of dots in right column (0-4)
            positive: If True, fill from top. If False, fill from bottom.

        Braille dots are numbered:
        1 • • 4
        2 • • 5
        3 • • 6
        7 • • 8
        """
        base = 0x2800  # Base Braille Unicode ⠀
        dot_values = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16, 6: 32, 7: 64, 8: 128}

        # Determine which dots to activate
        active_dots = []

        if positive:
            # Positive: fill from BOTTOM UP (like a bar chart going up)
            # Left column: dots 7,3,2,1 (bottom to top)
            if left_dots >= 1:
                active_dots.append(7)
            if left_dots >= 2:
                active_dots.append(3)
            if left_dots >= 3:
                active_dots.append(2)
            if left_dots >= 4:
                active_dots.append(1)

            # Right column: dots 8,6,5,4 (bottom to top)
            if right_dots >= 1:
                active_dots.append(8)
            if right_dots >= 2:
                active_dots.append(6)
            if right_dots >= 3:
                active_dots.append(5)
            if right_dots >= 4:
                active_dots.append(4)
        else:
            # Negative: fill from TOP DOWN (like a bar chart going down)
            # Left column: dots 1,2,3,7 (top to bottom)
            if left_dots >= 1:
                active_dots.append(1)
            if left_dots >= 2:
                active_dots.append(2)
            if left_dots >= 3:
                active_dots.append(3)
            if left_dots >= 4:
                active_dots.append(7)

            # Right column: dots 4,5,6,8 (top to bottom)
            if right_dots >= 1:
                active_dots.append(4)
            if right_dots >= 2:
                active_dots.append(5)
            if right_dots >= 3:
                active_dots.append(6)
            if right_dots >= 4:
                active_dots.append(8)

        # Calculate Unicode value
        for dot in active_dots:
            base += dot_values[dot]

        return chr(base)

    def _create_positive_braille_lookup(self) -> dict:
        """Create lookup table for POSITIVE values using correct dot mapping."""
        lookup = {}
        for left in range(5):
            for right in range(5):
                lookup[(left, right)] = self._make_braille_char(left, right, positive=True)
        return lookup

    def _create_negative_braille_lookup(self) -> dict:
        """Create lookup table for NEGATIVE values using correct dot mapping."""
        lookup = {}
        for left in range(5):
            for right in range(5):
                lookup[(left, right)] = self._make_braille_char(left, right, positive=False)
        return lookup

    def _value_to_dots(self, value: float, max_dots: int = 4) -> int:
        """Convert normalized value (0.0-1.0) to number of dots (0-4)."""
        if value <= 0:
            return 0
        elif value >= 1:
            return max_dots
        else:
            return int(value * max_dots)

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
        """Plot data with automatic time-axis handling."""
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
        """Plot samples with explicit sample period."""
        time_axis = TimeAxis(sample_period_sec, start_time_sec)
        buffer = DataBuffer(samples, time_axis)
        self.add_data_buffer(buffer)

    def set_ylim(self, y_min: float, y_max: float) -> None:
        """Set Y-axis limits manually (disables auto-scaling)."""
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

    def render_braille(self) -> list[str]:
        """Render plot as Braille characters with 2x horizontal resolution.

        Returns:
            List of strings, one per row of the plot
        """
        if not self.data_buffers or self.y_min is None or self.y_max is None:
            # Return empty plot
            return ["⠀" * self.width for _ in range(self.height)]

        # For now, render only the first data buffer
        buffer = self.data_buffers[0]

        # Get raw data and time axis
        raw_data = buffer.get_values()
        time_axis = buffer.get_time_axis()

        # Apply time-aware decimation for proper sample rate scaling
        # Use sliding window mode based on TIME DURATION, not sample count
        # This ensures identical waveforms use the same mode regardless of sampling rate
        if time_axis is not None:
            data_duration_sec = len(raw_data) * time_axis.sample_period_sec

            # CRITICAL FIX: Force sliding window mode for sample-driven data
            # Sample-driven graphs need index-based scrolling regardless of duration
            # Detection: regular sample periods indicate synthetic timestamps from TimeSeriesGraph
            if len(raw_data) >= 3:
                # For now, assume sample-driven if time_axis exists with regular period
                is_sample_driven = True

                if is_sample_driven:
                    # Force sliding window for sample-driven mode (index-based scrolling)
                    use_sliding_window = True
                else:
                    # Original logic for timestamp-driven mode
                    use_sliding_window = data_duration_sec < 2.0
            else:
                # Use sliding window if data spans less than 2 seconds (initialization phase)
                use_sliding_window = data_duration_sec < 2.0
        else:
            # Fallback to sample count if no time axis
            use_sliding_window = len(raw_data) < (self.width * 0.8)

        decimated_data, display_indices = SmartDecimation.decimate_time_aware(
            raw_data,
            time_axis,
            Backend.BRAILLE,
            self.width,
            self.height,
            sliding_window_mode=use_sliding_window,
            display_time_span_sec=self.display_time_span_sec,
        )

        # Multi-row Braille rendering with time-aware positioning
        rows = []
        total_levels = self.height * 4  # Each Braille char has 4 dot levels per column

        # Create a sparse data structure for time-positioned data
        # Each position can hold up to 2 data points (left and right columns)
        positioned_data = {}
        for data_idx, value in enumerate(decimated_data):
            if data_idx >= len(display_indices):
                break

            display_pos = display_indices[data_idx]
            char_col = display_pos // 2  # Which character column
            sub_col = display_pos % 2  # Left (0) or right (1) column within character

            if char_col < self.width:
                if char_col not in positioned_data:
                    positioned_data[char_col] = [0.0, 0.0]  # [left, right]
                positioned_data[char_col][sub_col] = value

        for row in range(self.height):
            row_chars = []
            for col in range(self.width):
                # Get data for this character position
                if col in positioned_data:
                    left_value, right_value = positioned_data[col]
                else:
                    left_value, right_value = 0.0, 0.0

                # Normalize values to [0, total_levels-1] range
                y_range = self.y_max - self.y_min
                if y_range == 0:
                    left_level = total_levels // 2
                    right_level = total_levels // 2
                else:
                    left_norm = (left_value - self.y_min) / y_range
                    right_norm = (right_value - self.y_min) / y_range
                    left_level = int(left_norm * (total_levels - 1))
                    right_level = int(right_norm * (total_levels - 1))

                # Clamp levels
                left_level = max(0, min(total_levels - 1, left_level))
                right_level = max(0, min(total_levels - 1, right_level))

                # Determine which row each level belongs to (bottom-up)
                left_target_row = self.height - 1 - (left_level // 4)
                right_target_row = self.height - 1 - (right_level // 4)
                left_dots_in_row = left_level % 4
                right_dots_in_row = right_level % 4

                # Calculate dots for this specific row
                if row == left_target_row:
                    left_dots = left_dots_in_row + 1  # +1 because we need 1-4, not 0-3
                elif row > left_target_row:
                    left_dots = 4  # Below target = full
                else:
                    left_dots = 0  # Above target = empty

                if row == right_target_row:
                    right_dots = right_dots_in_row + 1
                elif row > right_target_row:
                    right_dots = 4  # Below target = full
                else:
                    right_dots = 0  # Above target = empty

                # Get Braille character for this row
                char = self._positive_lookup.get((left_dots, right_dots), "⠀")
                row_chars.append(char)

            rows.append("".join(row_chars))

        return rows

    def get_performance_info(self) -> dict:
        """Get performance information about current data buffers."""
        info = {
            "backend": "BRAILLE",
            "num_buffers": len(self.data_buffers),
            "total_points": 0,
            "data_types": [],
            "has_time_axis": [],
            "memory_efficient": True,
            "effective_resolution": SmartDecimation.calculate_effective_resolution(
                Backend.BRAILLE, self.width, self.height
            ),
            "horizontal_density": 2.0,  # 2 data points per character
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

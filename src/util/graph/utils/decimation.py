"""Backend-aware data decimation algorithms for UILT.

Ported and enhanced from util/graphics with backend-specific optimizations.
This module provides intelligent data reduction preserving signal characteristics
while maximizing the effective resolution of each backend.
"""

from enum import Enum
from typing import Union

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

ArrayLike = Union[list[float], "np.ndarray"]


class Backend(Enum):
    """Supported rendering backends."""

    ASCII = "ascii"
    BRAILLE = "braille"
    MATPLOTLIB = "matplotlib"


class SmartDecimation:
    """Intelligent data reduction preserving signal characteristics."""

    @staticmethod
    def calculate_effective_resolution(backend: Backend, width: int, height: int) -> int:
        """Calculate effective data points based on backend capabilities.

        Args:
            backend: Rendering backend type
            width: Display width in characters
            height: Display height in rows

        Returns:
            Number of data points that can be effectively displayed
        """
        if backend == Backend.ASCII:
            return width  # 1 data point per character
        elif backend == Backend.BRAILLE:
            return width * 2  # 2 data points per character (left + right columns)
        else:
            return width  # Default fallback

    @staticmethod
    def decimate(data: ArrayLike, backend: Backend, width: int, height: int) -> ArrayLike:
        """Backend-aware decimation preserving signal characteristics.

        Args:
            data: Input data to decimate
            backend: Target rendering backend
            width: Display width in characters
            height: Display height in rows

        Returns:
            Decimated data optimized for the specified backend
        """
        target_points = SmartDecimation.calculate_effective_resolution(backend, width, height)

        # CRITICAL FIX: Always decimate to consistent target resolution
        # This ensures identical time durations produce identical visual results
        # regardless of original sampling rate
        if len(data) == 0:
            return [0.0] * target_points

        # Peak-preserving decimation
        # 1. Divide into bins
        # 2. Keep max/min in each bin to preserve spikes
        # 3. Use linear interpolation for smooth signals

        bin_size = len(data) / target_points
        decimated = []

        for i in range(target_points):
            start_idx = int(i * bin_size)
            end_idx = int((i + 1) * bin_size)
            bin_data = data[start_idx:end_idx]

            if not bin_data:
                continue

            # Keep peaks for spike preservation (adaptive threshold)
            signal_range = max(bin_data) - min(bin_data)
            # Use 10% of local range as threshold for detecting spikes
            threshold = signal_range * 0.1

            if signal_range > threshold:
                # Preserve peaks - choose max or min based on which is more significant
                max_val = max(bin_data)
                min_val = min(bin_data)
                mean_val = sum(bin_data) / len(bin_data)

                # Choose the value that deviates most from the mean
                if abs(max_val - mean_val) > abs(min_val - mean_val):
                    decimated.append(max_val)
                else:
                    decimated.append(min_val)
            else:
                # Smooth signal - use mean
                decimated.append(sum(bin_data) / len(bin_data))

        return decimated

    @staticmethod
    def decimate_time_aware(
        data: ArrayLike,
        time_axis,
        backend: Backend,
        width: int,
        height: int,
        sliding_window_mode: bool = False,
        display_time_span_sec: float = 4.0,
    ) -> tuple[ArrayLike, ArrayLike]:
        """Time-aware decimation that considers actual time span of data.

        This method properly scales signals with different sample rates to display
        proportionally according to their actual time duration, not just their sample count.

        Args:
            data: Input data to decimate
            time_axis: TimeAxis object with sample rate information
            backend: Target rendering backend
            width: Display width in characters
            height: Display height in rows
            sliding_window_mode: If True, always fill from left-to-right for consistent initialization
            display_time_span_sec: Time duration that maps to full display width (default 4.0 seconds)

        Returns:
            Tuple of (decimated_data, decimated_time_indices) where indices
            represent positions within the display width
        """
        if time_axis is None or sliding_window_mode:
            # Fallback to regular decimation if no time axis OR sliding window mode enabled
            decimated_data = SmartDecimation.decimate(data, backend, width, height)
            # CRITICAL FIX: Ensure indices span full width for target resolution
            target_points = SmartDecimation.calculate_effective_resolution(backend, width, height)
            if len(decimated_data) < target_points:
                # Spread available data evenly across full width (avoid duplicate indices)
                decimated_indices = []
                if len(decimated_data) == 1:
                    decimated_indices = [0]  # Single point at start
                else:
                    # Use numpy linspace equivalent to avoid index clustering
                    for i in range(len(decimated_data)):
                        index = int((i * (target_points - 1)) / (len(decimated_data) - 1))
                        if index not in decimated_indices:  # Prevent duplicates
                            decimated_indices.append(index)
                        else:
                            # If duplicate, increment to next available
                            while index in decimated_indices and index < target_points - 1:
                                index += 1
                            decimated_indices.append(index)
            else:
                decimated_indices = list(range(min(len(decimated_data), target_points)))
            return decimated_data, decimated_indices

        # Calculate actual time span of the data
        data_duration_sec = len(data) * time_axis.sample_period_sec

        # FIXED: For signals shorter than display span, use full width to avoid sparse rendering
        # This ensures clean visualization for any reasonable data duration
        # display_time_span_sec now configurable parameter (default 4.0 seconds)

        # SIMPLIFIED: Always use full width - let application define X-axis limits
        # Graphics library should NOT make decisions about time proportions
        effective_width = width  # Always use full display width

        # SLIDING WINDOW MODE: For initialization consistency, use left-to-right fill
        # when data duration is less than 50% of display span
        if data_duration_sec < (display_time_span_sec * 0.5):
            # Not enough data for proper time-based positioning - use sliding window
            decimated_data = SmartDecimation.decimate(data, backend, width, height)
            # CRITICAL FIX: Ensure indices span full width for proper display
            target_resolution = SmartDecimation.calculate_effective_resolution(backend, width, height)
            if len(decimated_data) < target_resolution:
                # Spread available data evenly across full width (avoid duplicate indices)
                decimated_indices = []
                if len(decimated_data) == 1:
                    decimated_indices = [0]  # Single point at start
                else:
                    # Use numpy linspace equivalent to avoid index clustering
                    for i in range(len(decimated_data)):
                        index = int((i * (target_resolution - 1)) / (len(decimated_data) - 1))
                        if index not in decimated_indices:  # Prevent duplicates
                            decimated_indices.append(index)
                        else:
                            # If duplicate, increment to next available
                            while index in decimated_indices and index < target_resolution - 1:
                                index += 1
                            decimated_indices.append(index)
            else:
                decimated_indices = list(range(len(decimated_data)))
            return decimated_data, decimated_indices

        # Get effective resolution for the actual width this data should occupy
        target_points = SmartDecimation.calculate_effective_resolution(backend, effective_width, height)

        # CRITICAL FIX: Always decimate to consistent target resolution
        # This ensures identical time durations produce identical visual results
        # regardless of original sampling rate

        # Always decimate all data to target_points for consistency
        # This ensures identical signals produce identical visual output regardless of sampling rate

        # Perform peak-preserving decimation to target points
        bin_size = len(data) / target_points
        decimated_data = []
        decimated_indices = []

        for i in range(target_points):
            start_idx = int(i * bin_size)
            end_idx = int((i + 1) * bin_size)

            # Ensure we don't go beyond data bounds
            end_idx = min(end_idx, len(data))

            if start_idx == end_idx:
                # Single sample bin - shouldn't happen with proper bin_size calculation
                if start_idx < len(data):
                    decimated_data.append(data[start_idx])
                else:
                    # Fallback to last known value
                    decimated_data.append(data[-1] if data else 0.0)
            else:
                # Multiple samples in bin - use peak preservation
                bin_data = data[start_idx:end_idx]

                if bin_data:
                    # Peak-preserving logic (same as regular decimation)
                    signal_range = max(bin_data) - min(bin_data)
                    threshold = signal_range * 0.1

                    if signal_range > threshold:
                        max_val = max(bin_data)
                        min_val = min(bin_data)
                        mean_val = sum(bin_data) / len(bin_data)

                        if abs(max_val - mean_val) > abs(min_val - mean_val):
                            decimated_data.append(max_val)
                        else:
                            decimated_data.append(min_val)
                    else:
                        decimated_data.append(sum(bin_data) / len(bin_data))
                else:
                    # Empty bin - use last known value
                    decimated_data.append(data[-1] if data else 0.0)

            # Calculate position within full backend resolution (not just effective width)
            # For Braille: map to 0-119 positions (60 chars × 2 sub-positions each)
            # For ASCII: map to 0-59 positions
            max_display_position = SmartDecimation.calculate_effective_resolution(backend, width, height) - 1
            position = int(i * max_display_position / (target_points - 1)) if target_points > 1 else 0
            decimated_indices.append(position)

        return decimated_data, decimated_indices

    @staticmethod
    def get_backend_info(backend: Backend, width: int, height: int) -> dict:
        """Get information about backend capabilities.

        Args:
            backend: Target rendering backend
            width: Display width in characters
            height: Display height in rows

        Returns:
            Dictionary with backend capability information
        """
        effective_resolution = SmartDecimation.calculate_effective_resolution(backend, width, height)

        info = {
            "backend": backend.value,
            "width": width,
            "height": height,
            "effective_resolution": effective_resolution,
            "horizontal_density": effective_resolution / width,
            "total_display_elements": width * height,
        }

        if backend == Backend.ASCII:
            info["description"] = "1 data point per character"
            info["advantages"] = ["Universal compatibility", "Simple encoding"]
            info["limitations"] = ["Lower horizontal resolution"]
        elif backend == Backend.BRAILLE:
            info["description"] = "2 data points per character (left + right columns)"
            info["advantages"] = ["2x horizontal resolution", "High data density"]
            info["limitations"] = ["Requires UTF-8 terminal", "Font dependent"]

        return info

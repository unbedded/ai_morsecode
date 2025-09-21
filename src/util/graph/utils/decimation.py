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

        if len(data) <= target_points:
            return data

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
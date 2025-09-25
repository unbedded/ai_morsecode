"""Time-series graph with automatic buffer management for UILT library.

This is the Phase 2 target API design that will consolidate all buffer management
into the library, making applications much simpler and eliminating recurring bugs.
"""

import time
from collections import deque

from .backends.ascii_backend import ASCIIBackend
from .backends.braille_backend import BrailleBackend


class TimeSeriesGraph:
    """Time-series graph with automatic sliding window buffer management.

    This class provides a clean API that handles all the complexity of:
    - Sliding window buffer management
    - Time-aware decimation
    - Sample rate detection
    - Backend selection
    - Consistent display behavior

    Applications simply call add_data_point() and render() - no buffer management needed.

    Example:
        # Create time-series graph
        graph = TimeSeriesGraph(width=80, height=6, time_window_sec=30.0)

        # Add data points over time
        for i, value in enumerate(sensor_data):
            timestamp = start_time + i * 0.1  # 10 Hz data
            graph.add_data_point(value, timestamp)

            if i % 10 == 0:  # Update display every second
                lines = graph.render()
                for line in lines:
                    print(line)
    """

    def __init__(
        self,
        width: int = 80,
        height: int = 6,
        time_window_sec: float = 30.0,
        backend: str = "auto",
        title: str = "Time Series",
        sample_rate_hz: float | None = None,
        playback_speed: float = 1.0,
        y_min: float | None = None,
        y_max: float | None = None,
        auto_scale: bool = True,
    ):
        """Initialize time-series graph with automatic buffer management.

        Args:
            width: Display width in characters
            height: Display height in rows
            time_window_sec: Time duration for sliding window
            backend: "auto", "ascii", or "braille"
            title: Graph title
            sample_rate_hz: Optional explicit sample rate (Hz). If None, auto-detects from timing.
            playback_speed: Playback speed multiplier for time synchronization (1.0 = normal speed)
            y_min: Fixed minimum Y value (disables auto-scaling if provided)
            y_max: Fixed maximum Y value (disables auto-scaling if provided)
            auto_scale: Enable auto-scaling (ignored if y_min/y_max provided)
        """
        self.width = width
        self.height = height
        self.time_window_sec = time_window_sec
        self.backend_type = backend
        self.title = title
        self.playback_speed = playback_speed
        self.y_min = y_min
        self.y_max = y_max
        self.auto_scale = auto_scale if (y_min is None and y_max is None) else False

        # STEP 1: Master time clock for synchronization
        self._start_time = time.time()  # Wall-clock start time

        # Calculate buffer size to enforce time window constraint
        # Use reasonable estimates for sample rates: 2-50 Hz range
        # Buffer should hold approximately time_window_sec worth of data
        estimated_sample_rate = 10.0  # Conservative middle estimate
        target_samples = int(time_window_sec * estimated_sample_rate)

        # Clamp to reasonable range: minimum 20 samples, maximum 200 samples
        self._buffer_size = max(20, min(200, target_samples))

        # Sample rate tracking
        self._explicit_sample_rate = sample_rate_hz
        self._calculated_sample_rate = sample_rate_hz if sample_rate_hz else 2.0  # Use explicit or default

        # Sliding window buffers
        self._data_buffer = deque(maxlen=self._buffer_size)
        self._time_buffer = deque(maxlen=self._buffer_size)

        # Only pre-fill if no explicit sample rate (for auto-detection mode)
        if self._explicit_sample_rate is None:
            initial_timestamp = time.time()
            self._data_buffer.extend([0.0] * self._buffer_size)
            self._time_buffer.extend(
                [
                    initial_timestamp - (self._buffer_size - i) * (time_window_sec / self._buffer_size)
                    for i in range(self._buffer_size)
                ]
            )
        self._last_timestamp: float | None = None
        self._sample_count = 0

        # Initialize backend
        self._backend: ASCIIBackend | BrailleBackend | None = None
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize rendering backend based on configuration."""
        # CRITICAL FIX: Use requested time_window_sec for consistent visual scaling
        # Different sample rates should have different visual time scales!
        # This ensures 2Hz data has 25x longer time span than 50Hz data
        display_time_span = self.time_window_sec

        if self.backend_type == "ascii":
            self._backend = ASCIIBackend(self.width, self.height, self.title, display_time_span_sec=display_time_span)
        elif self.backend_type == "braille":
            self._backend = BrailleBackend(self.width, self.height, self.title, display_time_span_sec=display_time_span)
        else:  # auto
            # Try braille first, fallback to ascii
            try:
                self._backend = BrailleBackend(
                    self.width, self.height, self.title, display_time_span_sec=display_time_span
                )
            except Exception:
                self._backend = ASCIIBackend(
                    self.width, self.height, self.title, display_time_span_sec=display_time_span
                )

        # Configure scaling after backend creation
        if self._backend:
            self._backend.auto_scale = self.auto_scale
            if self.y_min is not None and self.y_max is not None:
                self._backend.set_ylim(self.y_min, self.y_max)

    def add_data_point(self, value: float, timestamp: float | None = None) -> None:
        """Add a data point to the time-series graph.

        The library automatically handles:
        - Sliding window buffer management
        - Sample rate detection (if no explicit rate provided)
        - Time-aware decimation preparation

        Args:
            value: Data value to add
            timestamp: Optional timestamp (if None, uses sample-driven mode)
        """
        # SAMPLE-DRIVEN MODE: When explicit sample rate provided, ignore timestamps
        if self._explicit_sample_rate is not None:
            # Use sample-driven approach - calculate synthetic timestamps from sample rate
            synthetic_timestamp = self._start_time + (self._sample_count / self._explicit_sample_rate)
            self._data_buffer.append(value)
            self._time_buffer.append(synthetic_timestamp)
            self._sample_count += 1
            return

        # TIMESTAMP-DRIVEN MODE: Legacy behavior for auto-detection
        if timestamp is None:
            # Use scaled time for synchronization
            wall_time = time.time()
            scaled_elapsed = (wall_time - self._start_time) * self.playback_speed
            timestamp = self._start_time + scaled_elapsed

        # Update sample rate calculation (only if not explicitly set)
        if self._explicit_sample_rate is None and self._last_timestamp is not None:
            interval = timestamp - self._last_timestamp
            if interval > 0:
                instant_rate = 1.0 / interval
                # Exponential moving average for stable rate detection
                alpha = 0.1
                self._calculated_sample_rate = alpha * instant_rate + (1 - alpha) * self._calculated_sample_rate

        self._last_timestamp = timestamp
        self._sample_count += 1

        # Add to sliding window buffers
        self._data_buffer.append(value)
        self._time_buffer.append(timestamp)

    def _adjust_buffer_for_time_window(self) -> None:
        """Dynamically adjust buffer size to maintain time window constraint."""
        # Calculate ideal buffer size based on detected sample rate
        ideal_samples = int(self.time_window_sec * self._calculated_sample_rate)

        # Clamp to reasonable range
        new_buffer_size = max(20, min(200, ideal_samples))

        # Only resize if significantly different (avoid constant resizing)
        if abs(new_buffer_size - self._buffer_size) > 5:
            self._buffer_size = new_buffer_size

            # Create new buffers with updated size
            current_data = list(self._data_buffer)
            current_times = list(self._time_buffer)

            # Keep most recent data when downsizing, or pad with zeros when upsizing
            if new_buffer_size <= len(current_data):
                # Downsizing: keep most recent samples
                keep_data = current_data[-new_buffer_size:]
                keep_times = current_times[-new_buffer_size:]
            else:
                # Upsizing: pad with older zero data
                padding_needed = new_buffer_size - len(current_data)
                oldest_time = current_times[0] if current_times else time.time()
                time_step = (
                    (current_times[-1] - current_times[0]) / (len(current_times) - 1)
                    if len(current_times) > 1
                    else 1.0 / self._calculated_sample_rate
                )

                keep_data = [0.0] * padding_needed + current_data
                keep_times = [
                    oldest_time - (padding_needed - i) * time_step for i in range(padding_needed)
                ] + current_times

            # Replace buffers
            self._data_buffer = deque(keep_data, maxlen=new_buffer_size)
            self._time_buffer = deque(keep_times, maxlen=new_buffer_size)

    def render(self) -> list[str]:
        """Render the current time-series data to text lines.

        Returns:
            List of strings representing the rendered graph
        """
        if not self._backend or len(self._data_buffer) == 0:
            return [" " * self.width for _ in range(self.height)]

        # Create time axis for proper decimation
        # Note: sample_period calculation available but not currently used

        # Convert to format expected by backend
        data_list = list(self._data_buffer)

        # Clear and plot data
        self._backend.clear()

        # CRITICAL FIX: Use explicit sample rate in sample-driven mode for proper scrolling
        effective_sample_rate = (
            self._explicit_sample_rate if self._explicit_sample_rate is not None else self._calculated_sample_rate
        )
        self._backend.plot(data_list, sample_rate_hz=effective_sample_rate)

        # Render based on backend type
        if hasattr(self._backend, "render_braille"):
            return self._backend.render_braille()
        else:
            return self._backend.render_sparkline()

    def get_stats(self) -> dict:
        """Get statistics about the time-series graph state.

        Returns:
            Dictionary with current graph statistics
        """
        if len(self._time_buffer) > 1:
            actual_time_span = self._time_buffer[-1] - self._time_buffer[0]
        else:
            actual_time_span = 0.0

        return {
            "buffer_size": len(self._data_buffer),
            "max_buffer_size": self._buffer_size,
            "calculated_sample_rate_hz": self._calculated_sample_rate,
            "sample_count": self._sample_count,
            "time_window_sec": self.time_window_sec,
            "actual_time_span_sec": actual_time_span,
            "backend": self.backend_type,
            "buffer_utilization": len(self._data_buffer) / self._buffer_size,
        }

    def clear(self) -> None:
        """Clear all data from the time-series graph."""
        self._data_buffer.clear()
        self._time_buffer.clear()
        self._sample_count = 0
        self._last_timestamp = None

        # Refill with zeros for immediate display
        initial_timestamp = time.time()
        self._data_buffer.extend([0.0] * self._buffer_size)
        self._time_buffer.extend(
            [
                initial_timestamp - (self._buffer_size - i) * (self.time_window_sec / self._buffer_size)
                for i in range(self._buffer_size)
            ]
        )

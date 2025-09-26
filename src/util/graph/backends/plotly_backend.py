"""Plotly backend implementation with matplotlib-like interface.

Provides rich interactive web-based plotting following the UILT backend abstraction.
Offers real-time data visualization with zoom, pan, and interactive features
while maintaining the same interface as ASCII/Braille backends.
"""

import os
import tempfile
import webbrowser
from collections import deque
from typing import Union

from ..core.data_buffer import DataBuffer
from ..core.time_axis import TimeAxis
from ..utils.decimation import Backend, SmartDecimation

try:
    import numpy as np
    import plotly.graph_objects as go
    import plotly.io as pio

    HAS_PLOTLY = True
    HAS_NUMPY = True
except ImportError as e:
    HAS_PLOTLY = False
    HAS_NUMPY = False
    go = None
    pio = None
    np = None
    _import_error = str(e)


class PlotlyBackend:
    """Plotly backend for rich interactive plotting interface.

    Provides web-based visualization with zoom, pan, and real-time updates
    while following the same interface pattern as ASCII/Braille backends.
    """

    def __init__(self, width: int, height: int, title: str = "", display_time_span_sec: float = 4.0):
        """Initialize Plotly backend.

        Args:
            width: Display width (used for decimation, Plotly handles actual sizing)
            height: Display height (used for decimation, Plotly handles actual sizing)
            title: Plot title
            display_time_span_sec: Time duration that maps to full display width
        """
        if not HAS_PLOTLY:
            raise ImportError(
                f"Plotly backend requires 'plotly' package. Install with: pip install plotly. Error: {_import_error}"
            )

        self.width = width
        self.height = height
        self.title = title
        self.display_time_span_sec = display_time_span_sec

        # Data management (same pattern as ASCII/Braille backends)
        self.data_buffers: list[DataBuffer] = []
        self.auto_scale = True
        self.y_min = 0.0
        self.y_max = 1.0

        # Create Plotly figure with real-time configuration
        self.fig = go.Figure()
        self.fig.update_layout(
            title=title,
            xaxis_title="Time (seconds)",
            yaxis_title="Amplitude",
            template="plotly_white",
            hovermode="x unified",
            showlegend=True,
            # Real-time optimization
            uirevision=True,  # Preserve zoom/pan state
        )

        # Auto-update configuration for real-time data
        self._trace_count = 0
        self._last_html_file = None

    def plot(
        self,
        data: Union[list[float], deque, "np.ndarray"],
        sample_rate_hz: float,
        time_axis: TimeAxis | None = None,
        label: str = "Signal",
    ) -> None:
        """Plot time-series data using Plotly traces.

        Args:
            data: Y-axis data points
            sample_rate_hz: Sample rate for time axis calculation
            time_axis: Optional TimeAxis object (not used in Plotly, handled internally)
            label: Trace label for legend
        """
        # Create TimeAxis if needed
        if time_axis is None and sample_rate_hz:
            time_axis = TimeAxis(sample_rate_hz)
        buffer = DataBuffer(data, time_axis)
        buffer.label = label
        self.add_data_buffer(buffer)

    def add_data_buffer(self, buffer: DataBuffer) -> None:
        """Add data buffer and create/update Plotly trace."""
        # Update auto-scaling if enabled
        if self.auto_scale:
            self._update_auto_scale(buffer.get_values())

        # Perform backend-aware decimation for performance
        decimated_data, decimated_indices = SmartDecimation.decimate_time_aware(
            data=buffer.get_values(),
            time_axis=buffer.time_axis,
            backend=Backend.MATPLOTLIB,  # Use matplotlib-like resolution
            width=self.width,
            height=self.height,
            display_time_span_sec=self.display_time_span_sec,
        )

        # Calculate time axis for decimated data
        if buffer.time_axis and buffer.time_axis.sample_rate_hz:
            time_points = [i / buffer.time_axis.sample_rate_hz for i in decimated_indices]
        else:
            # Fallback: uniform time spacing
            time_points = [i * (self.display_time_span_sec / len(decimated_data)) for i in range(len(decimated_data))]

        # Add or update trace
        trace_name = buffer.label if hasattr(buffer, "label") else f"Trace {self._trace_count}"

        # Check if trace already exists
        existing_trace = None
        for trace in self.fig.data:
            if trace.name == trace_name:
                existing_trace = trace
                break

        if existing_trace:
            # Update existing trace data
            existing_trace.x = time_points
            existing_trace.y = decimated_data
        else:
            # Create new trace
            self.fig.add_trace(
                go.Scatter(
                    x=time_points,
                    y=decimated_data,
                    mode="lines",
                    name=trace_name,
                    line={"width": 2},
                )
            )
            self._trace_count += 1

        # Update layout with current data range
        self.fig.update_layout(
            yaxis={"range": [self.y_min, self.y_max]} if not self.auto_scale else None,
            xaxis={"range": [0, self.display_time_span_sec]},
        )

        # Store buffer for potential re-rendering
        self.data_buffers.append(buffer)

    def plot_samples(
        self,
        samples: Union[list[float], deque, "np.ndarray"],
        sample_rate_hz: float,
        label: str = "Samples",
    ) -> None:
        """Plot sample data directly without DataBuffer wrapper."""
        time_axis = TimeAxis(sample_rate_hz) if sample_rate_hz else None
        buffer = DataBuffer(samples, time_axis)
        buffer.label = label
        self.add_data_buffer(buffer)

    def set_ylim(self, y_min: float, y_max: float) -> None:
        """Set fixed Y-axis limits and disable auto-scaling."""
        self.y_min = y_min
        self.y_max = y_max
        self.auto_scale = False

        # Update figure layout
        self.fig.update_layout(yaxis={"range": [y_min, y_max]})

    def clear(self) -> None:
        """Clear all data buffers and traces."""
        self.data_buffers.clear()
        self.fig.data = []
        self._trace_count = 0

    def _update_auto_scale(self, data: Union[list[float], deque, "np.ndarray"]) -> None:
        """Update Y-axis scaling based on data range."""
        if not data:
            return

        data_min = min(data)
        data_max = max(data)

        # Add 5% padding
        padding = (data_max - data_min) * 0.05
        self.y_min = data_min - padding
        self.y_max = data_max + padding

    def render_html(self, auto_open: bool = False) -> str:
        """Render plot as HTML string.

        Args:
            auto_open: If True, automatically open in browser

        Returns:
            HTML string representation of the plot
        """
        html_content = self.fig.to_html(
            config={
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["pan2d", "lasso2d"],
                "responsive": True,
            }
        )

        if auto_open:
            # Save to temp file and open in browser
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                f.write(html_content)
                self._last_html_file = f.name

            webbrowser.open(f"file://{self._last_html_file}")

        return html_content

    def render_json(self) -> dict:
        """Render plot as JSON dictionary for API integration."""
        return self.fig.to_dict()

    def show(self) -> None:
        """Display plot in default browser or Jupyter notebook."""
        self.fig.show()

    def save_html(self, filename: str) -> None:
        """Save plot as HTML file."""
        self.fig.write_html(filename)

    def save_image(self, filename: str, width: int = 1200, height: int = 600) -> None:
        """Save plot as static image (requires kaleido: pip install kaleido)."""
        try:
            self.fig.write_image(filename, width=width, height=height)
        except Exception as e:
            raise ImportError(
                f"Image export requires 'kaleido' package. Install with: pip install kaleido. Error: {e}"
            ) from e

    def get_stats(self) -> dict:
        """Get backend statistics for debugging."""
        return {
            "backend": "plotly",
            "width": self.width,
            "height": self.height,
            "title": self.title,
            "trace_count": len(self.fig.data),
            "auto_scale": self.auto_scale,
            "y_range": [self.y_min, self.y_max],
            "display_time_span_sec": self.display_time_span_sec,
            "has_data": len(self.data_buffers) > 0,
        }

    def __del__(self):
        """Cleanup temp files on destruction."""
        if self._last_html_file and os.path.exists(self._last_html_file):
            try:
                os.unlink(self._last_html_file)
            except OSError:
                pass  # File already deleted or permission error

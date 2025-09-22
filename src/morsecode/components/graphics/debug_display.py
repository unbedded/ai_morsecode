"""ASCII debugging display component for real-time signal analysis.

This module provides ASCII-based time-series visualization to replicate
PyQt debugging capabilities over SSH connections. Focuses on normalized
magnitude signal visualization for Morse code signal analysis.
"""

from collections import deque
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import (
    ErrorEvent,
    FFTSpectrumEvent,
    FilteredMagnitudeEvent,
    MorsePatternEvent,
    MorseProbabilityEvent,
    TextDecodedEvent,
    ToneDetectedEvent,
)
from util.config import ConfigurableBase
from util.config.types import CfgField, CfgType
from util.graph import ASCIIBackend, BrailleBackend, plot_signal_auto

from .constants import (
    BufferConstants,
    ChartCalculations,
    DebugConstants,
    SignalConstants,
)


class DebugDisplayCfgKey(Enum):
    """Configuration keys for debug display component."""

    DISPLAY_WIDTH = "display_width_chars"
    DISPLAY_HEIGHT = "display_height_chars"
    REFRESH_RATE_FPS = "refresh_rate_fps"
    BUFFER_SIZE_SEC = "buffer_size_sec"
    ENABLE_DEBUG_LOGGING = "enable_debug_logging"
    BACKEND = "backend"


@dataclass
class DebugDisplaySchema:
    """Configuration schema for ASCII debug display."""

    display_width_chars = CfgField(
        type=CfgType.INT, default=80, min=40, max=200, unit="chars", description="Display width in characters"
    )

    display_height_chars = CfgField(
        type=CfgType.INT, default=20, min=10, max=50, unit="chars", description="Display height in characters"
    )

    refresh_rate_fps = CfgField(
        type=CfgType.INT, default=20, min=1, max=60, unit="fps", description="Display refresh rate"
    )

    buffer_size_sec = CfgField(
        type=CfgType.DOUBLE, default=5.0, min=0.5, max=20.0, unit="sec", description="Time-series buffer size"
    )

    enable_debug_logging = CfgField(type=CfgType.BOOL, default=False, description="Enable debug logging for display")

    backend = CfgField(type=CfgType.STRING, default="ascii", description="Graphics backend: auto, ascii, braille")


class ASCIIDebugDisplay(ConfigurableBase):
    """Real-time ASCII debugging display for signal analysis.

    Provides PyQt-like debugging capabilities using ASCII graphics over SSH.
    Focuses on normalized magnitude time-series visualization with threshold overlay.

    Features:
    - Horizontal scrolling oscilloscope display
    - Real-time magnitude normalization (-1 to +1 scale)
    - Binary threshold state overlay
    - Signal strength and frequency display
    - SSH-friendly pure ASCII output
    """

    # ConfigurableBase requirements
    CONFIG_SCHEMA = DebugDisplaySchema
    CONFIG_SECTION = "debug_display"
    CONFIG_KEYS = DebugDisplayCfgKey

    def __init__(self, cfg_mgr, overrides=None) -> None:
        """Initialize ASCII debug display with event subscriptions.

        Args:
            cfg_mgr: Configuration manager
            overrides: Optional configuration overrides
        """
        # Call ConfigurableBase constructor
        super().__init__(cfg_mgr, overrides)

        # Initialize display state with forced color support
        self._console = Console(force_terminal=True, color_system="standard")
        self._live_display: Live | None = None
        self._is_running = False

        # Override config width with actual terminal width for better display
        actual_width = self._console.size.width
        if actual_width > 40:  # Only override if we have a reasonable terminal size
            self.display_width_chars = actual_width
            self.logger.debug("Using actual terminal width: %d chars", actual_width)

        # Debug: Event handler call counter
        self._fft_event_count = 0

        # Debug: Instance ID for tracking multiple instances
        self._instance_id = id(self)

        # Current signal state
        self._current_magnitude = 0.0
        self._current_threshold = SignalConstants.DEFAULT_THRESHOLD
        self._current_frequency = 600.0
        self._current_binary_state = False
        self._decoded_text = ""
        self._last_pattern = ""
        self._error_count = 0
        self._chunk_counter = 0

        # Current FFT state
        self._current_fft_magnitude = 0.0
        self._current_fft_peak_freq = 600.0
        self._current_fft_total_energy = 0.0
        self._fft_magnitude_scale_max = 1.0  # For autoscaling

        # Current probability state
        self._current_prob_dit = 0.0
        self._current_prob_dash = 0.0
        self._current_prob_letter = 0.0
        self._current_prob_word = 0.0

        # Initialize UILT graphics backends (separate instances prevent data clearing conflicts)
        self._magnitude_backend: ASCIIBackend | BrailleBackend | None = None
        self._fft_backend: ASCIIBackend | BrailleBackend | None = None
        self._probability_backend: ASCIIBackend | BrailleBackend | None = None
        self._initialize_uilt_backends()

        # Get global event bus and subscribe to events
        self._event_bus = get_global_event_bus()
        self._setup_event_subscriptions()

        # Disable buffer priming to test if placeholder data is causing display issues
        # self._prime_buffers_with_placeholder_data()

        self.logger.info(
            "ASCII Debug Display initialized: %dx%d chars, %.1fs buffer",
            self.display_width_chars,
            self.display_height_chars,
            self.buffer_size_sec,
        )

    def _load_config_values(self) -> None:
        """Load configuration values using ConfigurableBase pattern."""
        print("🔧 _load_config_values() CALLED - BUFFER INITIALIZATION STARTING")  # Very obvious debug
        self.display_width_chars = self._cfg_section.get_int(DebugDisplayCfgKey.DISPLAY_WIDTH)
        self.display_height_chars = self._cfg_section.get_int(DebugDisplayCfgKey.DISPLAY_HEIGHT)
        self.refresh_rate_fps = self._cfg_section.get_int(DebugDisplayCfgKey.REFRESH_RATE_FPS)
        self.buffer_size_sec = self._cfg_section.get_double(DebugDisplayCfgKey.BUFFER_SIZE_SEC)
        self.enable_debug_logging = self._cfg_section.get_bool(DebugDisplayCfgKey.ENABLE_DEBUG_LOGGING)
        self.backend_type = self._cfg_section.get_string(DebugDisplayCfgKey.BACKEND)

        # NOW initialize buffers with proper config-loaded buffer size
        self._max_buffer_size = int(self.buffer_size_sec * BufferConstants.DEFAULT_BUFFER_UPDATE_RATE_HZ)

        # Time-series data buffers - WITH PROPER MAXLEN!
        self._magnitude_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        self._threshold_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        self._binary_buffer: deque[bool] = deque(maxlen=self._max_buffer_size)
        self._time_buffer: deque[float] = deque(maxlen=self._max_buffer_size)

        # FFT spectrum data buffers - WITH PROPER MAXLEN!
        self._fft_magnitude_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        self._fft_peak_freq_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        self._fft_total_energy_buffer: deque[float] = deque(maxlen=self._max_buffer_size)

        # DEBUG: Verify maxlen is set correctly
        self.logger.info(
            "Buffer initialization: max_buffer_size=%d, fft_buffer_maxlen=%s",
            self._max_buffer_size,
            self._fft_magnitude_buffer.maxlen,
        )

        # Morse probability data buffers - WITH PROPER MAXLEN!
        self._prob_dit_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        self._prob_dash_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        self._prob_letter_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        self._prob_word_buffer: deque[float] = deque(maxlen=self._max_buffer_size)
        # Probability time buffer to track event timestamps
        self._prob_time_buffer: deque[float] = deque(maxlen=self._max_buffer_size)

    def _on_reconfiguration(self) -> None:
        """Handle reconfiguration - reinitialize backends if needed."""
        # Reinitialize UILT backends with new settings
        self._initialize_uilt_backends()
        self.logger.info(
            "DebugDisplay reconfigured: backend=%s, size=%dx%d",
            self.backend_type,
            self.display_width_chars,
            self.display_height_chars,
        )

    def _setup_event_subscriptions(self) -> None:
        """Subscribe to all relevant events for debugging display."""
        self._event_bus.subscribe(FilteredMagnitudeEvent, self._on_magnitude_event)
        self._event_bus.subscribe(FFTSpectrumEvent, self._on_fft_spectrum_event)
        self._event_bus.subscribe(MorseProbabilityEvent, self._on_probability_event)
        self._event_bus.subscribe(ToneDetectedEvent, self._on_tone_event)
        self._event_bus.subscribe(MorsePatternEvent, self._on_pattern_event)
        self._event_bus.subscribe(TextDecodedEvent, self._on_text_event)
        self._event_bus.subscribe(ErrorEvent, self._on_error_event)

        self.logger.debug("Event subscriptions configured for debug display")

    def _clear_backend_data_only(self, backend) -> None:
        """Clear backend data buffers while preserving auto-scaling state.

        This prevents the infinite data accumulation issue while maintaining
        the established Y-axis scaling that was built up over time.
        """
        if backend:
            # Save current auto-scaling state
            saved_y_min = backend.y_min
            saved_y_max = backend.y_max
            saved_auto_scale = backend.auto_scale

            # Clear data buffers only
            backend.data_buffers.clear()

            # Restore auto-scaling state
            backend.y_min = saved_y_min
            backend.y_max = saved_y_max
            backend.auto_scale = saved_auto_scale

    def _initialize_uilt_backends(self) -> None:
        """Initialize separate UILT backends for each chart type to prevent data clearing conflicts."""
        # Use a smaller chart area for time series - leave room for headers and status
        chart_width = ChartCalculations.main_chart_width(self.display_width_chars)
        chart_height = ChartCalculations.main_chart_height(self.display_height_chars)
        prob_chart_height = 2  # Fixed height for probability charts

        if self.backend_type == "ascii":
            self._magnitude_backend = ASCIIBackend(chart_width, chart_height, "Magnitude")
            self._fft_backend = ASCIIBackend(chart_width, chart_height, "FFT")
            self._probability_backend = ASCIIBackend(chart_width, prob_chart_height, "Probability")
            self.logger.debug(
                "Initialized ASCII backends: main=%dx%d, prob=%dx%d",
                chart_width,
                chart_height,
                chart_width,
                prob_chart_height,
            )
        elif self.backend_type == "braille":
            self._magnitude_backend = BrailleBackend(chart_width, chart_height, "Magnitude")
            self._fft_backend = BrailleBackend(chart_width, chart_height, "FFT")
            self._probability_backend = BrailleBackend(chart_width, prob_chart_height, "Probability")
            self.logger.debug(
                "Initialized Braille backends: main=%dx%d, prob=%dx%d",
                chart_width,
                chart_height,
                chart_width,
                prob_chart_height,
            )
        else:  # auto
            # For auto mode, we'll use convenience function at render time
            self._magnitude_backend = None
            self._fft_backend = None
            self._probability_backend = None
            self.logger.debug("Using auto backend selection")

    def start_display(self) -> None:
        """Start the live ASCII display."""
        if self._is_running:
            self.logger.warning("Display already running")
            return

        try:
            layout = self._build_display_layout()
            # Use Rich Live for layout management, but don't over-update it
            self._live_display = Live(layout, console=self._console, refresh_per_second=self.refresh_rate_fps)
            self._live_display.start()
            self._is_running = True

            self.logger.info("ASCII debug display started")

        except Exception as e:
            self.logger.exception("Failed to start display: %s", e)
            raise

    def stop_display(self) -> None:
        """Stop the live display with proper cleanup."""
        if not self._is_running:
            return

        self.logger.debug("Stopping ASCII debug display...")

        # Mark as not running first to stop any refresh attempts
        self._is_running = False

        try:
            if self._live_display:
                # Render a final "Shutdown" message before stopping
                try:
                    from rich.panel import Panel
                    from rich.text import Text

                    shutdown_msg = Panel(
                        Text("Debug Display Shutdown Complete", style="bold green"), style="green", title="Status"
                    )
                    self._live_display.update(shutdown_msg)
                    self._live_display.refresh()
                except Exception:
                    pass  # Don't let final update prevent shutdown

                # Stop with timeout protection
                import threading

                def safe_stop():
                    """Safely stop the live display."""
                    try:
                        if self._live_display is not None:
                            self._live_display.stop()
                    except Exception as e:
                        self.logger.debug("Exception during live display stop: %s", e)

                # Use daemon thread with timeout
                stop_thread = threading.Thread(target=safe_stop, daemon=True)
                stop_thread.start()
                stop_thread.join(timeout=DebugConstants.THREAD_STOP_TIMEOUT_SEC)

                if stop_thread.is_alive():
                    self.logger.warning("Live display stop() hanging - continuing without wait")

                self._live_display = None

            self.logger.info("ASCII debug display stopped successfully")

        except Exception as e:
            self.logger.warning("Error during display shutdown: %s", e)
        finally:
            # Ensure cleanup regardless of errors
            self._live_display = None
            self._is_running = False

    def _build_display_layout(self) -> Layout:
        """Build the Rich layout for the debug display."""
        try:
            layout = Layout()

            # Create main sections - FFT, magnitude, 4 individual probability charts, status
            # Each probability chart gets 3 rows (2 for content + 1 for Panel borders, total: ~30 rows)
            layout.split_column(
                Layout(name="header", size=2),
                Layout(name="fft_chart", size=6),
                Layout(name="magnitude_chart", size=6),
                Layout(name="prob_dit", size=3),
                Layout(name="prob_dash", size=3),
                Layout(name="prob_letter", size=3),
                Layout(name="prob_word", size=3),
                Layout(name="status", size=6),
            )

            # Header section with detailed UILT information
            header_text = Text.assemble(
                ("🎯 UILT ", "bold blue"),
                ("ASCII/Braille Signal Visualization", "bold white"),
                (" | ", "dim white"),
                (self._get_backend_info(), "bright_cyan"),
                (" | ", "dim white"),
                (self._get_resolution_info(), "bright_green"),
                (" | SSH-Compatible Real-Time Display", "dim white"),
            )
            layout["header"].update(
                Panel(header_text, style="blue", title="Universal Interactive Live Terminal (UILT)")
            )

            # FFT chart section (frequency domain visualization)
            fft_chart_content = self._render_fft_chart()
            fft_title = (
                f"FFT Peak Magnitude (Autoscaled) | Data Points: {len(self._fft_magnitude_buffer)} | "
                f"Peak: {self._current_fft_peak_freq:.0f}Hz"
            )
            layout["fft_chart"].update(Panel(fft_chart_content, title=fft_title, style="cyan"))

            # Magnitude chart section (main time-series display)
            chart_content = self._render_magnitude_chart()
            magnitude_title = f"Normalized Magnitude (-1 to +1) | Data Points: {len(self._magnitude_buffer)}"
            layout["magnitude_chart"].update(Panel(chart_content, title=magnitude_title, style="green"))

            # Individual probability charts - full width, 2 rows each, same timescale as main charts
            dit_chart = self._render_full_width_probability_chart("dit", self._prob_dit_buffer, 2)
            dit_title = (
                f"Dit Probability (0-1) | Data Points: {len(self._prob_dit_buffer)} | "
                f"Current: {self._current_prob_dit:.2f}"
            )
            layout["prob_dit"].update(Panel(dit_chart, title=dit_title, style="bright_blue"))

            dash_chart = self._render_full_width_probability_chart("dash", self._prob_dash_buffer, 2)
            dash_title = (
                f"Dash Probability (0-1) | Data Points: {len(self._prob_dash_buffer)} | "
                f"Current: {self._current_prob_dash:.2f}"
            )
            layout["prob_dash"].update(Panel(dash_chart, title=dash_title, style="bright_red"))

            letter_chart = self._render_full_width_probability_chart("letter", self._prob_letter_buffer, 2)
            letter_title = (
                f"Letter Space Probability (0-1) | Data Points: {len(self._prob_letter_buffer)} | "
                f"Current: {self._current_prob_letter:.2f}"
            )
            layout["prob_letter"].update(Panel(letter_chart, title=letter_title, style="bright_magenta"))

            word_chart = self._render_full_width_probability_chart("word", self._prob_word_buffer, 2)
            word_title = (
                f"Word Space Probability (0-1) | Data Points: {len(self._prob_word_buffer)} | "
                f"Current: {self._current_prob_word:.2f}"
            )
            layout["prob_word"].update(Panel(word_chart, title=word_title, style="bright_yellow"))

            # Status section
            status_content = self._render_status_panel()
            layout["status"].update(Panel(status_content, title="Signal Status", style="yellow"))

            return layout

        except Exception as e:
            self.logger.exception("Error building display layout: %s", e)
            # Fallback to simple layout
            fallback_layout = Layout()
            fallback_layout.split_column(
                Layout(name="header", size=3), Layout(name="magnitude_chart", size=14), Layout(name="status", size=5)
            )

            # Simple content
            header_text = Text("🔍 ASCII Signal Debug Display (Fallback Mode)", style="bold blue")
            fallback_layout["header"].update(Panel(header_text, style="blue"))

            chart_content = Text("Layout error - using fallback mode", style="red")
            fallback_layout["magnitude_chart"].update(Panel(chart_content, title="Error", style="red"))

            status_content = Text("Check logs for layout errors", style="yellow")
            fallback_layout["status"].update(Panel(status_content, title="Status", style="yellow"))

            return fallback_layout

    def _render_magnitude_chart(self) -> Text:
        """Render signal magnitude chart using UILT backend (ASCII/Braille)."""
        chart_text = Text()

        if len(self._magnitude_buffer) < 1:
            # Not enough data yet (expected during startup in real-time mode)
            chart_text.append("Waiting for signal data...", style="dim white")
            return chart_text

        # Use UILT backend for high-resolution signal visualization
        try:
            # Convert deque to list for UILT - all data is real-time, no placeholder skipping needed
            signal_data = list(self._magnitude_buffer)

            # CRITICAL: Take only the most recent data points to create sliding window effect
            # Backend only renders first 'width' points, so we need to give it the LATEST data
            chart_width = ChartCalculations.main_chart_width(self.display_width_chars)
            if len(signal_data) > chart_width:
                # Sliding window: take the most recent chart_width points
                signal_data = signal_data[-chart_width:]

            if self._magnitude_backend:
                # Use dedicated magnitude backend - clear data but preserve auto-scaling
                self._clear_backend_data_only(self._magnitude_backend)
                self._magnitude_backend.plot(signal_data, sample_rate_hz=SignalConstants.CHART_SAMPLE_RATE_HZ)

                if hasattr(self._magnitude_backend, "render_braille"):
                    # Braille backend - much higher resolution
                    lines = self._magnitude_backend.render_braille()
                else:
                    # ASCII backend
                    lines = self._magnitude_backend.render_sparkline()

                # Title now in panel border - content area is pure chart data

            else:
                # Auto backend selection
                lines, backend_used = plot_signal_auto(
                    signal_data,
                    width=60,
                    height=6,
                    title="Magnitude",
                    sample_rate_hz=100.0,
                    prefer_braille=True,
                )
                # Title now in panel border - content area is pure chart data

            # Add the rendered chart lines
            for line in lines:
                chart_text.append(line + "\n", style="white")

            # Add threshold line indicator
            if hasattr(self, "_current_threshold"):
                binary_status = "ON" if self._current_binary_state else "OFF"
                threshold_text = f"Threshold: {self._current_threshold:.3f} | Binary: {binary_status}"
                chart_text.append(
                    threshold_text,
                    style="yellow" if self._current_binary_state else "dim yellow",
                )

        except Exception as e:
            # Fallback to simple text display
            chart_text.append(f"UILT Error: {e}\n", style="red")
            chart_text.append("Fallback: ", style="dim white")
            if hasattr(self, "_current_magnitude"):
                # Simple bar representation
                bar_length = min(40, int(abs(self._current_magnitude) * 40))
                bar = "█" * bar_length + "░" * (40 - bar_length)
                chart_text.append(f"{bar} {self._current_magnitude:.3f}", style="green")

        return chart_text

    def _render_fft_chart(self) -> Text:
        """Render FFT magnitude chart using UILT backend (consistent with magnitude chart)."""
        chart_text = Text()

        buffer_size = len(self._fft_magnitude_buffer)
        event_count = getattr(self, "_fft_event_count", 0)
        instance_id = getattr(self, "_instance_id", "unknown")

        if buffer_size < 1:
            # Not enough FFT data yet (expected during startup)
            # Debug: Log what renderer sees
            if hasattr(self, "logger"):
                log_msg = (
                    f"FFT renderer: EMPTY BUFFER - instance={instance_id}, "
                    f"buffer_size={buffer_size}, events={event_count}"
                )
                self.logger.info(log_msg)
            chart_text.append(f"Waiting for FFT spectrum data... (events: {event_count})", style="dim white")
            return chart_text
        else:
            # Debug: Log when we do have data
            if hasattr(self, "logger"):
                self.logger.info(f"FFT renderer: HAS DATA - buffer_size={buffer_size}, events={event_count}")

        # Convert deque to list for UILT - all data is real-time, no placeholder skipping needed
        fft_data = list(self._fft_magnitude_buffer)

        # CRITICAL: Take only the most recent data points to create sliding window effect
        chart_width = ChartCalculations.main_chart_width(self.display_width_chars)
        if len(fft_data) > chart_width:
            # Sliding window: take the most recent chart_width points
            fft_data = fft_data[-chart_width:]

        # Use UILT backend for consistent density and width with magnitude chart
        try:
            # Implement autoscaling: track running maximum with decay
            current_max = max(fft_data) if fft_data else 1.0
            if current_max > self._fft_magnitude_scale_max:
                self._fft_magnitude_scale_max = current_max
            else:
                # Slow decay to allow scaling down when signal gets weaker
                self._fft_magnitude_scale_max *= SignalConstants.SCALE_DECAY_FACTOR

            # Prevent division by zero
            scale_max = max(self._fft_magnitude_scale_max, SignalConstants.MIN_SCALE_VALUE)

            if self._fft_backend:
                # Use dedicated FFT backend - clear data but preserve auto-scaling
                self._clear_backend_data_only(self._fft_backend)
                self._fft_backend.plot(fft_data, sample_rate_hz=SignalConstants.CHART_SAMPLE_RATE_HZ)

                if hasattr(self._fft_backend, "render_braille"):
                    # Braille backend - consistent with magnitude chart
                    lines = self._fft_backend.render_braille()
                    backend_info = "Braille (2x resolution)"
                else:
                    # ASCII backend
                    lines = self._fft_backend.render_sparkline()
                    backend_info = "ASCII"

                # Add backend info and scale data
                chart_text.append(f"[UILT {backend_info}] ", style="dim cyan")
                chart_text.append(f"FFT (scale: 0-{int(scale_max)})\n", style="white")

            else:
                # Auto backend selection - same as magnitude chart
                lines, backend_used = plot_signal_auto(
                    fft_data,
                    width=60,
                    height=6,
                    title="FFT",
                    sample_rate_hz=100.0,
                    prefer_braille=True,
                )
                # Title and scale info now in panel border - content area is pure chart data

            # Add the rendered chart lines
            for line in lines:
                chart_text.append(line + "\n", style="white")

            # Add scale info
            chart_text.append(
                f"Autoscaled 0-{int(scale_max)} | Peak: {self._current_fft_peak_freq:.0f}Hz", style="yellow"
            )

        except Exception as e:
            # Fallback to simple text display
            chart_text.append(f"UILT FFT Error: {e}\n", style="red")
            chart_text.append("Fallback: FFT data not available", style="dim white")

        return chart_text

    def _render_probability_chart(self, prob_type: str, prob_buffer: deque[float]) -> Text:
        """Render 4-row probability chart for a specific Morse element (0.0 to 1.0)."""
        chart_text = Text()

        # Chart dimensions - narrower than main charts since we have 4 side by side
        chart_width = ChartCalculations.probability_chart_width(self.display_width_chars)
        chart_rows = SignalConstants.PROBABILITY_CHART_ROWS

        if len(prob_buffer) < 1:
            # Not enough data yet - show simplified test pattern
            chart_text.append(f"{prob_type[:3].upper()}\n", style="white")
            chart_text.append("████\n", style="white")
            chart_text.append("▇▅▃▁\n", style="white")
            chart_text.append("TEST", style="dim white")
            return chart_text

        # Get probability data (0.0 to 1.0 range)
        prob_data = list(prob_buffer)[-chart_width:]

        # Sparkline characters are now defined in SignalConstants.SPARKLINE_CHARS

        # Simple white color for now
        def get_prob_color(value):
            return "white"

        # Build 4-row display: 0.0 to 1.0
        for row in range(chart_rows):
            row_text = Text()

            # Row labels for probability range (4 levels from 0.0 to 1.0)
            if row == 0:  # Top row (1.0)
                row_text.append("1.0", style="white")
            elif row == 1:  # 0.75
                row_text.append("0.7", style="white")
            elif row == 2:  # 0.5
                row_text.append("0.5", style="white")
            else:  # Bottom row (0.0)
                row_text.append("0.0", style="white")

            for _col, prob_value in enumerate(prob_data):
                # Clamp probability to 0-1 range
                prob_value = max(0.0, min(1.0, prob_value))

                # Map probability 0.0 to 1.0 to 32 levels (4 rows × 8 sparklines)
                level_32 = int(prob_value * 31.99)  # 0-31 range
                level_32 = max(0, min(31, level_32))

                target_row = 3 - (level_32 // 8)  # Which row (3=bottom, 0=top)
                sparkline_level = level_32 % 8  # Which sparkline within row

                color = get_prob_color(prob_value)

                if row < target_row:
                    # Above the signal - empty
                    row_text.append(" ")
                elif row == target_row:
                    # Signal row - show appropriate sparkline
                    row_text.append(SignalConstants.SPARKLINE_CHARS[sparkline_level], style=color)
                else:
                    # Below signal - filled blocks (building up from bottom)
                    row_text.append("█", style=color)

            chart_text.append(row_text)

            # Add newline except for last row
            if row < SignalConstants.FFT_CHART_ROWS - 1:
                chart_text.append("\n")

        return chart_text

    def _render_probability_section(self) -> Text:
        """Render all 4 probability charts side-by-side in a single section."""
        prob_types = [
            ("DIT", self._prob_dit_buffer, "bright_blue"),
            ("DASH", self._prob_dash_buffer, "bright_red"),
            ("LTR", self._prob_letter_buffer, "bright_magenta"),
            ("WORD", self._prob_word_buffer, "bright_yellow"),
        ]

        section_text = Text()
        chart_width = ChartCalculations.probability_chart_width(self.display_width_chars)
        chart_rows = SignalConstants.PROBABILITY_CHART_ROWS

        # Build each row across all 4 charts
        for row in range(chart_rows):
            row_text = Text()

            for i, (prob_type, prob_buffer, color) in enumerate(prob_types):
                if i > 0:
                    row_text.append(" │ ", style="dim white")  # Separator between charts

                # Add row label on first chart only
                if i == 0:
                    if row == 0:
                        row_text.append("1.0 ", style="white")
                    elif row == 1:
                        row_text.append("0.7 ", style="white")
                    elif row == 2:
                        row_text.append("0.5 ", style="white")
                    else:
                        row_text.append("0.0 ", style="white")
                else:
                    row_text.append("    ", style="white")  # Padding for other charts

                # Chart title on top row
                if row == 0:
                    title_text = f"{prob_type[:4]:^{chart_width}}"[:chart_width]
                    row_text.append(title_text, style=color)
                else:
                    # Chart content
                    if len(prob_buffer) < 1:
                        # Fallback content
                        content = "█▇▅▃"[:chart_width].ljust(chart_width)
                        row_text.append(content, style=color)
                    else:
                        # Actual probability chart data
                        prob_data = list(prob_buffer)[-chart_width:]
                        # Using SignalConstants.SPARKLINE_CHARS instead

                        chart_content = ""
                        for prob_value in prob_data:
                            prob_value = max(0.0, min(1.0, prob_value))
                            level_32 = int(prob_value * 31.99)
                            level_32 = max(0, min(31, level_32))
                            target_row = 3 - (level_32 // 8)
                            sparkline_level = level_32 % 8

                            if row < target_row:
                                chart_content += " "
                            elif row == target_row:
                                chart_content += SignalConstants.SPARKLINE_CHARS[sparkline_level]
                            else:
                                chart_content += "█"

                        chart_content = chart_content.ljust(chart_width)[:chart_width]
                        row_text.append(chart_content, style=color)

            section_text.append(row_text)
            if row < SignalConstants.FFT_CHART_ROWS - 1:
                section_text.append("\n")

        return section_text

    def _render_full_width_probability_chart(self, prob_type: str, prob_buffer: deque[float], chart_rows: int) -> Text:
        """Render full-width probability chart using same core logic as magnitude chart.

        Args:
            prob_type: Type of probability (dit, dash, letter, word)
            prob_buffer: Buffer containing probability values (0.0 to 1.0)
            chart_rows: Number of rows for the chart (e.g., 2)
        """
        chart_text = Text()

        # Chart dimensions - same width as main charts for time alignment
        chart_width = self.display_width_chars - 12  # Account for row labels and padding
        # total_levels = chart_rows * 8  # 8 sparkline levels per row (calculated in constants)

        if len(prob_buffer) < 1:
            # Not enough probability data yet
            chart_text.append("Waiting for probability data...", style="dim white")
            return chart_text

        # Use UILT backend for probability charts - consistent with magnitude and FFT charts
        try:
            # Convert deque to list for UILT
            prob_data = list(prob_buffer)

            # CRITICAL: Take only the most recent data points to create sliding window effect
            chart_width = ChartCalculations.main_chart_width(self.display_width_chars)
            if len(prob_data) > chart_width:
                # Sliding window: take the most recent chart_width points
                prob_data = prob_data[-chart_width:]

            # Color based on probability type
            prob_colors = {
                "dit": "bright_blue",
                "dash": "bright_red",
                "letter": "bright_magenta",
                "word": "bright_yellow",
            }
            color = prob_colors.get(prob_type, "white")

            if self._probability_backend:
                # Use dedicated probability backend - clear data but preserve auto-scaling
                self._clear_backend_data_only(self._probability_backend)
                self._probability_backend.plot(prob_data, sample_rate_hz=SignalConstants.CHART_SAMPLE_RATE_HZ)

                if hasattr(self._probability_backend, "render_braille"):
                    # Braille backend - use configured height
                    lines = self._probability_backend.render_braille()
                else:
                    # ASCII backend - use configured height
                    lines = self._probability_backend.render_sparkline()

                # Ensure exactly chart_rows lines (pad or trim as needed)
                lines = self._ensure_chart_height(lines, chart_rows)

                # Title now in panel border - content area is pure chart data

            else:
                # Auto backend selection - ensure exact height for 2 lines
                lines, backend_used = plot_signal_auto(
                    prob_data,
                    width=60,
                    height=chart_rows,
                    title=f"{prob_type.title()}",
                    sample_rate_hz=100.0,
                    prefer_braille=True,
                )
                # Ensure exactly chart_rows lines (pad or trim as needed)
                lines = self._ensure_chart_height(lines, chart_rows)

                # Title now in panel border - content area is pure chart data

            # Add the rendered chart lines
            for line in lines:
                chart_text.append(line + "\n", style="white")

            # Add probability range info
            if len(prob_data) > 0:
                current_val = prob_data[-1]
                avg_val = sum(prob_data) / len(prob_data)
                chart_text.append(f"Current: {current_val:.2f} | Avg: {avg_val:.2f}", style=color)

        except Exception as e:
            # Fallback to simple text display
            chart_text.append(f"UILT Probability Error: {e}\n", style="red")
            chart_text.append("Fallback: Probability data not available", style="dim white")

        return chart_text

    def _get_backend_info(self) -> str:
        """Get current backend information for header display."""
        if self._magnitude_backend:
            if hasattr(self._magnitude_backend, "render_braille"):
                return "Braille Backend Active"
            else:
                return "ASCII Backend Active"
        else:
            return "Auto Backend Selection"

    def _get_resolution_info(self) -> str:
        """Get resolution information for header display."""
        if self._magnitude_backend and hasattr(self._magnitude_backend, "render_braille"):
            return "2x Resolution (Braille dots)"
        else:
            return "Standard Resolution (ASCII chars)"

    def _ensure_chart_height(self, lines: list[str], target_height: int) -> list[str]:
        """Ensure chart has exactly the target height by padding or trimming lines.

        Args:
            lines: List of chart lines from backend
            target_height: Desired number of lines

        Returns:
            List of lines with exactly target_height entries
        """
        if len(lines) == target_height:
            return lines
        elif len(lines) < target_height:
            # Pad with empty lines
            padding_needed = target_height - len(lines)
            return lines + [" " * (len(lines[0]) if lines else 60)] * padding_needed
        else:
            # Trim to target height (take the first target_height lines)
            return lines[:target_height]

    def _render_status_panel(self) -> Text:
        """Render the current status information."""
        status_text = Text()

        # Current values - line 1
        status_text.append("Magnitude: ", style="white")
        status_text.append(
            f"{self._current_magnitude:+5.2f}", style="bold green" if abs(self._current_magnitude) > 0.5 else "white"
        )
        status_text.append(" | ")

        status_text.append("Frequency: ", style="white")
        status_text.append(f"{self._current_frequency:6.1f} Hz", style="cyan")
        status_text.append(" | ")

        status_text.append("State: ", style="white")
        state_style = "bold green" if self._current_binary_state else "dim white"
        state_text = "SIGNAL" if self._current_binary_state else "SPACE"
        status_text.append(state_text, style=state_style)
        status_text.append("\n")

        # FFT values - line 2
        status_text.append("FFT Peak: ", style="white")
        status_text.append(f"{self._current_fft_magnitude:8.1f}", style="bright_yellow")
        status_text.append(" | ")

        status_text.append("Peak Freq: ", style="white")
        status_text.append(f"{self._current_fft_peak_freq:6.1f} Hz", style="bright_cyan")
        status_text.append(" | ")

        status_text.append("Scale Max: ", style="white")
        if self._fft_magnitude_scale_max >= SignalConstants.KILOUNIT_THRESHOLD:
            status_text.append(
                f"{self._fft_magnitude_scale_max / SignalConstants.KILOUNIT_THRESHOLD:.1f}K", style="yellow"
            )
        else:
            status_text.append(f"{self._fft_magnitude_scale_max:.1f}", style="yellow")
        status_text.append("\n")

        # Pattern and text
        status_text.append("Pattern: ", style="white")
        status_text.append(f"{self._last_pattern or 'None'}", style="yellow")
        status_text.append(" | ")

        status_text.append("Text: ", style="white")
        status_text.append(f'"{self._decoded_text[-20:]}"', style="bold white")  # Last 20 chars
        status_text.append("\n")

        # Morse probabilities - line 3
        status_text.append("Dit: ", style="white")
        status_text.append(f"{self._current_prob_dit:.3f}", style="bright_blue")
        status_text.append(" | ")

        status_text.append("Dash: ", style="white")
        status_text.append(f"{self._current_prob_dash:.3f}", style="bright_red")
        status_text.append(" | ")

        status_text.append("Letter: ", style="white")
        status_text.append(f"{self._current_prob_letter:.3f}", style="bright_magenta")
        status_text.append(" | ")

        status_text.append("Word: ", style="white")
        status_text.append(f"{self._current_prob_word:.3f}", style="bright_yellow")
        status_text.append("\n")

        # Buffer info
        buffer_pct = (len(self._magnitude_buffer) / self._max_buffer_size) * 100 if self._max_buffer_size > 0 else 0
        status_text.append(
            f"Buffer: {len(self._magnitude_buffer)}/{self._max_buffer_size} ({buffer_pct:.0f}%)", style="dim white"
        )

        if self._error_count > 0:
            status_text.append(f" | Errors: {self._error_count}", style="bold red")

        return status_text

    def _on_magnitude_event(self, event: FilteredMagnitudeEvent) -> None:
        """Handle filtered magnitude events for time-series display."""
        # Guard against early event calls before initialization completes
        if not hasattr(self, "_chunk_counter"):
            self.logger.warning("Magnitude event received before initialization complete, ignoring")
            return

        # Use event timestamp (microseconds since program start) for proper synchronization
        event_time_us = event.timestamp
        event_time_s = event_time_us / 1_000_000.0  # Convert to seconds for display
        self._chunk_counter += 1

        # Add to buffers
        self._magnitude_buffer.append(event.magnitude_norm)
        self._threshold_buffer.append(event.threshold_norm)
        self._binary_buffer.append(event.binary_state)
        self._time_buffer.append(event_time_s)

        # Buffer size automatically maintained by deque maxlen - no manual trimming needed

        # Update current state
        self._current_magnitude = event.magnitude_norm
        self._current_threshold = event.threshold_norm
        self._current_frequency = event.frequency_hz
        self._current_binary_state = event.binary_state

        # Mock probability events removed - now using real probability events from decoder

        # Note: Display updates are now handled by Rich Live timer at configured FPS
        # Removed event-driven updates to fix scrolling bug and improve performance

    def _on_tone_event(self, event: ToneDetectedEvent) -> None:
        """Handle tone detection events."""
        if event.frequency != self._current_frequency:
            self._current_frequency = event.frequency

    def _on_pattern_event(self, event: MorsePatternEvent) -> None:
        """Handle Morse pattern events."""
        self._last_pattern = event.pattern_type

    def _on_text_event(self, event: TextDecodedEvent) -> None:
        """Handle decoded text events."""
        self._decoded_text += event.text
        # Keep last N characters
        if len(self._decoded_text) > BufferConstants.DECODED_TEXT_MAX_LENGTH:
            self._decoded_text = self._decoded_text[-BufferConstants.DECODED_TEXT_MAX_LENGTH :]

    def _on_fft_spectrum_event(self, event: FFTSpectrumEvent) -> None:
        """Handle FFT spectrum events for frequency domain visualization."""
        # Debug: Count received events
        self._fft_event_count += 1

        # Debug: Log every 10th event
        if self._fft_event_count % 10 == 1:
            debug_msg = (
                f"FFT handler: instance={self._instance_id}, event #{self._fft_event_count}, "
                f"buffer_size={len(self._fft_magnitude_buffer)}"
            )
            self.logger.debug(debug_msg)

        # Add to FFT buffers
        self._fft_magnitude_buffer.append(event.peak_magnitude)
        self._fft_peak_freq_buffer.append(event.peak_frequency_hz)
        self._fft_total_energy_buffer.append(event.total_energy)

        # Debug: Log real data being added (count real vs placeholder events)
        if (
            DebugConstants.FFT_DEBUG_MIN_BUFFER
            <= len(self._fft_magnitude_buffer)
            <= DebugConstants.FFT_DEBUG_MAX_BUFFER
        ):
            self.logger.info(
                "FFT REAL DATA: magnitude=%.3f, freq=%.1f Hz, buffer_len=%d",
                event.peak_magnitude,
                event.peak_frequency_hz,
                len(self._fft_magnitude_buffer),
            )

        # Buffer size automatically maintained by deque maxlen - no manual trimming needed

        # Update current FFT state
        self._current_fft_magnitude = event.peak_magnitude
        self._current_fft_peak_freq = event.peak_frequency_hz
        self._current_fft_total_energy = event.total_energy

        # Force Rich Live refresh when we receive real data
        if self._live_display and self._is_running:
            try:
                # Rebuild and update the entire layout when we get new data
                updated_layout = self._build_display_layout()
                self._live_display.update(updated_layout)
                self._live_display.refresh()
            except Exception as e:
                self.logger.debug("Failed to refresh live display: %s", e)

    def _on_probability_event(self, event: MorseProbabilityEvent) -> None:
        """Handle Morse probability events for pattern visualization."""
        # Store event timestamp for proper time synchronization with magnitude events
        event_time_us = event.timestamp
        event_time_s = event_time_us / 1_000_000.0  # Convert to seconds for display

        # Debug: Check timing synchronization
        if self.enable_debug_logging and len(self._time_buffer) > 0:
            last_magnitude_time = self._time_buffer[-1]
            time_diff_ms = abs(event_time_s - last_magnitude_time) * 1000
            if time_diff_ms > DebugConstants.TIME_DIFF_WARNING_MS:
                self.logger.debug("Probability event timing drift: %.1fms from magnitude event", time_diff_ms)

        # Add to probability buffers
        self._prob_dit_buffer.append(event.prob_dit)
        self._prob_dash_buffer.append(event.prob_dash)
        self._prob_letter_buffer.append(event.prob_letter_space)
        self._prob_word_buffer.append(event.prob_word_space)
        self._prob_time_buffer.append(event_time_s)

        # Buffer size automatically maintained by deque maxlen - no manual trimming needed

        # Update current probability state
        self._current_prob_dit = event.prob_dit
        self._current_prob_dash = event.prob_dash
        self._current_prob_letter = event.prob_letter_space
        self._current_prob_word = event.prob_word_space

        # Note: Display updates are now handled by Rich Live timer at configured FPS
        # Removed event-driven updates to fix scrolling bug and improve performance

    def _on_error_event(self, event: ErrorEvent) -> None:
        """Handle error events."""
        self._error_count += 1
        if self.enable_debug_logging:
            self.logger.debug("Error event received: %s", event.message)

    def _prime_buffers_with_placeholder_data(self) -> None:
        """Prime all buffers with placeholder data so display renders immediately."""
        import math

        # Prime FFT buffer with a sine wave pattern (simulates 600 Hz signal)
        for i in range(BufferConstants.FFT_PRIMING_POINTS):
            magnitude = 0.5 + 0.3 * math.sin(i * 0.2)  # Sine wave between 0.2-0.8
            self._fft_magnitude_buffer.append(magnitude)
            self._fft_peak_freq_buffer.append(600.0)  # Target frequency
            self._fft_total_energy_buffer.append(magnitude * 1000)

        # Prime signal magnitude buffer with similar pattern
        for i in range(BufferConstants.SIGNAL_PRIMING_POINTS):
            signal = 0.6 * math.sin(i * 0.1) + 0.1 * math.sin(i * 0.3)  # Complex waveform
            self._magnitude_buffer.append(signal)
            self._threshold_buffer.append(SignalConstants.DEFAULT_THRESHOLD)
            self._binary_buffer.append(abs(signal) > SignalConstants.DEFAULT_THRESHOLD)
            self._time_buffer.append(i * 0.02)  # 20ms per sample

        # Prime probability buffers with realistic morse patterns
        for i in range(30):
            # Simulate morse pattern: dit-dash-dit pattern
            if i % 10 < 3:  # Dit
                dit_prob, dash_prob = 0.8, 0.1
            elif i % 10 < 7:  # Dash
                dit_prob, dash_prob = 0.1, 0.9
            else:  # Space
                dit_prob, dash_prob = 0.0, 0.0

            self._prob_dit_buffer.append(dit_prob)
            self._prob_dash_buffer.append(dash_prob)
            self._prob_letter_buffer.append(0.1 if i % 10 == 7 else 0.0)
            self._prob_word_buffer.append(0.1 if i % 30 == 29 else 0.0)
            self._prob_time_buffer.append(i * 0.1)

        # Set initial current values
        self._current_fft_magnitude = 0.5
        self._current_fft_peak_freq = 600.0
        self._current_magnitude = 0.0
        self._current_threshold = SignalConstants.DEFAULT_THRESHOLD

        self.logger.debug(
            "Buffers primed with placeholder data: FFT=%d, signal=%d, prob=%d",
            len(self._fft_magnitude_buffer),
            len(self._magnitude_buffer),
            len(self._prob_dit_buffer),
        )

"""Graphics display component for real-time signal analysis.

This module provides comprehensive real-time visualization capabilities
including ASCII, Braille, and Plotly backends for signal analysis.
Designed for both development and production use.
"""

import shutil

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
from util.graph.time_series_graph import TimeSeriesGraph

from .constants import (
    BufferConstants,
    DebugConstants,
    SignalConstants,
)
from .keys import GraphicsKey
from .schema import GraphicsSchema


def resolve_display_width(config_width: int) -> int:
    """Resolve display width from configuration value.

    Args:
        config_width: 0 for auto terminal detection, or fixed width integer

    Returns:
        Integer width in characters, clamped to 40-200 range
    """
    if config_width == 0:
        # Auto detection mode
        try:
            terminal_size = shutil.get_terminal_size()
            width = terminal_size.columns
            # Clamp to reasonable bounds for graphics display
            width = max(40, min(200, width))
            return width
        except OSError:
            # Fallback if terminal size detection fails (non-interactive environment)
            return 80
    else:
        # Fixed width mode - clamp to safe bounds
        return max(40, min(200, config_width))


class GraphicsDisplay(ConfigurableBase):
    """Comprehensive real-time graphics display for signal analysis.

    Provides multi-backend visualization capabilities including ASCII, Braille,
    and Plotly for signal analysis and debugging. Supports both development
    workflows and production monitoring.

    Features:
    - Multi-panel dashboard with FFT, magnitude, and probability displays
    - Multiple backend support: ASCII (universal), Braille (high-res), Plotly (interactive)
    - SSH-compatible terminal interface with Rich layouts
    - Real-time scrolling with synchronized time windows
    - Event-driven updates from morse decoder components
    """

    # ConfigurableBase requirements
    CONFIG_SCHEMA = GraphicsSchema
    CONFIG_SECTION = "graphics"
    CONFIG_KEYS = GraphicsKey

    def __init__(self, cfg_mgr, overrides=None) -> None:
        """Initialize graphics display with event subscriptions.

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

        # Override config width with actual terminal width only if no explicit override was provided
        actual_width = self._console.size.width
        width_was_overridden = overrides and "display_width_chars" in overrides
        if actual_width > 40 and not width_was_overridden:  # Only override if no explicit width was set
            self.display_width_chars = actual_width
            self.logger.debug("Using actual terminal width: %d chars", actual_width)
        elif width_was_overridden:
            self.logger.debug("Keeping explicit width override: %d chars", self.display_width_chars)

        # Debug: Event handler call counter
        self._fft_event_count = 0

        # Debug: Instance ID for tracking multiple instances
        self._instance_id = id(self)

        # Note: Magnitude TimeSeriesGraph created after time_window_sec calculation

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

        # CLEANUP: Old manual backend management removed - now using TimeSeriesGraph only

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

        # Load graphics mode first
        self.mode = self._cfg_section.get_string(GraphicsKey.MODE)
        self.enabled = self.mode != "disabled"  # Derived from mode

        # Resolve display width (0 = auto detection, >0 = fixed width)
        config_width = self._cfg_section.get_int(GraphicsKey.DISPLAY_WIDTH_CHARS)
        self.display_width_chars = resolve_display_width(config_width)

        # Log width resolution for transparency
        if config_width == 0:
            self.logger.info("Width: AUTO detected terminal size: %d chars", self.display_width_chars)
        else:
            self.logger.info("Width: Fixed configuration: %d → %d chars", config_width, self.display_width_chars)
        self.display_height_chars = self._cfg_section.get_int(GraphicsKey.DISPLAY_HEIGHT_CHARS)
        self.refresh_rate_fps = self._cfg_section.get_int(GraphicsKey.REFRESH_RATE_FPS)
        self.buffer_size_sec = self._cfg_section.get_double(GraphicsKey.BUFFER_SIZE_SEC)
        self.log_level = self._cfg_section.get_string(GraphicsKey.LOG_LEVEL)
        self.backend_type = self.mode if self.enabled else "disabled"

        # Register dynamic logging configuration to override app log level
        self._cfg_mgr.register_logging_config(__name__, default_level=self.log_level)

        # Note: timing parameters moved to application config where they belong

        # REMOVED: Legacy buffer size calculations - now handled by TimeSeriesGraph

        # REMOVED: Legacy buffer declarations - now using TimeSeriesGraph for all data management

        # PHASE 3: Replace complex buffer management with clean TimeSeriesGraph API
        # Calculate time window based on current configuration
        time_window_sec = max(5.0, self.buffer_size_sec)  # At least 5 seconds

        # FIXED: Use full display width for TimeSeriesGraph to avoid blank columns
        # The TimeSeriesGraph should use the full resolution, margin handling is done in display layout
        full_chart_width = self.display_width_chars  # Use full width for maximum resolution

        # Calculate expected sample rates from typical decoder behavior
        # Magnitude events: Audio chunks typically processed every 20ms
        chunk_size_ms = 20  # Typical audio chunk size
        magnitude_sample_rate_hz = 1000.0 / chunk_size_ms

        # Probability events: Convolution typically runs every 40ms (slower than magnitude)
        convolution_interval_ms = 40  # Typical convolution interval
        probability_sample_rate_hz = 1000.0 / convolution_interval_ms

        # Store sample rates as instance attributes for test access
        self._magnitude_sample_rate_hz = magnitude_sample_rate_hz
        self._probability_sample_rate_hz = probability_sample_rate_hz

        # SYNCHRONIZED SCROLLING: Use the fastest rate for all graphs to ensure uniform visual scrolling
        self.unified_scroll_rate_hz = max(magnitude_sample_rate_hz, probability_sample_rate_hz)

        # Create TimeSeriesGraph instances for each probability type
        # Fix: Use same width calculation as FFT and MAGNITUDE for consistency
        # FIXED SCALING: Probability graphs should use 0.0-1.0 range (no auto-scaling)
        self._prob_dit_graph = TimeSeriesGraph(
            width=full_chart_width,  # Use same full width as FFT and magnitude
            height=SignalConstants.PROBABILITY_CHART_ROWS,
            time_window_sec=time_window_sec,
            backend=self.backend_type,  # Config-driven backend selection
            title="Dit Probability",
            sample_rate_hz=self.unified_scroll_rate_hz,  # Unified rate for synchronized scrolling
            playback_speed=1.0,  # Default real-time
            y_min=0.0,  # Fixed probability range 0.0-1.0
            y_max=1.0,  # No auto-scaling for consistent comparison
            auto_scale=False,
        )

        self._prob_dash_graph = TimeSeriesGraph(
            width=full_chart_width,
            height=SignalConstants.PROBABILITY_CHART_ROWS,
            time_window_sec=time_window_sec,
            backend=self.backend_type,  # Config-driven backend selection
            title="Dash Probability",
            sample_rate_hz=self.unified_scroll_rate_hz,  # Unified rate for synchronized scrolling
            playback_speed=1.0,  # Default real-time
            y_min=0.0,  # Fixed probability range 0.0-1.0
            y_max=1.0,  # No auto-scaling for consistent comparison
            auto_scale=False,
        )

        self._prob_letter_graph = TimeSeriesGraph(
            width=full_chart_width,
            height=SignalConstants.PROBABILITY_CHART_ROWS,
            time_window_sec=time_window_sec,
            backend=self.backend_type,  # Config-driven backend selection
            title="Letter Space Probability",
            sample_rate_hz=self.unified_scroll_rate_hz,  # Unified rate for synchronized scrolling
            playback_speed=1.0,  # Default real-time
            y_min=0.0,  # Fixed probability range 0.0-1.0
            y_max=1.0,  # No auto-scaling for consistent comparison
            auto_scale=False,
        )

        self._prob_word_graph = TimeSeriesGraph(
            width=full_chart_width,
            height=SignalConstants.PROBABILITY_CHART_ROWS,
            time_window_sec=time_window_sec,
            backend=self.backend_type,  # Config-driven backend selection
            title="Word Space Probability",
            sample_rate_hz=self.unified_scroll_rate_hz,  # Unified rate for synchronized scrolling
            playback_speed=1.0,  # Default real-time
            y_min=0.0,  # Fixed probability range 0.0-1.0
            y_max=1.0,  # No auto-scaling for consistent comparison
            auto_scale=False,
        )

        # PHASE 4: Create magnitude TimeSeriesGraph for consistency
        # FIXED SCALING: Normalized magnitude should use 0.0-1.0 range (no auto-scaling)
        self._magnitude_graph = TimeSeriesGraph(
            width=full_chart_width,
            height=6,  # Same height as main magnitude chart
            time_window_sec=time_window_sec,
            backend=self.backend_type,  # Config-driven backend selection
            title="Filtered Magnitude",
            sample_rate_hz=self.unified_scroll_rate_hz,  # Unified rate for synchronized scrolling
            playback_speed=1.0,  # Default real-time
            y_min=0.0,  # Fixed normalized range 0.0-1.0
            y_max=1.0,  # No auto-scaling for consistent comparison
            auto_scale=False,
        )

        self.logger.info(
            "Phase 4: ALL TimeSeriesGraph instances created - time_window=%.1fs, full_width=%d (display=%d)",
            time_window_sec,
            full_chart_width,
            self.display_width_chars,
        )
        self.logger.info(
            "Sample rates: magnitude=%.1fHz (chunk=%dms), probability=%.1fHz (conv=%dms), unified_scroll=%.1fHz",
            magnitude_sample_rate_hz,
            chunk_size_ms,
            probability_sample_rate_hz,
            convolution_interval_ms,
            self.unified_scroll_rate_hz,
        )
        # CLEANUP: Create FFT TimeSeriesGraph to replace old manual backend system
        # FFT data comes at audio processing rate, not convolution rate

        self._fft_graph = TimeSeriesGraph(
            width=full_chart_width,
            height=6,  # Same height as other charts
            time_window_sec=time_window_sec,
            backend=self.backend_type,  # Config-driven backend selection
            title="FFT Magnitude Spectrum",
            sample_rate_hz=self.unified_scroll_rate_hz,  # Unified rate for synchronized scrolling
            playback_speed=1.0,  # Default real-time
        )

        self.logger.info("CLEANUP: All graphics now use unified TimeSeriesGraph - NO MORE FRAGMENTATION")
        self.logger.info("All charts: FFT, Magnitude, and Probability use identical system")

    def _on_reconfiguration(self) -> None:
        """Handle reconfiguration - reinitialize backends if needed."""
        # CLEANUP: No need to reinitialize - TimeSeriesGraph handles everything automatically
        self.logger.info(
            "DebugDisplay reconfigured: backend=%s, size=%dx%d",
            self.backend_type,
            self.display_width_chars,
            self.display_height_chars,
        )

    @property
    def _magnitude_backend(self):
        """Expose magnitude graph backend for testing."""
        return self._magnitude_graph

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

    def _compress_repeated_values(self, data: list[float], tolerance: float = 1e-6) -> list[float]:
        """Compress repeated cached values to match actual update rate.

        The convolution decoder caches probability values and publishes them every 20ms,
        creating ~25 repeated values for each actual 500ms convolution update.
        This function removes the repetition to restore the original update rate.

        Args:
            data: List of probability values with repeated cached values
            tolerance: Tolerance for detecting repeated values (accounting for floating point precision)

        Returns:
            Compressed list with repeated values removed
        """
        if len(data) <= 1:
            return data

        compressed = [data[0]]  # Always keep first value

        for i in range(1, len(data)):
            # Check if this value is significantly different from the last kept value
            if abs(data[i] - compressed[-1]) > tolerance:
                compressed.append(data[i])

        # Debug logging for compression efficiency
        if len(data) > 0:
            compression_ratio = len(data) / len(compressed) if len(compressed) > 0 else 1
            if compression_ratio > 2:  # Only log significant compression
                self.logger.debug(
                    "Compressed probability data: %d -> %d samples (%.1fx compression)",
                    len(data),
                    len(compressed),
                    compression_ratio,
                )

        return compressed

    # REMOVED: _clear_backend_data_only() - no longer needed with TimeSeriesGraph

    # CLEANUP: _initialize_uilt_backends() method removed - now using TimeSeriesGraph only

    def start_display(self) -> None:
        """Start the live ASCII display."""
        if self._is_running:
            self.logger.warning("Display already running")
            return

        try:
            # Handle Plotly backend differently - it opens in browser
            if self.backend_type == "plotly":
                self._is_running = True
                self.logger.info("Plotly debug display started - graphs will open in browser")
                self._start_plotly_dashboard()
            else:
                # Terminal-based backends (ASCII/Braille)
                layout = self._build_display_layout()
                # Use Rich Live for layout management, but don't over-update it
                self._live_display = Live(layout, console=self._console, refresh_per_second=self.refresh_rate_fps)
                self._live_display.start()
                self._is_running = True

                self.logger.info("ASCII debug display started")

        except Exception as e:
            self.logger.exception("Failed to start display: %s", e)
            raise

    def _start_plotly_dashboard(self) -> None:
        """Initialize Plotly dashboard with all graphs in browser."""
        import tempfile
        import time
        import webbrowser

        try:
            # Create a combined dashboard HTML with all graphs
            html_content = (
                """
<!DOCTYPE html>
<html>
<head>
    <title>Morse Code Decoder - Real-time Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .graph { background: white; border-radius: 8px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .full-width { grid-column: 1 / -1; }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>🎵 Morse Code Decoder - Real-time Dashboard</h1>
    <div class="info">
        <strong>Live Dashboard Active:</strong> Graphs will automatically update as new data arrives.
        <strong>Sample Rate:</strong> All graphs synchronized at """
                + f"{self.unified_scroll_rate_hz}"
                + """Hz for smooth scrolling.
    </div>
    <div class="dashboard">
        <div class="graph full-width" id="fft-graph">
            <div>FFT Peak Magnitude</div>
        </div>
        <div class="graph full-width" id="magnitude-graph">
            <div>Normalized Magnitude</div>
        </div>
        <div class="graph" id="dit-graph">
            <div>Dit Probability</div>
        </div>
        <div class="graph" id="dash-graph">
            <div>Dash Probability</div>
        </div>
        <div class="graph" id="letter-graph">
            <div>Letter Probability</div>
        </div>
        <div class="graph" id="word-graph">
            <div>Word Probability</div>
        </div>
    </div>

    <script>
        // Initialize empty plots that will be updated by the backend
        const config = {displayModeBar: true, displaylogo: false, responsive: true};
        const layout = {
            margin: {l: 50, r: 20, t: 40, b: 40},
            xaxis: {title: 'Time (s)'},
            yaxis: {title: 'Amplitude'},
            hovermode: 'x unified'
        };

        // Create placeholder plots
        Plotly.newPlot('fft-graph', [], {...layout, title: 'FFT Peak Magnitude'}, config);
        Plotly.newPlot('magnitude-graph', [], {...layout, title: 'Normalized Magnitude'}, config);
        Plotly.newPlot('dit-graph', [], {...layout, title: 'Dit Probability'}, config);
        Plotly.newPlot('dash-graph', [], {...layout, title: 'Dash Probability'}, config);
        Plotly.newPlot('letter-graph', [], {...layout, title: 'Letter Probability'}, config);
        Plotly.newPlot('word-graph', [], {...layout, title: 'Word Probability'}, config);

        console.log('Morse Code Decoder Dashboard initialized');
        console.log('Graphs will be updated via TimeSeriesGraph.show() calls');
    </script>
</body>
</html>"""
            )

            # Save to temp file and open in browser
            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
                f.write(html_content)
                self._plotly_dashboard_file = f.name

            webbrowser.open(f"file://{self._plotly_dashboard_file}")
            self.logger.info("Plotly dashboard opened in browser: %s", self._plotly_dashboard_file)

            # Show individual graphs as they receive data
            time.sleep(1)  # Give browser time to load
            if hasattr(self, "_fft_graph"):
                self._fft_graph.show()
            if hasattr(self, "_magnitude_graph"):
                self._magnitude_graph.show()

        except Exception as e:
            self.logger.exception("Failed to start Plotly dashboard: %s", e)
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
            # Each probability chart gets content rows + 2 for Panel borders
            prob_layout_size = SignalConstants.PROBABILITY_CHART_ROWS + 2
            layout.split_column(
                Layout(name="header", size=2),
                Layout(name="fft_chart", size=6),
                Layout(name="magnitude_chart", size=6),
                Layout(name="prob_dit", size=prob_layout_size),
                Layout(name="prob_dash", size=prob_layout_size),
                Layout(name="prob_letter", size=prob_layout_size),
                Layout(name="prob_word", size=prob_layout_size),
                Layout(name="status", size=6),
            )

            # Header section with detailed UILT information
            header_text = Text.assemble(
                ("🎯 UILT ", "bold blue"),
                ("TimeSeriesGraph Unified System", "bold white"),
                (" | ", "dim white"),
                ("All Braille Backend", "bright_cyan"),
                (" | ", "dim white"),
                ("Full Width Graphics", "bright_green"),
                (" | SSH-Compatible Real-Time Display", "dim white"),
            )
            layout["header"].update(
                Panel(header_text, style="blue", title="Universal Interactive Live Terminal (UILT)")
            )

            # FFT chart section (frequency domain visualization)
            # CLEANUP: Use TimeSeriesGraph for FFT - consistent with all other charts
            fft_chart = self._render_time_series_chart(self._fft_graph)
            fft_stats = self._fft_graph.get_stats()
            fft_title = (
                f"FFT Peak Magnitude | Samples: {fft_stats['sample_count']} | "
                f"Rate: {fft_stats['calculated_sample_rate_hz']:.1f}Hz | "
                f"Backend: {fft_stats['backend']}"
            )
            layout["fft_chart"].update(Panel(fft_chart, title=fft_title, style="cyan"))

            # Magnitude chart section (main time-series display)
            # PHASE 4: Use TimeSeriesGraph for magnitude - consistent with probability charts
            magnitude_chart = self._render_time_series_chart(self._magnitude_graph)
            magnitude_stats = self._magnitude_graph.get_stats()
            magnitude_title = (
                f"Normalized Magnitude (-1 to +1) | Samples: {magnitude_stats['sample_count']} | "
                f"Rate: {magnitude_stats['calculated_sample_rate_hz']:.1f}Hz | "
                f"Backend: {magnitude_stats['backend']}"
            )
            layout["magnitude_chart"].update(Panel(magnitude_chart, title=magnitude_title, style="green"))

            # Individual probability charts - full width, 2 rows each, same timescale as main charts
            # PHASE 3: Use TimeSeriesGraph API - clean, automatic buffer management
            dit_chart = self._render_time_series_chart(self._prob_dit_graph)
            dit_stats = self._prob_dit_graph.get_stats()
            dit_title = (
                f"Dit Probability (0-1) | Samples: {dit_stats['sample_count']} | "
                f"Rate: {dit_stats['calculated_sample_rate_hz']:.1f}Hz | "
                f"Current: {self._current_prob_dit:.2f}"
            )
            layout["prob_dit"].update(Panel(dit_chart, title=dit_title, style="bright_blue"))

            dash_chart = self._render_time_series_chart(self._prob_dash_graph)
            dash_stats = self._prob_dash_graph.get_stats()
            dash_title = (
                f"Dash Probability (0-1) | Samples: {dash_stats['sample_count']} | "
                f"Rate: {dash_stats['calculated_sample_rate_hz']:.1f}Hz | "
                f"Current: {self._current_prob_dash:.2f}"
            )
            layout["prob_dash"].update(Panel(dash_chart, title=dash_title, style="bright_red"))

            letter_chart = self._render_time_series_chart(self._prob_letter_graph)
            letter_stats = self._prob_letter_graph.get_stats()
            letter_title = (
                f"Letter Space Probability (0-1) | Samples: {letter_stats['sample_count']} | "
                f"Rate: {letter_stats['calculated_sample_rate_hz']:.1f}Hz | "
                f"Current: {self._current_prob_letter:.2f}"
            )
            layout["prob_letter"].update(Panel(letter_chart, title=letter_title, style="bright_magenta"))

            word_chart = self._render_time_series_chart(self._prob_word_graph)
            word_stats = self._prob_word_graph.get_stats()
            word_title = (
                f"Word Space Probability (0-1) | Samples: {word_stats['sample_count']} | "
                f"Rate: {word_stats['calculated_sample_rate_hz']:.1f}Hz | "
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

    # REMOVED: _render_magnitude_chart_OBSOLETE() - now using TimeSeriesGraph

    # REMOVED: _render_fft_chart_OBSOLETE() - now using TimeSeriesGraph

    # REMOVED: _render_probability_chart() - Dead code (side-by-side charts never used)

    # REMOVED: _render_probability_section() - Dead code (side-by-side section never used)

    def _render_time_series_chart(self, time_series_graph: TimeSeriesGraph) -> Text:
        """Render TimeSeriesGraph output to Rich Text format.

        Args:
            time_series_graph: TimeSeriesGraph instance to render

        Returns:
            Rich Text object containing the rendered chart
        """
        chart_text = Text()

        try:
            # Get rendered lines from TimeSeriesGraph - all buffer management handled automatically!
            lines = time_series_graph.render()

            if not lines:
                chart_text.append("No data available", style="dim")
                return chart_text

            # Convert each line to Rich Text
            for line in lines:
                chart_text.append(line + "\n", style="white")

            # Remove trailing newline
            chart_text.rstrip()

        except Exception as e:
            self.logger.debug("TimeSeriesGraph rendering failed: %s", e)
            chart_text.append(f"Render error: {str(e)}", style="red")

        return chart_text

    # REMOVED: _render_full_width_probability_chart_OBSOLETE() - now using TimeSeriesGraph

    # REMOVED: _get_backend_info(), _get_resolution_info(), _ensure_chart_height()
    # - helper methods for obsolete renderers

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

        # Buffer info from TimeSeriesGraph stats
        magnitude_stats = self._magnitude_graph.get_stats()
        buffer_pct = magnitude_stats["buffer_utilization"] * 100
        status_text.append(
            f"Buffer: {magnitude_stats['buffer_size']}/{magnitude_stats['max_buffer_size']} ({buffer_pct:.0f}%)",
            style="dim white",
        )

        if self._error_count > 0:
            status_text.append(f" | Errors: {self._error_count}", style="bold red")

        return status_text

    def _on_magnitude_event(self, event: FilteredMagnitudeEvent) -> None:
        """Handle filtered magnitude events using sample-driven TimeSeriesGraph API."""
        # Guard against early event calls before initialization completes
        if not hasattr(self, "_chunk_counter"):
            self.logger.warning("Magnitude event received before initialization complete, ignoring")
            return

        self._chunk_counter += 1

        # SAMPLE-DRIVEN: No timestamps! Let graph scroll at natural sample rate
        self._magnitude_graph.add_data_point(event.magnitude_norm)

        # REMOVED: Legacy buffer management - now handled by TimeSeriesGraph

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
        """Handle FFT spectrum events using clean TimeSeriesGraph API."""
        # FIXED: Use sample-driven approach (no timestamp) for consistent scrolling with other graphs
        # This eliminates timing synchronization issues between different event types
        self._fft_graph.add_data_point(event.peak_magnitude)

        # REMOVED: Legacy buffer management - now handled by TimeSeriesGraph

        # Debug: Log real data being added (using TimeSeriesGraph stats)
        fft_stats = self._fft_graph.get_stats()
        if DebugConstants.FFT_DEBUG_MIN_BUFFER <= fft_stats["buffer_size"] <= DebugConstants.FFT_DEBUG_MAX_BUFFER:
            self.logger.info(
                "FFT REAL DATA: magnitude=%.3f, freq=%.1f Hz, buffer_len=%d",
                event.peak_magnitude,
                event.peak_frequency_hz,
                fft_stats["buffer_size"],
            )

        # Buffer size automatically maintained by TimeSeriesGraph - no manual trimming needed

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
        """Handle Morse probability events using sample-driven TimeSeriesGraph API."""
        # SAMPLE-DRIVEN: No timestamps! Each graph scrolls at its configured sample rate
        self._prob_dit_graph.add_data_point(event.prob_dit)
        self._prob_dash_graph.add_data_point(event.prob_dash)
        self._prob_letter_graph.add_data_point(event.prob_letter_space)
        self._prob_word_graph.add_data_point(event.prob_word_space)

        # PHASE 4: Eliminated dual graphics system - now only use TimeSeriesGraph
        # Calculate dominant type for logging only
        probabilities = [event.prob_dit, event.prob_dash, event.prob_letter_space, event.prob_word_space]
        dominant_prob = max(probabilities)
        prob_types = ["dit", "dash", "letter", "word"]
        dominant_type = prob_types[probabilities.index(dominant_prob)]

        # LEGACY: Keep current probability state for other debug displays
        self._current_prob_dit = event.prob_dit
        self._current_prob_dash = event.prob_dash
        self._current_prob_letter = event.prob_letter_space
        self._current_prob_word = event.prob_word_space

        # Debug logging for timing synchronization
        if self.log_level == "DEBUG":
            self.logger.debug(
                "PHASE 3: TimeSeriesGraph + unified graphics: dominant=%s(%.3f)", dominant_type, dominant_prob
            )
        # Removed event-driven updates to fix scrolling bug and improve performance

    def _on_error_event(self, event: ErrorEvent) -> None:
        """Handle error events."""
        self._error_count += 1
        if self.log_level == "DEBUG":
            self.logger.debug("Error event received: %s", event.message)

    def _prime_buffers_with_placeholder_data(self) -> None:
        """Prime TimeSeriesGraphs with placeholder data so display renders immediately."""
        import math

        # Prime FFT graph with a sine wave pattern (simulates 600 Hz signal)
        # FIXED: Use sample-driven approach (no timestamps) for consistent scrolling
        for i in range(BufferConstants.FFT_PRIMING_POINTS):
            magnitude = 0.5 + 0.3 * math.sin(i * 0.2)  # Sine wave between 0.2-0.8
            self._fft_graph.add_data_point(magnitude)

        # Prime magnitude graph with similar pattern
        for i in range(BufferConstants.SIGNAL_PRIMING_POINTS):
            signal = 0.6 * math.sin(i * 0.1) + 0.1 * math.sin(i * 0.3)  # Complex waveform
            self._magnitude_graph.add_data_point(signal)

        # Prime probability graphs with realistic morse patterns
        for i in range(30):
            # Simulate morse pattern: dit-dash-dit pattern
            if i % 10 < 3:  # Dit
                dit_prob, dash_prob = 0.8, 0.1
            elif i % 10 < 7:  # Dash
                dit_prob, dash_prob = 0.1, 0.9
            else:  # Space
                dit_prob, dash_prob = 0.0, 0.0

            self._prob_dit_graph.add_data_point(dit_prob)
            self._prob_dash_graph.add_data_point(dash_prob)
            self._prob_letter_graph.add_data_point(0.1 if i % 10 == 7 else 0.0)
            self._prob_word_graph.add_data_point(0.1 if i % 30 == 29 else 0.0)

        # Set initial current values
        self._current_fft_magnitude = 0.5
        self._current_fft_peak_freq = 600.0
        self._current_magnitude = 0.0
        self._current_threshold = SignalConstants.DEFAULT_THRESHOLD

        # Get stats from TimeSeriesGraphs for logging
        fft_stats = self._fft_graph.get_stats()
        magnitude_stats = self._magnitude_graph.get_stats()
        prob_stats = self._prob_dit_graph.get_stats()

        self.logger.debug(
            "TimeSeriesGraphs primed with placeholder data: FFT=%d, signal=%d, prob=%d",
            fft_stats["buffer_size"],
            magnitude_stats["buffer_size"],
            prob_stats["buffer_size"],
        )

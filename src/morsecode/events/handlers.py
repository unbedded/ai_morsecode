"""Built-in event handlers for common use cases.

This module provides ready-to-use event handlers and middleware for
logging, metrics collection, debugging, and other cross-cutting concerns.
"""

import logging
import time
from collections import defaultdict, deque
from typing import Any, TextIO

from .types import (
    AudioChunkEvent,
    BaseEvent,
    ErrorEvent,
    MetricsEvent,
    MorsePatternEvent,
    PipelineStateEvent,
    TextDecodedEvent,
    ToneDetectedEvent,
)

logger = logging.getLogger(__name__)


class LoggingEventHandler:
    """Event handler that logs events with configurable verbosity.

    Provides structured logging for different event types with appropriate
    log levels and formatting.
    """

    def __init__(
        self,
        log_level: int = logging.INFO,
        include_audio_chunks: bool = False,
        include_metrics: bool = True,
    ):
        """Initialize logging event handler.

        Args:
            log_level: Minimum log level for event logging
            include_audio_chunks: Whether to log audio chunk events (very verbose)
            include_metrics: Whether to log metrics events
        """
        self.logger = logging.getLogger(f"{__name__}.LoggingEventHandler")
        self.log_level = log_level
        self.include_audio_chunks = include_audio_chunks
        self.include_metrics = include_metrics

    def __call__(self, event: BaseEvent) -> None:
        """Handle an event by logging it appropriately."""
        if not self.logger.isEnabledFor(self.log_level):
            return

        # Skip audio chunk events unless explicitly enabled (too verbose)
        if isinstance(event, AudioChunkEvent) and not self.include_audio_chunks:
            return

        # Skip metrics events unless explicitly enabled
        if isinstance(event, MetricsEvent) and not self.include_metrics:
            return

        # Log different event types with appropriate levels and formatting
        if isinstance(event, ErrorEvent):
            self._log_error_event(event)
        elif isinstance(event, TextDecodedEvent):
            self._log_text_event(event)
        elif isinstance(event, ToneDetectedEvent):
            self._log_tone_event(event)
        elif isinstance(event, MorsePatternEvent):
            self._log_pattern_event(event)
        elif isinstance(event, PipelineStateEvent):
            self._log_state_event(event)
        elif isinstance(event, MetricsEvent):
            self._log_metrics_event(event)
        elif isinstance(event, AudioChunkEvent):
            self._log_audio_event(event)
        else:
            self._log_generic_event(event)

    def _log_error_event(self, event: ErrorEvent) -> None:
        """Log error events with high visibility."""
        log_level = logging.ERROR if not event.recoverable else logging.WARNING
        self.logger.log(log_level, f"[{event.component}] {event.error_type}: {event.message}")

    def _log_text_event(self, event: TextDecodedEvent) -> None:
        """Log decoded text events as information."""
        marker = "🔤" if event.is_complete_word else "🔠"
        self.logger.info(
            f"{marker} Decoded: '{event.text}' "
            f"[{event.pattern_sequence}] "
            f"(WPM: {event.wpm_estimate:.1f}, confidence: {event.confidence:.2f})"
        )

    def _log_tone_event(self, event: ToneDetectedEvent) -> None:
        """Log tone detection events."""
        status = "🎵 TONE" if event.detected else "🔇 SILENCE"
        self.logger.debug(
            f"{status} @ {event.frequency:.0f}Hz "
            f"(confidence: {event.confidence:.2f}, SNR: {event.snr_db:.1f}dB)"
        )

    def _log_pattern_event(self, event: MorsePatternEvent) -> None:
        """Log Morse pattern recognition events."""
        pattern_symbols = {"dot": "●", "dash": "▬", "letter_space": "·", "word_space": "   "}
        symbol = pattern_symbols.get(event.pattern_type, event.pattern_type)
        self.logger.debug(
            f"Pattern: {symbol} ({event.pattern_type}) "
            f"[{event.duration_ms:.0f}ms, WPM: {event.wpm_estimate:.1f}]"
        )

    def _log_state_event(self, event: PipelineStateEvent) -> None:
        """Log pipeline state changes."""
        state_symbols = {
            "starting": "🚀",
            "processing": "⚙️",
            "paused": "⏸️",
            "stopped": "⏹️",
            "error": "❌",
        }
        symbol = state_symbols.get(event.state, "ℹ️")
        message_part = f": {event.message}" if event.message else ""
        self.logger.info(f"{symbol} [{event.component}] {event.state.upper()}{message_part}")

    def _log_metrics_event(self, event: MetricsEvent) -> None:
        """Log metrics events."""
        self.logger.debug(f"📊 [{event.component}] {event.metric_name}: {event.formatted_value}")

    def _log_audio_event(self, event: AudioChunkEvent) -> None:
        """Log audio chunk events (very verbose)."""
        self.logger.debug(
            f"🎧 Audio chunk #{event.chunk_number}: "
            f"{len(event.chunk_data)} samples @ {event.sample_rate}Hz"
        )

    def _log_generic_event(self, event: BaseEvent) -> None:
        """Log unknown event types generically."""
        self.logger.debug(f"Event: {type(event).__name__}")


class MetricsEventHandler:
    """Event handler that collects and aggregates metrics.

    Provides real-time metrics collection with windowed averages,
    counters, and performance statistics.
    """

    def __init__(self, window_size: int = 100):
        """Initialize metrics collection.

        Args:
            window_size: Number of recent samples to keep for rolling averages
        """
        self.logger = logging.getLogger(f"{__name__}.MetricsEventHandler")
        self.window_size = window_size

        # Metrics storage
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}
        self.timeseries: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=window_size))
        self.start_time = time.time()

    def __call__(self, event: BaseEvent) -> None:
        """Process event for metrics collection."""
        # Update general counters
        event_type = type(event).__name__
        self.counters[f"events.{event_type}"] += 1
        self.counters["events.total"] += 1

        # Event-specific metrics
        if isinstance(event, ToneDetectedEvent):
            self._collect_tone_metrics(event)
        elif isinstance(event, TextDecodedEvent):
            self._collect_text_metrics(event)
        elif isinstance(event, ErrorEvent):
            self._collect_error_metrics(event)
        elif isinstance(event, MetricsEvent):
            self._collect_explicit_metrics(event)

        # Update event rate
        self._update_event_rate()

    def _collect_tone_metrics(self, event: ToneDetectedEvent) -> None:
        """Collect metrics from tone detection events."""
        self.counters["tone.detections"] += 1
        if event.detected:
            self.counters["tone.detected"] += 1
            self.timeseries["tone.frequency"].append(event.frequency)
            self.timeseries["tone.confidence"].append(event.confidence)
            self.timeseries["tone.snr_db"].append(event.snr_db)
        else:
            self.counters["tone.silence"] += 1

        # Update current values
        self.gauges["tone.current_frequency"] = event.frequency
        self.gauges["tone.current_confidence"] = event.confidence
        self.gauges["tone.current_snr"] = event.snr_db

    def _collect_text_metrics(self, event: TextDecodedEvent) -> None:
        """Collect metrics from text decoded events."""
        self.counters["text.characters"] += len(event.text)
        self.counters["text.decodings"] += 1

        if event.is_complete_word:
            self.counters["text.words"] += 1

        self.timeseries["text.wpm"].append(event.wpm_estimate)
        self.timeseries["text.confidence"].append(event.confidence)
        self.gauges["text.current_wpm"] = event.wpm_estimate

    def _collect_error_metrics(self, event: ErrorEvent) -> None:
        """Collect metrics from error events."""
        self.counters[f"errors.{event.error_type}"] += 1
        self.counters[f"errors.{event.component}"] += 1
        if not event.recoverable:
            self.counters["errors.critical"] += 1

    def _collect_explicit_metrics(self, event: MetricsEvent) -> None:
        """Store explicitly published metrics."""
        metric_key = f"{event.component}.{event.metric_name}"
        self.timeseries[metric_key].append(event.value)
        self.gauges[metric_key] = event.value

    def _update_event_rate(self) -> None:
        """Calculate and update event processing rate."""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            rate = self.counters["events.total"] / elapsed
            self.gauges["events.rate_per_second"] = rate

    def get_summary(self) -> dict[str, Any]:
        """Get comprehensive metrics summary.

        Returns:
            Dictionary containing all collected metrics and statistics
        """
        # Calculate averages for time series data
        averages = {}
        for key, values in self.timeseries.items():
            if values:
                averages[f"{key}.avg"] = sum(values) / len(values)
                averages[f"{key}.min"] = min(values)
                averages[f"{key}.max"] = max(values)
                averages[f"{key}.count"] = len(values)

        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "averages": averages,
            "uptime_seconds": time.time() - self.start_time,
            "window_size": self.window_size,
        }

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.counters.clear()
        self.gauges.clear()
        self.timeseries.clear()
        self.start_time = time.time()


class DebugEventHandler:
    """Event handler for debugging and development.

    Provides detailed event tracing with optional output to file
    for troubleshooting and development purposes.
    """

    def __init__(
        self,
        output_file: str | None = None,
        max_events: int = 1000,
        include_stack_info: bool = False,
    ):
        """Initialize debug event handler.

        Args:
            output_file: Optional file path for debug output
            max_events: Maximum number of events to keep in memory
            include_stack_info: Whether to include call stack information
        """
        self.logger = logging.getLogger(f"{__name__}.DebugEventHandler")
        self.output_file = output_file
        self.max_events = max_events
        self.include_stack_info = include_stack_info

        self.events_log: deque[dict[str, Any]] = deque(maxlen=max_events)
        self.file_handle: TextIO | None = None

        if output_file:
            try:
                self.file_handle = open(output_file, "w", encoding="utf-8")
                self.logger.info(f"Debug output directed to: {output_file}")
            except OSError as e:
                self.logger.error(f"Failed to open debug file {output_file}: {e}")

    def __call__(self, event: BaseEvent) -> None:
        """Process event for debug output."""
        timestamp = time.strftime("%H:%M:%S.%f", time.localtime(event.timestamp))[:-3]
        event_info = {
            "timestamp": timestamp,
            "type": type(event).__name__,
            "age_ms": event.age_ms,
            "data": self._extract_event_data(event),
        }

        # Add to memory log
        self.events_log.append(event_info)

        # Output to console and/or file
        output_line = self._format_event_line(event_info)

        # Always output to debug logger
        self.logger.debug(output_line)

        # Also output to file if configured
        if self.file_handle:
            try:
                self.file_handle.write(output_line + "\n")
                self.file_handle.flush()  # Ensure immediate write
            except OSError as e:
                self.logger.error(f"Failed to write debug output: {e}")

    def _extract_event_data(self, event: BaseEvent) -> dict[str, Any]:
        """Extract relevant data from event for debugging."""
        data = {}

        if isinstance(event, ToneDetectedEvent):
            data = {
                "detected": event.detected,
                "frequency": f"{event.frequency:.0f}Hz",
                "confidence": f"{event.confidence:.2f}",
                "snr": f"{event.snr_db:.1f}dB",
            }
        elif isinstance(event, TextDecodedEvent):
            data = {
                "text": repr(event.text),
                "pattern": event.pattern_sequence,
                "wpm": f"{event.wpm_estimate:.1f}",
                "is_word": event.is_complete_word,
            }
        elif isinstance(event, MorsePatternEvent):
            data = {
                "type": event.pattern_type,
                "duration": f"{event.duration_ms:.0f}ms",
                "wpm": f"{event.wpm_estimate:.1f}",
            }
        elif isinstance(event, ErrorEvent):
            data = {
                "error": event.error_type,
                "message": event.message,
                "component": event.component,
                "recoverable": event.recoverable,
            }
        elif isinstance(event, PipelineStateEvent):
            data = {"state": event.state, "component": event.component, "message": event.message}

        return data

    def _format_event_line(self, event_info: dict[str, Any]) -> str:
        """Format event information for output."""
        timestamp = event_info["timestamp"]
        event_type = event_info["type"]
        age = event_info["age_ms"]
        data = event_info["data"]

        # Format data as key=value pairs
        data_str = ", ".join(f"{k}={v}" for k, v in data.items()) if data else ""

        return f"[{timestamp}] {event_type:<20} (age: {age:5.1f}ms) {data_str}"

    def get_recent_events(self, count: int | None = None) -> list[dict[str, Any]]:
        """Get recent events from the debug log.

        Args:
            count: Number of recent events to return (None for all)

        Returns:
            List of recent event information dictionaries
        """
        if count is None:
            return list(self.events_log)
        else:
            return list(self.events_log)[-count:]

    def dump_events_to_file(self, filename: str) -> None:
        """Dump all logged events to a file.

        Args:
            filename: Path to output file
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("# Debug Event Dump\n")
                f.write(f"# Total events: {len(self.events_log)}\n\n")

                for event_info in self.events_log:
                    f.write(self._format_event_line(event_info) + "\n")

            self.logger.info(f"Dumped {len(self.events_log)} events to {filename}")
        except OSError as e:
            self.logger.error(f"Failed to dump events to {filename}: {e}")

    def close(self) -> None:
        """Close debug file handle if open."""
        if self.file_handle:
            try:
                self.file_handle.close()
            except OSError:
                pass
            finally:
                self.file_handle = None

    def __del__(self) -> None:
        """Cleanup when handler is destroyed."""
        self.close()


# Convenience middleware functions


def create_logging_middleware(log_level: int = logging.INFO) -> LoggingEventHandler:
    """Create logging middleware with specified log level.

    Args:
        log_level: Minimum log level for events

    Returns:
        Configured LoggingEventHandler that can be used as middleware
    """
    return LoggingEventHandler(log_level=log_level)


def create_metrics_middleware(window_size: int = 100) -> MetricsEventHandler:
    """Create metrics collection middleware.

    Args:
        window_size: Size of rolling window for averages

    Returns:
        Configured MetricsEventHandler for metrics collection
    """
    return MetricsEventHandler(window_size=window_size)


def create_debug_middleware(output_file: str | None = None) -> DebugEventHandler:
    """Create debug middleware for development.

    Args:
        output_file: Optional file for debug output

    Returns:
        Configured DebugEventHandler for debugging
    """
    return DebugEventHandler(output_file=output_file)

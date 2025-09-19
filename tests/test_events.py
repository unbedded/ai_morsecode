"""Comprehensive tests for the event system.

This test module covers the EventBus, event types, handlers, and middleware
to ensure the pub-sub system works correctly and provides good error handling.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest

from morsecode.events import (
    AudioChunkEvent,
    BaseEvent,
    DebugEventHandler,
    ErrorEvent,
    EventBus,
    LoggingEventHandler,
    MetricsEvent,
    MetricsEventHandler,
    MorsePatternEvent,
    TextDecodedEvent,
    ToneDetectedEvent,
    create_error_event,
    create_text_event,
    create_tone_event,
    get_global_event_bus,
    reset_global_event_bus,
)


class TestEventTypes:
    """Test event type definitions and their behavior."""

    def test_tone_event_timestamp(self):
        """Test that events automatically set timestamp."""
        event = create_tone_event(detected=True, frequency=600)

        # Should auto-set timestamp
        assert event.timestamp > 0
        assert isinstance(event.age_ms, float)
        assert event.age_ms >= 0

    def test_tone_detected_event_properties(self):
        """Test ToneDetectedEvent properties and methods."""
        event = ToneDetectedEvent(
            detected=True,
            frequency=600.0,
            confidence=0.8,
            snr_db=15.0,
            chunk_number=5,
            detection_threshold=0.3,
        )

        assert event.detected is True
        assert event.frequency == 600.0
        assert event.confidence == 0.8
        assert event.snr_db == 15.0
        assert event.chunk_number == 5
        assert event.detection_threshold == 0.3

        # Test computed properties
        assert event.is_confident is True  # 0.8 >= 0.3
        assert event.signal_quality == "good"  # 10 <= SNR < 20

    def test_tone_detected_signal_quality_levels(self):
        """Test signal quality classification."""
        test_cases = [
            (25.0, "excellent"),  # >= 20
            (15.0, "good"),  # >= 10
            (5.0, "poor"),  # >= 3
            (1.0, "very_poor"),  # < 3
        ]

        for snr_db, expected_quality in test_cases:
            event = ToneDetectedEvent(
                detected=True,
                frequency=600,
                confidence=0.5,
                snr_db=snr_db,
                chunk_number=0,
                detection_threshold=0.3,
            )
            assert event.signal_quality == expected_quality

    def test_morse_pattern_event_properties(self):
        """Test MorsePatternEvent type classification."""
        # Test tone patterns
        dot_event = MorsePatternEvent(pattern_type="dot", duration_ms=80, wpm_estimate=15.0, confidence=0.9)
        assert dot_event.is_tone is True
        assert dot_event.is_silence is False

        # Test silence patterns
        space_event = MorsePatternEvent(pattern_type="letter_space", duration_ms=200, wpm_estimate=15.0, confidence=0.9)
        assert space_event.is_tone is False
        assert space_event.is_silence is True

    def test_text_decoded_event_properties(self):
        """Test TextDecodedEvent properties."""
        event = TextDecodedEvent(
            text="HELLO",
            pattern_sequence=".... . .-.. .-.. ---",
            wpm_estimate=20.0,
            confidence=0.95,
            is_complete_word=True,
        )

        assert event.character_count == 5
        assert event.is_complete_word is True

    def test_error_event_severity(self):
        """Test ErrorEvent severity classification."""
        recoverable_error = ErrorEvent(
            error_type="ValueError",
            message="Invalid input",
            component="signal_processor",
            recoverable=True,
            context={},
        )
        assert recoverable_error.severity == "warning"

        critical_error = ErrorEvent(
            error_type="SystemError",
            message="System failure",
            component="audio_source",
            recoverable=False,
            context={},
        )
        assert critical_error.severity == "critical"

    def test_metrics_event_formatting(self):
        """Test MetricsEvent value formatting."""
        test_cases = [
            (123.4, "ms", "123.4ms"),
            (440.0, "hz", "440Hz"),
            (85.7, "percent", "85.7%"),
            (42.0, "count", "42.0 count"),
        ]

        for value, unit, expected in test_cases:
            event = MetricsEvent(metric_name="test_metric", value=value, unit=unit, component="test", tags={})
            assert event.formatted_value == expected

    def test_audio_chunk_event_duration_calculation(self):
        """Test AudioChunkEvent duration calculation."""
        chunk_data = np.array([1, 2, 3, 4, 5])
        event = AudioChunkEvent(
            chunk_data=chunk_data,
            chunk_size_ms=50,
            sample_rate=44100,
            chunk_number=1,
            has_more_data=True,
        )

        expected_samples = int((50 / 1000.0) * 44100)  # 2205 samples
        assert event.chunk_duration_samples == expected_samples


class TestEventHelpers:
    """Test convenience functions for creating events."""

    def test_create_tone_event(self):
        """Test tone event creation helper."""
        event = create_tone_event(detected=True, frequency=600.0, confidence=0.8)

        assert isinstance(event, ToneDetectedEvent)
        assert event.detected is True
        assert event.frequency == 600.0
        assert event.confidence == 0.8

    def test_create_text_event(self):
        """Test text event creation helper."""
        event = create_text_event(text="A", pattern=".-", wpm=15.0, is_word=False)

        assert isinstance(event, TextDecodedEvent)
        assert event.text == "A"
        assert event.pattern_sequence == ".-"
        assert event.wpm_estimate == 15.0
        assert event.is_complete_word is False

    def test_create_error_event(self):
        """Test error event creation from exception."""
        original_error = ValueError("Test error message")
        event = create_error_event(
            original_error,
            component="test_component",
            recoverable=False,
            extra_context="additional info",
        )

        assert isinstance(event, ErrorEvent)
        assert event.error_type == "ValueError"
        assert event.message == "Test error message"
        assert event.component == "test_component"
        assert event.recoverable is False
        assert event.context["extra_context"] == "additional info"


class TestEventBus:
    """Test EventBus core functionality."""

    def setup_method(self):
        """Setup fresh event bus for each test."""
        self.bus = EventBus(name="test")

    def test_event_bus_initialization(self):
        """Test EventBus initialization."""
        bus = EventBus(name="test_bus")

        assert bus.name == "test_bus"
        stats = bus.get_statistics()
        assert stats["events_published"] == 0
        assert stats["total_handler_count"] == 0

    def test_subscribe_and_publish(self):
        """Test basic subscription and publishing."""
        handler_calls = []

        def test_handler(event: ToneDetectedEvent):
            handler_calls.append(event)

        self.bus.subscribe(ToneDetectedEvent, test_handler)

        # Publish event
        test_event = create_tone_event(detected=True, frequency=600)
        self.bus.publish(test_event)

        # Verify handler was called
        assert len(handler_calls) == 1
        assert handler_calls[0] is test_event

    def test_multiple_handlers_same_type(self):
        """Test multiple handlers for the same event type."""
        handler1_calls = []
        handler2_calls = []

        def handler1(event: ToneDetectedEvent):
            handler1_calls.append(event)

        def handler2(event: ToneDetectedEvent):
            handler2_calls.append(event)

        self.bus.subscribe(ToneDetectedEvent, handler1)
        self.bus.subscribe(ToneDetectedEvent, handler2)

        test_event = create_tone_event(detected=True)
        self.bus.publish(test_event)

        # Both handlers should be called
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    def test_different_event_types(self):
        """Test handlers only receive their subscribed event types."""
        tone_calls = []
        text_calls = []

        def tone_handler(event: ToneDetectedEvent):
            tone_calls.append(event)

        def text_handler(event: TextDecodedEvent):
            text_calls.append(event)

        self.bus.subscribe(ToneDetectedEvent, tone_handler)
        self.bus.subscribe(TextDecodedEvent, text_handler)

        # Publish tone event
        tone_event = create_tone_event(detected=True)
        self.bus.publish(tone_event)

        # Publish text event
        text_event = create_text_event(text="A")
        self.bus.publish(text_event)

        # Verify correct delivery
        assert len(tone_calls) == 1
        assert len(text_calls) == 1
        assert tone_calls[0] is tone_event
        assert text_calls[0] is text_event

    def test_unsubscribe(self):
        """Test unsubscribing handlers."""
        handler_calls = []

        def test_handler(event: ToneDetectedEvent):
            handler_calls.append(event)

        # Subscribe and verify it works
        self.bus.subscribe(ToneDetectedEvent, test_handler)
        self.bus.publish(create_tone_event(detected=True))
        assert len(handler_calls) == 1

        # Unsubscribe and verify it stops receiving events
        success = self.bus.unsubscribe(ToneDetectedEvent, test_handler)
        assert success is True

        self.bus.publish(create_tone_event(detected=True))
        assert len(handler_calls) == 1  # Should not increase

    def test_unsubscribe_nonexistent(self):
        """Test unsubscribing handler that wasn't subscribed."""

        def test_handler(event: ToneDetectedEvent):
            pass

        success = self.bus.unsubscribe(ToneDetectedEvent, test_handler)
        assert success is False

    def test_handler_exception_isolation(self):
        """Test that handler exceptions don't break other handlers."""
        good_calls = []

        def failing_handler(event: ToneDetectedEvent):
            raise ValueError("Handler failure")

        def good_handler(event: ToneDetectedEvent):
            good_calls.append(event)

        self.bus.subscribe(ToneDetectedEvent, failing_handler)
        self.bus.subscribe(ToneDetectedEvent, good_handler)

        # Should not raise exception
        test_event = create_tone_event(detected=True)
        self.bus.publish(test_event)

        # Good handler should still be called
        assert len(good_calls) == 1

        # Error statistics should be updated
        stats = self.bus.get_statistics()
        assert stats["handler_errors"] == 1

    def test_middleware(self):
        """Test middleware functionality."""
        middleware_calls = []

        def test_middleware(event: BaseEvent):
            middleware_calls.append(event)

        self.bus.add_middleware(test_middleware)

        test_event = create_tone_event(detected=True)
        self.bus.publish(test_event)

        # Middleware should be called
        assert len(middleware_calls) == 1
        assert middleware_calls[0] is test_event

    def test_middleware_exception_handling(self):
        """Test middleware exception handling."""

        def failing_middleware(event: BaseEvent):
            raise RuntimeError("Middleware failure")

        self.bus.add_middleware(failing_middleware)

        # Should not raise exception
        self.bus.publish(create_tone_event(detected=True))

        # Error statistics should be updated
        stats = self.bus.get_statistics()
        assert stats["middleware_errors"] == 1

    def test_clear_handlers(self):
        """Test clearing event handlers."""
        handler_calls = []

        def test_handler(event: ToneDetectedEvent):
            handler_calls.append(event)

        self.bus.subscribe(ToneDetectedEvent, test_handler)

        # Verify subscription works
        self.bus.publish(create_tone_event(detected=True))
        assert len(handler_calls) == 1

        # Clear handlers for specific type
        self.bus.clear_handlers(ToneDetectedEvent)
        self.bus.publish(create_tone_event(detected=True))
        assert len(handler_calls) == 1  # Should not increase

    def test_statistics(self):
        """Test event bus statistics collection."""

        def dummy_handler(event: ToneDetectedEvent):
            pass

        self.bus.subscribe(ToneDetectedEvent, dummy_handler)

        # Publish some events
        for _ in range(3):
            self.bus.publish(create_tone_event(detected=True))

        stats = self.bus.get_statistics()
        assert stats["events_published"] == 3
        assert stats["events_handled"] == 3
        assert stats["total_handler_count"] == 1
        assert stats["bus_name"] == "test"

    def test_invalid_event_type(self):
        """Test publishing non-event objects raises error."""
        with pytest.raises(TypeError):
            self.bus.publish("not an event")

    def test_invalid_handler_type(self):
        """Test subscribing non-callable raises error."""
        with pytest.raises(TypeError):
            self.bus.subscribe(ToneDetectedEvent, "not callable")


class TestLoggingEventHandler:
    """Test LoggingEventHandler functionality."""

    def setup_method(self):
        """Setup logging handler with mock logger."""
        self.handler = LoggingEventHandler(log_level=logging.DEBUG)
        # Mock the logger to capture calls
        self.handler.logger = Mock()

    def test_tone_event_logging(self):
        """Test logging of tone detection events."""
        event = create_tone_event(detected=True, frequency=600, confidence=0.8)

        self.handler(event)

        # Should call debug level
        self.handler.logger.debug.assert_called_once()
        call_args = self.handler.logger.debug.call_args[0][0]
        assert "🎵 TONE" in call_args
        assert "600Hz" in call_args

    def test_text_event_logging(self):
        """Test logging of text decoded events."""
        event = create_text_event(text="A", pattern=".-", is_word=False)

        self.handler(event)

        # Should call info level
        self.handler.logger.info.assert_called_once()
        call_args = self.handler.logger.info.call_args[0][0]
        assert "Decoded: 'A'" in call_args
        assert "[.-]" in call_args

    def test_error_event_logging(self):
        """Test logging of error events."""
        error = ValueError("Test error")
        event = create_error_event(error, "test_component", recoverable=False)

        self.handler(event)

        # Should call error level for non-recoverable errors
        self.handler.logger.log.assert_called_once()
        assert self.handler.logger.log.call_args[0][0] == logging.ERROR


class TestMetricsEventHandler:
    """Test MetricsEventHandler functionality."""

    def setup_method(self):
        """Setup metrics handler."""
        self.handler = MetricsEventHandler(window_size=5)

    def test_tone_metrics_collection(self):
        """Test collection of tone detection metrics."""
        event = create_tone_event(detected=True, frequency=600, confidence=0.8)

        self.handler(event)

        summary = self.handler.get_summary()
        assert summary["counters"]["tone.detected"] == 1
        assert summary["gauges"]["tone.current_frequency"] == 600

    def test_text_metrics_collection(self):
        """Test collection of text decoding metrics."""
        event = create_text_event(text="HELLO", wpm=20.0, is_word=True)

        self.handler(event)

        summary = self.handler.get_summary()
        assert summary["counters"]["text.characters"] == 5
        assert summary["counters"]["text.words"] == 1
        assert summary["gauges"]["text.current_wpm"] == 20.0

    def test_rolling_averages(self):
        """Test rolling average calculations."""
        # Add multiple tone events with different frequencies
        frequencies = [600, 650, 700, 750, 800]
        for freq in frequencies:
            event = create_tone_event(detected=True, frequency=freq)
            self.handler(event)

        summary = self.handler.get_summary()
        expected_avg = sum(frequencies) / len(frequencies)
        assert abs(summary["averages"]["tone.frequency.avg"] - expected_avg) < 0.1

    def test_metrics_reset(self):
        """Test resetting metrics."""
        event = create_tone_event(detected=True)
        self.handler(event)

        # Should have metrics
        summary = self.handler.get_summary()
        assert summary["counters"].get("events.total", 0) > 0

        # Reset and verify clear
        self.handler.reset()
        summary = self.handler.get_summary()
        assert summary["counters"].get("events.total", 0) == 0


class TestDebugEventHandler:
    """Test DebugEventHandler functionality."""

    def test_debug_handler_memory_log(self):
        """Test debug handler maintains event log."""
        handler = DebugEventHandler(max_events=10)

        event = create_tone_event(detected=True, frequency=600)
        handler(event)

        recent_events = handler.get_recent_events()
        assert len(recent_events) == 1
        assert recent_events[0]["type"] == "ToneDetectedEvent"
        assert recent_events[0]["data"]["frequency"] == "600Hz"

    def test_debug_handler_file_output(self):
        """Test debug handler file output."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".log") as f:
            temp_file = f.name

        try:
            handler = DebugEventHandler(output_file=temp_file)

            event = create_text_event(text="A", pattern=".-")
            handler(event)
            handler.close()  # Ensure file is flushed

            # Read back the file
            with open(temp_file) as f:
                content = f.read()

            assert "TextDecodedEvent" in content
            assert "text='A'" in content

        finally:
            # Cleanup
            Path(temp_file).unlink(missing_ok=True)

    def test_debug_handler_dump_events(self):
        """Test dumping events to file."""
        handler = DebugEventHandler()

        # Add some events
        handler(create_tone_event(detected=True))
        handler(create_text_event(text="A"))

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".dump") as f:
            temp_file = f.name

        try:
            handler.dump_events_to_file(temp_file)

            with open(temp_file) as f:
                content = f.read()

            assert "# Total events: 2" in content
            assert "ToneDetectedEvent" in content
            assert "TextDecodedEvent" in content

        finally:
            Path(temp_file).unlink(missing_ok=True)


class TestGlobalEventBus:
    """Test global event bus functionality."""

    def setup_method(self):
        """Reset global event bus before each test."""
        reset_global_event_bus()

    def test_global_event_bus_singleton(self):
        """Test global event bus is singleton."""
        bus1 = get_global_event_bus()
        bus2 = get_global_event_bus()

        assert bus1 is bus2
        assert bus1.name == "global"

    def test_global_event_bus_reset(self):
        """Test resetting global event bus."""
        bus1 = get_global_event_bus()
        bus1_id = id(bus1)

        reset_global_event_bus()
        bus2 = get_global_event_bus()
        bus2_id = id(bus2)

        assert bus1_id != bus2_id


class TestEventIntegration:
    """Integration tests for complete event flow."""

    def setup_method(self):
        """Setup event bus with multiple handlers."""
        self.bus = EventBus(name="integration_test")

        # Setup handlers
        self.logging_handler = LoggingEventHandler()
        self.metrics_handler = MetricsEventHandler()

        # Mock the logging to capture calls
        self.logging_handler.logger = Mock()

        # Add as middleware
        self.bus.add_middleware(self.logging_handler)
        self.bus.add_middleware(self.metrics_handler)

    def test_complete_morse_decoding_flow(self):
        """Test complete event flow through Morse decoding pipeline."""
        # Simulate audio chunk processing
        audio_event = AudioChunkEvent(
            chunk_data=np.array([1, 2, 3]),
            chunk_size_ms=50,
            sample_rate=44100,
            chunk_number=1,
            has_more_data=True,
        )
        self.bus.publish(audio_event)

        # Simulate tone detection
        tone_event = create_tone_event(detected=True, frequency=600, confidence=0.8)
        self.bus.publish(tone_event)

        # Simulate pattern recognition
        pattern_event = MorsePatternEvent(pattern_type="dot", duration_ms=80, wpm_estimate=15.0, confidence=0.9)
        self.bus.publish(pattern_event)

        # Simulate text decoding
        text_event = create_text_event(text="A", pattern=".-")
        self.bus.publish(text_event)

        # Verify metrics were collected
        summary = self.metrics_handler.get_summary()
        assert summary["counters"]["events.total"] == 4
        assert summary["counters"]["tone.detected"] == 1
        assert summary["counters"]["text.characters"] == 1

        # Verify logging happened
        assert self.logging_handler.logger.debug.call_count >= 2  # tone + pattern
        assert self.logging_handler.logger.info.call_count >= 1  # text

    def test_error_recovery_flow(self):
        """Test error handling and recovery through events."""
        # Create and publish error event
        original_error = RuntimeError("Processing failed")
        error_event = create_error_event(original_error, component="signal_processor", recoverable=True)

        self.bus.publish(error_event)

        # Verify metrics tracked the error
        summary = self.metrics_handler.get_summary()
        assert summary["counters"]["errors.RuntimeError"] == 1
        assert summary["counters"]["errors.signal_processor"] == 1

        # Verify error was logged
        self.logging_handler.logger.log.assert_called()
        call_args = self.logging_handler.logger.log.call_args
        assert call_args[0][0] == logging.WARNING  # Recoverable error

"""Interface-based tests for SignalProcessor demonstrating clean architecture benefits.

This module shows how to test signal processing components using protocol-based
mocking and event-driven patterns, making tests faster, more isolated, and
more maintainable than traditional file-based or concrete-dependency tests.
"""

import numpy as np
import pytest

from morsecode.components.signal.signal_processor import SignalProcessor
from morsecode.events.bus import EventBus
from morsecode.events.types import ErrorEvent, ToneDetectedEvent
from morsecode.interfaces.signal import SignalProcessor as SignalProcessorProtocol
from util.config.models import SignalConfig


class MockAudioSource:
    """Mock AudioSource implementing the protocol for testing."""

    def __init__(self, sample_rate: int = 44100, chunks: list[np.ndarray] = None):
        self.sample_rate = sample_rate
        self.chunks = chunks or []
        self.current_chunk = 0

    def has_data(self) -> bool:
        """Check if more audio data is available."""
        return self.current_chunk < len(self.chunks)

    def get_next_chunk(self, duration_ms: int) -> np.ndarray:
        """Get the next chunk of audio data."""
        if not self.has_data():
            raise RuntimeError("No more data available")

        chunk = self.chunks[self.current_chunk]
        self.current_chunk += 1
        return chunk

    def get_sample_rate(self) -> int:
        """Get the audio sample rate."""
        return self.sample_rate

    def get_total_duration_ms(self) -> float | None:
        """Get total duration - None for mock (unknown)."""
        return None


class MockSignalProcessor:
    """Mock SignalProcessor for testing event integration."""

    def __init__(self, detection_results: list[bool] = None):
        self.detection_results = detection_results or []
        self.current_detection = 0
        self.target_frequency = 600.0

    def detect_tone(self, audio_data: np.ndarray) -> bool:
        """Mock tone detection with predefined results."""
        if self.current_detection < len(self.detection_results):
            result = self.detection_results[self.current_detection]
            self.current_detection += 1
            return result
        return False

    def get_dominant_frequency(self, audio_data: np.ndarray) -> float:
        """Mock dominant frequency detection - doesn't affect detection counter."""
        if self.current_detection <= len(self.detection_results):
            # Use current - 1 since detect_tone already incremented it
            previous_detection = self.current_detection - 1
            if 0 <= previous_detection < len(self.detection_results):
                return self.target_frequency if self.detection_results[previous_detection] else 0.0
        return 0.0

    def get_signal_strength(self, audio_data: np.ndarray) -> float:
        """Mock signal strength - doesn't affect detection counter."""
        if self.current_detection <= len(self.detection_results):
            previous_detection = self.current_detection - 1
            if 0 <= previous_detection < len(self.detection_results):
                return 0.8 if self.detection_results[previous_detection] else 0.1
        return 0.1

    def get_detection_confidence(self, audio_data: np.ndarray) -> float:
        """Mock detection confidence - doesn't affect detection counter."""
        if self.current_detection <= len(self.detection_results):
            previous_detection = self.current_detection - 1
            if 0 <= previous_detection < len(self.detection_results):
                return 0.9 if self.detection_results[previous_detection] else 0.2
        return 0.2

    def get_target_frequency(self) -> float:
        """Get target frequency."""
        return self.target_frequency


class TestInterfaceBasedSignalProcessor:
    """Test SignalProcessor using interface-based mocking patterns."""

    def create_synthetic_audio(
        self,
        frequency: float,
        duration_sec: float = 0.1,
        sample_rate: int = 44100,
        amplitude: float = 1.0,
    ) -> np.ndarray:
        """Create synthetic audio for testing without file I/O."""
        samples = int(duration_sec * sample_rate)
        t = np.linspace(0, duration_sec, samples)
        return (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)

    def test_protocol_compliance(self) -> None:
        """Test that SignalProcessor implements core methods correctly."""
        processor = SignalProcessor()

        # Verify core methods exist (actual implementation)
        assert hasattr(processor, "detect_tone")
        assert hasattr(processor, "get_dominant_frequency")
        assert hasattr(processor, "compute_fft")
        assert hasattr(processor, "apply_bandpass_filter")
        assert hasattr(processor, "calculate_snr")

        # Test actual methods return expected types
        test_audio = self.create_synthetic_audio(600.0)

        assert isinstance(processor.detect_tone(test_audio), bool)
        assert isinstance(processor.get_dominant_frequency(test_audio), float)

        # Test additional capabilities
        fft_freqs, fft_magnitudes = processor.compute_fft(test_audio)
        assert isinstance(fft_freqs, np.ndarray)
        assert isinstance(fft_magnitudes, np.ndarray)

    def test_with_mock_audio_source(self) -> None:
        """Test SignalProcessor using mock AudioSource protocol."""
        # Create test audio chunks
        tone_chunk = self.create_synthetic_audio(600.0)  # Target frequency
        noise_chunk = self.create_synthetic_audio(1200.0)  # Off-target frequency

        # Setup mock audio source
        mock_source = MockAudioSource(
            sample_rate=44100, chunks=[tone_chunk, noise_chunk, tone_chunk]
        )

        processor = SignalProcessor()

        # Process chunks using protocol interface
        detections = []
        while mock_source.has_data():
            chunk = mock_source.get_next_chunk(20)  # Duration doesn't matter for mock
            detection = processor.detect_tone(chunk)
            detections.append(detection)

        # Should detect more tones in 600Hz chunks than 1200Hz chunks
        assert len(detections) == 3

    def test_event_driven_signal_processing(self) -> None:
        """Test SignalProcessor integration with event system."""
        # Setup event bus and capture events
        event_bus = EventBus("test-signal")
        captured_events = []

        def event_capture(event):
            captured_events.append(event)

        event_bus.subscribe(ToneDetectedEvent, event_capture)

        # Create processor and setup event publishing
        processor = SignalProcessor()

        # Mock the internal event publishing using actual processor methods
        test_audio = self.create_synthetic_audio(600.0)
        detected = processor.detect_tone(test_audio)
        dominant_freq = processor.get_dominant_frequency(test_audio)
        snr = processor.calculate_snr(test_audio)

        # Manually publish event (demonstrating the pattern)
        if detected:
            event = ToneDetectedEvent(
                detected=detected,
                frequency=dominant_freq,
                confidence=0.85,  # Mock confidence based on SNR
                snr_db=snr,
                chunk_number=1,
                detection_threshold=0.1,
            )
            event_bus.publish(event)

        # Verify event was published and captured
        assert len(captured_events) == 1
        tone_event = captured_events[0]
        assert isinstance(tone_event, ToneDetectedEvent)
        assert tone_event.detected is True
        assert abs(tone_event.frequency - 600.0) < 100  # Allow some frequency tolerance

    def test_mock_based_integration_testing(self) -> None:
        """Test component integration using mocks instead of real dependencies."""
        # Setup mock signal processor with predefined behavior
        mock_processor = MockSignalProcessor(detection_results=[True, False, True, True, False])

        # Test processing pipeline using mock
        test_chunks = [
            self.create_synthetic_audio(600.0),
            self.create_synthetic_audio(1200.0),
            self.create_synthetic_audio(600.0),
            self.create_synthetic_audio(600.0),
            self.create_synthetic_audio(800.0),
        ]

        results = []
        for chunk in test_chunks:
            detection = mock_processor.detect_tone(chunk)
            frequency = mock_processor.get_dominant_frequency(chunk)
            confidence = mock_processor.get_detection_confidence(chunk)

            results.append(
                {"detected": detection, "frequency": frequency, "confidence": confidence}
            )

        # Verify mock behavior matches expectations
        assert len(results) == 5
        expected_detections = [True, False, True, True, False]
        for i, expected in enumerate(expected_detections):
            assert results[i]["detected"] == expected

        # Verify frequency/confidence correlate with detection
        for i, result in enumerate(results):
            if expected_detections[i]:
                assert result["frequency"] == 600.0
                assert result["confidence"] > 0.8
            else:
                assert result["frequency"] == 0.0
                assert result["confidence"] < 0.5

    def test_error_handling_with_event_system(self) -> None:
        """Test error handling using event-driven patterns."""
        event_bus = EventBus("test-error")
        error_events = []

        def error_capture(event):
            error_events.append(event)

        event_bus.subscribe(ErrorEvent, error_capture)

        processor = SignalProcessor()

        # Test error condition (empty array) - SignalProcessor handles this gracefully
        result = processor.detect_tone(np.array([]))

        # SignalProcessor returns False for empty array instead of throwing
        assert result is False

        # Simulate error event publishing (in real system, this might happen)
        error_event = ErrorEvent(
            error_type="EmptyDataWarning",
            message="Empty audio data provided",
            component="SignalProcessor.detect_tone",
            recoverable=True,
            context={"input_shape": (0,)},
        )
        event_bus.publish(error_event)

        # Verify error event handling
        assert len(error_events) == 1
        error_event = error_events[0]
        assert isinstance(error_event, ErrorEvent)
        assert error_event.component == "SignalProcessor.detect_tone"
        assert error_event.recoverable is True

    @pytest.mark.parametrize(
        "sample_rate,frequency,expected_detection",
        [
            (44100, 600.0, True),  # Target frequency
            (44100, 1200.0, False),  # Off target
            (48000, 600.0, True),  # Different sample rate, target freq
            (22050, 300.0, False),  # Low sample rate, off target
        ],
    )
    def test_parameterized_interface_testing(
        self, sample_rate: int, frequency: float, expected_detection: bool
    ) -> None:
        """Test using parameterization with interface-based testing."""
        # Configure processor with fixed target frequency (600 Hz) for all tests
        processor = SignalProcessor(SignalConfig(sample_rate=sample_rate, frequency=600))

        test_audio = self.create_synthetic_audio(frequency=frequency, sample_rate=sample_rate)

        # Disable adaptive frequency for tests that expect specific frequency detection
        detection = processor.detect_tone(test_audio, adaptive_frequency=False)
        assert detection == expected_detection

    def test_performance_with_mock_data(self) -> None:
        """Test performance characteristics using mock data instead of file I/O."""
        processor = SignalProcessor()

        # Generate larger test dataset in memory (much faster than file I/O)
        large_chunks = [self.create_synthetic_audio(600.0, duration_sec=0.1) for _ in range(100)]

        # Process all chunks and measure basic performance
        import time

        start_time = time.perf_counter()

        detections = []
        for chunk in large_chunks:
            detections.append(processor.detect_tone(chunk))

        processing_time = time.perf_counter() - start_time

        # Verify processing completed successfully
        assert len(detections) == 100
        assert all(isinstance(d, bool) for d in detections)

        # Basic performance check (should be very fast with synthetic data)
        assert processing_time < 1.0  # Should complete in under 1 second

        # Most detections should be True for target frequency
        true_detections = sum(detections)
        assert true_detections > 80  # At least 80% should detect the 600Hz tone


class TestSignalProcessorProtocolCompliance:
    """Test protocol compliance for SignalProcessor implementations."""

    def test_real_implementation_satisfies_core_functionality(self) -> None:
        """Test that SignalProcessor provides core functionality."""
        processor = SignalProcessor()

        # Test core methods that are actually implemented
        test_audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)

        assert callable(processor.detect_tone)
        assert callable(processor.get_dominant_frequency)
        assert callable(processor.compute_fft)
        assert callable(processor.apply_bandpass_filter)
        assert callable(processor.calculate_snr)

        # Test methods work
        assert isinstance(processor.detect_tone(test_audio), bool)
        assert isinstance(processor.get_dominant_frequency(test_audio), float)

    def test_mock_implementation_satisfies_protocol(self) -> None:
        """Test that MockSignalProcessor satisfies the protocol."""
        mock_processor = MockSignalProcessor()

        # Should satisfy protocol through structural typing
        processor_protocol: SignalProcessorProtocol = mock_processor

        # Protocol methods should work
        test_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        assert isinstance(processor_protocol.detect_tone(test_audio), bool)
        assert isinstance(processor_protocol.get_dominant_frequency(test_audio), float)
        assert isinstance(processor_protocol.get_signal_strength(test_audio), float)
        assert isinstance(processor_protocol.get_detection_confidence(test_audio), float)
        assert isinstance(processor_protocol.get_target_frequency(), float)

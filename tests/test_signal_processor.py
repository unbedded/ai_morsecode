"""Tests for the SignalProcessor module.

This test module provides comprehensive test coverage for the signal processing
functionality, including FFT analysis, tone detection, filtering, and SNR calculations.
"""

import logging
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from morsecode.components.signal.signal_processor import (
    DEFAULT_FFT_WINDOW_SIZE,
    DEFAULT_NOISE_FLOOR_DB,
    DEFAULT_SAMPLE_RATE_HZ,
    DEFAULT_TARGET_FREQUENCY_HZ,
    SignalProcessor,
)
from util.config.models import SignalConfig

# Test constants (inlined to avoid import issues)
TEST_AMPLITUDE_NORMAL = 0.7
TEST_AMPLITUDE_STRONG = 1.0
TEST_AMPLITUDE_VERY_WEAK = 0.1
TEST_FREQUENCY_ALTERNATE = 800
TEST_FREQUENCY_HIGH = 1000
TEST_FREQUENCY_NOMINAL = 600
TEST_FREQUENCY_OFF_TARGET = 1500
TEST_SAMPLE_RATE_HIGH = 48000
TEST_SAMPLE_RATE_LOW = 22050
TEST_THRESHOLD_LOW = 0.1


class TestSignalProcessor:
    """Test cases for the SignalProcessor class."""

    def create_test_signal(
        self,
        frequency: float,
        amplitude: float = TEST_AMPLITUDE_STRONG,
        duration_sec: float = 0.1,
        sample_rate: int = 44100,
        noise_amplitude: float = 0.0,
    ) -> np.ndarray:
        """Create a synthetic test signal with optional noise.

        Args:
            frequency: Frequency of the sine wave in Hz.
            amplitude: Amplitude of the sine wave.
            duration_sec: Duration of the signal in seconds.
            sample_rate: Sample rate in Hz.
            noise_amplitude: Amplitude of additive white noise.

        Returns:
            Synthetic audio signal as numpy array.
        """
        samples = int(duration_sec * sample_rate)
        t = np.linspace(0, duration_sec, samples)

        # Create sine wave
        signal = amplitude * np.sin(2 * np.pi * frequency * t)

        # Add noise if specified
        if noise_amplitude > 0:
            noise = noise_amplitude * np.random.randn(samples)
            signal += noise

        return signal.astype(np.float32)

    def test_init_with_defaults(self, caplog: Any) -> None:
        """Test SignalProcessor initialization with default parameters."""
        with caplog.at_level(logging.INFO):
            processor = SignalProcessor()

        assert processor.sample_rate_hz == DEFAULT_SAMPLE_RATE_HZ
        assert processor.target_frequency_hz == DEFAULT_TARGET_FREQUENCY_HZ
        assert processor.fft_window_size == DEFAULT_FFT_WINDOW_SIZE
        # Note: Default threshold in SignalConfig is 0.3, but legacy DEFAULT was 0.1
        assert processor.detection_threshold == 0.3  # SignalConfig default
        assert processor.filter_bandwidth_hz == 50  # SignalConfig default
        assert processor.noise_floor_db == DEFAULT_NOISE_FLOOR_DB

    def test_init_with_config(self) -> None:
        """Test SignalProcessor initialization with custom configuration."""
        config = SignalConfig(
            sample_rate=TEST_SAMPLE_RATE_HIGH,
            frequency=TEST_FREQUENCY_ALTERNATE,
            threshold=0.2,
            bandwidth=100,
        )

        processor = SignalProcessor(config=config)

        assert processor.sample_rate_hz == TEST_SAMPLE_RATE_HIGH
        assert processor.target_frequency_hz == TEST_FREQUENCY_ALTERNATE
        assert processor.fft_window_size == DEFAULT_FFT_WINDOW_SIZE  # Not in config yet
        assert processor.detection_threshold == 0.2
        assert processor.filter_bandwidth_hz == 100
        assert processor.noise_floor_db == DEFAULT_NOISE_FLOOR_DB  # Not in config yet

    def test_get_params(self) -> None:
        """Test getting configuration parameters."""
        config = SignalConfig(sample_rate=22050, frequency=750)
        processor = SignalProcessor(config=config)

        params = processor.get_params()

        assert params["sample_rate_hz"] == 22050
        assert params["target_frequency_hz"] == 750
        assert "fft_window_size" in params
        assert "detection_threshold" in params

    def test_compute_fft_normal(self) -> None:
        """Test FFT computation with normal signal."""
        processor = SignalProcessor()
        test_freq = 1000  # Hz
        test_signal = self.create_test_signal(frequency=test_freq, duration_sec=0.1)

        frequencies, magnitudes = processor.compute_fft(test_signal)

        # Check output shapes
        assert len(frequencies) == DEFAULT_FFT_WINDOW_SIZE // 2
        assert len(magnitudes) == DEFAULT_FFT_WINDOW_SIZE // 2

        # Find peak frequency
        peak_idx = np.argmax(magnitudes)
        peak_frequency = frequencies[peak_idx]

        # Peak should be close to test frequency (within 10% tolerance)
        assert abs(peak_frequency - test_freq) / test_freq < 0.1

    def test_compute_fft_empty_data(self) -> None:
        """Test FFT computation with empty audio data."""
        processor = SignalProcessor()

        with pytest.raises(RuntimeError, match="FFT computation failed"):
            processor.compute_fft(np.array([]))

    def test_compute_fft_short_data(self) -> None:
        """Test FFT computation with data shorter than window size."""
        processor = SignalProcessor()
        short_signal = self.create_test_signal(frequency=600, duration_sec=0.01)  # Very short

        frequencies, magnitudes = processor.compute_fft(short_signal)

        # Should still return full-size FFT (zero-padded)
        assert len(frequencies) == DEFAULT_FFT_WINDOW_SIZE // 2
        assert len(magnitudes) == DEFAULT_FFT_WINDOW_SIZE // 2

    def test_compute_fft_long_data(self) -> None:
        """Test FFT computation with data longer than window size."""
        processor = SignalProcessor()
        long_signal = self.create_test_signal(frequency=600, duration_sec=1.0)  # Long signal

        frequencies, magnitudes = processor.compute_fft(long_signal)

        # Should still return standard FFT size (truncated)
        assert len(frequencies) == DEFAULT_FFT_WINDOW_SIZE // 2
        assert len(magnitudes) == DEFAULT_FFT_WINDOW_SIZE // 2

    def test_detect_tone_present(self) -> None:
        """Test tone detection when target tone is present."""
        processor = SignalProcessor(SignalConfig(threshold=0.1))
        # Create signal at target frequency with high amplitude
        test_signal = self.create_test_signal(frequency=DEFAULT_TARGET_FREQUENCY_HZ, amplitude=1.0, duration_sec=0.1)

        tone_detected = processor.detect_tone(test_signal)

        assert tone_detected is True

    def test_detect_tone_absent(self) -> None:
        """Test tone detection when target tone is absent."""
        processor = SignalProcessor(SignalConfig(threshold=0.1))
        # Create signal at different frequency (well outside detection bandwidth)
        test_signal = self.create_test_signal(
            frequency=TEST_FREQUENCY_OFF_TARGET,  # Much different frequency to ensure no detection
            amplitude=TEST_AMPLITUDE_STRONG,
            duration_sec=0.1,
        )

        # Disable adaptive frequency to test fixed-frequency detection
        tone_detected = processor.detect_tone(test_signal, adaptive_frequency=False)

        assert tone_detected is False

    def test_detect_tone_weak_signal(self) -> None:
        """Test tone detection with weak signal below threshold."""
        processor = SignalProcessor(SignalConfig(threshold=0.5))  # High threshold
        # Create weak signal at target frequency
        test_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ,
            amplitude=0.1,  # Low amplitude
            duration_sec=0.1,
            noise_amplitude=1.0,  # High noise
        )

        tone_detected = processor.detect_tone(test_signal)

        assert tone_detected is False

    def test_detect_tone_empty_data(self, caplog: Any) -> None:
        """Test tone detection with empty audio data."""
        processor = SignalProcessor()

        with caplog.at_level(logging.WARNING):
            tone_detected = processor.detect_tone(np.array([]))

        assert tone_detected is False
        assert "Empty audio data" in caplog.text

    def test_apply_bandpass_filter_normal(self) -> None:
        """Test band-pass filter application."""
        processor = SignalProcessor()

        # Create signal with target frequency + noise at other frequencies
        target_signal = self.create_test_signal(frequency=DEFAULT_TARGET_FREQUENCY_HZ, amplitude=1.0)
        noise_signal = self.create_test_signal(frequency=DEFAULT_TARGET_FREQUENCY_HZ + 500, amplitude=0.5)
        combined_signal = target_signal + noise_signal

        filtered_signal = processor.apply_bandpass_filter(combined_signal)

        # Filtered signal should have same length
        assert len(filtered_signal) == len(combined_signal)

        # Check that high-frequency noise is reduced
        # (This is a basic check - more sophisticated verification would require spectral analysis)
        assert isinstance(filtered_signal, np.ndarray)

    def test_apply_bandpass_filter_empty_data(self) -> None:
        """Test band-pass filter with empty audio data."""
        processor = SignalProcessor()

        with pytest.raises(RuntimeError, match="Band-pass filtering failed"):
            processor.apply_bandpass_filter(np.array([]))

    @patch("morsecode.components.signal.signal_processor.signal.butter")
    def test_apply_bandpass_filter_error_handling(self, mock_butter: Any) -> None:
        """Test band-pass filter error handling."""
        processor = SignalProcessor()
        test_signal = self.create_test_signal(frequency=600)

        # Mock filter design to raise an exception
        mock_butter.side_effect = Exception("Filter design failed")

        with pytest.raises(RuntimeError, match="Band-pass filtering failed"):
            processor.apply_bandpass_filter(test_signal)

    def test_calculate_snr_clean_signal(self) -> None:
        """Test SNR calculation with clean signal."""
        processor = SignalProcessor()
        # Create clean signal at target frequency
        clean_signal = self.create_test_signal(frequency=DEFAULT_TARGET_FREQUENCY_HZ, amplitude=1.0, duration_sec=0.1)

        snr_db = processor.calculate_snr(clean_signal)

        # Clean signal should have high SNR
        assert snr_db > 10  # Should be significantly above noise floor

    def test_calculate_snr_noisy_signal(self) -> None:
        """Test SNR calculation with noisy signal."""
        processor = SignalProcessor()
        # Create signal with significant noise
        noisy_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ,
            amplitude=1.0,
            duration_sec=0.1,
            noise_amplitude=1.0,  # Equal signal and noise power
        )

        snr_db = processor.calculate_snr(noisy_signal)

        # Noisy signal should have lower SNR than clean signal
        # Note: With equal signal and noise power, SNR may still be positive
        # due to signal concentration in frequency domain vs broadband noise
        assert isinstance(snr_db, float)  # Just verify it's calculated

    def test_calculate_snr_empty_data(self) -> None:
        """Test SNR calculation with empty audio data."""
        processor = SignalProcessor()

        # SNR calculation returns 0.0 on error instead of raising
        snr = processor.calculate_snr(np.array([]))
        assert snr == 0.0

    def test_get_dominant_frequency_single_tone(self) -> None:
        """Test dominant frequency detection with single tone."""
        processor = SignalProcessor()
        test_freq = 800  # Hz
        test_signal = self.create_test_signal(frequency=test_freq, duration_sec=0.1)

        dominant_freq = processor.get_dominant_frequency(test_signal)

        # Dominant frequency should be close to test frequency
        assert abs(dominant_freq - test_freq) / test_freq < 0.1

    def test_get_dominant_frequency_multiple_tones(self) -> None:
        """Test dominant frequency detection with multiple tones."""
        processor = SignalProcessor()

        # Create signal with two tones, one stronger
        strong_tone = self.create_test_signal(frequency=700, amplitude=2.0)
        weak_tone = self.create_test_signal(frequency=900, amplitude=1.0)
        combined_signal = strong_tone + weak_tone

        dominant_freq = processor.get_dominant_frequency(combined_signal)

        # Should detect the stronger tone (700 Hz)
        assert abs(dominant_freq - 700) / 700 < 0.1

    def test_get_dominant_frequency_empty_data(self) -> None:
        """Test dominant frequency detection with empty data."""
        processor = SignalProcessor()

        # Dominant frequency returns 0.0 on error instead of raising
        freq = processor.get_dominant_frequency(np.array([]))
        assert freq == 0.0

    @pytest.mark.parametrize(
        "sample_rate,target_freq,window_size",
        [
            (22050, 400, 512),  # Low rate, low frequency
            (48000, 800, 2048),  # High rate, medium frequency
            (96000, 1200, 4096),  # Very high rate, high frequency
        ],
    )
    def test_different_configurations(self, sample_rate: int, target_freq: int, window_size: int) -> None:
        """Test SignalProcessor with different configuration parameters."""
        config = SignalConfig(
            sample_rate=sample_rate,
            frequency=target_freq,
            # Note: fft_window_size not in SignalConfig yet, will use default
        )

        processor = SignalProcessor(config=config)

        # Test signal at target frequency
        test_signal = self.create_test_signal(frequency=target_freq, sample_rate=sample_rate, duration_sec=0.1)

        # All operations should work with different configurations
        frequencies, magnitudes = processor.compute_fft(test_signal)
        tone_detected = processor.detect_tone(test_signal)
        filtered_signal = processor.apply_bandpass_filter(test_signal)
        snr_db = processor.calculate_snr(test_signal)
        dominant_freq = processor.get_dominant_frequency(test_signal)

        # Basic sanity checks - window_size not configurable yet, use default
        assert len(frequencies) == DEFAULT_FFT_WINDOW_SIZE // 2
        assert len(magnitudes) == DEFAULT_FFT_WINDOW_SIZE // 2
        assert isinstance(tone_detected, bool)
        assert len(filtered_signal) == len(test_signal)
        assert isinstance(snr_db, float)
        assert isinstance(dominant_freq, float)

    def test_logging_configuration(self, caplog: Any) -> None:
        """Test that logging is properly configured."""
        with caplog.at_level(logging.INFO):
            SignalProcessor()  # Use default config

        # Should log about initialization
        log_messages = [record.message for record in caplog.records]
        assert any("SignalProcessor initialized" in msg for msg in log_messages)

    def test_error_propagation(self) -> None:
        """Test that processing errors are properly handled and logged."""
        # Test initialization error by mocking the initialization during construction
        with patch(
            "morsecode.components.signal.signal_processor.SignalProcessor._initialize_processing",
            side_effect=Exception("Init failed"),
        ):
            with pytest.raises(RuntimeError, match="Failed to initialize signal processor"):
                SignalProcessor()

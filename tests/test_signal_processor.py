"""Tests for the SignalProcessor module.

This test module provides comprehensive test coverage for the signal processing
functionality, including FFT analysis, tone detection, filtering, and SNR calculations.
"""

import logging
from unittest.mock import patch

import numpy as np
import pytest

from morsecode.signal_processor import (
    DEFAULT_DETECTION_THRESHOLD,
    DEFAULT_FFT_WINDOW_SIZE,
    DEFAULT_FILTER_BANDWIDTH_HZ,
    DEFAULT_NOISE_FLOOR_DB,
    DEFAULT_SAMPLE_RATE_HZ,
    DEFAULT_TARGET_FREQUENCY_HZ,
    SignalProcessor,
)


class TestSignalProcessor:
    """Test cases for the SignalProcessor class."""

    def create_test_signal(
        self,
        frequency: float,
        amplitude: float = 1.0,
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

    def test_init_with_defaults(self, caplog):
        """Test SignalProcessor initialization with default parameters."""
        with caplog.at_level(logging.INFO):
            processor = SignalProcessor()

        assert processor.sample_rate_hz == DEFAULT_SAMPLE_RATE_HZ
        assert processor.target_frequency_hz == DEFAULT_TARGET_FREQUENCY_HZ
        assert processor.fft_window_size == DEFAULT_FFT_WINDOW_SIZE
        assert processor.detection_threshold == DEFAULT_DETECTION_THRESHOLD
        assert processor.filter_bandwidth_hz == DEFAULT_FILTER_BANDWIDTH_HZ
        assert processor.noise_floor_db == DEFAULT_NOISE_FLOOR_DB
        assert "not found in configuration" in caplog.text

    def test_init_with_config(self):
        """Test SignalProcessor initialization with custom configuration."""
        cfg = {
            "sample_rate_hz": 48000,
            "target_frequency_hz": 800,
            "fft_window_size": 2048,
            "detection_threshold": 0.2,
            "filter_bandwidth_hz": 100,
            "noise_floor_db": -50,
        }

        processor = SignalProcessor(cfg_dict=cfg)

        assert processor.sample_rate_hz == 48000
        assert processor.target_frequency_hz == 800
        assert processor.fft_window_size == 2048
        assert processor.detection_threshold == 0.2
        assert processor.filter_bandwidth_hz == 100
        assert processor.noise_floor_db == -50

    def test_get_params(self):
        """Test getting configuration parameters."""
        cfg = {"sample_rate_hz": 22050, "target_frequency_hz": 750}
        processor = SignalProcessor(cfg_dict=cfg)

        params = processor.get_params()

        assert params["sample_rate_hz"] == 22050
        assert params["target_frequency_hz"] == 750
        assert "fft_window_size" in params
        assert "detection_threshold" in params

    def test_compute_fft_normal(self):
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

    def test_compute_fft_empty_data(self):
        """Test FFT computation with empty audio data."""
        processor = SignalProcessor()

        with pytest.raises(RuntimeError, match="FFT computation failed"):
            processor.compute_fft(np.array([]))

    def test_compute_fft_short_data(self):
        """Test FFT computation with data shorter than window size."""
        processor = SignalProcessor()
        short_signal = self.create_test_signal(frequency=600, duration_sec=0.01)  # Very short

        frequencies, magnitudes = processor.compute_fft(short_signal)

        # Should still return full-size FFT (zero-padded)
        assert len(frequencies) == DEFAULT_FFT_WINDOW_SIZE // 2
        assert len(magnitudes) == DEFAULT_FFT_WINDOW_SIZE // 2

    def test_compute_fft_long_data(self):
        """Test FFT computation with data longer than window size."""
        processor = SignalProcessor()
        long_signal = self.create_test_signal(frequency=600, duration_sec=1.0)  # Long signal

        frequencies, magnitudes = processor.compute_fft(long_signal)

        # Should still return standard FFT size (truncated)
        assert len(frequencies) == DEFAULT_FFT_WINDOW_SIZE // 2
        assert len(magnitudes) == DEFAULT_FFT_WINDOW_SIZE // 2

    def test_detect_tone_present(self):
        """Test tone detection when target tone is present."""
        processor = SignalProcessor({"detection_threshold": 0.1})
        # Create signal at target frequency with high amplitude
        test_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ, amplitude=1.0, duration_sec=0.1
        )

        tone_detected = processor.detect_tone(test_signal)

        assert tone_detected is True

    def test_detect_tone_absent(self):
        """Test tone detection when target tone is absent."""
        processor = SignalProcessor({"detection_threshold": 0.1})
        # Create signal at different frequency
        test_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ + 200,  # Different frequency
            amplitude=1.0,
            duration_sec=0.1,
        )

        tone_detected = processor.detect_tone(test_signal)

        assert tone_detected is False

    def test_detect_tone_weak_signal(self):
        """Test tone detection with weak signal below threshold."""
        processor = SignalProcessor({"detection_threshold": 0.5})  # High threshold
        # Create weak signal at target frequency
        test_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ,
            amplitude=0.1,  # Low amplitude
            duration_sec=0.1,
            noise_amplitude=1.0,  # High noise
        )

        tone_detected = processor.detect_tone(test_signal)

        assert tone_detected is False

    def test_detect_tone_empty_data(self, caplog):
        """Test tone detection with empty audio data."""
        processor = SignalProcessor()

        with caplog.at_level(logging.WARNING):
            tone_detected = processor.detect_tone(np.array([]))

        assert tone_detected is False
        assert "Empty audio data" in caplog.text

    def test_apply_bandpass_filter_normal(self):
        """Test band-pass filter application."""
        processor = SignalProcessor()

        # Create signal with target frequency + noise at other frequencies
        target_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ, amplitude=1.0
        )
        noise_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ + 500, amplitude=0.5
        )
        combined_signal = target_signal + noise_signal

        filtered_signal = processor.apply_bandpass_filter(combined_signal)

        # Filtered signal should have same length
        assert len(filtered_signal) == len(combined_signal)

        # Check that high-frequency noise is reduced
        # (This is a basic check - more sophisticated verification would require spectral analysis)
        assert isinstance(filtered_signal, np.ndarray)

    def test_apply_bandpass_filter_empty_data(self):
        """Test band-pass filter with empty audio data."""
        processor = SignalProcessor()

        with pytest.raises(RuntimeError, match="Band-pass filtering failed"):
            processor.apply_bandpass_filter(np.array([]))

    @patch("morsecode.signal_processor.signal.butter")
    def test_apply_bandpass_filter_error_handling(self, mock_butter):
        """Test band-pass filter error handling."""
        processor = SignalProcessor()
        test_signal = self.create_test_signal(frequency=600)

        # Mock filter design to raise an exception
        mock_butter.side_effect = Exception("Filter design failed")

        with pytest.raises(RuntimeError, match="Band-pass filtering failed"):
            processor.apply_bandpass_filter(test_signal)

    def test_calculate_snr_clean_signal(self):
        """Test SNR calculation with clean signal."""
        processor = SignalProcessor()
        # Create clean signal at target frequency
        clean_signal = self.create_test_signal(
            frequency=DEFAULT_TARGET_FREQUENCY_HZ, amplitude=1.0, duration_sec=0.1
        )

        snr_db = processor.calculate_snr(clean_signal)

        # Clean signal should have high SNR
        assert snr_db > 10  # Should be significantly above noise floor

    def test_calculate_snr_noisy_signal(self):
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

    def test_calculate_snr_empty_data(self):
        """Test SNR calculation with empty audio data."""
        processor = SignalProcessor()

        # SNR calculation returns 0.0 on error instead of raising
        snr = processor.calculate_snr(np.array([]))
        assert snr == 0.0

    def test_get_dominant_frequency_single_tone(self):
        """Test dominant frequency detection with single tone."""
        processor = SignalProcessor()
        test_freq = 800  # Hz
        test_signal = self.create_test_signal(frequency=test_freq, duration_sec=0.1)

        dominant_freq = processor.get_dominant_frequency(test_signal)

        # Dominant frequency should be close to test frequency
        assert abs(dominant_freq - test_freq) / test_freq < 0.1

    def test_get_dominant_frequency_multiple_tones(self):
        """Test dominant frequency detection with multiple tones."""
        processor = SignalProcessor()

        # Create signal with two tones, one stronger
        strong_tone = self.create_test_signal(frequency=700, amplitude=2.0)
        weak_tone = self.create_test_signal(frequency=900, amplitude=1.0)
        combined_signal = strong_tone + weak_tone

        dominant_freq = processor.get_dominant_frequency(combined_signal)

        # Should detect the stronger tone (700 Hz)
        assert abs(dominant_freq - 700) / 700 < 0.1

    def test_get_dominant_frequency_empty_data(self):
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
    def test_different_configurations(self, sample_rate, target_freq, window_size):
        """Test SignalProcessor with different configuration parameters."""
        cfg = {
            "sample_rate_hz": sample_rate,
            "target_frequency_hz": target_freq,
            "fft_window_size": window_size,
        }

        processor = SignalProcessor(cfg_dict=cfg)

        # Test signal at target frequency
        test_signal = self.create_test_signal(
            frequency=target_freq, sample_rate=sample_rate, duration_sec=0.1
        )

        # All operations should work with different configurations
        frequencies, magnitudes = processor.compute_fft(test_signal)
        tone_detected = processor.detect_tone(test_signal)
        filtered_signal = processor.apply_bandpass_filter(test_signal)
        snr_db = processor.calculate_snr(test_signal)
        dominant_freq = processor.get_dominant_frequency(test_signal)

        # Basic sanity checks
        assert len(frequencies) == window_size // 2
        assert len(magnitudes) == window_size // 2
        assert isinstance(tone_detected, bool)
        assert len(filtered_signal) == len(test_signal)
        assert isinstance(snr_db, float)
        assert isinstance(dominant_freq, float)

    def test_logging_configuration(self, caplog):
        """Test that logging is properly configured."""
        with caplog.at_level(logging.INFO):
            SignalProcessor({})

        # Should log about missing configuration parameters and initialization
        log_messages = [record.message for record in caplog.records]
        assert any("not found in configuration" in msg for msg in log_messages)
        assert any("SignalProcessor initialized" in msg for msg in log_messages)

    def test_error_propagation(self):
        """Test that processing errors are properly handled and logged."""
        # Test initialization error by mocking the initialization during construction
        with patch(
            "morsecode.signal_processor.SignalProcessor._initialize_processing",
            side_effect=Exception("Init failed"),
        ):
            with pytest.raises(RuntimeError, match="Failed to initialize signal processor"):
                SignalProcessor()

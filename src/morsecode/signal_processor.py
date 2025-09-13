"""Signal processing module for Morse code detection and analysis.

This module provides FFT-based signal analysis, tone detection, and filtering
capabilities for processing audio data containing Morse code signals. It supports
configurable detection thresholds and real-time audio stream processing.

Example usage:
    ```python
    from morsecode.signal_processor import SignalProcessor

    cfg = {
        'sample_rate_hz': 44100,
        'target_frequency_hz': 600,
        'fft_window_size': 1024
    }

    processor = SignalProcessor(cfg_dict=cfg)
    tone_detected = processor.detect_tone(audio_chunk)
    ```
"""

import logging
from typing import Any

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq

# Constants
DEFAULT_SAMPLE_RATE_HZ = 44100
DEFAULT_TARGET_FREQUENCY_HZ = 600  # Common CW frequency
DEFAULT_FFT_WINDOW_SIZE = 1024
DEFAULT_DETECTION_THRESHOLD = 0.1
DEFAULT_FILTER_BANDWIDTH_HZ = 50
DEFAULT_NOISE_FLOOR_DB = -40


class SignalProcessor:
    """A class to handle FFT-based signal analysis for Morse code detection.

    This class provides methods for frequency domain analysis, tone detection,
    and signal filtering specifically designed for Morse code processing.

    Attributes:
        sample_rate_hz: Audio sampling rate in Hz.
        target_frequency_hz: Target Morse code tone frequency in Hz.
        fft_window_size: Size of FFT analysis window.
        detection_threshold: Amplitude threshold for tone detection.
        filter_bandwidth_hz: Bandwidth of band-pass filter in Hz.
        noise_floor_db: Noise floor level in dB for SNR calculations.
    """

    def __init__(self, cfg_dict: dict[str, Any] | None = None) -> None:
        """Initialize the SignalProcessor with configuration parameters.

        Args:
            cfg_dict: Configuration dictionary containing initialization parameters.
                     Expected keys: 'sample_rate_hz', 'target_frequency_hz',
                     'fft_window_size', 'detection_threshold', 'filter_bandwidth_hz',
                     'noise_floor_db'
        """
        # Initialize logging as the first step in constructor
        self.logger = logging.getLogger(__name__)

        cfg_dict = cfg_dict or {}

        # Initialize configuration parameters
        self.sample_rate_hz: int = self._init_param(
            cfg_dict, "sample_rate_hz", DEFAULT_SAMPLE_RATE_HZ
        )
        self.target_frequency_hz: int = self._init_param(
            cfg_dict, "target_frequency_hz", DEFAULT_TARGET_FREQUENCY_HZ
        )
        self.fft_window_size: int = self._init_param(
            cfg_dict, "fft_window_size", DEFAULT_FFT_WINDOW_SIZE
        )
        self.detection_threshold: float = self._init_param(
            cfg_dict, "detection_threshold", DEFAULT_DETECTION_THRESHOLD
        )
        self.filter_bandwidth_hz: int = self._init_param(
            cfg_dict, "filter_bandwidth_hz", DEFAULT_FILTER_BANDWIDTH_HZ
        )
        self.noise_floor_db: int = self._init_param(
            cfg_dict, "noise_floor_db", DEFAULT_NOISE_FLOOR_DB
        )

        # Initialize processing state
        self._frequency_bins: np.ndarray | None = None
        self._window: np.ndarray | None = None

        try:
            self._initialize_processing()
        except Exception as e:
            self.logger.exception("Error initializing SignalProcessor: %s", str(e))
            raise RuntimeError(f"Failed to initialize signal processor: {e}") from e

        self.logger.info(
            "SignalProcessor initialized with target frequency %d Hz", self.target_frequency_hz
        )

    def _init_param(self, cfg_dict: dict[str, Any], key: str, default: Any) -> Any:
        """Initialize a parameter with a default value if the key is missing.

        Args:
            cfg_dict: Configuration dictionary.
            key: Parameter key to look up.
            default: Default value if key is not found.

        Returns:
            The parameter value from config or default.
        """
        value = cfg_dict.get(key, default)
        if key not in cfg_dict:
            self.logger.info(
                "Parameter '%s' not found in configuration. Using default: %s", key, default
            )
        return value

    def _initialize_processing(self) -> None:
        """Initialize FFT processing components and pre-compute constants."""
        try:
            # Pre-compute frequency bins for FFT
            self._frequency_bins = fftfreq(self.fft_window_size, 1.0 / self.sample_rate_hz)

            # Create Hanning window for FFT to reduce spectral leakage
            self._window = np.hanning(self.fft_window_size)

            self.logger.debug(
                "Processing initialization complete. FFT size: %d samples", self.fft_window_size
            )

        except Exception as e:
            self.logger.exception("Error initializing signal processing: %s", str(e))
            raise RuntimeError(f"Failed to initialize signal processor: {e}") from e

    def get_params(self) -> dict[str, Any]:
        """Return the current configuration parameters.

        Returns:
            Dictionary containing current configuration parameters.
        """
        return {
            "sample_rate_hz": self.sample_rate_hz,
            "target_frequency_hz": self.target_frequency_hz,
            "fft_window_size": self.fft_window_size,
            "detection_threshold": self.detection_threshold,
            "filter_bandwidth_hz": self.filter_bandwidth_hz,
            "noise_floor_db": self.noise_floor_db,
        }

    def compute_fft(self, audio_data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Compute FFT of audio data with windowing.

        Args:
            audio_data: Audio samples to analyze.

        Returns:
            Tuple of (frequencies, magnitudes) from FFT analysis.

        Raises:
            ValueError: If audio data is invalid or too short.
            RuntimeError: If FFT computation fails.
        """
        try:
            if len(audio_data) == 0:
                raise ValueError("Audio data cannot be empty")

            if len(audio_data) < self.fft_window_size:
                # Pad with zeros if audio data is shorter than window
                padded_data = np.zeros(self.fft_window_size)
                padded_data[: len(audio_data)] = audio_data
                audio_data = padded_data
            elif len(audio_data) > self.fft_window_size:
                # Truncate if longer than window
                audio_data = audio_data[: self.fft_window_size]

            # Apply windowing to reduce spectral leakage
            windowed_data = audio_data * self._window

            # Compute FFT
            fft_result = fft(windowed_data)

            # Compute magnitude spectrum (positive frequencies only)
            magnitude_spectrum = np.abs(fft_result[: self.fft_window_size // 2])
            frequency_spectrum = self._frequency_bins[: self.fft_window_size // 2]  # type: ignore[index]

            self.logger.debug(
                "FFT computed successfully. Peak frequency: %.1f Hz",
                frequency_spectrum[np.argmax(magnitude_spectrum)],
            )

            return frequency_spectrum, magnitude_spectrum

        except Exception as e:
            self.logger.exception("Error computing FFT: %s", str(e))
            raise RuntimeError(f"FFT computation failed: {e}") from e

    def detect_tone(self, audio_data: np.ndarray) -> bool:
        """Detect if target tone frequency is present in audio data.

        Args:
            audio_data: Audio samples to analyze for tone presence.

        Returns:
            True if target tone is detected above threshold, False otherwise.

        Raises:
            ValueError: If audio data is invalid.
        """
        try:
            if len(audio_data) == 0:
                self.logger.warning("Empty audio data provided to tone detection")
                return False

            # Compute FFT of audio data
            frequencies, magnitudes = self.compute_fft(audio_data)

            # Find frequency bin closest to target frequency
            target_bin_idx = np.argmin(np.abs(frequencies - self.target_frequency_hz))
            target_frequency = frequencies[target_bin_idx]

            # Define frequency range around target (bandwidth filter)
            freq_range_start = self.target_frequency_hz - self.filter_bandwidth_hz // 2
            freq_range_end = self.target_frequency_hz + self.filter_bandwidth_hz // 2

            # Find all bins within the target frequency range
            freq_mask = (frequencies >= freq_range_start) & (frequencies <= freq_range_end)

            if not np.any(freq_mask):
                self.logger.warning(
                    "No frequency bins found in target range [%d-%d] Hz",
                    freq_range_start,
                    freq_range_end,
                )
                return False

            # Sum energy in target frequency band
            target_energy = np.sum(magnitudes[freq_mask])

            # Compute total energy for normalization
            total_energy = np.sum(magnitudes)

            # Calculate relative energy ratio
            if total_energy > 0:
                energy_ratio = target_energy / total_energy
            else:
                energy_ratio = 0.0

            # Determine if tone is detected
            tone_detected = energy_ratio > self.detection_threshold

            self.logger.debug(
                "Tone detection: frequency=%.1f Hz, energy_ratio=%.3f, detected=%s",
                target_frequency,
                energy_ratio,
                tone_detected,
            )

            return bool(tone_detected)

        except Exception as e:
            self.logger.exception("Error in tone detection: %s", str(e))
            return False

    def apply_bandpass_filter(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply band-pass filter centered on target frequency.

        Args:
            audio_data: Audio samples to filter.

        Returns:
            Filtered audio data.

        Raises:
            ValueError: If audio data or filter parameters are invalid.
            RuntimeError: If filtering operation fails.
        """
        try:
            if len(audio_data) == 0:
                raise ValueError("Audio data cannot be empty")

            # Calculate filter parameters
            nyquist_freq = self.sample_rate_hz / 2
            low_cutoff = max(self.target_frequency_hz - self.filter_bandwidth_hz // 2, 1)
            high_cutoff = min(
                self.target_frequency_hz + self.filter_bandwidth_hz // 2, nyquist_freq - 1
            )

            # Normalize frequencies to [0, 1] range
            low_normalized = low_cutoff / nyquist_freq
            high_normalized = high_cutoff / nyquist_freq

            # Design Butterworth band-pass filter
            filter_order = 4
            sos = signal.butter(
                filter_order, [low_normalized, high_normalized], btype="band", output="sos"
            )

            # Apply filter
            filtered_data = signal.sosfilt(sos, audio_data)

            self.logger.debug("Band-pass filter applied: [%.1f-%.1f] Hz", low_cutoff, high_cutoff)

            return np.array(filtered_data)

        except Exception as e:
            self.logger.exception("Error applying band-pass filter: %s", str(e))
            raise RuntimeError(f"Band-pass filtering failed: {e}") from e

    def calculate_snr(self, audio_data: np.ndarray) -> float:
        """Calculate signal-to-noise ratio of audio data.

        Args:
            audio_data: Audio samples to analyze.

        Returns:
            Signal-to-noise ratio in dB.

        Raises:
            ValueError: If audio data is invalid.
        """
        try:
            if len(audio_data) == 0:
                raise ValueError("Audio data cannot be empty")

            # Compute FFT
            frequencies, magnitudes = self.compute_fft(audio_data)

            # Define signal band around target frequency
            signal_start = self.target_frequency_hz - self.filter_bandwidth_hz // 2
            signal_end = self.target_frequency_hz + self.filter_bandwidth_hz // 2
            signal_mask = (frequencies >= signal_start) & (frequencies <= signal_end)

            # Define noise bands (exclude signal region)
            noise_mask = ~signal_mask

            # Calculate signal and noise power
            signal_power = np.mean(magnitudes[signal_mask]) if np.any(signal_mask) else 0
            noise_power = np.mean(magnitudes[noise_mask]) if np.any(noise_mask) else 1e-10

            # Calculate SNR in dB
            snr_db = 20 * np.log10(signal_power / noise_power) if noise_power > 0 else 0

            self.logger.debug(
                "SNR calculation: signal_power=%.3f, noise_power=%.3f, SNR=%.1f dB",
                signal_power,
                noise_power,
                snr_db,
            )

            return float(snr_db)

        except Exception as e:
            self.logger.exception("Error calculating SNR: %s", str(e))
            return 0.0

    def get_dominant_frequency(self, audio_data: np.ndarray) -> float:
        """Find the dominant frequency in audio data.

        Args:
            audio_data: Audio samples to analyze.

        Returns:
            Frequency of the strongest spectral component in Hz.

        Raises:
            ValueError: If audio data is invalid.
        """
        try:
            if len(audio_data) == 0:
                raise ValueError("Audio data cannot be empty")

            # Compute FFT
            frequencies, magnitudes = self.compute_fft(audio_data)

            # Find peak frequency
            peak_idx = np.argmax(magnitudes)
            dominant_frequency = frequencies[peak_idx]

            self.logger.debug(
                "Dominant frequency: %.1f Hz (magnitude: %.3f)",
                dominant_frequency,
                magnitudes[peak_idx],
            )

            return float(dominant_frequency)

        except Exception as e:
            self.logger.exception("Error finding dominant frequency: %s", str(e))
            return 0.0

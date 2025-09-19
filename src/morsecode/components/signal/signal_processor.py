"""Signal processing module for Morse code detection and analysis.

This module provides FFT-based signal analysis, tone detection, and filtering
capabilities for processing audio data containing Morse code signals. It supports
configurable detection thresholds and real-time audio stream processing.

Example usage:
    ```python
    from morsecode.components.signal.signal_processor import SignalProcessor

    config = SignalConfig(
        sample_rate=44100,
        frequency=600,
        bandwidth=50
    )

    processor = SignalProcessor(config=config)
    tone_detected = processor.detect_tone(audio_chunk)
    ```
"""

from typing import Any

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq

from morsecode.components.signal.signal_config_keys import SignalCfgKey, SignalCfgSection
from morsecode.components.signal.signal_config_schema import SignalConfigSchema, SignalMode
from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import AudioChunkEvent, ToneDetectedEvent

# Constants - components should get values from config, not import constants directly
DEFAULT_SAMPLE_RATE_HZ = 44100
DEFAULT_TARGET_FREQUENCY_HZ = 600  # Fallback only - should come from config
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

    def __init__(self, cfg_mgr) -> None:
        """Initialize the SignalProcessor with enum-based configuration.

        Args:
            cfg_mgr: Config manager for enum-based configuration.
        """
        # STEP 1: Initialize ComponentLogger FIRST (required by CLAUDE.md)
        from util.logging import ComponentLogger

        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("SignalProcessor initializing...")

        # STEP 2: Register component configuration schema
        cfg_mgr.register_enum_config(SignalCfgSection.SIGNAL, SignalConfigSchema)
        cfg = cfg_mgr.get_section(SignalCfgSection.SIGNAL)

        # STEP 3: Register logging config for this component (enables config-driven log levels)
        cfg_mgr.register_logging_config(__name__, default_level="INFO")

        # STEP 4: Access configuration with type safety
        self.sample_rate_hz: int = cfg.get_int(SignalCfgKey.SAMPLE_RATE)
        self.target_frequency_hz: int = cfg.get_int(SignalCfgKey.FREQUENCY)
        self.detection_threshold: float = cfg.get_double(SignalCfgKey.THRESHOLD)
        self.filter_bandwidth_hz: int = cfg.get_int(SignalCfgKey.BANDWIDTH)
        self.mode: SignalMode = cfg.get_enum(SignalCfgKey.MODE, SignalMode)

        # STEP 5: Global config for cross-cutting concerns (recommended)
        global_cfg = cfg_mgr.get_section("global")
        self.debug = global_cfg.get_bool("debug") if global_cfg.get("debug") else False
        self.timeout_ms = global_cfg.get_int("timeout_ms") if global_cfg.get("timeout_ms") else 30000

        # STEP 6: Log completion with lazy % formatting (CRITICAL!)
        self.logger.info(
            "SignalProcessor initialized: freq=%d Hz, threshold=%.2f, bandwidth=%d Hz, mode=%s",
            self.target_frequency_hz,
            self.detection_threshold,
            self.filter_bandwidth_hz,
            self.mode.value,
        )

        # STEP 7: Debug logging controlled by config (not code!)
        self.logger.debug("Internal state: ready for processing")

        # Common initialization regardless of config method
        self.fft_window_size: int = DEFAULT_FFT_WINDOW_SIZE
        self.noise_floor_db: int = DEFAULT_NOISE_FLOOR_DB  # Not in config model yet

        # Initialize processing state
        self._frequency_bins: np.ndarray | None = None
        self._window: np.ndarray | None = None
        self._chunk_counter: int = 0

        # Get global event bus for publishing events
        self._event_bus = get_global_event_bus()

        try:
            self._initialize_processing()
        except Exception as e:
            self.logger.exception("Error initializing SignalProcessor: %s", str(e))
            raise RuntimeError(f"Failed to initialize signal processor: {e}") from e

        self.logger.info("SignalProcessor initialized with target frequency %d Hz", self.target_frequency_hz)

    def _initialize_processing(self) -> None:
        """Initialize FFT processing components and pre-compute constants."""
        try:
            # Pre-compute frequency bins for FFT
            self._frequency_bins = fftfreq(self.fft_window_size, 1.0 / self.sample_rate_hz)

            # Create Hanning window for FFT to reduce spectral leakage
            self._window = np.hanning(self.fft_window_size)

            self.logger.debug("Processing initialization complete. FFT size: %d samples", self.fft_window_size)

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

    def detect_tone(self, audio_data: np.ndarray, adaptive_frequency: bool = True) -> bool:
        """Detect if target tone frequency is present in audio data.

        Args:
            audio_data: Audio samples to analyze for tone presence.
            adaptive_frequency: If True, detect the strongest frequency and adapt to it.

        Returns:
            True if target tone is detected above threshold, False otherwise.

        Raises:
            ValueError: If audio data is invalid.
        """
        try:
            if len(audio_data) == 0:
                self.logger.warning("Empty audio data provided to tone detection")
                return False

            # Increment chunk counter
            self._chunk_counter += 1

            # Publish audio chunk event
            chunk_size_ms = int((len(audio_data) / self.sample_rate_hz) * 1000)
            audio_event = AudioChunkEvent(
                chunk_data=audio_data,
                chunk_size_ms=chunk_size_ms,
                sample_rate=self.sample_rate_hz,
                chunk_number=self._chunk_counter,
                has_more_data=True,  # Assume more data is coming in streaming scenario
            )
            self._event_bus.publish(audio_event)

            # Compute FFT of audio data
            frequencies, magnitudes = self.compute_fft(audio_data)

            # Determine actual target frequency
            if adaptive_frequency:
                # Find the strongest frequency peak in a reasonable range (200-2000 Hz)
                valid_range_mask = (frequencies >= 200) & (frequencies <= 2000)
                if np.any(valid_range_mask):
                    valid_magnitudes = magnitudes[valid_range_mask]
                    valid_frequencies = frequencies[valid_range_mask]
                    peak_idx = np.argmax(valid_magnitudes)
                    detected_frequency = valid_frequencies[peak_idx]

                    # Always use the detected frequency if it's strong enough
                    # This is more aggressive adaptation for better real-world performance
                    max_magnitude = np.max(magnitudes)
                    noise_floor = np.mean(magnitudes) + 2 * np.std(magnitudes)

                    if valid_magnitudes[peak_idx] > noise_floor and valid_magnitudes[peak_idx] > max_magnitude * 0.3:
                        actual_target_freq = detected_frequency
                        self.logger.debug(
                            f"Adaptive frequency detection: {actual_target_freq:.1f} Hz "
                            f"(was {self.target_frequency_hz} Hz)"
                        )
                    else:
                        actual_target_freq = self.target_frequency_hz
                else:
                    actual_target_freq = self.target_frequency_hz
            else:
                actual_target_freq = self.target_frequency_hz

            # Find frequency bin closest to actual target frequency
            target_bin_idx = np.argmin(np.abs(frequencies - actual_target_freq))
            target_frequency = frequencies[target_bin_idx]

            # Define frequency range around actual target (bandwidth filter)
            freq_range_start = actual_target_freq - self.filter_bandwidth_hz // 2
            freq_range_end = actual_target_freq + self.filter_bandwidth_hz // 2

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

            # Calculate confidence
            confidence = min(1.0, energy_ratio * 2.0)  # Scale confidence

            # Calculate SNR for additional context
            snr_db = self.calculate_snr(audio_data)

            # Determine if tone is detected
            tone_detected = energy_ratio > self.detection_threshold

            # Publish tone detection event
            tone_event = ToneDetectedEvent(
                detected=tone_detected,
                frequency=float(target_frequency),
                confidence=confidence,
                snr_db=snr_db,
                chunk_number=self._chunk_counter,
                detection_threshold=self.detection_threshold,
            )
            self._event_bus.publish(tone_event)

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
            high_cutoff = min(self.target_frequency_hz + self.filter_bandwidth_hz // 2, nyquist_freq - 1)

            # Normalize frequencies to [0, 1] range
            low_normalized = low_cutoff / nyquist_freq
            high_normalized = high_cutoff / nyquist_freq

            # Design Butterworth band-pass filter
            filter_order = 4
            sos = signal.butter(filter_order, [low_normalized, high_normalized], btype="band", output="sos")

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

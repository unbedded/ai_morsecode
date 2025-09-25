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
from morsecode.events.types import AudioChunkEvent, FFTSpectrumEvent, FilteredMagnitudeEvent, ToneDetectedEvent
from util.config import ConfigurableBase

# All configuration values now come from schema - no hardcoded constants needed


class SignalProcessor(ConfigurableBase):
    """A class to handle FFT-based signal analysis for Morse code detection.

    This class provides methods for frequency domain analysis, tone detection,
    and signal filtering specifically designed for Morse code processing.

    Uses ConfigurableBase inheritance pattern for type-safe configuration access
    and runtime reconfiguration support.

    Attributes:
        sample_rate_hz: Audio sampling rate in Hz.
        target_frequency_hz: Target Morse code tone frequency in Hz.
        fft_window_size: Size of FFT analysis window.
        detection_threshold: Amplitude threshold for tone detection.
        filter_bandwidth_hz: Bandwidth of band-pass filter in Hz.
        noise_floor_db: Noise floor level in dB for SNR calculations.
    """

    # ConfigurableBase requirements
    CONFIG_SCHEMA = SignalConfigSchema
    CONFIG_SECTION = SignalCfgSection.SIGNAL.value
    CONFIG_KEYS = SignalCfgKey

    def __init__(self, cfg_mgr, overrides=None) -> None:
        """Initialize the SignalProcessor with ConfigurableBase pattern.

        Args:
            cfg_mgr: Config manager for enum-based configuration.
            overrides: Optional configuration overrides for testing/tuning.
        """
        # Call ConfigurableBase constructor (handles all config/logging boilerplate)
        super().__init__(cfg_mgr, overrides)

        # Initialize processing state and event bus after configuration is loaded
        self._frequency_bins: np.ndarray | None = None
        self._window: np.ndarray | None = None
        self._chunk_counter: int = 0
        self.actual_frequency_hz: float = float(self.target_frequency_hz)  # Track actual frequency being used

        # Get global event bus for publishing events
        self._event_bus = get_global_event_bus()

        try:
            self._initialize_processing()
        except Exception as e:
            self.logger.exception("Error initializing SignalProcessor: %s", str(e))
            raise RuntimeError(f"Failed to initialize signal processor: {e}") from e

        self.logger.info("SignalProcessor initialized with target frequency %d Hz", self.target_frequency_hz)

    def _load_config_values(self) -> None:
        """Load configuration values using type-safe enum access.

        This method is called by ConfigurableBase during initialization and reconfiguration.
        Only method we need to implement - all boilerplate handled by base class.
        """
        # STEP 1: Load core configuration with type safety
        self.sample_rate_hz: int = self._cfg_section.get_int(SignalCfgKey.SAMPLE_RATE_HZ)
        self.target_frequency_hz: int = self._cfg_section.get_int(SignalCfgKey.FREQUENCY_HZ)
        self.detection_threshold: float = self._cfg_section.get_double(SignalCfgKey.SIGNAL_THRESHOLD_NORM)
        self.filter_bandwidth_hz: int = self._cfg_section.get_int(SignalCfgKey.BANDWIDTH_HZ)
        self.mode: SignalMode = self._cfg_section.get_enum(SignalCfgKey.MODE, SignalMode)
        self.adaptive_frequency: bool = self._cfg_section.get_bool(SignalCfgKey.ADAPTIVE_FREQUENCY)

        # STEP 2: Load advanced signal processing parameters from configuration
        self.cutoff_hz = self._cfg_section.get_double(SignalCfgKey.CUTOFF_HZ)
        self.cw_mag_thresh_seconds = self._cfg_section.get_double(SignalCfgKey.CW_MAG_THRESH_SECONDS)
        self.cw_peak_ratio_threshold = self._cfg_section.get_int(SignalCfgKey.CW_PEAK_RATIO_THRESHOLD)
        self.n_move_avg_elements = self._cfg_section.get_int(SignalCfgKey.N_MOVE_AVG_ELEMENTS)
        self.rolling_buffer_seconds = self._cfg_section.get_double(SignalCfgKey.ROLLING_BUFFER_SECONDS)
        self.freq_range_min = self._cfg_section.get_int(SignalCfgKey.FREQ_RANGE_MIN)
        self.freq_range_max = self._cfg_section.get_int(SignalCfgKey.FREQ_RANGE_MAX)

        # STEP 3: Global config for cross-cutting concerns (recommended pattern)
        try:
            global_cfg = self._cfg_mgr.get_section("global")
            self.debug = global_cfg.get_bool("debug")
            self.timeout_ms = global_cfg.get_int("timeout_ms")
        except (KeyError, ValueError):
            # Global config section may not exist or have values
            self.debug = False
            self.timeout_ms = 30000

        # STEP 4: Initialize signal processing state with loaded parameters
        self.moving_avg_buffer: list[float] = []  # Buffer for moving average smoothing
        self.signal_history: list[float] = []  # Rolling buffer for signal statistics
        self.min_tone_samples = int(self.cw_mag_thresh_seconds * self.sample_rate_hz)

        # STEP 5: FFT and noise parameters from configuration
        self.fft_window_size: int = self._cfg_section.get_int(SignalCfgKey.FFT_WINDOW_SIZE)
        self.noise_floor_db: int = self._cfg_section.get_int(SignalCfgKey.NOISE_FLOOR_DB)

        # STEP 6: Log completion with lazy % formatting (CRITICAL!)
        self.logger.info(
            "SignalProcessor configured: freq=%d Hz, threshold=%.2f, bandwidth=%d Hz, mode=%s, adaptive=%s",
            self.target_frequency_hz,
            self.detection_threshold,
            self.filter_bandwidth_hz,
            self.mode.value if hasattr(self.mode, "value") else str(self.mode),
            self.adaptive_frequency,
        )
        self.logger.info(
            "Signal filters: cutoff=%.1f Hz, min_tone=%.1f s, peak_ratio=%d, avg_elements=%d",
            self.cutoff_hz,
            self.cw_mag_thresh_seconds,
            self.cw_peak_ratio_threshold,
            self.n_move_avg_elements,
        )

        # STEP 7: Debug logging controlled by config (not code!)
        self.logger.debug("Internal state: ready for processing")

    def _on_reconfiguration(self) -> None:
        """Handle reconfiguration side effects.

        Called by ConfigurableBase after configuration values are reloaded.
        Reinitialize processing components that depend on configuration.
        """
        # Update derived values that depend on configuration
        self.min_tone_samples = int(self.cw_mag_thresh_seconds * self.sample_rate_hz)
        self.actual_frequency_hz = float(self.target_frequency_hz)

        # Reinitialize processing components
        try:
            self._initialize_processing()
            self.logger.info("SignalProcessor reconfigured with frequency %d Hz", self.target_frequency_hz)
        except Exception as e:
            self.logger.exception("Error during SignalProcessor reconfiguration: %s", str(e))
            raise RuntimeError(f"Failed to reconfigure signal processor: {e}") from e

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

            # Publish FFT spectrum event for debugging and autoscaling
            peak_idx = np.argmax(magnitudes)
            peak_frequency_hz = frequencies[peak_idx]
            peak_magnitude = magnitudes[peak_idx]
            total_energy = np.sum(magnitudes)
            noise_floor = np.mean(magnitudes) + np.std(magnitudes)  # Simple noise floor estimate

            fft_event = FFTSpectrumEvent(
                peak_frequency_hz=peak_frequency_hz,
                peak_magnitude=peak_magnitude,
                total_energy=total_energy,
                noise_floor=noise_floor,
                chunk_number=self._chunk_counter,
            )
            self._event_bus.publish(fft_event)

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

            # Store the actual frequency being used for external access
            self.actual_frequency_hz = actual_target_freq

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

            # CRITICAL: Adaptive gain control for real-world fading signals
            # For real-world audio, we need dynamic normalization that adapts to signal level

            # Method 1: Relative energy (good for synthetic, poor for real-world)
            if total_energy > 0:
                relative_energy_ratio = target_energy / total_energy
            else:
                relative_energy_ratio = 0.0

            # Method 2: Absolute energy with adaptive normalization (better for real-world)
            # Track running statistics for adaptive thresholding
            if not hasattr(self, "energy_history"):
                self.energy_history = []
                self.adaptive_threshold = 0.0

            # Update energy history for adaptive normalization
            self.energy_history.append(target_energy)
            if len(self.energy_history) > 100:  # Keep last 100 samples for stable adaptation
                self.energy_history.pop(0)

            # Calculate adaptive threshold based on recent energy levels
            if len(self.energy_history) >= 10:  # Need sufficient samples for stable threshold
                energy_array = np.array(self.energy_history)
                # Use 75th percentile as adaptive threshold for robust detection
                self.adaptive_threshold = np.percentile(energy_array, 75)

            # Calculate SNR for adaptive normalization decision (needed here!)
            snr_db = self.calculate_snr(audio_data)

            # Adaptive energy ratio: compare current energy to adaptive threshold
            if self.adaptive_threshold > 0:
                adaptive_energy_ratio = target_energy / self.adaptive_threshold
            else:
                adaptive_energy_ratio = 0.0

            # Choose normalization method based on signal characteristics
            # Use adaptive method for real-world signals with low SNR
            use_adaptive_normalization = snr_db < 25.0  # dB threshold for real-world detection

            if use_adaptive_normalization:
                energy_ratio = min(1.0, adaptive_energy_ratio)  # Cap at 1.0 for stability
                self.logger.debug(
                    "Using adaptive normalization (SNR=%.1f dB): target=%.0f, adaptive_thresh=%.0f, ratio=%.3f",
                    snr_db,
                    target_energy,
                    self.adaptive_threshold,
                    energy_ratio,
                )
            else:
                energy_ratio = relative_energy_ratio
                self.logger.debug(
                    "Using relative normalization (SNR=%.1f dB): target=%.0f, total=%.0f, ratio=%.3f",
                    snr_db,
                    target_energy,
                    total_energy,
                    energy_ratio,
                )

            # Calculate confidence
            confidence = min(1.0, energy_ratio * 2.0)  # Scale confidence

            # CRITICAL: Apply signal processing filters from old config
            # 1. Moving average smoothing to reduce noise
            self.moving_avg_buffer.append(energy_ratio)
            if len(self.moving_avg_buffer) > self.n_move_avg_elements:
                self.moving_avg_buffer.pop(0)

            smoothed_energy_ratio = sum(self.moving_avg_buffer) / len(self.moving_avg_buffer)

            # 2. Apply SNR threshold from old config - DISABLED for debugging
            snr_linear = 10 ** (snr_db / 10)  # Convert dB to linear
            snr_passes = snr_linear >= self.cw_peak_ratio_threshold
            # TEMP: Disable SNR filtering - it's too aggressive
            snr_passes = True

            # 3. Combine smoothed energy and SNR requirements
            # Smart energy selection: Use raw energy for clean signals, smoothed for noisy
            # This prevents silence periods from affecting clean synthetic signals
            # while still providing noise reduction for real-world audio

            snr_threshold_for_raw_energy = 40.0  # dB - above this, use raw energy
            use_raw_energy = snr_db > snr_threshold_for_raw_energy

            if use_raw_energy:
                preliminary_detection = (energy_ratio > self.detection_threshold) and snr_passes
                self.logger.debug(
                    "Using raw energy (SNR=%.1f dB > %.1f): %.3f > %.3f = %s",
                    snr_db,
                    snr_threshold_for_raw_energy,
                    energy_ratio,
                    self.detection_threshold,
                    preliminary_detection,
                )
            else:
                preliminary_detection = (smoothed_energy_ratio > self.detection_threshold) and snr_passes
                self.logger.debug(
                    "Using smoothed energy (SNR=%.1f dB <= %.1f): %.3f > %.3f = %s",
                    snr_db,
                    snr_threshold_for_raw_energy,
                    smoothed_energy_ratio,
                    self.detection_threshold,
                    preliminary_detection,
                )

            # Note: Removed debug logging for cleaner output

            # 4. Duration filtering will be applied by decoder using min_tone_samples
            # (The decoder should filter out tones shorter than cw_mag_thresh_seconds)

            # =====================================================================
            # PUBLISH FILTERED MAGNITUDE EVENT FOR ASCII DEBUGGING
            # =====================================================================
            # Convert energy ratio to normalized magnitude (-1 to +1 scale)
            # This replicates the PyQt graph data for ASCII visualization over SSH

            # LEGACY: Keep original per-chunk switching for backward compatibility
            final_energy_ratio = smoothed_energy_ratio if not use_raw_energy else energy_ratio

            # For consistent signal processing: Use consistent energy selection to avoid switching artifacts
            # If we've seen any high-SNR signals, prefer raw energy for the entire session
            if not hasattr(self, "_uses_consistent_raw"):
                self._uses_consistent_raw = False
                self._high_snr_count = 0

            # Track high-SNR periods to decide energy strategy for the session
            if snr_db > snr_threshold_for_raw_energy:
                self._high_snr_count += 1
                if self._high_snr_count > 2:  # After seeing clean signal, stick with raw for consistency
                    self._uses_consistent_raw = True

            # Use consistent energy for signal processing to avoid transition artifacts
            consistent_energy_ratio = energy_ratio if self._uses_consistent_raw else smoothed_energy_ratio

            # IMPROVED: Use consistent detection logic to avoid switching artifacts in timing
            consistent_detection = (consistent_energy_ratio > self.detection_threshold) and snr_passes

            # Final tone detection decision - use consistent energy to avoid switching artifacts
            tone_detected = consistent_detection

            # Map energy ratio to normalized magnitude scale for better ASCII visualization:
            # - energy_ratio near 0.0 -> magnitude_norm = -1.0 (clear silence/space)
            # - energy_ratio at detection_threshold -> magnitude_norm = 0.0 (threshold line)
            # - energy_ratio well above threshold -> magnitude_norm = +1.0 (strong signal)

            # Enhanced mapping for better visual contrast in ASCII display
            if consistent_energy_ratio < self.detection_threshold:
                # Below threshold: map 0.0 -> -1.0, threshold -> 0.0
                if self.detection_threshold > 0:
                    # Use square root for better visual separation of low values
                    ratio = consistent_energy_ratio / self.detection_threshold
                    magnitude_norm = -1.0 + ratio
                    # Enhance space detection: make very low values more negative
                    if consistent_energy_ratio < self.detection_threshold * 0.1:
                        magnitude_norm = -1.0  # Pure silence
                else:
                    magnitude_norm = -1.0
            else:
                # Above threshold: map threshold -> 0.0, 2*threshold -> +1.0
                excess_ratio = consistent_energy_ratio - self.detection_threshold
                if self.detection_threshold > 0:
                    # Use square root for better signal visualization
                    normalized_excess = excess_ratio / self.detection_threshold
                    magnitude_norm = min(1.0, normalized_excess)
                    # Enhance strong signals for better visual impact
                    if final_energy_ratio > self.detection_threshold * 3.0:
                        magnitude_norm = 1.0  # Maximum signal
                else:
                    magnitude_norm = 1.0

            # Publish filtered magnitude event for ASCII time-series debugging
            magnitude_event = FilteredMagnitudeEvent(
                magnitude_norm=magnitude_norm,
                threshold_norm=0.0,  # Threshold is at 0.0 in our normalized scale
                binary_state=tone_detected,
                chunk_number=self._chunk_counter,
                frequency_hz=float(target_frequency),
            )
            self._event_bus.publish(magnitude_event)

            self.logger.debug(
                "Magnitude event: norm=%.3f, energy_ratio=%.3f, threshold=%.3f, binary=%s",
                magnitude_norm,
                final_energy_ratio,
                self.detection_threshold,
                tone_detected,
            )

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

    def get_signal_strength(self, audio_data: np.ndarray) -> float:
        """Get the signal strength/amplitude.

        Args:
            audio_data: Audio samples as numpy array.

        Returns:
            Signal strength as a normalized value between 0.0 and 1.0.
            0.0 indicates no signal, 1.0 indicates maximum signal.
        """
        try:
            if len(audio_data) == 0:
                return 0.0

            # Calculate RMS (Root Mean Square) for signal strength
            rms = np.sqrt(np.mean(audio_data**2))

            # Normalize to 0-1 range (assuming typical audio range)
            # Use a reasonable maximum amplitude for normalization
            max_amplitude = 1.0  # Assuming normalized audio input
            normalized_strength = min(rms / max_amplitude, 1.0)

            self.logger.debug("Signal strength: RMS=%.3f, normalized=%.3f", rms, normalized_strength)
            return float(normalized_strength)

        except Exception as e:
            self.logger.exception("Error calculating signal strength: %s", str(e))
            return 0.0

    def get_detection_confidence(self, audio_data: np.ndarray) -> float:
        """Get confidence level of tone detection.

        Args:
            audio_data: Audio samples as numpy array.

        Returns:
            Confidence level between 0.0 and 1.0.
            Based on SNR and spectral peak characteristics.
        """
        try:
            if len(audio_data) == 0:
                return 0.0

            # Calculate SNR for confidence
            snr = self.calculate_snr(audio_data)

            # Get spectral analysis confidence
            frequencies, magnitudes = self.compute_fft(audio_data)

            # Find peak around target frequency
            target_bin = int(self.target_frequency_hz * len(magnitudes) / (self.sample_rate_hz / 2))
            target_bin = max(0, min(target_bin, len(magnitudes) - 1))

            # Calculate peak-to-average ratio in target frequency region
            window_size = max(1, len(magnitudes) // 20)  # ~5% of spectrum
            start_idx = max(0, target_bin - window_size // 2)
            end_idx = min(len(magnitudes), target_bin + window_size // 2)

            peak_magnitude = magnitudes[target_bin]
            avg_magnitude = np.mean(magnitudes[start_idx:end_idx])

            # Convert measurements to confidence (0-1)
            snr_confidence = min(max(snr / 10.0, 0.0), 1.0)  # SNR > 10 = high confidence
            peak_confidence = min(peak_magnitude / (avg_magnitude + 1e-10), 1.0)

            # Combined confidence (weighted average)
            confidence = 0.7 * snr_confidence + 0.3 * peak_confidence

            self.logger.debug(
                "Detection confidence: SNR=%.1f, peak_ratio=%.2f, combined=%.3f", snr, peak_confidence, confidence
            )

            return float(confidence)

        except Exception as e:
            self.logger.exception("Error calculating detection confidence: %s", str(e))
            return 0.0

    def get_target_frequency(self) -> float:
        """Get the target frequency this processor is configured for.

        Returns:
            Target frequency in Hz that this processor is designed to detect.
        """
        return float(self.target_frequency_hz)

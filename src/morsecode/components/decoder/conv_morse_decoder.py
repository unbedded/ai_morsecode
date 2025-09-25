"""Convolution-based Morse Code Decoder with Matched Filtering.

This module implements the original sophisticated matched filter approach using
symmetric synthetic patterns and proper numpy convolution. It restores the
scientific rigor that was lost during the previous port while integrating
with the modern pub/sub component architecture.

The core algorithm uses:
- Symmetric synthetic patterns: [(-1,1), (+1,1), (-1,1)] for dit
- Proper convolution: numpy.convolve(pattern, signal, mode='same')
- Derivative-based peak detection with zero crossings
- Competitive selection with winner-take-all thresholding
- Gain weighting to prevent bias between dit/dash/space patterns

This produces the expected symmetric triangular correlation responses
when symmetric patterns are convolved with square wave signals.
"""

from typing import Any

import numpy as np

from morsecode.components.decoder.keys import CfgKey
from morsecode.components.decoder.schema import ConfigSchema
from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import MorseProbabilityEvent
from util.config import AwesomeConfigManager
from util.config.configurable_base import ConfigurableBase


class SyntheticPatternGenerator:
    """Generates symmetric synthetic patterns for matched filtering.

    This is a direct port of the original synpat_code.py logic with
    the proven gain weighting and pattern definitions.
    """

    def __init__(self):
        """Initialize synthetic pattern constants."""
        # Original gain constants from synpat_code.py
        self.DIT_GAIN = 0.333 * 1.3  # = 0.433
        self.NIT_GAIN = 0.333 * 1.3  # = 0.433
        self.DAH_GAIN = 0.2 * 1.1  # = 0.22
        self.LETTER_GAIN = 0.2 * 1.1  # = 0.22
        self.WORD_GAIN = 0.125 * 1.0  # = 0.125
        self.WPM_FACTOR = 1.2  # PARIS timing factor

    def create_synthetic(
        self, fft_rate_hz: float, dit_msec: float, pattern: list[tuple[float, float]], amplitude_multiplier: float
    ) -> np.ndarray:
        """Create synthetic array from pattern definition.

        Args:
            fft_rate_hz: Sampling rate in Hz
            dit_msec: Duration of one dit in milliseconds
            pattern: List of (value, duration_in_dits) tuples
            amplitude_multiplier: Gain scaling factor

        Returns:
            Synthetic pattern array for convolution
        """
        samples_per_dit = (fft_rate_hz * dit_msec) / 1000
        synthetic_list = []

        for value, duration_in_dits in pattern:
            num_samples = int(samples_per_dit * duration_in_dits) if duration_in_dits != 0 else 1
            synthetic_list.extend([value] * num_samples)

        # Convert to numpy array and apply gain
        synthetic_array = np.array(synthetic_list) * amplitude_multiplier
        return synthetic_array

    def generate_synthetic_patterns(self, fft_rate_hz: float, dit_msec: float) -> dict[str, np.ndarray]:
        """Generate all synthetic patterns for matched filtering.

        This recreates the original symmetric patterns:
        - dit:    [(-1,1), (+1,1), (-1,1)]  → Symmetric -1,+1,-1
        - ndit:   [(+1,1), (-1,1), (+1,1)]  → Symmetric +1,-1,+1
        - dah:    [(-1,1), (+1,3), (-1,1)]  → Symmetric -1,+3,-1
        - letter: [(+1,1), (-1,3), (+1,1)]  → Symmetric +1,-3,+1
        - word:   [(+1,1), (-1,7)]          → Edge space +1,-7

        Args:
            fft_rate_hz: Sampling rate in Hz
            dit_msec: Duration of one dit in milliseconds

        Returns:
            Dictionary of pattern name to synthetic array
        """
        # Original symmetric patterns from synpat_code.py
        patterns = {
            "dit": [(-1.0, 1.0), (+1.0, 1.0), (-1.0, 1.0)],  # Symmetric
            "ndit": [(+1.0, 1.0), (-1.0, 1.0), (+1.0, 1.0)],  # Symmetric (inverted dit)
            "dah": [(-1.0, 1.0), (+1.0, 3.0), (-1.0, 1.0)],  # Symmetric
            "letter": [(+1.0, 1.0), (-1.0, 3.0), (+1.0, 1.0)],  # Symmetric (inverted dah)
            "word": [(+1.0, 1.0), (-1.0, 7.0)],  # Word space pattern
        }

        # Original gain weighting to prevent bias
        gains = {
            "dit": self.DIT_GAIN,
            "ndit": self.NIT_GAIN,
            "dah": self.DAH_GAIN,
            "letter": self.LETTER_GAIN,
            "word": self.WORD_GAIN,
        }

        syn_dict = {}
        for key, pattern in patterns.items():
            synthetic_array = self.create_synthetic(fft_rate_hz, dit_msec, pattern, gains[key])
            # Original normalization from synpat_code.py line 118
            synthetic_array /= (fft_rate_hz * dit_msec) / 1000
            syn_dict[key] = synthetic_array

        return syn_dict

    def dit_sec_from_wpm(self, wpm: float) -> float:
        """Calculate dit duration from WPM using PARIS timing."""
        return self.WPM_FACTOR / wpm

    def wpm_from_dit_sec(self, dit_sec: float) -> float:
        """Calculate WPM from dit duration using PARIS timing."""
        return self.WPM_FACTOR / dit_sec


class ConvMorseDecoder(ConfigurableBase):
    """Convolution-based Morse code decoder using matched filtering.

    This decoder restores the original sophisticated algorithm:
    1. Symmetric synthetic pattern generation with gain weighting
    2. Proper numpy convolution: conv = np.convolve(pattern, signal, mode='same')
    3. Derivative-based peak detection using zero crossings
    4. Competitive selection with winner-take-all thresholding
    5. Event publishing for real-time probability visualization

    The algorithm produces symmetric triangular correlation responses
    as expected from proper matched filtering theory.
    """

    CONFIG_SCHEMA = ConfigSchema
    CONFIG_SECTION = "decoder"
    CONFIG_KEYS = CfgKey

    def __init__(self, cfg_mgr: AwesomeConfigManager, overrides: dict[str, Any] | None = None):
        """Initialize the ConvMorseDecoder."""
        super().__init__(cfg_mgr, overrides)

        # Initialize synthetic pattern generator
        self._pattern_gen = SyntheticPatternGenerator()

        # Get global event bus for publishing events
        self._event_bus = get_global_event_bus()

        # Signal processing state
        self._signal_buffer: np.ndarray | None = None
        self._sample_rate_hz: float = 1000.0  # Default 1kHz
        self._current_time: float = 0.0

        # Probability arrays for event publishing
        self._dit_probability: np.ndarray | None = None
        self._dah_probability: np.ndarray | None = None
        self._letter_probability: np.ndarray | None = None
        self._word_probability: np.ndarray | None = None

        # Impulse detection arrays
        self._dit_impulse: np.ndarray | None = None
        self._dah_impulse: np.ndarray | None = None
        self._letter_impulse: np.ndarray | None = None
        self._word_impulse: np.ndarray | None = None

        self.logger.info("ConvMorseDecoder initialized with matched filtering")

    def _load_config_values(self) -> None:
        """Load configuration values - required by ConfigurableBase."""
        # Core timing parameters
        self.wpm_estimate: int = self._cfg_section.get_int(CfgKey.WPM)
        self.dot_duration_ms: float = self._cfg_section.get_double(CfgKey.DOT_DURATION_MS)

        # Convolution-specific parameters
        self.probability_threshold: float = self._cfg_section.get_double(CfgKey.TIMING_TOLERANCE_NORM)

        # Auto-detection parameters
        self.auto_detect_wpm: bool = self._cfg_section.get_bool(CfgKey.AUTO_DETECT_WPM)
        self.wpm_range_min: int = self._cfg_section.get_int(CfgKey.WPM_RANGE_MIN)
        self.wpm_range_max: int = self._cfg_section.get_int(CfgKey.WPM_RANGE_MAX)

        # Calculate derived timing parameters using PARIS formula
        self._recalculate_timing_parameters()

        self.logger.info("ConvMorseDecoder configured: %d WPM, %.1fms dit", self.wpm_estimate, self.dot_duration_ms)

    def _recalculate_timing_parameters(self) -> None:
        """Recalculate timing parameters from current WPM."""
        # Use PARIS timing: 1200ms / WPM = dit duration
        self.dot_duration_ms = 1200.0 / self.wpm_estimate
        self.dash_duration_ms = self.dot_duration_ms * 3.0

        self.logger.debug("Timing recalculated: dit=%.1fms, dash=%.1fms", self.dot_duration_ms, self.dash_duration_ms)

    def set_sample_rate(self, sample_rate_hz: float) -> None:
        """Set the signal sampling rate for convolution processing.

        Args:
            sample_rate_hz: Signal sampling rate in Hz
        """
        self._sample_rate_hz = sample_rate_hz
        self.logger.info("Sample rate set to %.1f Hz", sample_rate_hz)

    def process_signal_chunk(self, signal_chunk: np.ndarray, chunk_duration_ms: float) -> None:
        """Process a chunk of signal data using matched filtering convolution.

        This is the core algorithm that performs:
        1. Generate synthetic patterns for current WPM
        2. Convolve each pattern with the signal
        3. Extract positive/negative correlations
        4. Detect peaks using derivative zero crossings
        5. Apply competitive selection with thresholding
        6. Publish probability events for visualization

        Args:
            signal_chunk: Normalized signal data (should be zero-mean)
            chunk_duration_ms: Duration of this chunk in milliseconds
        """
        try:
            if len(signal_chunk) == 0:
                return

            self._current_time += chunk_duration_ms

            # Generate synthetic patterns for current WPM and sample rate
            syn_patterns = self._pattern_gen.generate_synthetic_patterns(self._sample_rate_hz, self.dot_duration_ms)

            # Initialize probability and impulse arrays
            signal_len = len(signal_chunk)
            dit_probability = np.zeros(signal_len)
            nit_probability = np.zeros(signal_len)
            dah_probability = np.zeros(signal_len)
            letter_probability = np.zeros(signal_len)
            word_probability = np.zeros(signal_len)

            dit_impulse = np.zeros(signal_len, dtype=bool)
            nit_impulse = np.zeros(signal_len, dtype=bool)
            dah_impulse = np.zeros(signal_len, dtype=bool)
            letter_impulse = np.zeros(signal_len, dtype=bool)
            word_impulse = np.zeros(signal_len, dtype=bool)

            # CORE ALGORITHM: Convolution with synthetic patterns (original lines 125-141)

            # Dit/Nit convolution
            conv_dit = np.convolve(syn_patterns["dit"], signal_chunk, mode="same")
            dit_probability = np.maximum(conv_dit, 0)  # Positive correlation
            nit_probability = np.maximum(-conv_dit, 0)  # Negative correlation

            # Derivative-based peak detection for dit
            deriv_dit = np.diff(conv_dit)
            dit_zero_crossings = np.diff(np.sign(deriv_dit)) != 0
            dit_peaks = np.zeros(signal_len, dtype=bool)
            # Safely copy zero crossings with proper length handling
            copy_len = min(len(dit_zero_crossings), signal_len - 2)
            dit_peaks[:copy_len] = dit_zero_crossings[:copy_len]

            # Dah/Letter convolution
            conv_dah = np.convolve(syn_patterns["dah"], signal_chunk, mode="same")
            dah_probability = np.maximum(conv_dah, 0)  # Positive correlation
            letter_probability = np.maximum(-conv_dah, 0)  # Negative correlation

            # Derivative-based peak detection for dah
            deriv_dah = np.diff(conv_dah)
            dah_zero_crossings = np.diff(np.sign(deriv_dah)) != 0
            dah_peaks = np.zeros(signal_len, dtype=bool)
            # Safely copy zero crossings with proper length handling
            copy_len = min(len(dah_zero_crossings), signal_len - 2)
            dah_peaks[:copy_len] = dah_zero_crossings[:copy_len]

            # Word space convolution
            conv_word = np.convolve(syn_patterns["word"], signal_chunk, mode="same")
            word_probability = np.maximum(conv_word, 0)  # Positive correlation only

            # Derivative-based peak detection for word
            deriv_word = np.diff(conv_word)
            word_zero_crossings = np.diff(np.sign(deriv_word)) != 0
            word_peaks = np.zeros(signal_len, dtype=bool)
            # Safely copy zero crossings with proper length handling
            copy_len = min(len(word_zero_crossings), signal_len - 2)
            word_peaks[:copy_len] = word_zero_crossings[:copy_len]

            # COMPETITIVE SELECTION: Winner-take-all with thresholding (original lines 142-152)
            for index in range(signal_len - 2):  # Account for derivative length
                max_prob = max(
                    dit_probability[index],
                    nit_probability[index],
                    dah_probability[index],
                    letter_probability[index],
                    word_probability[index],
                )

                # Only mark impulse if above threshold AND this pattern won
                if max_prob > self.probability_threshold:
                    if dit_peaks[index]:  # Peak detected in dit correlation
                        dit_impulse[index] = dit_probability[index] == max_prob
                        nit_impulse[index] = nit_probability[index] == max_prob
                    if dah_peaks[index]:  # Peak detected in dah correlation
                        dah_impulse[index] = dah_probability[index] == max_prob
                        letter_impulse[index] = letter_probability[index] == max_prob
                    if word_peaks[index]:  # Peak detected in word correlation
                        word_impulse[index] = word_probability[index] == max_prob

            # Store probability arrays for event publishing
            self._dit_probability = dit_probability
            self._dah_probability = dah_probability
            self._letter_probability = letter_probability
            self._word_probability = word_probability

            self._dit_impulse = dit_impulse
            self._dah_impulse = dah_impulse
            self._letter_impulse = letter_impulse
            self._word_impulse = word_impulse

            # Publish probability event for real-time visualization
            self._publish_probability_event()

            self.logger.debug(
                "Processed signal chunk: %d samples, max_dit_prob=%.3f, max_dah_prob=%.3f",
                signal_len,
                np.max(dit_probability),
                np.max(dah_probability),
            )

        except Exception as e:
            self.logger.exception("Error processing signal chunk: %s", str(e))

    def _publish_probability_event(self) -> None:
        """Publish probability arrays via event bus for visualization."""
        try:
            if (
                self._dit_probability is not None
                and self._dah_probability is not None
                and self._letter_probability is not None
                and self._word_probability is not None
            ):
                # Create probability event with correct field names
                event = MorseProbabilityEvent(
                    prob_dit=float(np.mean(self._dit_probability[-10:])),  # Recent average
                    prob_dash=float(np.mean(self._dah_probability[-10:])),
                    prob_letter_space=float(np.mean(self._letter_probability[-10:])),
                    prob_word_space=float(np.mean(self._word_probability[-10:])),
                    chunk_number=int(self._current_time // 20),  # Approximate chunk number
                )

                self._event_bus.publish(event)

        except Exception as e:
            self.logger.debug("Error publishing probability event: %s", str(e))

    def get_current_probabilities(self) -> dict[str, float]:
        """Get current probability values for external access.

        Returns:
            Dictionary with current probability values
        """
        if self._dit_probability is None:
            return {"dit": 0.0, "dah": 0.0, "letter": 0.0, "word": 0.0}

        # Debug logging for probability arrays
        dit_len = len(self._dit_probability) if self._dit_probability is not None else 0
        dah_len = len(self._dah_probability) if self._dah_probability is not None else 0
        letter_len = len(self._letter_probability) if self._letter_probability is not None else 0
        word_len = len(self._word_probability) if self._word_probability is not None else 0

        self.logger.debug(
            "Probability array lengths: dit=%d, dah=%d, letter=%d, word=%d", dit_len, dah_len, letter_len, word_len
        )

        # Show max values for debugging
        if self._dit_probability is not None and len(self._dit_probability) > 0:
            self.logger.debug(
                "Dit probability max=%.3f, recent values: %s",
                np.max(self._dit_probability),
                self._dit_probability[-5:].tolist()
                if len(self._dit_probability) >= 5
                else self._dit_probability.tolist(),
            )

        if self._dah_probability is not None and len(self._dah_probability) > 0:
            self.logger.debug(
                "Dah probability max=%.3f, recent values: %s",
                np.max(self._dah_probability),
                self._dah_probability[-5:].tolist()
                if len(self._dah_probability) >= 5
                else self._dah_probability.tolist(),
            )

        # For real-time display, use sliding maximum to show pattern strength
        # This gives a better representation of ongoing pattern detection
        def get_pattern_strength(prob_array, window_size=100):
            """Get rolling maximum probability for real-time display."""
            if prob_array is None or len(prob_array) < 5:
                return 0.0

            # Use a larger window to capture pattern strength over longer time
            recent_window = prob_array[-window_size:] if len(prob_array) >= window_size else prob_array
            max_val = float(np.max(recent_window))

            # If no recent patterns, fall back to a smaller decay from global max
            if max_val < 0.01:  # Very low threshold
                global_max = float(np.max(prob_array))
                # Decay factor based on how recent the detection was
                decay_factor = 0.3  # Show 30% of global max if no recent activity
                max_val = global_max * decay_factor

            self.logger.debug(
                "get_pattern_strength: array_len=%d, window_max=%.3f, result=%.3f",
                len(prob_array),
                float(np.max(recent_window)),
                max_val,
            )
            return max_val

        return {
            "dit": get_pattern_strength(self._dit_probability),
            "dah": get_pattern_strength(self._dah_probability),
            "letter": get_pattern_strength(self._letter_probability),
            "word": get_pattern_strength(self._word_probability),
        }

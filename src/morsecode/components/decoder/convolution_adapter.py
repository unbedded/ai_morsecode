"""Adapter for ConvMorseDecoder to implement MorseDecoder Protocol.

This adapter allows the new convolution-based decoder to work seamlessly
with the existing CLI and test infrastructure without breaking changes.

The adapter converts the simple tone detection interface to the signal
processing interface used by the convolution decoder.
"""

from typing import Any

import numpy as np

from morsecode.components.decoder.conv_morse_decoder import ConvMorseDecoder
from util.config import AwesomeConfigManager
from util.logging import ComponentLogger


class ConvolutionMorseDecoder:
    """Adapter to make ConvMorseDecoder compatible with MorseDecoder Protocol.

    This adapter bridges the gap between:
    - Old interface: process_detection(tone_detected: bool, duration_ms: float)
    - New interface: process_signal_chunk(signal_chunk: np.ndarray, chunk_duration_ms: float)

    The adapter maintains internal state to:
    1. Convert boolean tone detection to signal chunks
    2. Buffer signal data for efficient processing
    3. Extract decoded text from probability events
    4. Provide statistics in the expected format
    """

    def __init__(self, cfg_mgr: AwesomeConfigManager, overrides: dict[str, Any] | None = None):
        """Initialize the ConvolutionMorseDecoder."""
        # Initialize the underlying convolution decoder
        self._conv_decoder = ConvMorseDecoder(cfg_mgr, overrides)

        # Initialize logging
        self._logger = ComponentLogger(__name__, cfg_mgr)

        # FIXED: Use reasonable default instead of decoder details that leaked into graphics config
        # Convolution interval should be an application-level timing parameter, not graphics config
        self._max_buffer_duration_ms: float = 500.0  # 500ms convolution interval (reasonable default)

        # State for converting detection events to signal chunks
        self._current_tone_state: bool = False
        self._current_tone_duration: float = 0.0
        self._signal_buffer: list[float] = []
        self._buffer_duration_ms: float = 0.0

        # State for text extraction from probability events
        self._decoded_text: str = ""
        self._last_decoded_char: str = ""
        self._probability_threshold: float = 0.08  # Lower threshold to catch dit patterns (0.097)

        # Cache for last valid probability values (for real-time publishing)
        self._cached_probabilities: dict[str, float] = {"dit": 0.0, "dah": 0.0, "letter": 0.0, "word": 0.0}

        # Statistics tracking
        self._total_detections: int = 0
        self._dots_detected: int = 0
        self._dashes_detected: int = 0
        self._characters_decoded: int = 0
        self._words_decoded: int = 0

        # Set sample rate for convolution processing
        self._sample_rate_hz: float = 1000.0  # 1ms resolution
        self._conv_decoder.set_sample_rate(self._sample_rate_hz)

        self._logger.info(
            "ConvolutionMorseDecoder initialized with convolution_interval_ms=%.1f", self._max_buffer_duration_ms
        )

        # Inform graphics system of our probability sample rate at initialization
        self._notify_graphics_sample_rate()

    def process_detection(self, tone_detected: bool, duration_ms: float) -> None:
        """Process a tone detection event (MorseDecoder Protocol method).

        Converts boolean tone detection to signal chunks for convolution processing.

        Args:
            tone_detected: True if tone is currently detected, False if silence
            duration_ms: Duration this detection state has been active
        """
        try:
            self._total_detections += 1

            # Convert tone detection to signal value
            signal_value = 1.0 if tone_detected else 0.0

            # Add samples to buffer based on duration
            num_samples = int(duration_ms * self._sample_rate_hz / 1000.0)
            self._signal_buffer.extend([signal_value] * max(1, num_samples))
            self._buffer_duration_ms += duration_ms

            # Track tone state changes for element detection
            if tone_detected != self._current_tone_state:
                if self._current_tone_state and self._current_tone_duration > 0:
                    # End of tone - classify as dot or dash
                    if self._current_tone_duration < 100:  # Rough threshold
                        self._dots_detected += 1
                    else:
                        self._dashes_detected += 1

                self._current_tone_state = tone_detected
                self._current_tone_duration = 0.0

            if tone_detected:
                self._current_tone_duration += duration_ms

            # FIXED: Only publish probability events when convolution actually runs (every 500ms)
            # This prevents 10x width bug from duplicate cached values published every 50ms
            # Real probability publishing now happens in _process_signal_buffer()

            # DEBUG: Log buffer accumulation
            if self._total_detections % 100 == 1:  # Log every 100 detections
                self._logger.info(
                    "BUFFER STATUS: %.1f ms accumulated (threshold: %.1f ms), %d samples",
                    self._buffer_duration_ms,
                    self._max_buffer_duration_ms,
                    len(self._signal_buffer),
                )

            # Process buffered signal when we have enough data
            if self._buffer_duration_ms >= self._max_buffer_duration_ms:
                self._logger.info(
                    "TRIGGERING BUFFER PROCESSING: %.1f ms >= %.1f ms threshold",
                    self._buffer_duration_ms,
                    self._max_buffer_duration_ms,
                )
                self._process_signal_buffer()

        except Exception as e:
            self._logger.exception("Error processing detection: %s", str(e))

    def _process_signal_buffer(self) -> None:
        """Process accumulated signal buffer through convolution decoder."""
        try:
            if len(self._signal_buffer) == 0:
                return

            # Convert buffer to numpy array
            signal_chunk = np.array(self._signal_buffer)

            # DEBUG: Log signal chunk characteristics for real audio
            self._logger.info(
                "SIGNAL CHUNK: %d samples, min=%.3f, max=%.3f, mean=%.3f",
                len(signal_chunk),
                np.min(signal_chunk),
                np.max(signal_chunk),
                np.mean(signal_chunk),
            )

            # Process through convolution decoder
            self._conv_decoder.process_signal_chunk(signal_chunk, self._buffer_duration_ms)

            # DEBUG: Log every convolution processing for real audio debugging
            self._logger.info(
                "REAL AUDIO: Processed %d samples in %.1f ms", len(signal_chunk), self._buffer_duration_ms
            )

            # Extract probability information for text decoding
            probabilities = self._conv_decoder.get_current_probabilities()

            # DEBUG: Log all probability values from real audio processing
            self._logger.info(
                "REAL AUDIO PROBS: dit=%.4f, dah=%.4f, letter=%.4f, word=%.4f",
                probabilities.get("dit", 0.0),
                probabilities.get("dah", 0.0),
                probabilities.get("letter", 0.0),
                probabilities.get("word", 0.0),
            )

            # DEBUG: Always log when text extraction is called
            self._logger.info("CALLING TEXT EXTRACTION with probabilities: %s", probabilities)
            self._update_decoded_text_from_probabilities(probabilities)

            # Debug: Log convolution results
            self._logger.debug("Convolution decoder probabilities: %s", probabilities)

            # Update cached probabilities for real-time publishing
            self._cached_probabilities.update(probabilities)

            # CRITICAL FIX: Publish probability event only when convolution runs (every 500ms)
            # This gives graphics true 2 Hz sample rate instead of 20 Hz with duplicates
            self._publish_actual_probability_event(probabilities)

            # Clear buffer
            self._signal_buffer.clear()
            self._buffer_duration_ms = 0.0

        except Exception as e:
            self._logger.exception("Error processing signal buffer: %s", str(e))

    def _update_decoded_text_from_probabilities(self, probabilities: dict[str, float]) -> None:
        """Extract text from probability values (placeholder implementation).

        This is a simplified approach. In practice, you'd want more sophisticated
        text extraction from the impulse events and competitive selection.

        Args:
            probabilities: Current probability values from convolution decoder
        """
        try:
            # Better text extraction with independent thresholds for each pattern type
            dit_prob = probabilities.get("dit", 0.0)
            dah_prob = probabilities.get("dah", 0.0)
            letter_prob = probabilities.get("letter", 0.0)
            word_prob = probabilities.get("word", 0.0)

            self._logger.info(
                "TEXT EXTRACT: dit=%.3f, dah=%.3f, letter=%.3f, word=%.3f, threshold=%.3f",
                dit_prob,
                dah_prob,
                letter_prob,
                word_prob,
                self._probability_threshold,
            )

            # Independent threshold-based detection for element patterns
            element_detected = False

            # Check for dit (higher priority than letter for same threshold)
            if dit_prob > self._probability_threshold and self._last_decoded_char != ".":
                self._decoded_text += "."
                self._last_decoded_char = "."
                element_detected = True
                self._logger.info("ADDED DIT: text='%s'", self._decoded_text)

            # Check for dash (higher priority than letter for same threshold)
            elif dah_prob > self._probability_threshold and self._last_decoded_char != "-":
                self._decoded_text += "-"
                self._last_decoded_char = "-"
                element_detected = True
                self._logger.info("ADDED DAH: text='%s'", self._decoded_text)

            # Only check spacing if no element was detected
            if not element_detected:
                # Check for letter space
                if letter_prob > self._probability_threshold:
                    if self._decoded_text and not self._decoded_text.endswith(" "):
                        self._decoded_text += " "
                        self._characters_decoded += 1
                        self._last_decoded_char = " "
                        self._logger.debug("Added letter space: text='%s'", self._decoded_text)

                # Check for word space
                elif word_prob > self._probability_threshold:
                    if self._decoded_text and not self._decoded_text.endswith("  "):
                        self._decoded_text += "  "
                        self._words_decoded += 1
                        self._last_decoded_char = "  "
                        self._logger.debug("Added word space: text='%s'", self._decoded_text)

        except Exception as e:
            self._logger.debug("Error updating decoded text: %s", str(e))

    def _publish_realtime_probability_event(self, tone_detected: bool, duration_ms: float) -> None:
        """DEPRECATED: Legacy method that published cached probability values every 50ms.

        This method caused 10x width bug by flooding graphics with duplicate values.
        Real probability events are now published only when convolution runs (every 500ms)
        via _publish_actual_probability_event() method.

        Args:
            tone_detected: Whether tone was detected in this chunk
            duration_ms: Duration this detection state has been active
        """
        try:
            # Import here to avoid circular import
            from morsecode.events.bus import get_global_event_bus
            from morsecode.events.types import MorseProbabilityEvent

            # Inform graphics system about our probability update rate on first call
            if self._total_detections == 1:
                # Publish sample rate info: we update probabilities every 500ms
                # This helps graphics align with FFT data (which updates every 20ms)
                self._logger.info("PROBABILITY SAMPLE RATE: 500ms intervals (vs FFT 20ms intervals)")
                # Note: Graphics system could use this to interpolate or align display

            # Use cached probabilities for consistent real-time publishing
            # (convolution decoder only runs every 100ms, but we publish every 20ms)

            # Calculate actual time-based chunk number for graphics synchronization
            # Each probability update represents 500ms of data, FFT updates every 20ms
            # So we need to map our 500ms intervals to 20ms FFT intervals
            time_based_chunk = int(
                self._total_detections * 0.5
            )  # 500ms intervals -> time in seconds * 10 (for 100ms resolution)

            # Create probability event compatible with graphics display
            event = MorseProbabilityEvent(
                prob_dit=self._cached_probabilities.get("dit", 0.0),
                prob_dash=self._cached_probabilities.get("dah", 0.0),  # Note: 'dah' in conv, 'dash' in event
                prob_letter_space=self._cached_probabilities.get("letter", 0.0),
                prob_word_space=self._cached_probabilities.get("word", 0.0),
                chunk_number=time_based_chunk,  # Time-based for graphics synchronization
            )

            # Publish event to global event bus
            event_bus = get_global_event_bus()
            event_bus.publish(event)

            self._logger.debug(
                "Published probability event: dit=%.3f, dah=%.3f, letter=%.3f, word=%.3f",
                event.prob_dit,
                event.prob_dash,
                event.prob_letter_space,
                event.prob_word_space,
            )

        except Exception as e:
            self._logger.debug("Error publishing realtime probability event: %s", str(e))

    def _publish_actual_probability_event(self, probabilities: dict[str, float]) -> None:
        """Publish probability event with fresh convolution results (every 500ms).

        This method publishes events only when convolution decoder actually runs,
        providing graphics with genuine 2 Hz sample rate instead of 20 Hz duplicates.

        Args:
            probabilities: Fresh probability values from convolution processing
        """
        try:
            # Import here to avoid circular import
            from morsecode.events.bus import get_global_event_bus
            from morsecode.events.types import MorseProbabilityEvent

            # Use actual processing time for chunk number (better timing accuracy)
            # Each convolution run represents 500ms of processed audio
            # Note: convolution_run_count calculation available but not currently used

            # Create probability event with fresh values
            event = MorseProbabilityEvent(
                prob_dit=probabilities.get("dit", 0.0),
                prob_dash=probabilities.get("dah", 0.0),  # Note: 'dah' in conv, 'dash' in event
                prob_letter_space=probabilities.get("letter", 0.0),
                prob_word_space=probabilities.get("word", 0.0),
                chunk_number=self._total_detections,  # Use detection count as time reference
            )

            # Publish event to global event bus
            event_bus = get_global_event_bus()
            event_bus.publish(event)

            self._logger.info(
                "Published FRESH probability event (convolution run): dit=%.4f, dah=%.4f, letter=%.4f, word=%.4f",
                event.prob_dit,
                event.prob_dash,
                event.prob_letter_space,
                event.prob_word_space,
            )

        except Exception as e:
            self._logger.exception("Error publishing actual probability event: %s", str(e))

    def get_decoded_text(self) -> str:
        """Get the currently decoded text (MorseDecoder Protocol method).

        Returns:
            Decoded Morse code text as a string
        """
        return self._decoded_text

    def finalize(self) -> None:
        """Finalize the decoding process (MorseDecoder Protocol method).

        Processes any remaining buffered data and completes decoding.
        """
        try:
            # Process any remaining signal buffer
            if len(self._signal_buffer) > 0:
                self._process_signal_buffer()

            # Finalize any partial tone detection
            if self._current_tone_state and self._current_tone_duration > 0:
                if self._current_tone_duration < 100:
                    self._dots_detected += 1
                else:
                    self._dashes_detected += 1

            self._logger.info("ConvolutionMorseDecoder finalized")

        except Exception as e:
            self._logger.exception("Error finalizing decoder: %s", str(e))

    def finalize_decoding(self) -> None:
        """Legacy method name - calls finalize() for compatibility.

        This method exists for backward compatibility with the original
        MorseDecoder interface used by the main application.
        """
        self.finalize()

    def process_tone_detection(self, tone_detected: bool, chunk_duration_ms: float) -> None:
        """Legacy method name - calls process_detection() for compatibility.

        This method exists for backward compatibility with the original
        MorseDecoder interface used by the main application.

        Args:
            tone_detected: True if tone is currently detected, False if silence
            chunk_duration_ms: Duration this detection state has been active
        """
        self.process_detection(tone_detected, chunk_duration_ms)

    def reset(self) -> None:
        """Reset the decoder to initial state (MorseDecoder Protocol method)."""
        try:
            # Reset all internal state
            self._current_tone_state = False
            self._current_tone_duration = 0.0
            self._signal_buffer.clear()
            self._buffer_duration_ms = 0.0

            self._decoded_text = ""
            self._last_decoded_char = ""

            # Reset cached probabilities
            self._cached_probabilities = {"dit": 0.0, "dah": 0.0, "letter": 0.0, "word": 0.0}

            # Reset statistics
            self._total_detections = 0
            self._dots_detected = 0
            self._dashes_detected = 0
            self._characters_decoded = 0
            self._words_decoded = 0

            self._logger.info("ConvolutionMorseDecoder reset")

        except Exception as e:
            self._logger.exception("Error resetting decoder: %s", str(e))

    def get_statistics(self) -> dict[str, int | float]:
        """Get decoding statistics (MorseDecoder Protocol method).

        Returns:
            Dictionary containing statistics about the decoding process
        """
        try:
            # Get WPM estimate from underlying decoder
            estimated_wpm = getattr(self._conv_decoder, "wpm_estimate", 15)

            return {
                "characters_decoded": self._characters_decoded,
                "dots_detected": self._dots_detected,
                "dashes_detected": self._dashes_detected,
                "words_decoded": self._words_decoded,
                "estimated_wpm": float(estimated_wpm),
                "total_detections": self._total_detections,
                "buffer_size": len(self._signal_buffer),
            }

        except Exception as e:
            self._logger.exception("Error getting statistics: %s", str(e))
            return {
                "characters_decoded": 0,
                "dots_detected": 0,
                "dashes_detected": 0,
                "words_decoded": 0,
                "estimated_wpm": 15.0,
                "total_detections": 0,
                "buffer_size": 0,
            }

    def set_wpm_estimate(self, wpm: float) -> None:
        """Update the WPM estimate for timing calculations (MorseDecoder Protocol method).

        Args:
            wpm: Words per minute estimate. Should be positive.

        Raises:
            ValueError: If wpm is not positive
        """
        try:
            if wpm <= 0:
                raise ValueError(f"WPM must be positive: {wpm}")

            # Update underlying convolution decoder WPM
            if hasattr(self._conv_decoder, "wpm_estimate"):
                self._conv_decoder.wpm_estimate = int(wpm)
                self._conv_decoder._recalculate_timing_parameters()

            self._logger.info("WPM estimate updated to %.1f", wpm)

        except Exception as e:
            self._logger.exception("Error setting WPM estimate: %s", str(e))
            raise

    def get_current_probabilities(self) -> dict[str, float]:
        """Get current probability values from underlying convolution decoder.

        This method provides access to the probability values for debugging
        and visualization, but is not part of the standard MorseDecoder protocol.

        Returns:
            Dictionary with current probability values
        """
        return self._conv_decoder.get_current_probabilities()

    def get_convolution_decoder(self) -> ConvMorseDecoder:
        """Get access to underlying convolution decoder for advanced use.

        Returns:
            The underlying ConvMorseDecoder instance
        """
        return self._conv_decoder

    def _notify_graphics_sample_rate(self) -> None:
        """Inform graphics system about probability vs FFT sample rate difference."""
        try:
            # CORRECTED: Probability events are published every 20ms (same as FFT)!
            # The confusion was that convolution processing happens every 500ms,
            # but cached probability values are published every 20ms via _publish_realtime_probability_event()
            cli_chunk_duration_ms = 20.0  # CLI processes 20ms chunks
            probability_event_hz = 1000.0 / cli_chunk_duration_ms  # 50 Hz
            fft_event_hz = 1000.0 / cli_chunk_duration_ms  # 50 Hz
            convolution_update_hz = 1000.0 / self._max_buffer_duration_ms  # 2 Hz

            self._logger.info(
                "GRAPHICS TIMING INFO: Probability events every %.1f ms (%.1f Hz), "
                "FFT events every %.1f ms (%.1f Hz), convolution updates every %.1f ms (%.1f Hz)",
                cli_chunk_duration_ms,
                probability_event_hz,
                cli_chunk_duration_ms,
                fft_event_hz,
                self._max_buffer_duration_ms,
                convolution_update_hz,
            )

            # Both probability and FFT events have the same sample rate
            self._probability_sample_rate_hz = probability_event_hz

        except Exception as e:
            self._logger.debug("Error notifying graphics sample rate: %s", str(e))

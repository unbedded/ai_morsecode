"""Morse code decoding module with pattern recognition and timing analysis.

This module provides Morse code pattern detection, timing analysis, and character
decoding capabilities. It processes signal processor output to identify dots, dashes,
and character boundaries for accurate Morse code translation.

Example usage:
    ```python
    from morsecode.components.decoder.morse_decoder import MorseDecoder
    from util.config.registry import AwesomeConfigManager

    cfg_mgr = AwesomeConfigManager("morse.yaml")
    decoder = MorseDecoder(cfg_mgr)

    # Process tone detection events
    decoder.process_tone_detection(True, 80.0)   # Dot
    decoder.process_tone_detection(False, 80.0)  # Silence
    decoder.process_tone_detection(True, 240.0)  # Dash

    decoded_text = decoder.get_decoded_text()
    ```
"""

from typing import Any

import numpy as np

from morsecode.components.decoder.keys import CfgKey, CfgSection
from morsecode.components.decoder.schema import ConfigSchema
from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import MorsePatternEvent, MorseProbabilityEvent, TextDecodedEvent
from util.config import ConfigurableBase

# Constants for morse code timing
DEFAULT_WPM = 15
DEFAULT_DOT_DURATION_MS = 80  # For 15 WPM
DEFAULT_DASH_RATIO = 3.0  # Dash is 3x dot duration
DEFAULT_ELEMENT_SPACING_RATIO = 1.0  # Space between dots/dashes within character
DEFAULT_CHARACTER_SPACING_RATIO = 3.0  # Space between characters
DEFAULT_WORD_SPACING_RATIO = 7.0  # Space between words
DEFAULT_DETECTION_TOLERANCE = 0.3  # 30% tolerance for timing variations

# Morse code lookup table
MORSE_CODE_TABLE = {
    ".-": "A",
    "-...": "B",
    "-.-.": "C",
    "-..": "D",
    ".": "E",
    "..-.": "F",
    "--.": "G",
    "....": "H",
    "..": "I",
    ".---": "J",
    "-.-": "K",
    ".-..": "L",
    "--": "M",
    "-.": "N",
    "---": "O",
    ".--.": "P",
    "--.-": "Q",
    ".-.": "R",
    "...": "S",
    "-": "T",
    "..-": "U",
    "...-": "V",
    ".--": "W",
    "-..-": "X",
    "-.--": "Y",
    "--..": "Z",
    ".----": "1",
    "..---": "2",
    "...--": "3",
    "....-": "4",
    ".....": "5",
    "-....": "6",
    "--...": "7",
    "---..": "8",
    "----.": "9",
    "-----": "0",
    "--..--": ",",
    ".-.-.-": ".",
    "..--..": "?",
    "-..-.": "/",
    "-....-": "-",
    "-.--.": "(",
    "-.--.-": ")",
    ".--.-.": "@",
    "---...": ":",
    "-.-.-.": ";",
    "-...-": "=",
    ".-.-.": "+",
    ".-..--.": '"',
    ".-----.": "'",
    "..--.-": "_",
    "-.-.--": "!",
}

# Reverse lookup for debugging
CHARACTER_TO_MORSE = {v: k for k, v in MORSE_CODE_TABLE.items()}


class MorseDecoder(ConfigurableBase):
    """A class to decode Morse code patterns from tone detection events.

    This class processes sequences of tone on/off events with timing information
    to identify Morse code patterns and translate them to text characters.

    Uses ConfigurableBase inheritance pattern for type-safe configuration access
    and runtime reconfiguration support.

    Attributes:
        wpm_estimate: Estimated words per minute for timing calculations.
        dot_duration_ms: Duration of a dot in milliseconds.
        dash_duration_ms: Duration of a dash in milliseconds.
        element_spacing_ms: Expected spacing between elements within a character.
        character_spacing_ms: Expected spacing between characters.
        word_spacing_ms: Expected spacing between words.
        detection_tolerance: Tolerance factor for timing variations (0.0-1.0).
    """

    # ConfigurableBase requirements
    CONFIG_SCHEMA = ConfigSchema
    CONFIG_SECTION = CfgSection.DECODER.value
    CONFIG_KEYS = CfgKey

    def __init__(self, cfg_mgr, overrides=None) -> None:
        """Initialize the MorseDecoder with ConfigurableBase pattern.

        Args:
            cfg_mgr: Config manager for enum-based configuration.
            overrides: Optional configuration overrides for testing/tuning.
        """
        # Call ConfigurableBase constructor (handles all config/logging boilerplate)
        super().__init__(cfg_mgr, overrides)

        # Initialize decoding state after configuration is loaded
        self._current_pattern: list[str] = []
        self._decoded_characters: list[str] = []
        self._tone_start_time: float | None = None
        self._last_tone_end_time: float | None = None
        self._current_time: float = 0.0
        self._total_dots_decoded: int = 0
        self._total_dashes_decoded: int = 0
        self._total_characters_decoded: int = 0
        self._chunk_counter: int = 0

        # Get global event bus for publishing events
        self._event_bus = get_global_event_bus()

        try:
            self._validate_configuration()
        except Exception as e:
            self.logger.exception("Error validating MorseDecoder configuration: %s", str(e))
            raise RuntimeError(f"Failed to initialize morse decoder: {e}") from e

        self.logger.info("MorseDecoder initialized with %d WPM, dot=%.1fms", self.wpm_estimate, self.dot_duration_ms)

    def _load_config_values(self) -> None:
        """Load configuration values using type-safe enum access.

        This method is called by ConfigurableBase during initialization and reconfiguration.
        Only method we need to implement - all boilerplate handled by base class.
        """
        # STEP 1: Load core configuration with type safety
        self.wpm_estimate: int = self._cfg_section.get_int(CfgKey.WPM)
        self.dot_duration_ms: float = self._cfg_section.get_double(CfgKey.DOT_DURATION_MS)
        self.detection_tolerance: float = self._cfg_section.get_double(CfgKey.TIMING_TOLERANCE_NORM)

        # Calculate dot_duration_ms from WPM if not provided (standard PARIS formula)
        if self.dot_duration_ms is None or self.dot_duration_ms <= 0:
            self.dot_duration_ms = 1200.0 / self.wpm_estimate
            self.logger.debug(
                "Calculated dot_duration_ms from WPM: %.1fms from %d WPM", self.dot_duration_ms, self.wpm_estimate
            )

        # STEP 2: Global config for cross-cutting concerns (recommended pattern)
        try:
            global_cfg = self._cfg_mgr.get_section("global")
            self.debug = global_cfg.get_bool("debug")
            self.timeout_ms = global_cfg.get_int("timeout_ms")
        except (KeyError, ValueError):
            # Global config section may not exist or have values
            self.debug = False
            self.timeout_ms = 30000

        # STEP 3: Calculate derived timing parameters using defaults
        dash_ratio = DEFAULT_DASH_RATIO
        character_spacing_ratio = DEFAULT_CHARACTER_SPACING_RATIO
        word_spacing_ratio = DEFAULT_WORD_SPACING_RATIO

        self.dash_duration_ms: float = self.dot_duration_ms * dash_ratio
        self.element_spacing_ms: float = self.dot_duration_ms * DEFAULT_ELEMENT_SPACING_RATIO
        self.character_spacing_ms: float = self.dot_duration_ms * character_spacing_ratio
        self.word_spacing_ms: float = self.dot_duration_ms * word_spacing_ratio

        # STEP 4: Log completion with lazy % formatting (CRITICAL!)
        self.logger.info(
            "MorseDecoder configured: %d WPM, dot=%.1fms, tolerance=%.2f",
            self.wpm_estimate,
            self.dot_duration_ms,
            self.detection_tolerance,
        )
        self.logger.info(
            "Timing parameters: dash=%.1fms, char_spacing=%.1fms, word_spacing=%.1fms",
            self.dash_duration_ms,
            self.character_spacing_ms,
            self.word_spacing_ms,
        )

        # STEP 5: Debug logging controlled by config (not code!)
        self.logger.debug("Internal state: ready for decoding")

    def _on_reconfiguration(self) -> None:
        """Handle reconfiguration side effects.

        Called by ConfigurableBase after configuration values are reloaded.
        Recalculate derived timing parameters that depend on configuration.
        """
        # Recalculate derived timing parameters
        dash_ratio = DEFAULT_DASH_RATIO
        character_spacing_ratio = DEFAULT_CHARACTER_SPACING_RATIO
        word_spacing_ratio = DEFAULT_WORD_SPACING_RATIO

        self.dash_duration_ms = self.dot_duration_ms * dash_ratio
        self.element_spacing_ms = self.dot_duration_ms * DEFAULT_ELEMENT_SPACING_RATIO
        self.character_spacing_ms = self.dot_duration_ms * character_spacing_ratio
        self.word_spacing_ms = self.dot_duration_ms * word_spacing_ratio

        # Revalidate configuration
        try:
            self._validate_configuration()
            self.logger.info(
                "MorseDecoder reconfigured with %d WPM, dot=%.1fms", self.wpm_estimate, self.dot_duration_ms
            )
        except Exception as e:
            self.logger.exception("Error during MorseDecoder reconfiguration: %s", str(e))
            raise RuntimeError(f"Failed to reconfigure morse decoder: {e}") from e

    def _validate_configuration(self) -> None:
        """Validate decoder configuration parameters."""
        if self.wpm_estimate <= 0:
            raise ValueError(f"WPM estimate must be positive: {self.wpm_estimate}")

        if self.dot_duration_ms <= 0:
            raise ValueError(f"Dot duration must be positive: {self.dot_duration_ms}")

        if not (0.0 <= self.detection_tolerance <= 1.0):
            raise ValueError(f"Detection tolerance must be 0-1: {self.detection_tolerance}")

        self.logger.debug("Configuration validation passed")

    def get_params(self) -> dict[str, Any]:
        """Return the current configuration parameters.

        Returns:
            Dictionary containing current configuration parameters.
        """
        return {
            "wpm_estimate": self.wpm_estimate,
            "dot_duration_ms": self.dot_duration_ms,
            "dash_duration_ms": self.dash_duration_ms,
            "element_spacing_ms": self.element_spacing_ms,
            "character_spacing_ms": self.character_spacing_ms,
            "word_spacing_ms": self.word_spacing_ms,
            "detection_tolerance": self.detection_tolerance,
        }

    def process_tone_detection(self, tone_detected: bool, chunk_duration_ms: float) -> None:
        """Process a tone detection event with timing information.

        Args:
            tone_detected: Whether tone was detected in this chunk.
            chunk_duration_ms: Duration of the audio chunk in milliseconds.
        """
        try:
            # Note: Removed debug logging for cleaner output

            if tone_detected:
                # Check for accumulated silence before this tone
                if self._tone_start_time is None and self._last_tone_end_time is not None:
                    silence_duration = self._current_time - self._last_tone_end_time
                    if silence_duration > 0:
                        self.logger.debug("Processing silence gap: %.1fms", silence_duration)
                        self._process_silence_gap(silence_duration)

                if self._tone_start_time is None:
                    # Start of new tone
                    self._tone_start_time = self._current_time
                    self.logger.debug("Tone started at %.1fms", self._current_time)
            else:
                if self._tone_start_time is not None:
                    # End of tone - process the element
                    tone_duration = self._current_time - self._tone_start_time
                    self.logger.debug("Processing tone element: %.1fms", tone_duration)
                    self._process_tone_element(tone_duration)

                    self._last_tone_end_time = self._current_time
                    self._tone_start_time = None

                    self.logger.debug("Tone ended at %.1fms, duration: %.1fms", self._current_time, tone_duration)

            # Update current time and chunk counter
            self._current_time += chunk_duration_ms
            self._chunk_counter += 1

            # Calculate and publish probability events for real-time visualization
            self._publish_probability_event(tone_detected, chunk_duration_ms)

        except Exception as e:
            self.logger.exception("Error processing tone detection: %s", str(e))

    def _process_tone_element(self, duration_ms: float) -> None:
        """Process a single tone element (dot or dash) based on duration.

        Args:
            duration_ms: Duration of the tone element in milliseconds.
        """
        try:
            # Determine if this is a dot or dash based on duration
            dot_threshold = self.dot_duration_ms * (1 + self.detection_tolerance)
            dash_threshold = self.dash_duration_ms * (1 - self.detection_tolerance)

            element_type = ""
            confidence = 0.0

            if duration_ms <= dot_threshold:
                # This is a dot
                element_type = "."
                self._current_pattern.append(".")
                self._total_dots_decoded += 1
                confidence = 1.0 - abs(duration_ms - self.dot_duration_ms) / self.dot_duration_ms
                self.logger.debug("Decoded DOT (%.1fms)", duration_ms)
            elif duration_ms >= dash_threshold:
                # This is a dash
                element_type = "-"
                self._current_pattern.append("-")
                self._total_dashes_decoded += 1
                confidence = 1.0 - abs(duration_ms - self.dash_duration_ms) / self.dash_duration_ms
                self.logger.debug("Decoded DASH (%.1fms)", duration_ms)
            else:
                # Ambiguous duration - use closest match
                dot_diff = abs(duration_ms - self.dot_duration_ms)
                dash_diff = abs(duration_ms - self.dash_duration_ms)

                if dot_diff < dash_diff:
                    element_type = "."
                    self._current_pattern.append(".")
                    self._total_dots_decoded += 1
                    confidence = 0.5  # Lower confidence for ambiguous
                    self.logger.debug("Decoded ambiguous as DOT (%.1fms)", duration_ms)
                else:
                    element_type = "-"
                    self._current_pattern.append("-")
                    self._total_dashes_decoded += 1
                    confidence = 0.5  # Lower confidence for ambiguous
                    self.logger.debug("Decoded ambiguous as DASH (%.1fms)", duration_ms)

            # Publish morse pattern event
            pattern_type = "dot" if element_type == "." else "dash"
            pattern_event = MorsePatternEvent(
                pattern_type=pattern_type,
                duration_ms=duration_ms,
                wpm_estimate=float(self.wpm_estimate),
                confidence=min(1.0, max(0.0, confidence)),
            )
            self._event_bus.publish(pattern_event)

        except Exception as e:
            self.logger.exception("Error processing tone element: %s", str(e))

    def _process_silence_gap(self, silence_duration_ms: float) -> None:
        """Process silence gap to determine character/word boundaries.

        Args:
            silence_duration_ms: Duration of silence in milliseconds.
        """
        try:
            character_threshold = self.character_spacing_ms * (1 - self.detection_tolerance)
            word_threshold = self.word_spacing_ms * (1 - self.detection_tolerance)

            if silence_duration_ms >= word_threshold:
                # Word boundary
                self._finalize_current_character()
                if self._decoded_characters and self._decoded_characters[-1] != " ":
                    self._decoded_characters.append(" ")
                    self.logger.debug("Word boundary detected (%.1fms silence)", silence_duration_ms)

            elif silence_duration_ms >= character_threshold:
                # Character boundary
                self._finalize_current_character()
                self.logger.debug("Character boundary detected (%.1fms silence)", silence_duration_ms)

            # Keep last tone end time for continued silence tracking

        except Exception as e:
            self.logger.exception("Error processing silence gap: %s", str(e))

    def _finalize_current_character(self) -> None:
        """Finalize the current character pattern and decode it."""
        try:
            if not self._current_pattern:
                return

            # Convert pattern to string
            pattern_str = "".join(self._current_pattern)
            character = ""
            confidence = 1.0

            # Look up character in morse code table
            if pattern_str in MORSE_CODE_TABLE:
                character = MORSE_CODE_TABLE[pattern_str]
                self._decoded_characters.append(character)
                self._total_characters_decoded += 1
                self.logger.debug("Decoded pattern '%s' as character '%s'", pattern_str, character)
            else:
                # Unknown pattern - add placeholder
                character = "?"
                confidence = 0.0
                self._decoded_characters.append("?")
                self.logger.warning("Unknown morse pattern: '%s'", pattern_str)

            # Publish text decoded event
            text_event = TextDecodedEvent(
                text=character,
                pattern_sequence=pattern_str,
                wpm_estimate=float(self.wpm_estimate),
                confidence=confidence,
                is_complete_word=False,  # Individual characters, not complete words
            )
            self._event_bus.publish(text_event)

            # Reset current pattern
            self._current_pattern.clear()

        except Exception as e:
            self.logger.exception("Error finalizing character: %s", str(e))

    def finalize_decoding(self) -> None:
        """Finalize any remaining decoding and complete the process."""
        try:
            # Process any remaining tone
            if self._tone_start_time is not None:
                tone_duration = self._current_time - self._tone_start_time
                self._process_tone_element(tone_duration)
                self._tone_start_time = None

            # Finalize any remaining character
            self._finalize_current_character()

            self.logger.info(
                "Decoding finalized: %d characters, %d dots, %d dashes",
                self._total_characters_decoded,
                self._total_dots_decoded,
                self._total_dashes_decoded,
            )

        except Exception as e:
            self.logger.exception("Error finalizing decoding: %s", str(e))

    def get_decoded_text(self) -> str:
        """Get the currently decoded text.

        Returns:
            Decoded text string.
        """
        return "".join(self._decoded_characters)

    def get_statistics(self) -> dict[str, int]:
        """Get decoding statistics.

        Returns:
            Dictionary containing decoding statistics.
        """
        return {
            "total_characters": self._total_characters_decoded,
            "total_dots": self._total_dots_decoded,
            "total_dashes": self._total_dashes_decoded,
            "current_pattern_length": len(self._current_pattern),
        }

    def reset_decoder(self) -> None:
        """Reset the decoder state for new input."""
        try:
            self._current_pattern.clear()
            self._decoded_characters.clear()
            self._tone_start_time = None
            self._last_tone_end_time = None
            self._current_time = 0.0
            self._total_dots_decoded = 0
            self._total_dashes_decoded = 0
            self._total_characters_decoded = 0

            self.logger.info("Decoder state reset")

        except Exception as e:
            self.logger.exception("Error resetting decoder: %s", str(e))

    def estimate_wpm_from_timing(self, sample_dots: list[float], sample_dashes: list[float]) -> float:
        """Estimate WPM from sample dot and dash durations.

        Args:
            sample_dots: List of measured dot durations in milliseconds.
            sample_dashes: List of measured dash durations in milliseconds.

        Returns:
            Estimated words per minute.
        """
        try:
            if not sample_dots:
                self.logger.warning("No dot samples provided for WPM estimation")
                return float(self.wpm_estimate)

            # Use median to be robust against outliers
            median_dot_duration = float(np.median(sample_dots))

            # Standard formula: WPM = 1200 / dot_duration_ms
            # This comes from the standard word "PARIS " which is 50 dot units
            # At 1 WPM: 60 seconds / word = 60000ms / 50 units = 1200ms per dot unit
            estimated_wpm = 1200.0 / median_dot_duration

            self.logger.info("Estimated WPM: %.1f (from %.1fms dot duration)", estimated_wpm, median_dot_duration)

            return estimated_wpm

        except Exception as e:
            self.logger.exception("Error estimating WPM: %s", str(e))
            return float(self.wpm_estimate)

    def _publish_probability_event(self, tone_detected: bool, chunk_duration_ms: float) -> None:
        """Calculate and publish Morse probability events for real-time visualization.

        Args:
            tone_detected: Whether tone was detected in this chunk
            chunk_duration_ms: Duration of the audio chunk in milliseconds
        """
        try:
            # Calculate probabilities based on current decoder state
            prob_dit = self._calculate_dit_probability(tone_detected)
            prob_dash = self._calculate_dash_probability(tone_detected)
            prob_letter_space = self._calculate_letter_space_probability()
            prob_word_space = self._calculate_word_space_probability()

            # Create and publish the event
            event = MorseProbabilityEvent(
                prob_dit=prob_dit,
                prob_dash=prob_dash,
                prob_letter_space=prob_letter_space,
                prob_word_space=prob_word_space,
                chunk_number=self._chunk_counter,
            )

            self._event_bus.publish(event)

        except Exception as e:
            self.logger.debug("Error publishing probability event: %s", str(e))

    def _calculate_dit_probability(self, tone_detected: bool) -> float:
        """Calculate probability that current state represents a dit (dot)."""
        if not tone_detected:
            return 0.0

        if self._tone_start_time is None:
            return 0.1  # Low probability at start of tone

        # Calculate current tone duration
        current_duration = self._current_time - self._tone_start_time
        expected_dot = self.dot_duration_ms
        tolerance = self.detection_tolerance

        # Gaussian-like probability centered on expected dot duration
        deviation = abs(current_duration - expected_dot) / expected_dot
        if deviation <= tolerance:
            return max(0.1, 1.0 - (deviation / tolerance) * 0.8)
        else:
            return 0.1

    def _calculate_dash_probability(self, tone_detected: bool) -> float:
        """Calculate probability that current state represents a dash."""
        if not tone_detected:
            return 0.0

        if self._tone_start_time is None:
            return 0.1  # Low probability at start of tone

        # Calculate current tone duration
        current_duration = self._current_time - self._tone_start_time
        expected_dash = self.dash_duration_ms
        tolerance = self.detection_tolerance

        # Gaussian-like probability centered on expected dash duration
        deviation = abs(current_duration - expected_dash) / expected_dash
        if deviation <= tolerance:
            return max(0.1, 1.0 - (deviation / tolerance) * 0.8)
        else:
            return 0.1

    def _calculate_letter_space_probability(self) -> float:
        """Calculate probability that we're in a letter space (between characters)."""
        if self._tone_start_time is not None:
            return 0.0  # Can't be in letter space during tone

        if self._last_tone_end_time is None:
            return 0.0  # No previous tone

        # Calculate current silence duration
        silence_duration = self._current_time - self._last_tone_end_time
        expected_letter_space = self.character_spacing_ms
        tolerance = self.detection_tolerance

        # Probability increases as we approach expected letter space duration
        if silence_duration < expected_letter_space * (1 - tolerance):
            return float(min(0.9, silence_duration / (expected_letter_space * (1 - tolerance))))
        elif silence_duration > expected_letter_space * (1 + tolerance):
            return float(max(0.1, 1.0 - (silence_duration - expected_letter_space) / expected_letter_space * 0.5))
        else:
            return 0.9

    def _calculate_word_space_probability(self) -> float:
        """Calculate probability that we're in a word space (between words)."""
        if self._tone_start_time is not None:
            return 0.0  # Can't be in word space during tone

        if self._last_tone_end_time is None:
            return 0.0  # No previous tone

        # Calculate current silence duration
        silence_duration = self._current_time - self._last_tone_end_time
        expected_word_space = self.word_spacing_ms
        tolerance = self.detection_tolerance

        # Probability increases as we approach expected word space duration
        if silence_duration < expected_word_space * (1 - tolerance):
            return float(min(0.9, silence_duration / (expected_word_space * (1 - tolerance))))
        else:
            return 0.9

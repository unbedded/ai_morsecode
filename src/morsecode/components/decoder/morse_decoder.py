"""Morse code decoding module with pattern recognition and timing analysis.

This module provides Morse code pattern detection, timing analysis, and character
decoding capabilities. It processes signal processor output to identify dots, dashes,
and character boundaries for accurate Morse code translation.

Example usage:
    ```python
    from morsecode.morse_decoder import MorseDecoder
    from morsecode.signal_processor import SignalProcessor

    cfg = {
        'wpm_estimate': 15,
        'dot_duration_ms': 80,
        'character_spacing_ratio': 3.0
    }

    decoder = MorseDecoder(cfg_dict=cfg)
    processor = SignalProcessor()

    # Process audio chunks
    for audio_chunk in audio_stream:
        tone_detected = processor.detect_tone(audio_chunk)
        decoder.process_tone_detection(tone_detected, chunk_duration_ms)

    decoded_text = decoder.get_decoded_text()
    ```
"""

import logging
from typing import Any

import numpy as np

from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import MorsePatternEvent, TextDecodedEvent

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


class MorseDecoder:
    """A class to decode Morse code patterns from tone detection events.

    This class processes sequences of tone on/off events with timing information
    to identify Morse code patterns and translate them to text characters.

    Attributes:
        wpm_estimate: Estimated words per minute for timing calculations.
        dot_duration_ms: Duration of a dot in milliseconds.
        dash_duration_ms: Duration of a dash in milliseconds.
        element_spacing_ms: Expected spacing between elements within a character.
        character_spacing_ms: Expected spacing between characters.
        word_spacing_ms: Expected spacing between words.
        detection_tolerance: Tolerance factor for timing variations (0.0-1.0).
    """

    def __init__(self, cfg_dict: dict[str, Any] | None = None) -> None:
        """Initialize the MorseDecoder with configuration parameters.

        Args:
            cfg_dict: Configuration dictionary containing timing parameters.
                     Expected keys: 'wpm_estimate', 'dot_duration_ms',
                     'dash_ratio', 'character_spacing_ratio', 'word_spacing_ratio',
                     'detection_tolerance'
        """
        # Initialize logging as the first step in constructor
        self.logger = logging.getLogger(__name__)

        cfg_dict = cfg_dict or {}

        # Initialize timing parameters
        self.wpm_estimate: int = self._init_param(cfg_dict, "wpm_estimate", DEFAULT_WPM)
        self.dot_duration_ms: float = self._init_param(
            cfg_dict, "dot_duration_ms", DEFAULT_DOT_DURATION_MS
        )

        # Calculate derived timing parameters
        dash_ratio = self._init_param(cfg_dict, "dash_ratio", DEFAULT_DASH_RATIO)
        character_spacing_ratio = self._init_param(
            cfg_dict, "character_spacing_ratio", DEFAULT_CHARACTER_SPACING_RATIO
        )
        word_spacing_ratio = self._init_param(
            cfg_dict, "word_spacing_ratio", DEFAULT_WORD_SPACING_RATIO
        )

        self.dash_duration_ms: float = self.dot_duration_ms * dash_ratio
        self.element_spacing_ms: float = self.dot_duration_ms * DEFAULT_ELEMENT_SPACING_RATIO
        self.character_spacing_ms: float = self.dot_duration_ms * character_spacing_ratio
        self.word_spacing_ms: float = self.dot_duration_ms * word_spacing_ratio

        self.detection_tolerance: float = self._init_param(
            cfg_dict, "detection_tolerance", DEFAULT_DETECTION_TOLERANCE
        )

        # Initialize decoding state
        self._current_pattern: list[str] = []
        self._decoded_characters: list[str] = []
        self._tone_start_time: float | None = None
        self._last_tone_end_time: float | None = None
        self._current_time: float = 0.0
        self._total_dots_decoded: int = 0
        self._total_dashes_decoded: int = 0
        self._total_characters_decoded: int = 0

        # Get global event bus for publishing events
        self._event_bus = get_global_event_bus()

        try:
            self._validate_configuration()
        except Exception as e:
            self.logger.exception("Error validating MorseDecoder configuration: %s", str(e))
            raise RuntimeError(f"Failed to initialize morse decoder: {e}") from e

        self.logger.info(
            "MorseDecoder initialized: %d WPM, dot=%.1fms, dash=%.1fms",
            self.wpm_estimate,
            self.dot_duration_ms,
            self.dash_duration_ms,
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
        if key not in cfg_dict or value is None:
            self.logger.info(
                "Parameter '%s' not found in configuration or is None. Using default: %s",
                key,
                default,
            )
            return default
        return value

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
            if tone_detected:
                # Check for accumulated silence before this tone
                if self._tone_start_time is None and self._last_tone_end_time is not None:
                    silence_duration = self._current_time - self._last_tone_end_time
                    if silence_duration > 0:
                        self._process_silence_gap(silence_duration)

                if self._tone_start_time is None:
                    # Start of new tone
                    self._tone_start_time = self._current_time
                    self.logger.debug("Tone started at %.1fms", self._current_time)
            else:
                if self._tone_start_time is not None:
                    # End of tone - process the element
                    tone_duration = self._current_time - self._tone_start_time
                    self._process_tone_element(tone_duration)

                    self._last_tone_end_time = self._current_time
                    self._tone_start_time = None

                    self.logger.debug(
                        "Tone ended at %.1fms, duration: %.1fms", self._current_time, tone_duration
                    )

            # Update current time
            self._current_time += chunk_duration_ms

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
                    self.logger.debug(
                        "Word boundary detected (%.1fms silence)", silence_duration_ms
                    )

            elif silence_duration_ms >= character_threshold:
                # Character boundary
                self._finalize_current_character()
                self.logger.debug(
                    "Character boundary detected (%.1fms silence)", silence_duration_ms
                )

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

    def estimate_wpm_from_timing(
        self, sample_dots: list[float], sample_dashes: list[float]
    ) -> float:
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

            self.logger.info(
                "Estimated WPM: %.1f (from %.1fms dot duration)", estimated_wpm, median_dot_duration
            )

            return estimated_wpm

        except Exception as e:
            self.logger.exception("Error estimating WPM: %s", str(e))
            return float(self.wpm_estimate)

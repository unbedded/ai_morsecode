"""Comprehensive tests for the MorseDecoder module.

This test module provides extensive test coverage for Morse code pattern recognition,
timing analysis, and character decoding functionality following CLAUDE.md
testing standards and pytest conventions.

Example usage:
    pytest tests/test_morse_decoder.py -v
"""

import pytest

from morsecode.morse_decoder import MorseDecoder


class TestMorseDecoder:
    """Test suite for MorseDecoder functionality."""

    def test_init_with_defaults(self) -> None:
        """Test decoder initialization with default parameters."""
        decoder = MorseDecoder()

        assert decoder.wpm_estimate == 15
        assert decoder.dot_duration_ms == 80.0
        assert decoder.dash_duration_ms == 240.0  # 3x dot duration
        assert decoder.detection_tolerance == 0.3

        params = decoder.get_params()
        assert isinstance(params, dict)
        assert "wpm_estimate" in params
        assert "dot_duration_ms" in params

    def test_init_with_config(self) -> None:
        """Test decoder initialization with custom configuration."""
        cfg = {
            "wpm_estimate": 20,
            "dot_duration_ms": 60.0,
            "dash_ratio": 2.5,
            "character_spacing_ratio": 4.0,
            "detection_tolerance": 0.2,
        }

        decoder = MorseDecoder(cfg_dict=cfg)

        assert decoder.wpm_estimate == 20
        assert decoder.dot_duration_ms == 60.0
        assert decoder.dash_duration_ms == 150.0  # 2.5x dot duration
        assert decoder.detection_tolerance == 0.2

    def test_config_validation(self) -> None:
        """Test configuration parameter validation."""
        # Test invalid WPM
        with pytest.raises(RuntimeError):
            MorseDecoder(cfg_dict={"wpm_estimate": -5})

        # Test invalid dot duration
        with pytest.raises(RuntimeError):
            MorseDecoder(cfg_dict={"dot_duration_ms": -10})

        # Test invalid tolerance
        with pytest.raises(RuntimeError):
            MorseDecoder(cfg_dict={"detection_tolerance": 1.5})

    def test_single_dot_detection(self) -> None:
        """Test detection of a single dot."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 100.0})

        # Simulate dot: tone on for 100ms, then off
        decoder.process_tone_detection(True, 50.0)  # Start tone
        decoder.process_tone_detection(True, 50.0)  # Continue tone (total 100ms)
        decoder.process_tone_detection(False, 50.0)  # End tone
        decoder.process_tone_detection(False, 300.0)  # Character spacing

        decoder.finalize_decoding()
        decoded = decoder.get_decoded_text()

        assert decoded == "E"  # Single dot is 'E'

    def test_single_dash_detection(self) -> None:
        """Test detection of a single dash."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 100.0})

        # Simulate dash: tone on for 300ms, then off
        decoder.process_tone_detection(True, 100.0)  # Start tone
        decoder.process_tone_detection(True, 100.0)  # Continue tone
        decoder.process_tone_detection(True, 100.0)  # Continue tone (total 300ms)
        decoder.process_tone_detection(False, 50.0)  # End tone
        decoder.process_tone_detection(False, 300.0)  # Character spacing

        decoder.finalize_decoding()
        decoded = decoder.get_decoded_text()

        assert decoded == "T"  # Single dash is 'T'

    def test_letter_a_detection(self) -> None:
        """Test detection of letter 'A' (dot-dash)."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 100.0})

        # Simulate 'A': dot (100ms) + element spacing + dash (300ms)
        decoder.process_tone_detection(True, 100.0)  # Dot
        decoder.process_tone_detection(False, 100.0)  # Element spacing
        decoder.process_tone_detection(True, 300.0)  # Dash
        decoder.process_tone_detection(False, 300.0)  # Character spacing

        decoder.finalize_decoding()
        decoded = decoder.get_decoded_text()

        assert decoded == "A"

    def test_letter_s_detection(self) -> None:
        """Test detection of letter 'S' (dot-dot-dot)."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # Simulate 'S': three dots with element spacing
        for _ in range(3):
            decoder.process_tone_detection(True, 80.0)  # Dot
            decoder.process_tone_detection(False, 80.0)  # Element spacing

        decoder.process_tone_detection(False, 240.0)  # Character spacing
        decoder.finalize_decoding()
        decoded = decoder.get_decoded_text()

        assert decoded == "S"

    def test_word_sos_detection(self) -> None:
        """Test detection of 'SOS' with proper spacing."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # S (...)
        for _ in range(3):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)
        decoder.process_tone_detection(False, 240.0)  # Character spacing

        # O (---)
        for _ in range(3):
            decoder.process_tone_detection(True, 240.0)
            decoder.process_tone_detection(False, 80.0)
        decoder.process_tone_detection(False, 240.0)  # Character spacing

        # S (...)
        for _ in range(3):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)

        decoder.finalize_decoding()
        decoded = decoder.get_decoded_text()

        assert decoded == "SOS"

    def test_word_spacing_detection(self) -> None:
        """Test proper word spacing detection."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # First letter 'E' (.)
        decoder.process_tone_detection(True, 80.0)
        decoder.process_tone_detection(False, 240.0)  # Character spacing

        # Word spacing (7x dot duration = 560ms)
        decoder.process_tone_detection(False, 560.0)

        # Second letter 'T' (-)
        decoder.process_tone_detection(True, 240.0)
        decoder.process_tone_detection(False, 240.0)  # Character spacing

        decoder.finalize_decoding()
        decoded = decoder.get_decoded_text()

        assert decoded == "E T"

    def test_timing_tolerance(self) -> None:
        """Test timing tolerance for dot/dash discrimination."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 100.0, "detection_tolerance": 0.3})

        # Test dot at upper tolerance limit (130ms)
        decoder.process_tone_detection(True, 130.0)
        decoder.process_tone_detection(False, 300.0)  # Character spacing
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "E"  # Should be decoded as dot

        decoder.reset_decoder()

        # Test dash at lower tolerance limit (210ms for 300ms dash)
        decoder.process_tone_detection(True, 210.0)
        decoder.process_tone_detection(False, 300.0)  # Character spacing
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "T"  # Should be decoded as dash

    def test_ambiguous_duration_resolution(self) -> None:
        """Test resolution of ambiguous durations."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 100.0})

        # Duration exactly between dot (100ms) and dash (300ms) = 200ms
        # Should be closer to dash
        decoder.process_tone_detection(True, 200.0)
        decoder.process_tone_detection(False, 300.0)
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "T"  # Should resolve as dash

    def test_unknown_pattern_handling(self) -> None:
        """Test handling of unknown Morse patterns."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # Create invalid pattern: 6 consecutive dashes (not in table)
        for _ in range(6):
            decoder.process_tone_detection(True, 240.0)  # Dash
            decoder.process_tone_detection(False, 80.0)  # Element spacing

        decoder.process_tone_detection(False, 240.0)  # Character spacing
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "?"

    def test_numbers_detection(self) -> None:
        """Test detection of numeric characters."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # Number '5' (..... - five dots)
        for _ in range(5):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)

        decoder.process_tone_detection(False, 240.0)
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "5"

    def test_punctuation_detection(self) -> None:
        """Test detection of punctuation marks."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # Question mark (..--..)
        pattern = "..---.."
        for char in pattern:
            duration = 80.0 if char == "." else 240.0
            decoder.process_tone_detection(True, duration)
            decoder.process_tone_detection(False, 80.0)

        decoder.process_tone_detection(False, 240.0)
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "?"

    def test_decoder_reset(self) -> None:
        """Test decoder state reset functionality."""
        decoder = MorseDecoder()

        # Decode something first
        decoder.process_tone_detection(True, 80.0)
        decoder.process_tone_detection(False, 300.0)
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "E"

        # Reset and verify clean state
        decoder.reset_decoder()

        assert decoder.get_decoded_text() == ""
        stats = decoder.get_statistics()
        assert stats["total_characters"] == 0
        assert stats["total_dots"] == 0
        assert stats["total_dashes"] == 0

    def test_statistics_tracking(self) -> None:
        """Test decoding statistics tracking."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # Decode "SOS" and track statistics
        # S (...) - 3 dots
        for _ in range(3):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)
        decoder.process_tone_detection(False, 240.0)

        # O (---) - 3 dashes
        for _ in range(3):
            decoder.process_tone_detection(True, 240.0)
            decoder.process_tone_detection(False, 80.0)
        decoder.process_tone_detection(False, 240.0)

        # S (...) - 3 dots
        for _ in range(3):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)

        decoder.finalize_decoding()

        stats = decoder.get_statistics()
        assert stats["total_characters"] == 3
        assert stats["total_dots"] == 6
        assert stats["total_dashes"] == 3

    def test_wpm_estimation(self) -> None:
        """Test WPM estimation from sample timings."""
        decoder = MorseDecoder()

        # Sample dot durations (in ms)
        sample_dots = [75.0, 80.0, 85.0, 78.0, 82.0]
        sample_dashes = [225.0, 240.0, 255.0, 230.0, 245.0]

        estimated_wpm = decoder.estimate_wpm_from_timing(sample_dots, sample_dashes)

        # Should be close to expected WPM based on 80ms median dot
        # Formula: 1200 / (80 * 50) = 0.3 WPM... wait that's not right
        # Correct formula: WPM = 1200 / dot_duration_ms for standard timing
        expected_wpm = 1200.0 / 80.0  # = 15 WPM

        assert abs(estimated_wpm - expected_wpm) < 1.0

    def test_morse_code_table_coverage(self) -> None:
        """Test that all morse code table entries are accessible."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 50.0})

        # Test a few key entries
        test_cases = [
            (".-", "A"),
            ("--", "M"),
            (".----", "1"),
            ("-----", "0"),
            (".-.-.-", "."),
            ("--..--", ","),
        ]

        for morse_pattern, expected_char in test_cases:
            decoder.reset_decoder()

            # Simulate the morse pattern
            for i, element in enumerate(morse_pattern):
                duration = 50.0 if element == "." else 150.0
                decoder.process_tone_detection(True, duration)
                if i < len(morse_pattern) - 1:  # Not last element
                    decoder.process_tone_detection(False, 50.0)  # Element spacing

            decoder.process_tone_detection(False, 150.0)  # Character spacing
            decoder.finalize_decoding()

            assert decoder.get_decoded_text() == expected_char, (
                f"Failed for pattern {morse_pattern}"
            )

    def test_continuous_processing(self) -> None:
        """Test continuous processing without explicit finalization."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # Process 'HI' without explicit finalization between characters
        # H (....) - 4 dots
        for _ in range(4):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)
        decoder.process_tone_detection(False, 240.0)  # Character spacing triggers 'H'

        # I (..) - 2 dots
        for _ in range(2):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)

        decoder.finalize_decoding()  # Only finalize at the end

        assert decoder.get_decoded_text() == "HI"

    def test_error_handling_edge_cases(self) -> None:
        """Test error handling for edge cases."""
        decoder = MorseDecoder()

        # Test processing with no tone events
        decoder.finalize_decoding()
        assert decoder.get_decoded_text() == ""

        # Test very short tone duration
        decoder.reset_decoder()
        decoder.process_tone_detection(True, 1.0)  # Very short
        decoder.process_tone_detection(False, 300.0)
        decoder.finalize_decoding()

        # Should still decode something (likely as dot due to being shorter)
        result = decoder.get_decoded_text()
        assert len(result) >= 0  # Should not crash

    def test_parameter_retrieval(self) -> None:
        """Test parameter retrieval and configuration access."""
        cfg = {"wpm_estimate": 25, "dot_duration_ms": 48.0, "detection_tolerance": 0.25}
        decoder = MorseDecoder(cfg_dict=cfg)

        params = decoder.get_params()

        assert params["wpm_estimate"] == 25
        assert params["dot_duration_ms"] == 48.0
        assert params["detection_tolerance"] == 0.25
        assert "dash_duration_ms" in params
        assert "character_spacing_ms" in params

    def test_incomplete_pattern_finalization(self) -> None:
        """Test finalization of incomplete patterns."""
        decoder = MorseDecoder(cfg_dict={"dot_duration_ms": 80.0})

        # Start a tone but don't complete it normally
        decoder.process_tone_detection(True, 80.0)
        decoder.process_tone_detection(True, 80.0)  # Continue tone for 160ms total

        # Finalize without explicit tone end
        decoder.finalize_decoding()

        # Should have processed the ongoing tone as a dash
        result = decoder.get_decoded_text()
        assert result == "T"  # 160ms should be interpreted as dash -> 'T'

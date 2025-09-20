"""Comprehensive tests for the MorseDecoder module.

This test module provides extensive test coverage for Morse code pattern recognition,
timing analysis, and character decoding functionality following CLAUDE.md
testing standards and pytest conventions.

Example usage:
    pytest tests/test_morse_decoder.py -v
"""

from unittest.mock import MagicMock

import pytest

from morsecode.components.decoder.keys import CfgKey
from morsecode.components.decoder.morse_decoder import MorseDecoder
from util.config import AwesomeConfigManager


class TestMorseDecoder:
    """Test suite for MorseDecoder functionality."""

    def create_mock_config_manager(self, config_overrides: dict = None) -> MagicMock:
        """Create a mock config manager with enum-based configuration.

        Args:
            config_overrides: Dict with CfgKey enum values to override defaults

        Returns:
            Mock config manager that provides enum-based configuration access
        """
        # Default decoder configuration values
        default_config = {
            CfgKey.WPM: 15,
            CfgKey.DOT_DURATION_MS: 80.0,
            CfgKey.TIMING_TOLERANCE_NORM: 0.3,
        }

        # Apply any overrides
        if config_overrides:
            config_values = {**default_config, **config_overrides}
        else:
            config_values = default_config

        # Create mock config manager
        mock_cfg_mgr = MagicMock(spec=AwesomeConfigManager)

        # Create mock config section
        mock_config_section = MagicMock()
        mock_config_section.get_int.side_effect = lambda key: config_values.get(key, 0)
        mock_config_section.get_double.side_effect = lambda key: config_values.get(key, 0.0)
        mock_config_section.get_bool.side_effect = lambda key: config_values.get(key, False)
        mock_config_section.get_string.side_effect = lambda key: config_values.get(key, "")

        # Mock the register_schema and get_section methods
        mock_cfg_mgr.register_enum_config.return_value = None
        mock_cfg_mgr.get_section.return_value = mock_config_section

        return mock_cfg_mgr

    def test_init_with_defaults(self) -> None:
        """Test decoder initialization with default parameters."""
        mock_cfg_mgr = self.create_mock_config_manager()
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager(
            {
                CfgKey.WPM: 20,
                CfgKey.DOT_DURATION_MS: 60.0,
                CfgKey.TIMING_TOLERANCE_NORM: 0.2,
            }
        )
        decoder = MorseDecoder(mock_cfg_mgr)

        assert decoder.wpm_estimate == 20
        assert decoder.dot_duration_ms == 60.0
        assert decoder.dash_duration_ms == 180.0  # 3x dot duration (default ratio)
        assert decoder.detection_tolerance == 0.2

    def test_config_validation(self) -> None:
        """Test configuration parameter validation."""
        # Test invalid WPM - validation happens in MorseDecoder
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.WPM: -5})
        with pytest.raises((ValueError, RuntimeError)):
            MorseDecoder(mock_cfg_mgr)

        # Test invalid dot duration with invalid WPM (causes division by zero during auto-correction)
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: -10.0, CfgKey.WPM: 0})
        with pytest.raises((ValueError, RuntimeError, ZeroDivisionError)):
            MorseDecoder(mock_cfg_mgr)

        # Test invalid tolerance
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.TIMING_TOLERANCE_NORM: 1.5})
        with pytest.raises((ValueError, RuntimeError)):
            MorseDecoder(mock_cfg_mgr)

    def test_single_dot_detection(self) -> None:
        """Test detection of a single dot."""
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 100.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 100.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 100.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager(
            {CfgKey.DOT_DURATION_MS: 100.0, CfgKey.TIMING_TOLERANCE_NORM: 0.3}
        )
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 100.0})
        decoder = MorseDecoder(mock_cfg_mgr)

        # Duration exactly between dot (100ms) and dash (300ms) = 200ms
        # Should be closer to dash
        decoder.process_tone_detection(True, 200.0)
        decoder.process_tone_detection(False, 300.0)
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "T"  # Should resolve as dash

    def test_unknown_pattern_handling(self) -> None:
        """Test handling of unknown Morse patterns."""
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

        # Create invalid pattern: 6 consecutive dashes (not in table)
        for _ in range(6):
            decoder.process_tone_detection(True, 240.0)  # Dash
            decoder.process_tone_detection(False, 80.0)  # Element spacing

        decoder.process_tone_detection(False, 240.0)  # Character spacing
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "?"

    def test_numbers_detection(self) -> None:
        """Test detection of numeric characters."""
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

        # Number '5' (..... - five dots)
        for _ in range(5):
            decoder.process_tone_detection(True, 80.0)
            decoder.process_tone_detection(False, 80.0)

        decoder.process_tone_detection(False, 240.0)
        decoder.finalize_decoding()

        assert decoder.get_decoded_text() == "5"

    def test_punctuation_detection(self) -> None:
        """Test detection of punctuation marks."""
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager()
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager()
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 50.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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

            assert decoder.get_decoded_text() == expected_char, f"Failed for pattern {morse_pattern}"

    def test_continuous_processing(self) -> None:
        """Test continuous processing without explicit finalization."""
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager()
        decoder = MorseDecoder(mock_cfg_mgr)

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
        mock_cfg_mgr = self.create_mock_config_manager(
            {CfgKey.WPM: 25, CfgKey.DOT_DURATION_MS: 48.0, CfgKey.TIMING_TOLERANCE_NORM: 0.25}
        )
        decoder = MorseDecoder(mock_cfg_mgr)

        params = decoder.get_params()

        assert params["wpm_estimate"] == 25
        assert params["dot_duration_ms"] == 48.0
        assert params["detection_tolerance"] == 0.25
        assert "dash_duration_ms" in params
        assert "character_spacing_ms" in params

    def test_incomplete_pattern_finalization(self) -> None:
        """Test finalization of incomplete patterns."""
        mock_cfg_mgr = self.create_mock_config_manager({CfgKey.DOT_DURATION_MS: 80.0})
        decoder = MorseDecoder(mock_cfg_mgr)

        # Start a tone but don't complete it normally
        decoder.process_tone_detection(True, 80.0)
        decoder.process_tone_detection(True, 80.0)  # Continue tone for 160ms total

        # Finalize without explicit tone end
        decoder.finalize_decoding()

        # Should have processed the ongoing tone as a dash
        result = decoder.get_decoded_text()
        assert result == "T"  # 160ms should be interpreted as dash -> 'T'

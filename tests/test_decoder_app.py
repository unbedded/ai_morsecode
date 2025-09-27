"""Tests for decoder_app.py module using ConfigurableBase architecture.

This test module provides coverage for the simplified, single-architecture
decoder application that uses ConfigurableBase components directly.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from morsecode.decoder_app import (
    ProgressReporter,
    _write_output,
    run_decoder_configurable,
)
from morsecode.events.types import (
    AudioChunkEvent,
    MorsePatternEvent,
    TextDecodedEvent,
    ToneDetectedEvent,
)
from util.config import AwesomeConfigManager


class TestProgressReporter:
    """Test the ProgressReporter class functionality."""

    def test_progress_reporter_init(self) -> None:
        """Test ProgressReporter initialization."""
        reporter = ProgressReporter()
        assert reporter.chunk_count == 0
        assert reporter.tone_detections == 0
        assert reporter.patterns_decoded == 0
        assert reporter.characters_decoded == 0
        assert reporter.current_text == ""

    def test_handle_audio_chunk(self, capsys) -> None:
        """Test audio chunk event handling."""
        reporter = ProgressReporter()

        # Test chunk counting without progress display
        event = AudioChunkEvent(
            chunk_size_ms=50,
            sample_rate=44100,
            has_more_data=True,
        )

        for _ in range(50):
            reporter.handle_audio_chunk(event)

        assert reporter.chunk_count == 50
        captured = capsys.readouterr()
        assert captured.out == ""  # No output for < 100 chunks

    def test_handle_tone_detected(self) -> None:
        """Test tone detection event handling."""
        reporter = ProgressReporter()

        # Test with detected tone
        detected_event = ToneDetectedEvent(detected=True, frequency=600.0, confidence=0.5)
        reporter.handle_tone_detected(detected_event)
        assert reporter.tone_detections == 1

        # Test with undetected tone
        undetected_event = ToneDetectedEvent(detected=False, frequency=600.0, confidence=0.1)
        reporter.handle_tone_detected(undetected_event)
        assert reporter.tone_detections == 1  # Should not increment

    def test_handle_morse_pattern(self) -> None:
        """Test morse pattern event handling."""
        reporter = ProgressReporter()

        # Test dot pattern
        dot_event = MorsePatternEvent(pattern_type="dot", duration_ms=80.0, confidence=0.9)
        reporter.handle_morse_pattern(dot_event)
        assert reporter.patterns_decoded == 1

        # Test dash pattern
        dash_event = MorsePatternEvent(pattern_type="dash", duration_ms=240.0, confidence=0.8)
        reporter.handle_morse_pattern(dash_event)
        assert reporter.patterns_decoded == 2

    def test_handle_text_decoded(self) -> None:
        """Test text decoded event handling."""
        reporter = ProgressReporter()

        # Test character accumulation
        event1 = TextDecodedEvent(text="H")
        reporter.handle_text_decoded(event1)
        assert reporter.characters_decoded == 1
        assert reporter.current_text == "H"

        event2 = TextDecodedEvent(text="ELLO")
        reporter.handle_text_decoded(event2)
        assert reporter.characters_decoded == 2
        assert reporter.current_text == "HELLO"


class TestWriteOutput:
    """Test the _write_output function."""

    def test_write_to_stdout(self, capsys) -> None:
        """Test writing output to stdout."""
        _write_output("HELLO WORLD")

        captured = capsys.readouterr()
        assert "Decoded text:" in captured.out
        assert "HELLO WORLD" in captured.out

    def test_write_to_file(self) -> None:
        """Test writing output to file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            _write_output("HELLO WORLD", temp_path)

            # Verify file contents
            with open(temp_path) as f:
                content = f.read()
            assert content.strip() == "HELLO WORLD"
        finally:
            Path(temp_path).unlink()

    def test_write_to_file_error(self, capsys) -> None:
        """Test file write error handling."""
        invalid_path = "/nonexistent/directory/file.txt"

        _write_output("HELLO WORLD", invalid_path)

        captured = capsys.readouterr()
        assert "Error writing output file:" in captured.err  # Error goes to stderr
        assert "HELLO WORLD" in captured.out  # Should fallback to stdout


class TestRunDecoderConfigurable:
    """Test the run_decoder_configurable function."""

    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.DecoderFactory")
    @patch("morsecode.decoder_app._write_output")
    def test_successful_decoding(self, mock_write, mock_decoder_class, mock_processor_class, mock_hal_class) -> None:
        """Test successful decoding with ConfigurableBase architecture."""
        # Setup mocks
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        mock_hal_class.return_value = mock_hal
        mock_processor_class.return_value = mock_processor
        mock_decoder_class.create.return_value = mock_decoder

        # Mock the processing loop
        mock_hal.has_data.side_effect = [True, True, False]  # Two chunks then stop
        mock_hal.get_next_chunk.return_value = MagicMock()
        mock_processor.detect_tone.return_value = True
        mock_decoder.get_decoded_text.return_value = "HELLO"

        # Create config manager
        config_manager = AwesomeConfigManager()
        overrides = {"audio": {"wav_filename": "test.wav"}}

        # Run decoder
        result = run_decoder_configurable(config_manager, overrides)

        # Verify success
        assert result == 0

        # Verify components were initialized with overrides
        mock_hal_class.assert_called_once_with(config_manager, overrides={"wav_filename": "test.wav"})
        mock_processor_class.assert_called_once_with(cfg_mgr=config_manager, overrides=None)
        mock_decoder_class.create.assert_called_once_with(cfg_mgr=config_manager, overrides=None)

        # Verify processing was called
        mock_decoder.finalize_decoding.assert_called_once()
        mock_write.assert_called_once_with("HELLO", None)

    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_component_initialization_error(self, mock_hal_class) -> None:
        """Test error handling during component initialization."""
        # Make HAL initialization fail
        mock_hal_class.side_effect = Exception("HAL init failed")

        config_manager = AwesomeConfigManager()

        # Run decoder and expect error
        result = run_decoder_configurable(config_manager)
        assert result == 1

    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.DecoderFactory")
    def test_no_data_available(self, mock_decoder_class, mock_processor_class, mock_hal_class) -> None:
        """Test handling when HAL has no data."""
        # Setup mocks
        mock_hal = MagicMock()
        mock_hal_class.return_value = mock_hal
        mock_hal.has_data.return_value = False

        config_manager = AwesomeConfigManager()

        # Run decoder
        result = run_decoder_configurable(config_manager)
        assert result == 1  # Should return error code for no data

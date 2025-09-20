"""Comprehensive tests for the decoder_app module.

This test module provides complete coverage for the main application module
that integrates CLI with decoder components, including progress reporting,
typed and legacy configuration support, and output handling.

Example usage:
    pytest tests/test_decoder_app.py -v
"""

from typing import Any
from unittest.mock import MagicMock, mock_open, patch

import numpy as np

from morsecode.decoder_app import (
    ProgressReporter,
    _process_audio,
    _process_audio_typed,
    _write_output,
    run_decoder_legacy,
    run_decoder_typed,
)
from morsecode.events.types import (
    AudioChunkEvent,
    MorsePatternEvent,
    TextDecodedEvent,
    ToneDetectedEvent,
)
from util.config.models import AppConfig, AudioConfig, DecoderConfig, SignalConfig


class TestProgressReporter:
    """Test the ProgressReporter class functionality."""

    def test_progress_reporter_init(self) -> None:
        """Test ProgressReporter initialization."""
        reporter = ProgressReporter()

        assert reporter.start_time > 0
        assert reporter.chunk_count == 0
        assert reporter.tone_detections == 0
        assert reporter.patterns_decoded == 0
        assert reporter.characters_decoded == 0
        assert reporter.current_text == ""
        assert reporter.last_progress_time > 0

    def test_handle_audio_chunk_regular(self, capsys: Any) -> None:
        """Test handling regular audio chunk events."""
        reporter = ProgressReporter()
        event = AudioChunkEvent(chunk_number=1, chunk_data=np.array([0.1, 0.2]), has_more_data=True)

        # Should not print on first chunk
        reporter.handle_audio_chunk(event)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert reporter.chunk_count == 1

    def test_handle_audio_chunk_every_100th(self, capsys: Any) -> None:
        """Test handling every 100th audio chunk event."""
        reporter = ProgressReporter()
        reporter.chunk_count = 99  # Set to 99 so next increment triggers output

        event = AudioChunkEvent(chunk_number=100, chunk_data=np.array([0.1, 0.2]), has_more_data=True)

        reporter.handle_audio_chunk(event)
        captured = capsys.readouterr()

        assert "Processed 100 chunks" in captured.out
        assert "Tones: 0" in captured.out
        assert "Patterns: 0" in captured.out
        assert "Text: ''" in captured.out
        assert reporter.chunk_count == 100

    def test_handle_audio_chunk_completion(self, capsys: Any) -> None:
        """Test handling final audio chunk event."""
        reporter = ProgressReporter()
        reporter.chunk_count = 50
        reporter.tone_detections = 10
        reporter.patterns_decoded = 5
        reporter.current_text = "SOS"

        event = AudioChunkEvent(chunk_number=51, chunk_data=np.array([0.1, 0.2]), has_more_data=False)

        reporter.handle_audio_chunk(event)
        captured = capsys.readouterr()

        assert "Processed 51 chunks" in captured.out
        assert "Tones: 10" in captured.out
        assert "Patterns: 5" in captured.out
        assert "Text: 'SOS'" in captured.out
        # Should have newline at completion
        assert captured.out.endswith("\n")

    def test_handle_tone_detected_true(self) -> None:
        """Test handling tone detected events (tone present)."""
        reporter = ProgressReporter()
        event = ToneDetectedEvent(
            detected=True,
            frequency=600.0,
            confidence=0.8,
            snr_db=20.0,
            chunk_number=1,
            detection_threshold=0.3,
        )

        reporter.handle_tone_detected(event)
        assert reporter.tone_detections == 1

    def test_handle_tone_detected_false(self) -> None:
        """Test handling tone detected events (no tone)."""
        reporter = ProgressReporter()
        event = ToneDetectedEvent(
            detected=False,
            frequency=0.0,
            confidence=0.1,
            snr_db=5.0,
            chunk_number=1,
            detection_threshold=0.3,
        )

        reporter.handle_tone_detected(event)
        assert reporter.tone_detections == 0  # Should not increment

    def test_handle_morse_pattern_dot(self) -> None:
        """Test handling morse pattern events (dot)."""
        reporter = ProgressReporter()
        event = MorsePatternEvent(pattern_type="dot", duration_ms=80.0, confidence=0.9)

        reporter.handle_morse_pattern(event)
        assert reporter.patterns_decoded == 1

    def test_handle_morse_pattern_dash(self) -> None:
        """Test handling morse pattern events (dash)."""
        reporter = ProgressReporter()
        event = MorsePatternEvent(pattern_type="dash", duration_ms=240.0, confidence=0.9)

        reporter.handle_morse_pattern(event)
        assert reporter.patterns_decoded == 1

    def test_handle_morse_pattern_other(self) -> None:
        """Test handling morse pattern events (other types)."""
        reporter = ProgressReporter()
        event = MorsePatternEvent(pattern_type="silence", duration_ms=100.0, confidence=0.5)

        reporter.handle_morse_pattern(event)
        assert reporter.patterns_decoded == 0  # Should not increment

    def test_handle_text_decoded(self) -> None:
        """Test handling text decoded events."""
        reporter = ProgressReporter()
        event = TextDecodedEvent(text="A", confidence=0.9)

        reporter.handle_text_decoded(event)
        assert reporter.characters_decoded == 1
        assert reporter.current_text == "A"

    def test_handle_text_decoded_truncation(self) -> None:
        """Test text truncation to 20 characters."""
        reporter = ProgressReporter()
        long_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 26 characters

        for char in long_text:
            event = TextDecodedEvent(text=char, confidence=0.9)
            reporter.handle_text_decoded(event)

        # Should keep only last 20 characters
        assert len(reporter.current_text) == 20
        assert reporter.current_text == "GHIJKLMNOPQRSTUVWXYZ"
        assert reporter.characters_decoded == 26

    @patch("morsecode.decoder_app.get_global_event_bus")
    def test_setup_event_subscriptions(self, mock_get_bus: Any) -> None:
        """Test event subscription setup."""
        mock_bus = MagicMock()
        mock_get_bus.return_value = mock_bus

        reporter = ProgressReporter()
        reporter.setup_event_subscriptions()

        # Verify all required subscriptions were made
        expected_calls = [
            (AudioChunkEvent, reporter.handle_audio_chunk),
            (ToneDetectedEvent, reporter.handle_tone_detected),
            (MorsePatternEvent, reporter.handle_morse_pattern),
            (TextDecodedEvent, reporter.handle_text_decoded),
        ]

        assert mock_bus.subscribe.call_count == 4
        for i, (event_type, handler) in enumerate(expected_calls):
            args, kwargs = mock_bus.subscribe.call_args_list[i]
            assert args[0] == event_type
            assert args[1] == handler


class TestRunDecoderTyped:
    """Test the run_decoder_typed function."""

    @patch("morsecode.decoder_app._process_audio_typed")
    @patch("morsecode.decoder_app.ProgressReporter")
    @patch("morsecode.decoder_app.MorseDecoder")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_run_decoder_typed_success(
        self,
        mock_hal: Any,
        mock_signal: Any,
        mock_decoder: Any,
        mock_progress: Any,
        mock_process: Any,
    ) -> None:
        """Test successful run_decoder_typed execution."""
        # Setup mocks
        mock_process.return_value = 0
        mock_progress_instance = MagicMock()
        mock_progress.return_value = mock_progress_instance

        # Create test configurations
        audio_config = AudioConfig(wav_filename="test.wav")
        signal_config = SignalConfig(frequency_hz=600)
        decoder_config = DecoderConfig(wpm=15)
        app_config = AppConfig()

        result = run_decoder_typed(audio_config, signal_config, decoder_config, app_config)

        assert result == 0
        # All components now use cfg_mgr parameter (unified constructor pattern)
        mock_hal.assert_called_once()
        assert "cfg_mgr" in mock_hal.call_args[1]
        mock_signal.assert_called_once()
        assert "cfg_mgr" in mock_signal.call_args[1]
        mock_decoder.assert_called_once()
        assert "cfg_mgr" in mock_decoder.call_args[1]
        mock_progress.assert_called_once()
        mock_progress_instance.setup_event_subscriptions.assert_called_once()
        mock_process.assert_called_once()

    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_run_decoder_typed_hal_failure(self, mock_hal: Any, capsys: Any) -> None:
        """Test run_decoder_typed with HAL initialization failure."""
        mock_hal.side_effect = Exception("HAL init failed")

        audio_config = AudioConfig(wav_filename="test.wav")
        signal_config = SignalConfig()
        decoder_config = DecoderConfig()
        app_config = AppConfig()

        result = run_decoder_typed(audio_config, signal_config, decoder_config, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "Unexpected error - HAL init failed" in captured.err

    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    @patch("morsecode.decoder_app.SignalProcessor")
    def test_run_decoder_typed_signal_failure(self, mock_signal: Any, mock_hal: Any, capsys: Any) -> None:
        """Test run_decoder_typed with SignalProcessor initialization failure."""
        mock_signal.side_effect = Exception("Signal init failed")

        audio_config = AudioConfig(wav_filename="test.wav")
        signal_config = SignalConfig()
        decoder_config = DecoderConfig()
        app_config = AppConfig()

        result = run_decoder_typed(audio_config, signal_config, decoder_config, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "Unexpected error - Signal init failed" in captured.err

    @patch("morsecode.decoder_app._process_audio_typed")
    @patch("morsecode.decoder_app.ProgressReporter")
    @patch("morsecode.decoder_app.MorseDecoder")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_run_decoder_typed_processing_failure(
        self,
        mock_hal: Any,
        mock_signal: Any,
        mock_decoder: Any,
        mock_progress: Any,
        mock_process: Any,
        capsys: Any,
    ) -> None:
        """Test run_decoder_typed with processing failure."""
        mock_process.side_effect = Exception("Processing failed")

        audio_config = AudioConfig(wav_filename="test.wav")
        signal_config = SignalConfig()
        decoder_config = DecoderConfig()
        app_config = AppConfig()

        result = run_decoder_typed(audio_config, signal_config, decoder_config, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "Unexpected error - Processing failed" in captured.err


class TestRunDecoderLegacy:
    """Test the run_decoder_legacy function."""

    @patch("morsecode.decoder_app._process_audio")
    @patch("morsecode.decoder_app.ProgressReporter")
    @patch("morsecode.decoder_app.MorseDecoder")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_run_decoder_legacy_success(
        self,
        mock_hal: Any,
        mock_signal: Any,
        mock_decoder: Any,
        mock_progress: Any,
        mock_process: Any,
    ) -> None:
        """Test successful run_decoder_legacy execution."""
        mock_process.return_value = 0

        hal_config = {"wav_filename": "test.wav", "audio_rate_hz": 44100}
        signal_config = {"target_frequency_hz": 600, "sample_rate_hz": 44100}
        decoder_config = {"wpm_estimate": 15}
        app_config = {"output_file": None}

        result = run_decoder_legacy(hal_config, signal_config, decoder_config, app_config)

        assert result == 0
        mock_hal.assert_called_once()
        mock_signal.assert_called_once()
        mock_decoder.assert_called_once()
        mock_process.assert_called_once()

    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_run_decoder_legacy_failure(self, mock_hal: Any, capsys: Any) -> None:
        """Test run_decoder_legacy with failure."""
        mock_hal.side_effect = Exception("Legacy init failed")

        hal_config = {"wav_filename": "test.wav"}
        signal_config = {}
        decoder_config = {}
        app_config = {}

        result = run_decoder_legacy(hal_config, signal_config, decoder_config, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "Unexpected error - Legacy init failed" in captured.err

    @patch("morsecode.decoder_app._process_audio")
    @patch("morsecode.decoder_app.ProgressReporter")
    @patch("morsecode.decoder_app.MorseDecoder")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_run_decoder_legacy_config_defaults(
        self,
        mock_hal: Any,
        mock_signal: Any,
        mock_decoder: Any,
        mock_progress: Any,
        mock_process: Any,
    ) -> None:
        """Test run_decoder_legacy with default config values."""
        mock_process.return_value = 0

        # Empty configs should use defaults
        hal_config: dict[str, Any] = {}
        signal_config: dict[str, Any] = {}
        decoder_config: dict[str, Any] = {}
        app_config: dict[str, Any] = {}

        result = run_decoder_legacy(hal_config, signal_config, decoder_config, app_config)

        assert result == 0

        # Verify HAL was called with cfg_mgr (mock config manager)
        mock_hal.assert_called_once()
        assert "cfg_mgr" in mock_hal.call_args[1]
        # All components now use unified constructor pattern with mock config managers
        mock_signal.assert_called_once()
        assert "cfg_mgr" in mock_signal.call_args[1]
        # Configuration values are passed through mock config managers


class TestProcessAudioTyped:
    """Test the _process_audio_typed function."""

    @patch("morsecode.decoder_app._write_output")
    def test_process_audio_typed_success(self, mock_write: Any, capsys: Any) -> None:
        """Test successful audio processing with typed config."""
        # Create mock components
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        # Setup mock behavior
        mock_hal.has_data.side_effect = [True, True, False]  # Two chunks then done
        mock_hal.get_next_chunk.side_effect = [np.array([0.1, 0.2, 0.3]), np.array([0.4, 0.5, 0.6])]
        mock_processor.detect_tone.side_effect = [True, False]
        mock_decoder.get_decoded_text.return_value = "SOS"

        app_config = AppConfig(output_file=None)

        result = _process_audio_typed(mock_hal, mock_processor, mock_decoder, app_config)

        assert result == 0
        captured = capsys.readouterr()
        assert "Processing audio..." in captured.out
        assert "Audio processing complete" in captured.out

        # Verify all components were called correctly
        assert mock_hal.get_next_chunk.call_count == 2
        assert mock_processor.detect_tone.call_count == 2
        assert mock_decoder.process_tone_detection.call_count == 2
        mock_decoder.finalize_decoding.assert_called_once()
        mock_write.assert_called_once_with("SOS", None)

    @patch("morsecode.decoder_app._write_output")
    def test_process_audio_typed_no_text_detected(self, mock_write: Any) -> None:
        """Test audio processing when no morse text is detected."""
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        mock_hal.has_data.side_effect = [True, False]
        mock_hal.get_next_chunk.return_value = np.array([0.1, 0.2])
        mock_processor.detect_tone.return_value = False
        mock_decoder.get_decoded_text.return_value = ""  # No text detected

        app_config = AppConfig(output_file="output.txt")

        result = _process_audio_typed(mock_hal, mock_processor, mock_decoder, app_config)

        assert result == 0
        mock_write.assert_called_once_with("[No Morse code detected]", "output.txt")

    def test_process_audio_typed_keyboard_interrupt(self, capsys: Any) -> None:
        """Test keyboard interrupt handling."""
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        mock_hal.has_data.return_value = True
        mock_hal.get_next_chunk.side_effect = KeyboardInterrupt()

        app_config = AppConfig()

        result = _process_audio_typed(mock_hal, mock_processor, mock_decoder, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "Interrupted by user" in captured.out

    def test_process_audio_typed_processing_error(self, capsys: Any) -> None:
        """Test processing error handling."""
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        mock_hal.has_data.return_value = True
        mock_hal.get_next_chunk.side_effect = Exception("Processing error")

        app_config = AppConfig()

        result = _process_audio_typed(mock_hal, mock_processor, mock_decoder, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "Processing error" in captured.err


class TestProcessAudio:
    """Test the _process_audio function (legacy)."""

    @patch("morsecode.decoder_app._write_output")
    def test_process_audio_success(self, mock_write: Any, capsys: Any) -> None:
        """Test successful legacy audio processing."""
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        mock_hal.has_data.side_effect = [True, False]
        mock_hal.get_next_chunk.return_value = np.array([0.1, 0.2])
        mock_processor.detect_tone.return_value = True
        mock_decoder.get_decoded_text.return_value = "TEST"

        app_config = {"output_file": "test.txt"}

        result = _process_audio(mock_hal, mock_processor, mock_decoder, app_config)

        assert result == 0
        captured = capsys.readouterr()
        assert "Processing audio..." in captured.out
        assert "Audio processing complete" in captured.out

        mock_write.assert_called_once_with("TEST", "test.txt")

    @patch("morsecode.decoder_app._write_output")
    def test_process_audio_empty_result(self, mock_write: Any) -> None:
        """Test legacy processing with empty result."""
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        mock_hal.has_data.side_effect = [True, False]
        mock_hal.get_next_chunk.return_value = np.array([0.1])
        mock_decoder.get_decoded_text.return_value = "   "  # Whitespace only

        app_config = {"output_file": None}

        result = _process_audio(mock_hal, mock_processor, mock_decoder, app_config)

        assert result == 0
        mock_write.assert_called_once_with("[No Morse code detected]", None)

    def test_process_audio_error(self, capsys: Any) -> None:
        """Test legacy processing error handling."""
        mock_hal = MagicMock()
        mock_processor = MagicMock()
        mock_decoder = MagicMock()

        mock_hal.has_data.side_effect = Exception("HAL error")

        app_config: dict[str, Any] = {}

        result = _process_audio(mock_hal, mock_processor, mock_decoder, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error during processing" in captured.err


class TestWriteOutput:
    """Test the _write_output function."""

    def test_write_output_to_stdout(self, capsys: Any) -> None:
        """Test writing output to stdout."""
        decoded_text = "HELLO WORLD"

        _write_output(decoded_text, None)

        captured = capsys.readouterr()
        assert "Decoded text:" in captured.out
        assert "HELLO WORLD" in captured.out

    @patch("builtins.open", mock_open())
    @patch("morsecode.decoder_app.Path")
    def test_write_output_to_file_success(self, mock_path: Any, capsys: Any) -> None:
        """Test successful writing to file."""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        decoded_text = "SOS"
        output_file = "output.txt"

        _write_output(decoded_text, output_file)

        captured = capsys.readouterr()
        assert f"Decoded text written to: {output_file}" in captured.out

        # Verify file operations
        mock_path.assert_called_once_with(output_file)

    @patch("builtins.open")
    @patch("morsecode.decoder_app.Path")
    def test_write_output_to_file_error(self, mock_path: Any, mock_open: Any, capsys: Any) -> None:
        """Test file writing error handling."""
        mock_open.side_effect = OSError("Permission denied")

        decoded_text = "SOS"
        output_file = "protected.txt"

        _write_output(decoded_text, output_file)

        captured = capsys.readouterr()
        assert "Error writing output file" in captured.err
        assert "Permission denied" in captured.err
        assert "Decoded text: SOS" in captured.out  # Fallback to stdout

    @patch("builtins.open", mock_open())
    @patch("morsecode.decoder_app.Path")
    def test_write_output_file_content(self, mock_path: Any) -> None:
        """Test that file content is written correctly."""
        decoded_text = "TEST MESSAGE"
        output_file = "test.txt"

        with patch("builtins.open", mock_open()) as m:
            _write_output(decoded_text, output_file)

        # Verify file was opened in write mode with UTF-8 encoding
        m.assert_called_once_with(mock_path.return_value, "w", encoding="utf-8")
        handle = m.return_value

        # Verify content written
        write_calls = handle.write.call_args_list
        assert len(write_calls) == 2
        assert write_calls[0][0][0] == "TEST MESSAGE"
        assert write_calls[1][0][0] == "\n"


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    @patch("morsecode.decoder_app._write_output")
    @patch("morsecode.decoder_app.ProgressReporter")
    @patch("morsecode.decoder_app.MorseDecoder")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_full_typed_pipeline(
        self,
        mock_hal_class: Any,
        mock_signal_class: Any,
        mock_decoder_class: Any,
        mock_progress_class: Any,
        mock_write: Any,
        capsys: Any,
    ) -> None:
        """Test complete typed pipeline integration."""
        # Setup component mocks
        mock_hal = MagicMock()
        mock_signal = MagicMock()
        mock_decoder = MagicMock()
        mock_progress = MagicMock()

        mock_hal_class.return_value = mock_hal
        mock_signal_class.return_value = mock_signal
        mock_decoder_class.return_value = mock_decoder
        mock_progress_class.return_value = mock_progress

        # Setup processing behavior
        mock_hal.has_data.side_effect = [True, True, True, False]
        mock_hal.get_next_chunk.side_effect = [
            np.array([0.1, 0.2]),
            np.array([0.3, 0.4]),
            np.array([0.5, 0.6]),
        ]
        mock_signal.detect_tone.side_effect = [True, False, True]
        mock_decoder.get_decoded_text.return_value = "SOS"

        # Create configurations
        audio_config = AudioConfig(wav_filename="morse.wav", sample_rate=22050)
        signal_config = SignalConfig(frequency_hz=800, signal_threshold_norm=0.4)
        decoder_config = DecoderConfig(wpm=20, timing_tolerance_norm=0.2)
        app_config = AppConfig(output_file="result.txt", debug=True)

        result = run_decoder_typed(audio_config, signal_config, decoder_config, app_config)

        assert result == 0

        # Verify component initialization with correct configs
        # All components now use cfg_mgr parameter (unified constructor pattern)
        mock_hal_class.assert_called_once()
        assert "cfg_mgr" in mock_hal_class.call_args[1]
        mock_signal_class.assert_called_once()
        assert "cfg_mgr" in mock_signal_class.call_args[1]
        mock_decoder_class.assert_called_once()
        assert "cfg_mgr" in mock_decoder_class.call_args[1]

        # Verify progress reporting setup
        mock_progress.setup_event_subscriptions.assert_called_once()

        # Verify processing occurred
        assert mock_hal.get_next_chunk.call_count == 3
        assert mock_signal.detect_tone.call_count == 3
        assert mock_decoder.process_tone_detection.call_count == 3

        # Verify finalization and output
        mock_decoder.finalize_decoding.assert_called_once()
        mock_write.assert_called_once_with("SOS", "result.txt")

    @patch("morsecode.decoder_app._write_output")
    @patch("morsecode.decoder_app.ProgressReporter")
    @patch("morsecode.decoder_app.MorseDecoder")
    @patch("morsecode.decoder_app.SignalProcessor")
    @patch("morsecode.decoder_app.HardwareAbstractionLayer")
    def test_full_legacy_pipeline(
        self,
        mock_hal_class: Any,
        mock_signal_class: Any,
        mock_decoder_class: Any,
        mock_progress_class: Any,
        mock_write: Any,
    ) -> None:
        """Test complete legacy pipeline integration."""
        # Setup mocks
        mock_hal = MagicMock()
        mock_signal = MagicMock()
        mock_decoder = MagicMock()

        mock_hal_class.return_value = mock_hal
        mock_signal_class.return_value = mock_signal
        mock_decoder_class.return_value = mock_decoder

        # Setup processing
        mock_hal.has_data.side_effect = [True, False]
        mock_hal.get_next_chunk.return_value = np.array([0.1])
        mock_signal.detect_tone.return_value = False
        mock_decoder.get_decoded_text.return_value = "E"

        # Legacy config dictionaries
        hal_config = {
            "wav_filename": "legacy.wav",
            "audio_rate_hz": 48000,
            "auto_gain_control": False,
            "chunk_size_ms": 25,
        }
        signal_config = {
            "sample_rate_hz": 48000,
            "target_frequency_hz": 700,
            "detection_threshold": 0.2,
            "filter_bandwidth_hz": 100,
        }
        decoder_config = {
            "wpm_estimate": 25,
            "detection_tolerance": 0.4,
            "dot_duration_ms": 48.0,
            "min_silence_duration_ms": 150.0,
        }
        app_config = {"output_file": "legacy_out.txt"}

        result = run_decoder_legacy(hal_config, signal_config, decoder_config, app_config)

        assert result == 0

        # Verify configs were converted correctly - all components now use cfg_mgr
        mock_hal_class.assert_called_once()
        assert "cfg_mgr" in mock_hal_class.call_args[1]
        mock_signal_class.assert_called_once()
        assert "cfg_mgr" in mock_signal_class.call_args[1]
        # All components now use unified constructor pattern with mock config managers

        # Decoder now uses cfg_mgr parameter (mock config manager)
        mock_decoder_class.assert_called_once()
        assert "cfg_mgr" in mock_decoder_class.call_args[1]

        mock_write.assert_called_once_with("E", "legacy_out.txt")

    def test_error_chain_propagation(self, capsys: Any) -> None:
        """Test that errors propagate correctly through the call chain."""
        # Test configuration that will fail during HAL init
        audio_config = AudioConfig(wav_filename="/nonexistent/path/file.wav")
        signal_config = SignalConfig()
        decoder_config = DecoderConfig()
        app_config = AppConfig()

        with patch("morsecode.decoder_app.HardwareAbstractionLayer") as mock_hal:
            mock_hal.side_effect = FileNotFoundError("File not found")

            result = run_decoder_typed(audio_config, signal_config, decoder_config, app_config)

        assert result == 1
        captured = capsys.readouterr()
        assert "File not found" in captured.err

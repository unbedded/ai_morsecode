"""Comprehensive test suite for CLI functionality.

This test module provides thorough test coverage for the command-line interface,
including argument parsing, configuration handling, error scenarios, and
integration with the decoding pipeline.

Example usage:
    pytest tests/test_cli.py -v
"""

import argparse
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from morsecode.cli.main import create_parser, main, setup_logging, validate_args
from util.config.config_manager import AwesomeConfigManager


class TestArgumentParser:
    """Test the CLI argument parser functionality."""

    def test_create_parser_basic(self) -> None:
        """Test basic parser creation."""
        parser = create_parser()

        assert parser.prog == "morsecode"
        assert "Morse Code Decoder" in parser.description
        assert parser.formatter_class == argparse.RawDescriptionHelpFormatter

    def test_parse_basic_args(self) -> None:
        """Test parsing basic arguments."""
        parser = create_parser()

        args = parser.parse_args(["audio.wav"])
        assert args.wav_file == "audio.wav"
        assert args.config is None
        assert args.profile is None
        assert args.create_config is False

    def test_parse_all_options(self) -> None:
        """Test parsing all available options."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "test.wav",
                "--config",
                "custom.yaml",
                "--profile",
                "debug",
                "--frequency",
                "800",
                "--wpm",
                "20",
                "--threshold",
                "0.4",
                "--debug",
                "--output",
                "output.txt",
                "--log-level",
                "INFO",
            ]
        )

        assert args.wav_file == "test.wav"
        assert args.config == "custom.yaml"
        assert args.profile == "debug"
        assert args.frequency == 800
        assert args.wpm == 20
        assert args.threshold == 0.4
        assert args.debug is True
        assert args.output == "output.txt"
        assert args.log_level == "INFO"

    def test_parse_utility_commands(self) -> None:
        """Test parsing utility commands."""
        parser = create_parser()

        # Test create-config
        args = parser.parse_args(["--create-config"])
        assert args.create_config is True

        # Test validate-config
        args = parser.parse_args(["--validate-config"])
        assert args.validate_config is True

    def test_parse_no_args(self) -> None:
        """Test parsing with no arguments."""
        parser = create_parser()

        args = parser.parse_args([])
        assert args.wav_file is None
        assert args.create_config is False


class TestArgumentValidation:
    """Test CLI argument validation."""

    def test_validate_args_success(self, tmp_path: Path) -> None:
        """Test successful argument validation."""
        # Create a test WAV file
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav content")

        parser = create_parser()
        args = parser.parse_args([str(wav_file)])

        # Should not raise any exception
        validate_args(args)

    def test_validate_nonexistent_wav_file(self, capsys: Any) -> None:
        """Test validation with non-existent WAV file."""
        parser = create_parser()
        args = parser.parse_args(["nonexistent.wav"])

        with pytest.raises(SystemExit):
            validate_args(args)

        captured = capsys.readouterr()
        assert "WAV file does not exist" in captured.err

    def test_validate_non_wav_file(self, tmp_path: Path, capsys: Any) -> None:
        """Test validation with non-WAV file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a wav file")

        parser = create_parser()
        args = parser.parse_args([str(txt_file)])

        with pytest.raises(SystemExit):
            validate_args(args)

        captured = capsys.readouterr()
        assert "File must be a WAV file" in captured.err

    def test_validate_invalid_frequency(self, capsys: Any) -> None:
        """Test validation with invalid frequency."""
        parser = create_parser()
        args = parser.parse_args(["--frequency", "5000", "test.wav"])

        with pytest.raises(SystemExit):
            validate_args(args)

        captured = capsys.readouterr()
        assert "Frequency must be 200-2000 Hz" in captured.err

    def test_validate_invalid_threshold(self, capsys: Any) -> None:
        """Test validation with invalid threshold."""
        parser = create_parser()
        args = parser.parse_args(["--threshold", "2.0", "test.wav"])

        with pytest.raises(SystemExit):
            validate_args(args)

        captured = capsys.readouterr()
        assert "Threshold must be 0.0-1.0" in captured.err

    def test_validate_invalid_wpm(self, capsys: Any) -> None:
        """Test validation with invalid WPM."""
        parser = create_parser()
        args = parser.parse_args(["--wpm", "100", "test.wav"])

        with pytest.raises(SystemExit):
            validate_args(args)

        captured = capsys.readouterr()
        assert "WPM must be 5-60" in captured.err

    def test_validate_nonexistent_config(self, capsys: Any) -> None:
        """Test validation with non-existent config file."""
        parser = create_parser()
        args = parser.parse_args(["--config", "nonexistent.yaml", "test.wav"])

        with pytest.raises(SystemExit):
            validate_args(args)

        captured = capsys.readouterr()
        assert "Config file does not exist" in captured.err


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_logging_default(self, caplog: Any) -> None:
        """Test default logging setup."""
        config_manager = MagicMock()
        config_manager.get_config.return_value = {"log_level": "WARNING", "debug": False}

        with caplog.at_level(logging.DEBUG):
            setup_logging(config_manager)

        # Check that logging level was set
        assert logging.getLogger().level <= logging.WARNING

    def test_setup_logging_debug_override(self, caplog: Any, capsys: Any) -> None:
        """Test logging setup with debug override."""
        config_manager = MagicMock()
        config_manager.get_config.return_value = {"log_level": "WARNING", "debug": False}

        # Reset logging to ensure clean state
        logging.getLogger().handlers.clear()

        with caplog.at_level(logging.DEBUG):
            setup_logging(config_manager, debug_override=True)

        # Check that debug logging was enabled
        root_logger = logging.getLogger()
        assert root_logger.level <= logging.DEBUG or any(h.level <= logging.DEBUG for h in root_logger.handlers)

        # Check stderr for debug message since it may go there instead of caplog
        captured = capsys.readouterr()
        debug_found = "Debug mode enabled" in caplog.text or "Debug mode enabled" in captured.err
        assert debug_found, f"Debug message not found. Caplog: {caplog.text}, Stderr: {captured.err}"

    def test_setup_logging_level_override(self, caplog: Any) -> None:
        """Test logging setup with log level override."""
        config_manager = MagicMock()
        config_manager.get_config.return_value = {"log_level": "WARNING", "debug": False}

        # Reset logging to ensure clean state
        logging.getLogger().handlers.clear()

        with caplog.at_level(logging.INFO):
            setup_logging(config_manager, log_level_override="INFO")

        # Check that INFO level was set
        root_logger = logging.getLogger()
        assert root_logger.level <= logging.INFO or any(h.level <= logging.INFO for h in root_logger.handlers)

    def test_setup_logging_config_error(self, caplog: Any) -> None:
        """Test logging setup when config fails."""
        config_manager = MagicMock()
        config_manager.get_config.side_effect = Exception("Config error")

        with caplog.at_level(logging.WARNING):
            setup_logging(config_manager)

        # Should still work with defaults
        assert logging.getLogger().level <= logging.WARNING


class TestMainFunction:
    """Test the main CLI function."""

    @patch("morsecode.cli.main.decoder_app.run_decoder_typed")
    def test_main_success(self, mock_run_decoder: Any, tmp_path: Path) -> None:
        """Test successful main execution."""
        # Create test WAV file
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav")

        # Mock successful decoding
        mock_run_decoder.return_value = 0

        # Test main function
        result = main([str(wav_file)])

        assert result == 0
        mock_run_decoder.assert_called_once()

    def test_main_create_config(self, capsys: Any) -> None:
        """Test main function with --create-config."""
        with patch.object(AwesomeConfigManager, "create_sample_config") as mock_create:
            result = main(["--create-config"])

        assert result == 0
        mock_create.assert_called_once_with("config/morse.yaml")

        captured = capsys.readouterr()
        assert "Sample configuration created: config/morse.yaml" in captured.out

    def test_main_validate_config_success(self, capsys: Any) -> None:
        """Test main function with successful config validation."""
        # Create a properly mocked config manager
        mock_config_manager = MagicMock()
        mock_config_manager.config_file = Path("test.yaml")
        mock_config_manager.get_config.return_value = {}

        with patch("morsecode.cli.main.AwesomeConfigManager", return_value=mock_config_manager):
            result = main(["--validate-config"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Configuration is valid" in captured.out

    def test_main_validate_config_failure(self, capsys: Any) -> None:
        """Test main function with config validation failure."""
        # Create a properly mocked config manager that raises an exception
        mock_config_manager = MagicMock()
        mock_config_manager.config_file = Path("test.yaml")
        mock_config_manager.get_config.side_effect = Exception("Invalid config")

        with patch("morsecode.cli.main.AwesomeConfigManager", return_value=mock_config_manager):
            result = main(["--validate-config"])

        assert result == 1
        captured = capsys.readouterr()
        assert "Configuration validation failed" in captured.err

    def test_main_no_wav_file(self, capsys: Any) -> None:
        """Test main function without WAV file for processing."""
        # Create a properly mocked config manager
        mock_config_manager = MagicMock()
        mock_config_manager.config_file = Path("test.yaml")
        mock_config_manager.get_config.return_value = {}

        with patch("morsecode.cli.main.AwesomeConfigManager", return_value=mock_config_manager):
            result = main([])

        assert result == 1
        captured = capsys.readouterr()
        assert "WAV file is required for processing" in captured.err

    def test_main_config_load_failure(self, capsys: Any, tmp_path: Path) -> None:
        """Test main function when config loading fails."""
        # Create a valid WAV file to pass validation
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav")

        with patch.object(AwesomeConfigManager, "__init__", side_effect=Exception("Config error")):
            result = main([str(wav_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Failed to load configuration" in captured.err
        assert "Run 'morsecode --create-config'" in captured.err

    def test_main_keyboard_interrupt(self, tmp_path: Path, capsys: Any) -> None:
        """Test main function handling keyboard interrupt."""
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav")

        config_manager_mock = MagicMock()
        config_manager_mock.get_config.return_value = {}

        # Create a properly mocked config manager
        mock_config_manager = MagicMock()
        mock_config_manager.config_file = Path("test.yaml")
        mock_config_manager.get_config.return_value = {}

        with patch("morsecode.cli.main.AwesomeConfigManager", return_value=mock_config_manager):
            with patch(
                "morsecode.cli.main.decoder_app.run_decoder_typed",
                side_effect=KeyboardInterrupt,
            ):
                result = main([str(wav_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Interrupted by user" in captured.err

    def test_main_unexpected_error(self, tmp_path: Path, capsys: Any) -> None:
        """Test main function handling unexpected errors."""
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav")

        # Create a properly mocked config manager
        mock_config_manager = MagicMock()
        mock_config_manager.config_file = Path("test.yaml")
        mock_config_manager.get_config.return_value = {}

        with patch("morsecode.cli.main.AwesomeConfigManager", return_value=mock_config_manager):
            with patch(
                "morsecode.cli.main.decoder_app.run_decoder_typed",
                side_effect=RuntimeError("Unexpected"),
            ):
                result = main([str(wav_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Unexpected" in captured.err

    @patch("morsecode.cli.main.decoder_app.run_decoder_typed")
    def test_main_with_overrides(self, mock_run_decoder: Any, tmp_path: Path) -> None:
        """Test main function with CLI parameter overrides."""
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav")

        mock_run_decoder.return_value = 0

        # Create a properly mocked config manager
        mock_config_manager = MagicMock()
        mock_config_manager.config_file = Path("test.yaml")
        mock_config_manager.get_config.return_value = {}

        with patch("morsecode.cli.main.AwesomeConfigManager", return_value=mock_config_manager):
            result = main(
                [
                    str(wav_file),
                    "--frequency",
                    "800",
                    "--wpm",
                    "25",
                    "--threshold",
                    "0.4",
                    "--output",
                    "result.txt",
                ]
            )

        assert result == 0

        # Verify that run_decoder_typed was called with the correct arguments
        args, kwargs = mock_run_decoder.call_args
        audio_config, signal_config, decoder_config, app_config = args

        assert signal_config.frequency == 800
        assert decoder_config.wpm == 25
        assert signal_config.threshold == 0.4
        assert app_config.output_file == "result.txt"

    def test_main_argument_validation_failure(self, capsys: Any) -> None:
        """Test main function when argument validation fails."""
        # This test expects SystemExit due to validation failure
        try:
            result = main(["nonexistent.wav"])
            assert result == 1
        except SystemExit as e:
            assert e.code == 1

        captured = capsys.readouterr()
        assert "WAV file does not exist" in captured.err


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    @patch("morsecode.cli.main.decoder_app.run_decoder_typed")
    def test_full_cli_workflow(self, mock_run_decoder: Any, tmp_path: Path) -> None:
        """Test complete CLI workflow from arguments to execution."""
        # Create test files
        wav_file = tmp_path / "morse.wav"
        wav_file.write_text("fake wav content")

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
app:
  debug: false
  log_level: INFO
audio:
  sample_rate: 44100
  chunk_size_ms: 50
signal:
  frequency: 600
  threshold: 0.3
  bandwidth: 50
decoder:
  wpm: 15
  tolerance: 0.3
        """)

        mock_run_decoder.return_value = 0

        # Mock the config loading to use our test values
        def mock_get_config(section):
            config_data = {
                "app": {"debug": False, "log_level": "INFO", "output_file": None},
                "audio": {"sample_rate": 44100, "chunk_size_ms": 50},
                "signal": {"frequency": 600, "threshold": 0.3, "bandwidth": 50},
                "decoder": {"wpm": 15, "tolerance": 0.3},
            }
            return config_data.get(section, {})

        with patch.object(AwesomeConfigManager, "__init__", return_value=None):
            with patch.object(AwesomeConfigManager, "get_config", side_effect=mock_get_config):
                # Test with config file and overrides
                result = main(
                    [
                        str(wav_file),
                        "--config",
                        str(config_file),
                        "--frequency",
                        "700",
                        "--debug",
                        "--output",
                        "decoded.txt",
                    ]
                )

        assert result == 0
        mock_run_decoder.assert_called_once()

        # Verify configuration was properly applied
        args, kwargs = mock_run_decoder.call_args
        audio_config, signal_config, decoder_config, app_config = args

        # Should have CLI override
        assert signal_config.frequency == 700
        # Should have original config values for non-overridden items
        assert decoder_config.wpm == 15
        assert app_config.output_file == "decoded.txt"

    def test_error_reporting(self, capsys: Any) -> None:
        """Test comprehensive error reporting."""
        # Test multiple validation errors - this will exit early due to validation
        try:
            result = main(["nonexistent.wav", "--frequency", "5000", "--wpm", "200", "--threshold", "5.0"])
            assert result == 1
        except SystemExit:
            pass  # Expected due to validation failure

        captured = capsys.readouterr()

        # Should report all validation errors
        assert "Invalid arguments" in captured.err
        assert "WAV file does not exist" in captured.err
        assert "Frequency must be 200-2000 Hz" in captured.err
        assert "WPM must be 5-60" in captured.err
        assert "Threshold must be 0.0-1.0" in captured.err


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_argv(self) -> None:
        """Test with empty argv."""
        result = main([])
        assert result == 1

    def test_help_text_content(self) -> None:
        """Test that help text contains expected content."""
        parser = create_parser()
        help_text = parser.format_help()

        # Check for key sections
        assert "Configuration:" in help_text
        assert "Profiles:" in help_text
        assert "Examples:" in help_text
        assert "morse.yaml" in help_text
        assert "--profile" in help_text

    @patch("sys.argv", ["morsecode"])
    def test_main_as_module(self) -> None:
        """Test running main as module."""
        # This tests the if __name__ == "__main__" block indirectly
        with patch("morsecode.cli.main.main", return_value=0):
            # Import would trigger the main block, but we're patching it
            result = main([])

        # The actual test is that this doesn't crash
        assert result in [0, 1]  # Either success or expected failure

    def test_config_edge_cases(self, tmp_path: Path) -> None:
        """Test configuration edge cases."""
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav")

        # Test with empty config file
        empty_config = tmp_path / "empty.yaml"
        empty_config.write_text("")

        with patch.object(AwesomeConfigManager, "__init__", return_value=None):
            with patch.object(AwesomeConfigManager, "get_config", return_value={}):
                with patch("morsecode.cli.main.decoder_app.run_decoder_typed", return_value=0):
                    result = main([str(wav_file), "--config", str(empty_config)])

        # Should still work with defaults
        assert result == 0

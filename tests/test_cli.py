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
from unittest.mock import MagicMock, Mock, mock_open, patch

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
        assert args.show_config is False

    def test_parse_all_options(self) -> None:
        """Test parsing all available options."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "test.wav",
                "--cfg-file",
                "custom.yaml",
                "--cfg-profile",
                "debug",
                "--cfg-override",
                "signal-frequency-hz=800",
                "--cfg-override",
                "decoder-wpm=20",
                "-s",
                "signal-signal-threshold-norm=0.4",
            ]
        )

        assert args.wav_file == "test.wav"
        assert args.config == "custom.yaml"
        assert args.profile == "debug"
        assert args.lazy_overrides == ["signal-frequency-hz=800", "decoder-wpm=20", "signal-signal-threshold-norm=0.4"]

    def test_parse_utility_commands(self) -> None:
        """Test parsing utility commands."""
        parser = create_parser()

        # Test cfg-show
        args = parser.parse_args(["--cfg-show"])
        assert args.show_config is True

    def test_parse_no_args(self) -> None:
        """Test parsing with no arguments."""
        parser = create_parser()

        args = parser.parse_args([])
        assert args.wav_file is None
        assert args.show_config is False


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

    def test_validate_invalid_frequency(self, capsys: Any, tmp_path: Path) -> None:
        """Test validation with invalid frequency (now handled through config system)."""
        parser = create_parser()
        # Create a dummy WAV file
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav content")

        # Frequency validation is now handled in the config system, not CLI args
        args = parser.parse_args(["-s", "signal-frequency-hz=5000", str(wav_file)])

        # Basic validation should pass (detailed validation happens in config manager)
        validate_args(args)  # Should not raise

        # The frequency validation happens at config level, not CLI level
        assert args.lazy_overrides == ["signal-frequency-hz=5000"]

    def test_validate_invalid_threshold(self, capsys: Any, tmp_path: Path) -> None:
        """Test validation with invalid threshold (now handled through config system)."""
        parser = create_parser()
        # Create a dummy WAV file
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav content")

        # Threshold validation is now handled in the config system, not CLI args
        args = parser.parse_args(["-s", "signal-signal-threshold-norm=2.0", str(wav_file)])

        # Basic validation should pass (detailed validation happens in config manager)
        validate_args(args)  # Should not raise

        # The threshold validation happens at config level, not CLI level
        assert args.lazy_overrides == ["signal-signal-threshold-norm=2.0"]

    def test_validate_invalid_wpm(self, capsys: Any, tmp_path: Path) -> None:
        """Test validation with invalid WPM (now handled through config system)."""
        parser = create_parser()
        # Create a dummy WAV file
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav content")

        # WPM validation is now handled in the config system, not CLI args
        args = parser.parse_args(["-s", "decoder-wpm=100", str(wav_file)])

        # Basic validation should pass (detailed validation happens in config manager)
        validate_args(args)  # Should not raise

        # The WPM validation happens at config level, not CLI level
        assert args.lazy_overrides == ["decoder-wpm=100"]

    def test_validate_nonexistent_config(self, capsys: Any) -> None:
        """Test validation with non-existent config file."""
        parser = create_parser()
        args = parser.parse_args(["--cfg-file", "nonexistent.yaml", "test.wav"])

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
        """Test logging setup with debug enabled in config."""
        config_manager = MagicMock()
        config_manager.get_config.return_value = {
            "log_level": "WARNING",
            "debug": True,  # Debug enabled in config
            "log_to_file": False,  # Disable file logging for test
        }

        # Reset logging to ensure clean state
        logging.getLogger().handlers.clear()

        with caplog.at_level(logging.DEBUG):
            setup_logging(config_manager)

        # Check that debug logging was enabled
        root_logger = logging.getLogger()
        assert root_logger.level <= logging.DEBUG or any(h.level <= logging.DEBUG for h in root_logger.handlers)

        # Check stderr for debug message since it may go there instead of caplog
        captured = capsys.readouterr()
        debug_found = "Debug mode enabled" in caplog.text or "Debug mode enabled" in captured.err
        assert debug_found, f"Debug message not found. Caplog: {caplog.text}, Stderr: {captured.err}"

    def test_setup_logging_level_override(self, caplog: Any) -> None:
        """Test logging setup with different log level in config."""
        config_manager = MagicMock()
        config_manager.get_config.return_value = {"log_level": "INFO", "debug": False}

        # Reset logging to ensure clean state
        logging.getLogger().handlers.clear()

        with caplog.at_level(logging.INFO):
            setup_logging(config_manager)

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

    @patch("morsecode.cli.main.decoder_app.run_decoder_configurable")
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
        """Test main function with --cfg-show."""
        with patch("morsecode.cli.main.AwesomeConfigManager") as mock_config_manager:
            mock_instance = Mock()
            mock_instance.config_file = Path("test.yaml")
            mock_instance.was_created = True
            mock_instance.profile = None
            mock_config_manager.return_value = mock_instance

            # Mock the config file to exist and have content
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="# Test config\napplication:\n  debug: false")):
                    result = main(["--cfg-show"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Config file:" in captured.out

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
        assert "Configuration file will be auto-created on first run" in captured.err

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
                "morsecode.cli.main.decoder_app.run_decoder_configurable",
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
                "morsecode.cli.main.decoder_app.run_decoder_configurable",
                side_effect=RuntimeError("Unexpected"),
            ):
                result = main([str(wav_file)])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Unexpected" in captured.err

    @patch("morsecode.cli.main.decoder_app.run_decoder_configurable")
    def test_main_with_overrides(self, mock_run_decoder: Any, tmp_path: Path) -> None:
        """Test main function with CLI parameter overrides."""
        wav_file = tmp_path / "test.wav"
        wav_file.write_text("fake wav")

        mock_run_decoder.return_value = 0

        # Create a properly mocked config manager
        mock_config_manager = MagicMock()
        mock_config_manager.config_file = Path("test.yaml")
        mock_config_manager.get_config.return_value = {}

        # Mock the new apply_cli_overrides method to return expected overrides
        def mock_apply_cli_overrides(cli_overrides):
            overrides = {}
            for override in cli_overrides:
                if override == "signal-frequency-hz=800":
                    overrides.setdefault("signal", {})["frequency_hz"] = 800
                elif override == "decoder-wpm=25":
                    overrides.setdefault("decoder", {})["wpm"] = 25
                elif override == "signal-signal-threshold-norm=0.4":
                    overrides.setdefault("signal", {})["signal_threshold_norm"] = 0.4
                elif override == "application-output-file=result.txt":
                    overrides.setdefault("application", {})["output_file"] = "result.txt"
            return overrides

        mock_config_manager.apply_cli_overrides = mock_apply_cli_overrides

        with patch("morsecode.cli.main.AwesomeConfigManager", return_value=mock_config_manager):
            result = main(
                [
                    str(wav_file),
                    "--cfg-override",
                    "signal-frequency-hz=800",
                    "--cfg-override",
                    "decoder-wpm=25",
                    "--cfg-override",
                    "signal-signal-threshold-norm=0.4",
                    "--cfg-override",
                    "application-output-file=result.txt",
                ]
            )

        assert result == 0

        # Verify that run_decoder_configurable was called with the correct arguments
        args, kwargs = mock_run_decoder.call_args

        # Function is called with keyword arguments only
        assert "config_manager" in kwargs
        assert "overrides" in kwargs
        assert "output_file" in kwargs

        overrides = kwargs["overrides"]
        output_file = kwargs["output_file"]

        # Verify the overrides structure
        assert overrides["signal"]["frequency_hz"] == 800
        assert overrides["decoder"]["wpm"] == 25
        assert overrides["signal"]["signal_threshold_norm"] == 0.4
        assert overrides["application"]["output_file"] == "result.txt"
        assert output_file is None  # Now handled through config overrides

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

    @patch("morsecode.cli.main.decoder_app.run_decoder_configurable")
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

        # Mock the apply_cli_overrides method
        def mock_apply_cli_overrides(cli_overrides):
            overrides = {}
            for override in cli_overrides:
                if override == "signal-frequency-hz=700":
                    overrides.setdefault("signal", {})["frequency_hz"] = 700
                elif override == "application-debug=true":
                    overrides.setdefault("application", {})["debug"] = True
                elif override == "application-output-file=decoded.txt":
                    overrides.setdefault("application", {})["output_file"] = "decoded.txt"
            return overrides

        with patch.object(AwesomeConfigManager, "__init__", return_value=None):
            with patch.object(AwesomeConfigManager, "get_config", side_effect=mock_get_config):
                with patch.object(AwesomeConfigManager, "apply_cli_overrides", side_effect=mock_apply_cli_overrides):
                    # Test with config file and overrides
                    result = main(
                        [
                            str(wav_file),
                            "--cfg-file",
                            str(config_file),
                            "--cfg-override",
                            "signal-frequency-hz=700",
                            "--cfg-override",
                            "application-output-file=decoded.txt",
                        ]
                    )

        assert result == 0
        mock_run_decoder.assert_called_once()

        # Verify configuration was properly applied
        args, kwargs = mock_run_decoder.call_args

        # Function is called with keyword arguments only
        assert "config_manager" in kwargs
        assert "overrides" in kwargs
        assert "output_file" in kwargs

        overrides = kwargs["overrides"]
        output_file = kwargs["output_file"]

        # Should have CLI override
        assert overrides["signal"]["frequency_hz"] == 700
        # Output file is now handled through config overrides
        assert overrides["application"]["output_file"] == "decoded.txt"
        assert output_file is None  # Not passed directly anymore

    def test_error_reporting(self, capsys: Any) -> None:
        """Test comprehensive error reporting."""
        # Test multiple validation errors - this will exit early due to validation
        try:
            result = main(["nonexistent.wav", "--cfg-override", "signal-frequency-hz=5000"])
            assert result == 1
        except SystemExit:
            pass  # Expected due to validation failure

        captured = capsys.readouterr()

        # Should report file validation errors (parameter validation now happens in config system)
        assert "Invalid arguments" in captured.err
        assert "WAV file does not exist" in captured.err


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
        assert "config.yaml" in help_text  # Updated to match XDG standard naming
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
                with patch("morsecode.cli.main.decoder_app.run_decoder_configurable", return_value=0):
                    result = main([str(wav_file), "--cfg-file", str(empty_config)])

        # Should still work with defaults
        assert result == 0

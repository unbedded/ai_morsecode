"""Updated command-line interface using the new YAML+Schema config system.

This module provides a comprehensive CLI that integrates with the awesome config system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from .. import decoder_app
from ..config.registry import ConfigRegistry

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with simplified structure.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="morsecode",
        description="Morse Code Decoder - Process audio files and extract "
        "decoded text using YAML configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration:
  The decoder uses a YAML configuration file (morse.yaml) with four main sections:
  - app: Application settings (debug, log_level, output_file)
  - audio: Audio processing (sample_rate, chunk_size_ms, wav_filename)
  - signal: Signal processing (frequency, threshold, bandwidth)
  - decoder: Morse decoding (wpm, tolerance, dot_duration_ms)

Profiles:
  Use --profile to activate profile-specific overrides via postfix naming:

  Example morse.yaml with profiles:
    signal:
      frequency: 600           # Default
      frequency_debug: 400     # Used with --profile debug
      frequency_production: 800 # Used with --profile production

Examples:
  morsecode audio.wav                           # Use morse.yaml defaults
  morsecode audio.wav --profile debug           # Use debug profile overrides
  morsecode --config custom.yaml audio.wav     # Use custom config file
  morsecode audio.wav --frequency 800           # Override single parameter
  morsecode --create-config                     # Create sample morse.yaml
        """,
    )

    # Positional arguments
    parser.add_argument(
        "wav_file",
        nargs="?",
        help="Path to WAV audio file to decode",
        type=str,
    )

    # Configuration options
    parser.add_argument(
        "--config",
        "-c",
        metavar="FILE",
        help="YAML configuration file path (default: morse.yaml)",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--profile",
        "-p",
        metavar="NAME",
        help="Configuration profile name (uses postfix overrides like setting_PROFILE)",
        type=str,
        default=None,
    )

    # Utility options
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a sample morse.yaml configuration file and exit",
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration file and exit",
    )

    # Common override options (most frequently used)
    override_group = parser.add_argument_group("Quick Overrides")
    override_group.add_argument(
        "--frequency",
        "-f",
        metavar="HZ",
        help="Override signal frequency in Hz (200-2000)",
        type=int,
    )
    override_group.add_argument(
        "--wpm",
        "-w",
        metavar="WPM",
        help="Override WPM estimate (5-60)",
        type=int,
    )
    override_group.add_argument(
        "--threshold",
        "-t",
        metavar="FLOAT",
        help="Override tone detection threshold (0.0-1.0)",
        type=float,
    )
    override_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (overrides config file)",
    )
    override_group.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Output file for decoded text (overrides config file)",
        type=str,
    )
    override_group.add_argument(
        "--log-level",
        metavar="LEVEL",
        help="Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command line arguments.

    Args:
        args: Parsed arguments to validate

    Raises:
        SystemExit: If validation fails
    """
    errors = []

    # WAV file validation (if provided)
    if args.wav_file:
        wav_path = Path(args.wav_file)
        if not wav_path.exists():
            errors.append(f"WAV file does not exist: {args.wav_file}")
        elif not wav_path.suffix.lower() == ".wav":
            errors.append(f"File must be a WAV file: {args.wav_file}")

    # Override validation
    if args.frequency is not None and not (200 <= args.frequency <= 2000):
        errors.append(f"Frequency must be 200-2000 Hz, got: {args.frequency}")

    if args.threshold is not None and not (0.0 <= args.threshold <= 1.0):
        errors.append(f"Threshold must be 0.0-1.0, got: {args.threshold}")

    if args.wpm is not None and not (5 <= args.wpm <= 60):
        errors.append(f"WPM must be 5-60, got: {args.wpm}")

    # Config file validation (if specified)
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            errors.append(f"Config file does not exist: {args.config}")

    if errors:
        print("Error: Invalid arguments:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def setup_logging(
    config_manager: Any, debug_override: bool = False, log_level_override: str | None = None
) -> None:
    """Configure logging based on configuration.

    Args:
        config_manager: AwesomeConfigManager instance
        debug_override: CLI debug flag override
        log_level_override: CLI log level override
    """
    try:
        app_config = config_manager.get_config("app")
    except Exception:
        app_config = {"log_level": "WARNING", "debug": False}

    # Priority: CLI log level override > debug override > config file
    if log_level_override:
        log_level = log_level_override
    elif debug_override:
        log_level = "DEBUG"
    else:
        log_level = app_config.get("log_level", "WARNING")

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if debug_override or app_config.get("debug", False):
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Optional argument list (for testing)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse arguments
        parser = create_parser()
        args = parser.parse_args(argv)

        # Initialize registry (auto-discovers modules and generates schemas)
        registry = ConfigRegistry()

        # Handle utility commands first
        if args.create_config:
            registry.create_sample_config("morse.yaml")
            print("Sample configuration created: morse.yaml")
            print("Edit this file to customize your settings, then run:")
            print("  morsecode audio.wav")
            return 0

        # Validate basic arguments
        validate_args(args)

        # Initialize configuration manager
        try:
            config_manager = registry.get_config_manager(
                config_file=args.config, profile=args.profile
            )
        except Exception as e:
            print(f"Error: Failed to load configuration - {e}", file=sys.stderr)
            print(
                "Tip: Run 'morsecode --create-config' to create a sample config file",
                file=sys.stderr,
            )
            return 1

        if args.validate_config:
            try:
                # Test loading all module configs
                config_manager.get_config("app")
                config_manager.get_config("audio")
                config_manager.get_config("signal")
                config_manager.get_config("decoder")
                print("Configuration is valid")
                return 0
            except Exception as e:
                print(f"Configuration validation failed: {e}", file=sys.stderr)
                return 1

        # Require WAV file for processing
        if not args.wav_file:
            print("Error: WAV file is required for processing", file=sys.stderr)
            print("Usage: morsecode [options] audio.wav", file=sys.stderr)
            return 1

        # Setup logging
        setup_logging(config_manager, args.debug, args.log_level)

        logger.info("Morse Code Decoder started with registry-based config")
        logger.info("Processing file: %s", args.wav_file)
        if args.profile:
            logger.info("Using profile: %s", args.profile)

        # Get legacy configs for existing modules with CLI overrides
        hal_config = registry.get_legacy_config("audio", config_manager, wav_filename=args.wav_file)
        signal_config = registry.get_legacy_config("signal", config_manager)
        decoder_config = registry.get_legacy_config("decoder", config_manager)

        # Apply CLI overrides to legacy configs
        if args.frequency is not None:
            signal_config["target_frequency_hz"] = args.frequency
        if args.wpm is not None:
            decoder_config["wpm_estimate"] = args.wpm
        if args.threshold is not None:
            signal_config["detection_threshold"] = args.threshold

        # Get app config for output
        app_config = config_manager.get_config("app")
        if args.output is not None:
            app_config["output_file"] = args.output

        # Run the decoder with legacy format
        result: int = decoder_app.run_decoder_legacy(
            hal_config, signal_config, decoder_config, app_config
        )
        return result

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Updated command-line interface using the new YAML+Schema config system.

This module provides a comprehensive CLI that integrates with the awesome config system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from util.config.config_manager import AwesomeConfigManager
from util.config.models import AppConfig, AudioConfig, DecoderConfig, SignalConfig

from .. import decoder_app

logger = logging.getLogger(__name__)


def show_config_info(config_manager: AwesomeConfigManager) -> None:
    """Display configuration file locations and current settings.

    Args:
        config_manager: Initialized config manager instance
    """
    from pathlib import Path

    print("🔧 Morse Code Decoder Configuration")
    print("=" * 50)

    # Show current config file
    current_path = config_manager.config_file
    print(f"📄 Current config file: {current_path}")
    print(f"   Status: {'✨ Auto-created' if config_manager.was_created else '📁 Existing'}")

    if config_manager.profile:
        print(f"   Profile: {config_manager.profile}")

    print()

    # Show all possible locations
    print("📍 Config file search order:")
    search_paths = [
        Path("config/morse.yaml"),
        Path.home() / ".config" / "morsecode" / "config.yaml",
        Path.home() / ".morse.yaml",
    ]

    for i, path in enumerate(search_paths, 1):
        exists = "✅" if path.exists() else "❌"
        current = "← CURRENT" if path == current_path else ""
        print(f"   {i}. {path} {exists} {current}")

    print()

    # Show current settings
    try:
        print("⚙️  Current settings:")
        for module_name in ["app", "audio", "signal", "decoder"]:
            try:
                module_config = config_manager.get_config(module_name)
                print(f"   {module_name}:")
                for key, value in module_config.items():
                    print(f"     {key}: {value}")
            except Exception as e:
                print(f"   {module_name}: Error loading - {e}")
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")

    print()
    print("💡 Tips:")
    print(f"   • Edit config file: {current_path}")
    print("   • Validate config: morsecode --validate-config")
    print("   • Create new config: morsecode --create-config")
    print("   • Use project config: Create 'config/morse.yaml' in current directory")


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with simplified structure.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="morsecode",
        description="Morse Code Decoder - Process audio files and extract decoded text using YAML configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Configuration:
  The decoder automatically creates and uses a YAML configuration file with four main sections:
  - app: Application settings (debug, log_level, output_file)
  - audio: Audio processing (sample_rate, chunk_size_ms, wav_filename)
  - signal: Signal processing (frequency, threshold, bandwidth)
  - decoder: Morse decoding (wpm, tolerance, dot_duration_ms)

Configuration Files (searched in order):
  1. ./config/morse.yaml                        # Project-specific config
  2. ~/.config/morsecode/config.yaml           # User config (auto-created)
  3. ~/.morse.yaml                             # Fallback location

Profiles:
  Use --profile to activate profile-specific overrides via postfix naming:

  Example config with profiles:
    signal:
      frequency: 600           # Default
      frequency_debug: 400     # Used with --profile debug
      frequency_production: 800 # Used with --profile production

Examples:
  morsecode audio.wav                           # Auto-detects/creates config
  morsecode audio.wav --profile debug           # Use debug profile overrides
  morsecode --config custom.yaml audio.wav     # Use custom config file
  morsecode audio.wav --frequency 800           # Override single parameter
  morsecode --show-config                       # Show config locations
  morsecode --create-config                     # Create sample config/morse.yaml
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
        help="YAML configuration file path (default: config/morse.yaml)",
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
        help="Create a sample configuration file (config/morse.yaml in current directory)",
    )

    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Validate configuration file and exit",
    )

    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show configuration file locations and current settings",
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


def setup_logging(config_manager: Any, debug_override: bool = False, log_level_override: str | None = None) -> None:
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

        # Handle utility commands first
        if args.create_config:
            # Use the config manager's create_sample_config method
            config_manager = AwesomeConfigManager()
            output_file = "config/morse.yaml"
            config_manager.create_sample_config(output_file)
            print(f"✅ Sample configuration created: {output_file}")
            print("💡 Edit this file to customize your settings, then run:")
            print("   morsecode audio.wav")
            print(f"   morsecode --config {output_file} audio.wav")
            return 0

        # Validate basic arguments
        validate_args(args)

        # Initialize configuration manager
        try:
            config_manager = AwesomeConfigManager(config_file=args.config, profile=args.profile)

            # Provide user feedback about config location
            if not args.config:  # Only show message for auto-detected configs
                config_path = config_manager.config_file
                if config_manager.was_created:
                    print(f"✨ Created new default configuration: {config_path}")
                    print("💡 Tip: Edit this file to customize your settings")
                elif config_path.name == "config.yaml" and ".config/morsecode" in str(config_path):
                    print(f"📁 Using config: {config_path}")
                elif str(config_path) == "config/morse.yaml":
                    print(f"📁 Using project config: {config_path}")
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
                print("✅ Configuration is valid")
                return 0
            except Exception as e:
                print(f"❌ Configuration validation failed: {e}", file=sys.stderr)
                return 1

        if args.show_config:
            show_config_info(config_manager)
            return 0

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

        # Create typed configs from config manager
        audio_config = AudioConfig.from_config_manager(config_manager)
        signal_config = SignalConfig.from_config_manager(config_manager)
        decoder_config = DecoderConfig.from_config_manager(config_manager)
        app_config = AppConfig.from_config_manager(config_manager)

        # Apply CLI overrides to typed configs
        if args.wav_file:
            audio_config.wav_filename = args.wav_file
        if args.frequency is not None:
            signal_config.frequency = args.frequency
        if args.wpm is not None:
            decoder_config.wpm = args.wpm
        if args.threshold is not None:
            signal_config.threshold = args.threshold
        if args.output is not None:
            app_config.output_file = args.output

        # Run the decoder with typed configs
        result: int = decoder_app.run_decoder_typed(audio_config, signal_config, decoder_config, app_config)
        return result

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Updated command-line interface using the new YAML+Schema config system.

This module provides a comprehensive CLI that integrates with the awesome config system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from util.config.config_manager import AwesomeConfigManager

from .. import decoder_app

# Initialize graphics component FIRST (auto-subscribes to events)
from ..components import graphics  # noqa: F401

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
  morsecode audio.wav --wpm 20                 # Standard usage (adjust WPM to match audio)
  morsecode audio.wav --wpm 13                 # For slower operators
  morsecode pattern.wav --profile debug        # For synthetic test patterns (stricter timing)
  morsecode audio.wav --frequency 600 --profile fixed  # Use exact frequency (no adaptive)
  morsecode --config custom.yaml audio.wav     # Use custom config file
  morsecode audio.wav --signal-threshold 0.3   # Override signal detection threshold
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
        "--signal-threshold",
        metavar="FLOAT",
        help="Override signal detection threshold (0.0-1.0)",
        type=float,
    )
    override_group.add_argument(
        "--timing-tolerance",
        "-t",
        metavar="FLOAT",
        help="Override decoder timing tolerance for dot/dash discrimination (0.0-1.0)",
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

    if args.signal_threshold is not None and not (0.0 <= args.signal_threshold <= 1.0):
        errors.append(f"Signal threshold must be 0.0-1.0, got: {args.signal_threshold}")

    if args.timing_tolerance is not None and not (0.0 <= args.timing_tolerance <= 1.0):
        errors.append(f"Timing tolerance must be 0.0-1.0, got: {args.timing_tolerance}")

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

        # Prepare configuration overrides from CLI arguments
        overrides: dict[str, dict[str, Any]] = {}

        # Audio section overrides
        if args.wav_file:
            overrides.setdefault("audio", {})["wav_filename"] = args.wav_file

        # Signal section overrides
        if args.frequency is not None:
            overrides.setdefault("signal", {})["frequency_hz"] = args.frequency
        if args.signal_threshold is not None:
            overrides.setdefault("signal", {})["signal_threshold_norm"] = args.signal_threshold

        # Decoder section overrides
        if args.wpm is not None:
            overrides.setdefault("decoder", {})["wpm"] = args.wpm
        if args.timing_tolerance is not None:
            overrides.setdefault("decoder", {})["timing_tolerance_norm"] = args.timing_tolerance

        # Run the decoder with ConfigurableBase architecture (simplified, single approach)
        result: int = decoder_app.run_decoder_configurable(
            config_manager=config_manager, overrides=overrides, output_file=args.output
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

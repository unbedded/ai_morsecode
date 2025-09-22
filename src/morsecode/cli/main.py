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
    print("🔧 Morse Code Decoder Configuration")
    print("=" * 50)

    # Show current config file
    current_path = config_manager.config_file
    print(f"📄 Current config file: {current_path}")
    print(f"   Status: {'✨ Auto-created' if config_manager.was_created else '📁 Existing'}")

    if config_manager.profile:
        print(f"   Profile: {config_manager.profile}")

    print()

    # Show config location (simplified)
    print("📍 Configuration:")
    exists = "✅" if current_path.exists() else "❌"
    print(f"   Location: {current_path} {exists}")
    print("   Override with: --cfg-file /path/to/config.yaml")

    print()

    # Show current settings
    try:
        print("⚙️  Current settings:")
        # Try different section names that might exist
        section_mappings = {
            "app": ["app", "application"],
            "audio": ["audio"],
            "signal": ["signal"],
            "decoder": ["decoder"],
            "graphics": ["graphics"],
        }

        for display_name, possible_names in section_mappings.items():
            found_config = None
            found_section = None

            for section_name in possible_names:
                try:
                    config = config_manager.get_config(section_name)
                    if config:  # Only use if not empty
                        found_config = config
                        found_section = section_name
                        break
                except Exception:
                    continue

            if found_config:
                print(f"   {display_name} ({found_section}):")
                for key, value in found_config.items():
                    print(f"     {key}: {value}")
            else:
                print(f"   {display_name}: (no configuration found)")

    except Exception as e:
        print(f"❌ Error reading configuration: {e}")

    print()
    print("💡 Tips:")
    print(f"   • Edit config file: {current_path}")
    print("   • Validate config: morsecode --cfg-validate")
    print("   • Auto-created on first run")
    print("   • Use custom config: morsecode --cfg-file /path/to/config.yaml")


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

Configuration:
  Default: ~/.config/morsecode/config.yaml     # XDG standard location (auto-created)
  Override: --cfg-file /path/to/config.yaml   # Custom config file

Profiles:
  Use --profile to activate profile-specific overrides via postfix naming:

  Example config with profiles:
    signal:
      frequency: 600           # Default
      frequency_debug: 400     # Used with --profile debug
      frequency_production: 800 # Used with --profile production

Examples:
  morsecode audio.wav --dec-wpm 20              # Standard usage (adjust WPM to match audio)
  morsecode audio.wav --dec-wpm 13              # For slower operators
  morsecode pattern.wav --cfg-profile debug    # For synthetic test patterns (stricter timing)
  morsecode audio.wav --sig-freq 600 --cfg-profile fixed  # Use exact frequency (no adaptive)
  morsecode --cfg-file custom.yaml audio.wav   # Use custom config file
  morsecode audio.wav --sig-threshold 0.3      # Override signal detection threshold
  morsecode audio.wav --cfg-set signal.frequency_hz=800  # General override syntax
  morsecode --cfg-show                          # Show config locations
  morsecode --dbg-graphics audio.wav           # Enable real-time signal visualization
  morsecode --dbg-graphics --opt-realtime audio.wav  # Real-time mode with graphics
  morsecode --cfg-set debug_display.backend=braille audio.wav  # Use Braille backend (2x resolution)
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
    config_group = parser.add_argument_group("CONFIGURATION")
    config_group.add_argument(
        "--cfg-file",
        "-c",
        metavar="FILE",
        help="YAML configuration file path (default: ~/.config/morsecode/config.yaml)",
        type=str,
        default=None,
        dest="config",
    )
    config_group.add_argument(
        "--cfg-profile",
        "-p",
        metavar="NAME",
        help="Configuration profile name (uses postfix overrides like setting_PROFILE)",
        type=str,
        default=None,
        dest="profile",
    )
    config_group.add_argument(
        "--cfg-set",
        "-s",
        metavar="SECTION.KEY=VALUE",
        help="Override any configuration parameter (e.g., --cfg-set signal.frequency_hz=800)",
        action="append",
        dest="config_overrides",
    )
    config_group.add_argument(
        "--cfg-validate",
        action="store_true",
        help="Validate configuration file and exit",
        dest="validate_config",
    )
    config_group.add_argument(
        "--cfg-show",
        action="store_true",
        help="Show configuration file locations and current settings",
        dest="show_config",
    )

    # Debug options
    debug_group = parser.add_argument_group("DEBUG")
    debug_group.add_argument(
        "--dbg-enable",
        action="store_true",
        help="Enable debug mode (overrides config file)",
        dest="debug",
    )
    debug_group.add_argument(
        "--dbg-graphics",
        action="store_true",
        help="Enable real-time graphics display (ASCII/Braille) for signal visualization (SSH-friendly)",
        dest="graph_ascii",
    )

    # Common options
    options_group = parser.add_argument_group("OPTIONS")
    options_group.add_argument(
        "--opt-realtime",
        action="store_true",
        help="Process audio in real-time for live debugging (slows down to actual audio speed)",
        dest="real_time",
    )
    options_group.add_argument(
        "--opt-output",
        "-o",
        metavar="FILE",
        help="Output file for decoded text (overrides config file)",
        type=str,
        dest="output",
    )
    options_group.add_argument(
        "--opt-loglevel",
        metavar="LEVEL",
        help="Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        dest="log_level",
    )

    # Quick shortcuts for common overrides (convenience aliases)
    shortcuts_group = parser.add_argument_group("SHORTCUTS")
    shortcuts_group.add_argument(
        "--sig-freq",
        "-f",
        metavar="HZ",
        help="Shortcut for --cfg-set signal.frequency_hz=VALUE (200-2000)",
        type=int,
        dest="frequency",
    )
    shortcuts_group.add_argument(
        "--dec-wpm",
        "-w",
        metavar="WPM",
        help="Shortcut for --cfg-set decoder.wpm=VALUE (5-60)",
        type=int,
        dest="wpm",
    )
    shortcuts_group.add_argument(
        "--sig-threshold",
        metavar="FLOAT",
        help="Shortcut for --cfg-set signal.signal_threshold_norm=VALUE (0.0-1.0)",
        type=float,
        dest="signal_threshold",
    )
    shortcuts_group.add_argument(
        "--dec-tolerance",
        "-t",
        metavar="FLOAT",
        help="Shortcut for --cfg-set decoder.timing_tolerance_norm=VALUE (0.0-1.0)",
        type=float,
        dest="timing_tolerance",
    )

    return parser


def parse_config_override(override_str: str) -> tuple[str, str, str]:
    """Parse a configuration override string.

    Args:
        override_str: String in format "section.key=value"

    Returns:
        Tuple of (section, key, value)

    Raises:
        ValueError: If format is invalid
    """
    if "=" not in override_str:
        raise ValueError(f"Invalid override format: {override_str} (expected: section.key=value)")

    key_path, value = override_str.split("=", 1)

    if "." not in key_path:
        raise ValueError(f"Invalid override format: {override_str} (expected: section.key=value)")

    section, key = key_path.split(".", 1)

    return section, key, value


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

    # Shortcut override validation
    if args.frequency is not None and not (200 <= args.frequency <= 2000):
        errors.append(f"Frequency must be 200-2000 Hz, got: {args.frequency}")

    if args.signal_threshold is not None and not (0.0 <= args.signal_threshold <= 1.0):
        errors.append(f"Signal threshold must be 0.0-1.0, got: {args.signal_threshold}")

    if args.timing_tolerance is not None and not (0.0 <= args.timing_tolerance <= 1.0):
        errors.append(f"Timing tolerance must be 0.0-1.0, got: {args.timing_tolerance}")

    if args.wpm is not None and not (5 <= args.wpm <= 60):
        errors.append(f"WPM must be 5-60, got: {args.wpm}")

    # Config override validation
    if hasattr(args, "config_overrides") and args.config_overrides:
        for override_str in args.config_overrides:
            try:
                section, key, value = parse_config_override(override_str)
                # Basic validation - more detailed validation happens in config manager
                if not section or not key or value == "":
                    errors.append(f"Invalid override: {override_str} (empty section, key, or value)")
            except ValueError as e:
                errors.append(str(e))

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
    """Configure logging based on configuration with embedded system defaults.

    Args:
        config_manager: AwesomeConfigManager instance
        debug_override: CLI debug flag override
        log_level_override: CLI log level override
    """
    from datetime import datetime
    from pathlib import Path

    try:
        app_config = config_manager.get_config("application")
    except Exception:
        app_config = {"log_level": "INFO", "debug": False, "log_to_file": True, "development_mode": True}

    # Read development mode from config (configurable per deployment)
    DEVELOPMENT_MODE = app_config.get("development_mode", True)

    # Priority: CLI log level override > debug override > config file
    if log_level_override:
        log_level = log_level_override
    elif debug_override:
        log_level = "DEBUG"
    else:
        log_level = app_config.get("log_level", "INFO")

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Embedded system: Default to file logging for performance monitoring
    log_to_file = app_config.get("log_to_file", True)
    log_file_path = None

    if log_to_file:
        if DEVELOPMENT_MODE:
            # Development mode: current directory, simple naming
            log_dir_path = Path.cwd()
            log_file_path = log_dir_path / "morsecode-latest.log"
        else:
            # Production mode: proper embedded system logging
            log_dir = app_config.get("log_directory", "/var/log/morsecode")
            try:
                log_dir_path = Path(log_dir)
                log_dir_path.mkdir(parents=True, exist_ok=True)
                # Test write permission
                test_file = log_dir_path / ".write_test"
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                # Fallback to user directory
                log_dir_path = Path.home() / ".local" / "share" / "morsecode" / "logs"
                log_dir_path.mkdir(parents=True, exist_ok=True)

            # Production mode: timestamped naming with rotation
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_file_path = log_dir_path / f"morsecode-{timestamp}.log"

        # Log rotation (only in production mode)
        if not DEVELOPMENT_MODE:
            max_files = app_config.get("log_max_files", 10)
            _rotate_log_files(log_dir_path, max_files)

        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
            filename=str(log_file_path),
            filemode="w",
        )
        print(f"📊 Logs: {log_file_path}")
    else:
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    if debug_override or app_config.get("debug", False):
        logging.getLogger().setLevel(logging.DEBUG)
        # Use root logger directly to ensure debug message is captured
        logging.getLogger().debug("Debug mode enabled")


def _rotate_log_files(log_dir: Path, max_files: int) -> None:
    """Rotate log files keeping only the most recent ones.

    Args:
        log_dir: Directory containing log files
        max_files: Maximum number of log files to keep
    """
    try:
        # Find all morsecode log files
        log_files = list(log_dir.glob("morsecode-*.log"))

        # Sort by modification time (newest first)
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Remove old files beyond the limit
        for old_file in log_files[max_files - 1 :]:  # Keep space for new file
            try:
                old_file.unlink()
                logger.debug(f"Rotated old log file: {old_file}")
            except OSError:
                pass  # Ignore rotation errors
    except Exception:
        pass  # Ignore rotation errors in embedded systems


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

        # Validate basic arguments
        validate_args(args)

        # Initialize configuration manager
        try:
            config_manager = AwesomeConfigManager(config_file=args.config, profile=args.profile)

            # Provide user feedback about config location
            if not args.config:  # Only show message for auto-detected configs
                config_path = config_manager.config_file
                if config_manager.was_created:
                    print(f"✨ Created new configuration: {config_path}")
                    print("💡 Tip: Edit this file to customize your settings")
                else:
                    print(f"📁 Using config: {config_path}")
        except Exception as e:
            print(f"Error: Failed to load configuration - {e}", file=sys.stderr)
            print(
                "Tip: Configuration file will be auto-created on first run",
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

        # Process general config overrides (--set)
        if hasattr(args, "config_overrides") and args.config_overrides:
            for override_str in args.config_overrides:
                try:
                    section, key, value = parse_config_override(override_str)

                    # Auto-convert common value types
                    converted_value: Any = value
                    if value.lower() in ("true", "false"):
                        converted_value = value.lower() == "true"
                    elif value.lower() == "null":
                        converted_value = None
                    else:
                        # Try to convert to number if possible
                        try:
                            if "." in value:
                                converted_value = float(value)
                            else:
                                converted_value = int(value)
                        except ValueError:
                            # Keep as string if not a number
                            converted_value = value

                    overrides.setdefault(section, {})[key] = converted_value
                    logger.info("Config override: %s.%s = %s", section, key, converted_value)
                except ValueError as e:
                    logger.error("Invalid config override: %s", e)
                    print(f"Error: {e}", file=sys.stderr)
                    return 1

        # Process shortcut overrides (convert to general overrides)
        if args.frequency is not None:
            overrides.setdefault("signal", {})["frequency_hz"] = args.frequency
        if args.signal_threshold is not None:
            overrides.setdefault("signal", {})["signal_threshold_norm"] = args.signal_threshold
        if args.wpm is not None:
            overrides.setdefault("decoder", {})["wpm"] = args.wpm
        if args.timing_tolerance is not None:
            overrides.setdefault("decoder", {})["timing_tolerance_norm"] = args.timing_tolerance

        # Run the decoder with ConfigurableBase architecture (simplified, single approach)
        result: int = decoder_app.run_decoder_configurable(
            config_manager=config_manager,
            overrides=overrides,
            output_file=args.output,
            debug_graphics=args.graph_ascii,
            real_time=args.real_time,
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

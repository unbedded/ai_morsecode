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
  The decoder automatically creates and uses a YAML configuration file with multiple sections:
  - application: App settings (debug, log_level, output_file, realtime, playback_speed)
  - graphics: Real-time visualization settings (enabled, backend, display size, refresh rate)
  - signal: Signal processing (frequency, threshold, bandwidth, sample_rate, mode)
  - decoder: Morse decoding (wpm, tolerance, dot_duration_ms)

Configuration File Locations:
  Development: ./config/morse.yaml              # Project-local config (if exists, takes priority)
  Production:  ~/.config/morsecode/config.yaml # XDG standard location (auto-created)
  Override:    --cfg-file /path/to/config.yaml # Custom config file

  Config Mode Control:
    The system automatically detects mode by checking for ./config/morse.yaml:
    - If ./config/morse.yaml exists → Development mode (project-local config used)
    - If ./config/morse.yaml missing → Production mode (XDG user config used)
    - Set application.development_mode: false in config for embedded/production deployment

Profiles:
  Use --profile to activate profile-specific overrides via postfix naming:

  Example config with profiles:
    signal:
      frequency: 600           # Default
      frequency_debug: 400     # Used with --profile debug
      frequency_production: 800 # Used with --profile production

Examples:
  morsecode audio.wav -s decoder-wpm=20                      # Standard usage (adjust WPM to match audio)
  morsecode audio.wav -s decoder-wpm=13                      # For slower operators
  morsecode pattern.wav --cfg-profile debug                  # For synthetic test patterns (stricter timing)
  morsecode --cfg-file custom.yaml audio.wav                 # Use custom config file
  morsecode audio.wav -s signal-signal-threshold-norm=0.3    # Override signal detection threshold
  morsecode audio.wav -s signal-frequency-hz=800             # Override target frequency
  morsecode --cfg-show                                        # Show config file with comments
  morsecode --cfg-bkup-reset2defaults                        # Backup and delete config file (simple reset)
  morsecode audio.wav -s graphics-mode=ascii                 # ASCII graphs (SSH-compatible)
  morsecode audio.wav -s graphics-mode=braille               # High-resolution Braille graphs
  morsecode audio.wav -s graphics-mode=plotly                # Interactive web-based graphs
  morsecode audio.wav -s graphics-mode=pattern               # Simple pattern logging
  morsecode audio.wav -s application-debug=true              # Enable debug mode
  morsecode audio.wav -s application-log-level=DEBUG         # Set debug log level
  morsecode audio.wav -s application-output-file=result.txt  # Save decoded text to file
  morsecode audio.wav -s application-playback-speed=1.0      # Real-time processing (default)
  morsecode audio.wav -s application-playback-speed=0        # Batch mode (as fast as possible)
  morsecode audio.wav -s application-playback-speed=2.0      # 2x faster than real-time

Multiple overrides (comma-separated for convenience):
  morsecode audio.wav -s "signal-frequency-hz=800,decoder-wpm=25,application-debug=true"
  morsecode audio.wav -s "debug-display-backend=plotly,graphics-enabled=true,application-log-level=DEBUG"
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
        "--cfg-override",
        "-s",
        metavar="SECTION-KEY=VALUE",
        help="Override config values (ephemeral - does not modify config file). Supports comma-separated formats",
        action="append",
        dest="lazy_overrides",
    )
    config_group.add_argument(
        "--cfg-show",
        action="store_true",
        help="Show configuration file locations and current settings",
        dest="show_config",
    )
    config_group.add_argument(
        "--cfg-bkup-reset2defaults",
        "-R",
        action="store_true",
        help="Backup and delete config file to restore schema defaults (simple and reliable)",
        dest="reset_config",
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


def setup_logging(config_manager: Any) -> None:
    """Configure logging based on configuration with embedded system defaults.

    Args:
        config_manager: AwesomeConfigManager instance
    """
    from datetime import datetime
    from pathlib import Path

    try:
        app_config = config_manager.get_config("application")
    except Exception:
        app_config = {"log_level": "INFO", "debug": False, "log_to_file": True, "development_mode": True}

    # Read development mode from config (configurable per deployment)
    DEVELOPMENT_MODE = app_config.get("development_mode", True)

    # Log level comes from config file (can be overridden via --cfg-override)
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

    if app_config.get("debug", False):
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

            # Provide user feedback about config location and mode
            if not args.config:  # Only show message for auto-detected configs
                config_path = config_manager.config_file
                # Determine mode
                project_config = Path("config/morse.yaml")
                if project_config.exists():
                    mode_info = "(Development mode - project-local config)"
                else:
                    mode_info = "(Production mode - XDG user config)"

                if config_manager.was_created:
                    print(f"✨ Created new configuration: {config_path} {mode_info}")
                    print("💡 Tip: Edit this file to customize your settings")
                else:
                    print(f"📁 Using config: {config_path} {mode_info}")
        except Exception as e:
            print(f"Error: Failed to load configuration - {e}", file=sys.stderr)
            print(
                "Tip: Configuration file will be auto-created on first run",
                file=sys.stderr,
            )
            return 1

        if args.show_config:
            # Simple approach: just show the actual YAML file with helpful comments
            # Note: Don't register schemas here as it triggers auto-cleanup that removes working config
            config_path = config_manager.config_file
            print(f"📄 Config file: {config_path}")
            if config_path.exists():
                print(f"Status: {'✨ Auto-created' if config_manager.was_created else '📁 Existing'}")
                if config_manager.profile:
                    print(f"Profile: {config_manager.profile}")
                print()
                try:
                    with open(config_path) as f:
                        print(f.read())
                except Exception as e:
                    print(f"❌ Error reading config file: {e}", file=sys.stderr)
                    return 1
            else:
                print("❌ Config file does not exist")
                return 1
            return 0

        if args.reset_config:
            # Simple and reliable: backup and delete config file
            config_path = config_manager.config_file
            print(f"🔄 Backup and delete config file to restore defaults: {config_path}")
            print("⚠️  Config file will be deleted and recreated with schema defaults")
            print("📁 A backup will be created automatically")

            if config_path.exists():
                # Create backup before deletion
                import shutil
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                backup_path = config_path.with_suffix(f".backup-{timestamp}.yaml")
                shutil.copy2(config_path, backup_path)
                print(f"📦 Backup created: {backup_path}")

                # Delete the config file - AwesomeConfigManager will recreate with defaults
                config_path.unlink()
                print("✅ Config file deleted - fresh defaults will be created on next run")
                print(f"💡 To restore previous config: cp {backup_path} {config_path}")
            else:
                print("✅ No config file exists - defaults will be used automatically")
                print("💡 Config file will be created with schema defaults on next run")

            return 0

        # Require WAV file for processing
        if not args.wav_file:
            print("Error: WAV file is required for processing", file=sys.stderr)
            print("Usage: morsecode [options] audio.wav", file=sys.stderr)
            return 1

        # Setup logging (debug and log level handled through config overrides)
        setup_logging(config_manager)

        logger.info("Morse Code Decoder started with registry-based config")
        logger.info("Processing file: %s", args.wav_file)
        if args.profile:
            logger.info("Using profile: %s", args.profile)

        # Prepare configuration overrides from CLI arguments
        overrides: dict[str, dict[str, Any]] = {}

        # Audio section overrides
        if args.wav_file:
            overrides.setdefault("audio", {})["wav_filename"] = args.wav_file

        # Process config overrides through unified system
        if hasattr(args, "lazy_overrides") and args.lazy_overrides:
            try:
                parsed_overrides = config_manager.apply_cli_overrides(args.lazy_overrides)
                for section, section_overrides in parsed_overrides.items():
                    for key, value in section_overrides.items():
                        overrides.setdefault(section, {})[key] = value
                        print(f"🔧 Config override: {section}.{key} = {value}")
            except ValueError as e:
                print(f"❌ {e}", file=sys.stderr)
                return 1

        # Run the decoder with ConfigurableBase architecture
        # All settings now handled through config overrides
        result: int = decoder_app.run_decoder_configurable(
            config_manager=config_manager,
            overrides=overrides,
            output_file=None,  # Handled through config overrides
            debug_graphics=False,  # Handled through config overrides
            real_time=False,  # Handled through config overrides
            playback_speed=1.0,  # Handled through config overrides
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

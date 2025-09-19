"""Centralized logging setup for application startup.

This module provides one-time logging configuration that reads from the
configuration system and sets up appropriate logging for the entire application.

Example usage:
    from util.logging.setup import setup_logging_from_config

    def main():
        # STEP 1: Load config
        cfg_mgr = AwesomeConfigManager("config/morse.yaml")

        # STEP 2: Setup logging ONCE from config
        setup_logging_from_config(cfg_mgr)

        # STEP 3: Create components (loggers already configured!)
        audio_hal = HardwareAbstractionLayer(cfg_mgr)
        signal_processor = SignalProcessor(cfg_mgr)
        decoder = MorseDecoder(cfg_mgr)
"""

import logging
import logging.handlers
import sys
from pathlib import Path

from util.config.config_manager import AwesomeConfigManager


def setup_logging_from_config(cfg_mgr: AwesomeConfigManager, log_file: str | None = None) -> None:
    """Configure logging once at application startup.

    Args:
        cfg_mgr: Configuration manager
        log_file: Optional log file path (default: logs/morse.log)
    """
    try:
        # Get application configuration
        app_cfg = cfg_mgr.get_section("application")

        # Global log level from config
        global_level = app_cfg.get("log_level", "INFO")

        # Setup basic configuration
        _setup_basic_logging(global_level, log_file)

        # Apply per-module overrides
        _apply_module_overrides(app_cfg)

        # Log successful setup
        logger = logging.getLogger(__name__)
        logger.info("Logging configured: global_level=%s", global_level)

    except Exception as e:
        # Fallback to basic logging if config fails
        logging.basicConfig(level=logging.WARNING)
        logger = logging.getLogger(__name__)
        logger.error("Failed to setup logging from config: %s (using fallback)", e)


def _setup_basic_logging(global_level: str, log_file: str | None) -> None:
    """Setup basic logging configuration with console and file handlers."""
    # Convert string level to numeric
    numeric_level = getattr(logging, global_level.upper(), logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_formatter = logging.Formatter("%(levelname)-8s | %(name)-20s | %(message)s")

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        _setup_file_handler(root_logger, log_file, detailed_formatter, numeric_level)


def _setup_file_handler(root_logger: logging.Logger, log_file: str, formatter: logging.Formatter, level: int) -> None:
    """Setup file handler with rotation."""
    try:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler (10MB max, keep 5 files)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        print(f"📁 Log file configured: {log_file}")

    except Exception as e:
        print(f"⚠️  Failed to setup file logging: {e}")


def _apply_module_overrides(app_cfg: dict) -> None:
    """Apply per-module log level overrides from config."""
    # Get logging overrides section
    logging_cfg = app_cfg.get("logging", {})

    if not logging_cfg:
        return

    override_count = 0
    for module_name, level_str in logging_cfg.items():
        try:
            # Convert string level to numeric
            numeric_level = getattr(logging, level_str.upper(), logging.INFO)

            # Set module logger level
            module_logger = logging.getLogger(module_name)
            module_logger.setLevel(numeric_level)

            override_count += 1
            print(f"📝 Module {module_name} log level set to {level_str}")

        except Exception as e:
            print(f"⚠️  Failed to set log level for {module_name}: {e}")

    if override_count > 0:
        print(f"✅ Applied {override_count} module log level overrides")


def setup_basic_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """Setup basic logging without config manager (for utilities/tests).

    Args:
        level: Log level string ("DEBUG", "INFO", "WARNING", "ERROR")
        log_file: Optional log file path
    """
    _setup_basic_logging(level, log_file)


def setup_debug_logging() -> None:
    """Quick setup for debug logging (console only)."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    print("🐛 Debug logging enabled")


def setup_production_logging(log_file: str = "logs/morse_production.log") -> None:
    """Setup production logging (WARNING level, file only).

    Args:
        log_file: Production log file path
    """
    try:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup production logging
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=50 * 1024 * 1024,  # 50MB
                    backupCount=10,
                )
            ],
        )
        print(f"🏭 Production logging configured: {log_file}")

    except Exception as e:
        print(f"❌ Failed to setup production logging: {e}")
        # Fallback to basic console logging
        logging.basicConfig(level=logging.WARNING)


if __name__ == "__main__":
    """Command-line interface for logging setup testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Test logging setup")
    parser.add_argument("--debug", action="store_true", help="Setup debug logging")
    parser.add_argument("--production", action="store_true", help="Setup production logging")
    parser.add_argument("--level", default="INFO", help="Log level")
    parser.add_argument("--file", help="Log file path")

    args = parser.parse_args()

    if args.debug:
        setup_debug_logging()
    elif args.production:
        setup_production_logging(args.file or "logs/test_production.log")
    else:
        setup_basic_logging(args.level, args.file)

    # Test logging
    logger = logging.getLogger("test")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    print("✅ Logging test complete")

"""CLAUDE.md-compliant component logger - application agnostic.

This module provides a simple logging wrapper that automatically enforces
CLAUDE.md logging policies without over-engineering.

Key principles:
- YAGNI: Only implements what's needed now
- CLAUDE.md compliance: Lazy %, security, thread-safety
- Config integration: Simple log level overrides
- Application agnostic: Works for any Python project

Example usage:
    from util.logging import ComponentLogger

    def __init__(self, cfg_mgr):
        # CLAUDE.md: Initialize as first step in constructor
        self.logger = ComponentLogger(__name__, cfg_mgr)

        # All policies auto-enforced, simple and clean
        self.logger.info("Component initialized: rate=%dHz", self.rate_hz)
"""

import logging
import re
import threading

from util.config.config_manager import AwesomeConfigManager


class ComponentLogger:
    """CLAUDE.md-compliant logging wrapper - simple and application agnostic.

    Features (only what's needed now):
    - Lazy % formatting (performance) - automatic
    - Thread-safe logging - built-in locks
    - Security filtering - auto-redacts secrets
    - Config integration - reads application.logging settings
    - Clean API - just the essential logging methods

    YAGNI: No runtime control, no complex patterns, no over-engineering.
    """

    # Security patterns - automatically filtered from all log messages
    _SECRET_PATTERNS = [
        re.compile(r"(?i)(password|passwd|secret|key|token|api_key)[\s=:]+\S+"),
        re.compile(r"(?i)bearer\s+\S+"),
        re.compile(r"(?i)authorization:\s*\S+"),
    ]

    _lock = threading.Lock()  # Thread safety for initialization

    def __init__(self, name: str, cfg_mgr: AwesomeConfigManager | None = None):
        """Initialize logger - designed for first step in constructors.

        Args:
            name: Logger name (typically __name__)
            cfg_mgr: Optional config manager for level configuration
        """
        with self._lock:  # Thread-safe initialization
            self._name = name
            self._logger = logging.getLogger(name)

            # Simple config integration - just read log level override
            if cfg_mgr:
                self._setup_from_config(cfg_mgr)

    def _setup_from_config(self, cfg_mgr: AwesomeConfigManager) -> None:
        """Simple log level setup from config with graceful failure."""
        try:
            app_cfg = cfg_mgr.get_section("application")

            # Check for module-specific override in application.logging section
            logging_cfg = app_cfg.get("logging", {}) or {}
            if logging_cfg and self._name in logging_cfg:
                level = logging_cfg[self._name]
                self._logger.setLevel(level)
                # Use basic print for bootstrap logging to avoid recursion
                print(f"📝 Logger {self._name} configured to {level} from config")

        except Exception:
            # Fail gracefully - logging setup must never break the application
            pass

    def _sanitize_message(self, msg: str) -> str:
        """Auto-sanitize sensitive data from log messages."""
        sanitized = msg
        for pattern in self._SECRET_PATTERNS:
            sanitized = pattern.sub("[REDACTED]", sanitized)
        return sanitized

    def _sanitize_args(self, args: tuple) -> tuple:
        """Sanitize arguments for safe logging."""
        if not args:
            return args

        safe_args = []
        for arg in args:
            # Only sanitize string arguments, preserve numeric types for % formatting
            if isinstance(arg, str):
                safe_args.append(self._sanitize_message(arg))
            else:
                # For non-strings, convert to string, sanitize, but preserve original if no changes
                str_arg = str(arg)
                sanitized_str = self._sanitize_message(str_arg)
                if sanitized_str == str_arg:
                    # No sanitization needed, preserve original type
                    safe_args.append(arg)
                else:
                    # Sanitization occurred, use sanitized string
                    safe_args.append(sanitized_str)
        return tuple(safe_args)

    # CLAUDE.md Policy: Lazy % formatting for performance
    def debug(self, msg: str, *args) -> None:
        """Debug level logging with lazy % formatting."""
        if self._logger.isEnabledFor(logging.DEBUG):  # Lazy evaluation!
            sanitized_msg = self._sanitize_message(msg)
            safe_args = self._sanitize_args(args)
            self._logger.debug(sanitized_msg, *safe_args)

    def info(self, msg: str, *args) -> None:
        """Info level logging with lazy % formatting."""
        if self._logger.isEnabledFor(logging.INFO):
            sanitized_msg = self._sanitize_message(msg)
            safe_args = self._sanitize_args(args)
            self._logger.info(sanitized_msg, *safe_args)

    def warning(self, msg: str, *args) -> None:
        """Warning level logging with lazy % formatting."""
        if self._logger.isEnabledFor(logging.WARNING):
            sanitized_msg = self._sanitize_message(msg)
            safe_args = self._sanitize_args(args)
            self._logger.warning(sanitized_msg, *safe_args)

    def error(self, msg: str, *args) -> None:
        """Error level logging with lazy % formatting."""
        sanitized_msg = self._sanitize_message(msg)
        safe_args = self._sanitize_args(args)
        self._logger.error(sanitized_msg, *safe_args)

    def exception(self, msg: str, *args) -> None:
        """Exception logging with stack trace - CLAUDE.md compliant."""
        sanitized_msg = self._sanitize_message(msg)
        safe_args = self._sanitize_args(args)
        self._logger.exception(sanitized_msg, *safe_args)

    # Property access for compatibility
    @property
    def name(self) -> str:
        """Get logger name."""
        return self._name

    @property
    def level(self) -> int:
        """Get current log level."""
        return self._logger.level

    @property
    def effective_level(self) -> int:
        """Get effective log level (considering parent loggers)."""
        return self._logger.getEffectiveLevel()

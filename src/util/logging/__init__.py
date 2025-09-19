"""Application-agnostic logging utilities for any Python project.

This module provides CLAUDE.md-compliant logging that automatically enforces:
- Lazy % formatting for performance
- Thread-safe operations
- Security (auto-redacts secrets)
- Config integration
- YAGNI: Simple, no over-engineering

Example usage:
    from util.logging import ComponentLogger

    def __init__(self, cfg_mgr):
        # First step in constructor - CLAUDE.md compliant
        self.logger = ComponentLogger(__name__, cfg_mgr)

        # All policies auto-enforced, simple and clean!
        self.logger.info("Component initialized: rate=%d", self.rate_hz)
"""

from .component_logger import ComponentLogger
from .setup import setup_logging_from_config

__all__ = ["ComponentLogger", "setup_logging_from_config"]

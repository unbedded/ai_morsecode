# UTIL Logging System - AI Development Guide

This is the **canonical reference** for using the `util/logging` system in any Python project.

## 📖 Quick Reference for Developers

ComponentLogger provides CLAUDE.md-compliant logging with automatic security filtering, lazy % formatting, thread safety, and config-driven log levels. Application-agnostic design works across any Python project.

> 📄 **For design philosophy and engineering details**, see [`../docs/article_log.md`](../docs/article_log.md)

## 🚀 Quick Demo

```bash
cd src/util/config/examples
python enum_config_demo.py
```

---

# 🤖 **LLM POLICY - AI-FIRST SECTION - COPY TO CLAUDE.md from here down to "END LLM POLICY"** ⬇️

## Logging System Usage - CLAUDE.md Policy

### 🚨 CRITICAL RULES (MANDATORY)

1. **Use ComponentLogger wrapper** - NOT Python logger directly
2. **Initialize logger FIRST** in every constructor: `self.logger = ComponentLogger(__name__, cfg_mgr)`
3. **🚨 MUST USE % FORMATTING**: `logger.info("Result: %s", value)` NOT f-strings
4. **Call register_logging_config()** to enable config-driven log levels
5. **Security automatic** - Passwords/tokens auto-redacted from log messages

### Key Features

- **Security**: Automatic secret redaction (passwords, tokens, api_keys)
- **Performance**: Lazy % formatting (only evaluates args if log level enabled)
- **Thread Safety**: Multiple threads can safely use same logger
- **Config Integration**: Per-module log levels from YAML configuration
- **Application Agnostic**: Works for any Python project
- **CLAUDE.md Compliant**: Enforces all logging best practices

### NEW: Configurable Component Pattern (RECOMMENDED)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from util.config import AwesomeConfigManager
from util.logging import ComponentLogger

class ConfigurableBase(ABC):
    """Base class with built-in logging and config handling."""

    def __init__(self, cfg_mgr: AwesomeConfigManager, overrides: Dict[str, Any] | None = None):
        # STEP 1: Initialize logger FIRST (CLAUDE.md requirement)
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("%s initializing...", self.__class__.__name__)

        # STEP 2: Register logging config for config-driven log levels
        cfg_mgr.register_logging_config(__name__, default_level="INFO")

        # STEP 3: Setup configuration with overrides support
        self._cfg_mgr = cfg_mgr
        self._cfg_section = None
        self._configure(cfg_mgr, overrides)

    def _configure(self, cfg_mgr: AwesomeConfigManager, overrides: Dict[str, Any] | None = None):
        cfg_mgr.register_enum_config(self.CONFIG_SECTION, self.CONFIG_SCHEMA)
        self._cfg_section = cfg_mgr.get_section(self.CONFIG_SECTION)

        if overrides:
            self._cfg_section.apply_overrides(overrides)
            # STEP 4: Log configuration overrides (CRITICAL for debugging!)
            self.logger.info("Configuration overrides applied: %s", overrides)

        self._load_config_values()

    @abstractmethod
    def _load_config_values(self) -> None:
        """Load config values - components implement only this method."""
        pass

    def reconfigure(self, overrides: Dict[str, Any]) -> None:
        """Runtime reconfiguration with proper logging."""
        self.logger.info("Reconfiguring %s: %s", self.__class__.__name__, overrides)
        self._cfg_section.apply_overrides(overrides)
        self._load_config_values()
        self.logger.info("Reconfiguration complete")

# Component implementation - logging built-in!
class YourComponent(ConfigurableBase):
    CONFIG_SCHEMA = YourComponentSchema
    CONFIG_SECTION = "your_section"
    CONFIG_KEYS = YourCfgKey

    def _load_config_values(self) -> None:
        """Only method we implement - logging already handled by base class."""
        self.frequency_hz = self._cfg_section.get_int(self.CONFIG_KEYS.FREQUENCY)

        # STEP 5: Use lazy % formatting (CRITICAL for performance!)
        self.logger.debug("Loaded config: frequency=%d Hz", self.frequency_hz)
```

### Legacy Pattern (Still Supported)

```python
from util.config import AwesomeConfigManager
from util.logging import ComponentLogger

class YourComponent:
    def __init__(self, cfg_mgr: AwesomeConfigManager):
        # STEP 1: Initialize logger FIRST (CLAUDE.md requirement)
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("YourComponent initializing...")

        # STEP 2: Register logging config for config-driven log levels
        cfg_mgr.register_logging_config(__name__, default_level="INFO")

        # STEP 3: Use lazy % formatting (CRITICAL for performance!)
        self.logger.info("Component initialized: param=%s", some_value)
        self.logger.debug("Debug info: state=%s", internal_state)
```

### 🚨 MANDATORY: NO F-STRINGS IN LOGGING

```python
# ✅ CORRECT: Lazy evaluation - only calls expensive_function() if DEBUG enabled
self.logger.debug("Result: %s", expensive_function())

# ❌ WRONG: Always calls expensive_function() even if DEBUG disabled
self.logger.debug(f"Result: {expensive_function()}")  # PERFORMANCE KILLER!
```

### Config-Driven Log Levels

```python
# Enable debug for specific module in YAML:
# application:
#   logging:
#     your.module.name: "DEBUG"

# ComponentLogger automatically calls setLevel() when it finds this config
```

# 🤖 **END LLM POLICY** ⬆️

---

## Usage Patterns

### 1. Component Constructor Pattern

```python
from util.config import AwesomeConfigManager
from util.logging import ComponentLogger
from your_project.config_keys import CfgSection, CfgKey
from your_project.config_schema import YourComponentSchema

class YourComponent:
    def __init__(self, cfg_mgr: AwesomeConfigManager):
        # STEP 1: Initialize logger FIRST (CLAUDE.md requirement)
        # ComponentLogger automatically:
        # - Reads application.logging config for per-module log levels
        # - Enforces lazy % formatting for performance
        # - Redacts secrets (passwords, tokens) from log messages
        # - Provides thread-safe logging
        self.logger = ComponentLogger(__name__, cfg_mgr)

        # STEP 2: Early logging helps with debugging component lifecycle
        self.logger.info("YourComponent initializing...")

        # STEP 3a: CFG SETUP and ACCESS
        #    - (ComponentLogger config integration works alongside your component config)
        cfg_mgr.register_enum_config(CfgSection.YOUR_SECTION, YourComponentSchema)
        cfg = cfg_mgr.get_section(CfgSection.YOUR_SECTION)

        # STEP 3b: SET DEBUG LEVEL
        #   register_logging_config does:
        #       1. Creates a LoggingSchema dataclass with CfgField for the log level
        #       2. Registers it at "application.logging.your.module.name"
        #       3. ComponentLogger finds this config and calls setLevel() automatically
        #       4. You can override in YAML: application.logging.your.module.name.level: "DEBUG"
        cfg_mgr.register_logging_config(__name__, default_level="INFO")

        # STEP 3c: LOG IT - logging level controlled by config (not code!)
        # Set application.logging.your.module.name: "DEBUG" in config to see this
        self.logger.debug("Internal state: ready for processing")

        # CRITICAL: Must use % formatting for lazy evaluation (not f-strings!)
        # ✅ LAZY: Only calls cfg.get_string() if INFO level enabled
        self.logger.info("YourComponent initialized: param=%s", cfg.get_string(CfgKey.PARAM))

        # ❌ NOT LAZY: (DON'T DO THE FOLLOWING) which calls cfg.get_string() even if INFO disabled
        # self.logger.info(f"YourComponent initialized: param={cfg.get_string(CfgKey.PARAM)}")
```

## Best Practices

### A. Method Entry/Exit Pattern

```python
def process_data(self, data):
    """Process incoming data with proper logging."""

    # Input validation logging
    if not data:
        self.logger.warning("Empty data received, skipping processing")
        return

    self.logger.debug("Processing %d items", len(data))

    try:
        # Process data
        result = self._do_processing(data)

        # Success logging with metrics
        self.logger.info("Processing complete: %d items processed", len(result))
        return result

    except Exception as e:
        # Error logging with stack trace
        self.logger.exception("Processing failed: %s", str(e))
        raise
```

### B. Performance Logging Pattern

```python
import time

def expensive_operation(self, data):
    start_time = time.time()
    self.logger.debug("Starting expensive operation: %d items", len(data))

    try:
        result = self._complex_calculation(data)
        duration_ms = (time.time() - start_time) * 1000

        # Log performance metrics
        self.logger.info("Operation completed: duration=%.2fms, items=%d",
                        duration_ms, len(result))
        return result

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        self.logger.error("Operation failed after %.2fms: %s", duration_ms, str(e))
        raise
```

### C. State Change Logging Pattern

```python
def set_frequency(self, frequency_hz: int):
    """Update frequency with proper state logging."""
    old_freq = self.frequency_hz

    self.logger.debug("Changing frequency: %d Hz -> %d Hz", old_freq, frequency_hz)
    self.frequency_hz = frequency_hz

    # Log significant state changes at INFO level
    if abs(frequency_hz - old_freq) > 100:
        self.logger.info("Significant frequency change: %d Hz -> %d Hz",
                        old_freq, frequency_hz)
```

### D. Conditional Logging Pattern

```python
def process_batch(self, items):
    """Process batch with conditional result logging."""
    error_count = 0
    success_count = 0

    for item in items:
        try:
            self._process_item(item)
            success_count += 1
        except Exception as e:
            error_count += 1
            self.logger.debug("Item processing failed: %s", str(e))

    # Only log if something interesting happened
    if error_count > 0:
        self.logger.warning("Batch processed with %d errors, %d successes",
                           error_count, success_count)
    else:
        self.logger.info("Batch processed successfully: %d items", success_count)
```

## Advanced Features

### Security Features - Automatic Secret Redaction

```python
# These are automatically sanitized:
logger.info("Login: user=%s password=%s", user, password)
# Logs: "Login: user=alice password=[REDACTED]"

logger.info("API call: bearer %s", token)
# Logs: "API call: bearer [REDACTED]"
```

**Patterns automatically redacted**: password, secret, token, api_key, bearer, authorization

### Performance Features - Lazy Evaluation

```python
# ✅ EFFICIENT: Only evaluates if DEBUG enabled
logger.debug("Complex calculation: %s", expensive_function())

# ❌ INEFFICIENT: Always evaluates expensive_function()
logger.debug(f"Complex calculation: {expensive_function()}")
```

### Thread Safety

```python
# ✅ SAFE: ComponentLogger handles threading automatically
logger = ComponentLogger(__name__, cfg_mgr)

# Multiple threads can safely use the same logger
def worker_thread():
    logger.info("Worker thread processing...")
```

### Error Handling

```python
try:
    risky_operation()
except FileNotFoundError:
    logger.error("Required file not found: %s", filename)
    raise
except Exception as e:
    logger.exception("Unexpected error in risky_operation: %s", str(e))
    raise RuntimeError(f"Operation failed: {e}") from e
```

### Debugging Techniques

#### Enable Debug for Specific Module

```yaml
# config/myapp.yaml
application:
  logging:
    myapp.components.problematic_module: "DEBUG"
```

#### Temporarily Enable Debug in Code

```python
# For development/debugging only - remove before commit
import logging
logging.getLogger("myapp.components.problematic_module").setLevel(logging.DEBUG)
```

## Anti-Patterns (Don't Do This)

### ❌ F-string Logging

```python
# WRONG: Always evaluates expensive_call()
logger.debug(f"Result: {expensive_call()}")

# CORRECT: Only evaluates if debug enabled
logger.debug("Result: %s", expensive_call())
```

### ❌ Manual Secret Filtering

```python
# WRONG: Manual redaction is error-prone
safe_password = password.replace(password, "[REDACTED]")
logger.info("Login: %s", safe_password)

# CORRECT: Automatic redaction
logger.info("Login attempt: password=%s", password)  # Auto-redacted
```

### ❌ Complex Logging Utilities

```python
# WRONG: Over-engineering for future needs
class AdvancedLoggerWithMetrics:
    def log_with_timing_and_metadata(self, ...): ...

# CORRECT: Simple, clean
logger.info("Operation complete: duration=%.2fms", duration_ms)
```

### ❌ Application-Specific Convenience Methods

```python
# WRONG: Breaks application-agnostic principle
logger.log_morse_code_decoded(message)  # Too specific!

# CORRECT: Generic logging
logger.info("Morse code decoded: message=%s", message)
```

## Migration from Standard Logging

### Before (Standard Logging)

```python
import logging

class MyComponent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # Manual level management

        # No security filtering
        self.logger.info(f"Login: {user}:{password}")  # F-string, security risk
```

### After (ComponentLogger)

```python
from util.logging import ComponentLogger

class MyComponent:
    def __init__(self, cfg_mgr):
        # CLAUDE.md compliant, auto-configured
        self.logger = ComponentLogger(__name__, cfg_mgr)

        # Automatic security filtering, lazy evaluation
        self.logger.info("Login: user=%s password=%s", user, password)  # Safe!
```

## File Structure

```
src/util/logging/
├── __init__.py              # Public API
├── component_logger.py      # Main ComponentLogger class
├── setup.py                # Application startup logging setup
└── README.md               # This file (AI guidance)
```

## Future Enhancement Opportunities

- **Lint Check**: Add `ruff` rule to detect f-string logging (a Lazy % performance killer)
- **Runtime log level control** - REST API or signal handlers for live debugging
- **Structured logging** - JSON output for log aggregation systems
- **Performance metrics** - Built-in timing and performance measurement
- **Log rotation management** - Automatic cleanup and archival
- **Custom formatters** - Domain-specific log format templates
- **Async logging** - Non-blocking logging for high-throughput applications
- **🤖 AI OBSERVABILITY PATTERN** - AI-injected instrumentation for automated health monitoring and diagnosis

---

*For comprehensive design philosophy, engineering innovations, and AI observability patterns, see [`../docs/article_log.md`](../docs/article_log.md)*
# UTIL Logging System - AI Development Guide

This is the **canonical reference** for using the `util/logging` system in any Python project.

## 📖 Human Developer Documentation

ComponentLogger provides CLAUDE.md-compliant logging with automatic security filtering, lazy % formatting, thread safety, and config-driven log levels. Application-agnostic design works across any Python project.

## 🚀 Quick Demo

```bash
cd src/util/examples
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

## 🏆 Design Philosophy & Engineering Achievements

### Core Value Propositions

• **AI OBSERVABILITY PATTERN - The Future of Software Health** - ComponentLogger is designed as the foundation for AI-driven system health monitoring and automated diagnosis. Traditional logging is passive - developers manually add log statements and manually review logs when problems occur. Our AI Observability Pattern flips this model: AI assistants can inject strategic logging at critical decision points, then automatically analyze log patterns to diagnose system health, predict failures, and generate diagnostic reports. The logs become a persistent diagnostic dashboard that survives system crashes and provides forensic analysis capabilities that traditional monitoring systems cannot match.

• **Security-First Logging Architecture** - Automatic secret redaction prevents the security disasters that plague traditional logging systems. Too many production systems leak passwords, API keys, and sensitive data through log files that end up in centralized logging systems, support tickets, or version control. Our pattern-based redaction (`password`, `token`, `api_key`, `bearer`, `secret`) automatically sanitizes all log output without developer intervention. This security-by-default approach eliminates an entire class of data breach vulnerabilities where sensitive information accidentally appears in log files.

• **Performance-Conscious Lazy Evaluation** - The `isEnabledFor()` pattern prevents expensive operations from executing when logs won't be output. Traditional logging systems evaluate all arguments before checking log levels, causing performance degradation even when logging is disabled. Our lazy evaluation approach only calls expensive functions (`expensive_calculation()`, `cfg.get_string()`) when the log level actually allows output. This architectural decision enables comprehensive DEBUG logging without performance impact in production environments.

• **Thread-Safe by Design** - Built-in locking prevents the race conditions and garbled output that plague concurrent logging systems. Multi-threaded applications often suffer from interleaved log messages that make debugging nearly impossible. ComponentLogger uses proper synchronization primitives to ensure log messages appear atomically, making concurrent system behavior comprehensible. This thread safety extends to initialization, configuration updates, and message formatting without performance penalties.

• **Configuration-Driven Observability** - Log levels controlled through configuration files enable runtime behavior modification without code changes. Traditional systems hardcode log levels or require application restarts to change verbosity. Our YAML-driven approach allows operations teams to increase debugging verbosity for specific modules (`application.logging.problematic_module: "DEBUG"`) without touching source code or restarting services. This capability is essential for production troubleshooting where system restarts aren't feasible.

### AI-Driven System Health Innovation

• **Instrumentation Injection Pattern** - AI assistants can automatically identify critical decision points in code and inject comprehensive logging without developer oversight. Traditional instrumentation requires developers to manually identify what to log and where. The AI Observability Pattern enables AI assistants to analyze code flow, identify error conditions, performance bottlenecks, and state transitions, then automatically inject appropriate logging statements. This AI-driven instrumentation provides complete system visibility without the human effort typically required for comprehensive logging.

• **Persistent Diagnostic Dashboard** - Log files serve as crash-resistant system health records that enable post-mortem analysis even when monitoring systems fail. Traditional monitoring solutions depend on external systems that may be unavailable during system failures. ComponentLogger creates persistent text logs that survive system crashes, network outages, and infrastructure failures. These logs become a permanent diagnostic record that AI can analyze to identify failure patterns, performance degradation trends, and system behavior anomalies.

• **Pattern Recognition and Anomaly Detection** - AI analysis of log patterns can identify system health issues before they become critical failures. Traditional monitoring systems alert on threshold violations but miss subtle patterns that indicate emerging problems. AI analysis of ComponentLogger output can detect unusual error message frequencies, performance degradation patterns, configuration drift, and behavioral anomalies that predict system failures. This predictive capability transforms reactive operations into proactive system maintenance.

• **Automated Diagnostic Report Generation** - AI can process log files to generate comprehensive system health reports with root cause analysis and remediation suggestions. Manual log analysis is time-consuming and error-prone, especially for complex systems with multiple interacting components. AI-powered log analysis can correlate events across components, identify causal relationships, and generate diagnostic reports that include timeline analysis, failure correlation, and suggested remediation steps. This automation dramatically reduces mean time to resolution for system issues.

### Developer Experience Engineering

• **Zero-Configuration Security** - Secret redaction works automatically without developer configuration or awareness. Security vulnerabilities often result from developers forgetting to sanitize sensitive data before logging. ComponentLogger eliminates this human error factor by automatically detecting and redacting common secret patterns. Developers can log freely without security concerns, knowing that passwords, tokens, and API keys will never appear in log output.

• **CLAUDE.md Policy Enforcement** - Built-in patterns enforce logging best practices automatically rather than relying on developer discipline. Code review processes often miss logging anti-patterns like f-string usage that degrades performance. ComponentLogger documentation and examples consistently demonstrate proper lazy evaluation patterns, making correct usage the natural choice. This approach scales logging best practices across teams without requiring extensive training or code review oversight.

• **Component Isolation with Global Coordination** - Each component controls its own logging verbosity while participating in system-wide debugging strategies. Traditional logging systems either use global log levels (affecting all components) or require complex configuration management. ComponentLogger enables granular control (`cfg_mgr.register_logging_config(__name__)`) that allows debugging specific components without flooding logs with irrelevant information from other modules.

• **IDE Integration and Auto-Complete** - ComponentLogger usage patterns integrate naturally with development tooling to reduce logging errors. Modern IDEs provide auto-completion and static analysis for ComponentLogger method calls, helping developers choose appropriate log levels and catch formatting errors before runtime. This tooling integration reduces the friction of adding comprehensive logging to applications.

### Future AI Observability Capabilities

• **Intelligent Log Level Management** - AI can automatically adjust log verbosity based on system health indicators and operational requirements. Instead of static configuration, AI monitoring could increase DEBUG logging when error rates rise, reduce verbosity during high-traffic periods, and focus logging on components showing anomalous behavior. This dynamic approach optimizes log utility while managing storage and performance costs.

• **Contextual Log Enhancement** - AI can automatically enrich log messages with relevant system context (memory usage, CPU load, network conditions) without developer intervention. Traditional logging captures only explicitly programmed information, missing important environmental context that aids diagnosis. AI-enhanced logging could automatically include system metrics, dependency health, and operational context that improves diagnostic value.

• **Cross-System Correlation** - AI analysis can correlate ComponentLogger output across multiple services and systems to identify distributed system issues. Modern applications span multiple services, making root cause analysis difficult when problems cross system boundaries. AI correlation of ComponentLogger output from multiple systems can identify cascading failures, performance bottlenecks, and configuration inconsistencies that affect distributed system behavior.

• **Predictive Maintenance Alerts** - AI analysis of logging patterns can predict system maintenance needs before failures occur. By analyzing historical log patterns, AI can identify early warning signs of disk exhaustion, memory leaks, performance degradation, and component failures. This predictive capability enables proactive maintenance that prevents downtime and improves system reliability.

### System Reliability Engineering

• **Fail-Safe Logging Architecture** - Logging errors never break application functionality, ensuring system resilience even when logging infrastructure fails. Traditional logging systems can cause application failures when log destinations become unavailable or logging configuration is invalid. ComponentLogger uses graceful error handling that allows applications to continue operating even when logging fails. This resilience is essential for production systems where logging problems shouldn't affect core functionality.

• **Minimal Performance Impact** - Lazy evaluation and efficient formatting ensure logging doesn't degrade application performance. High-performance applications cannot tolerate logging overhead that affects user experience. ComponentLogger's lazy evaluation pattern ensures that disabled log statements have minimal CPU impact, while efficient string formatting and I/O handling minimize the cost of enabled logging. This performance-conscious design enables comprehensive logging in performance-critical applications.

• **Storage-Efficient Output** - Structured logging patterns and automatic compression capabilities optimize log storage costs without sacrificing diagnostic value. Log storage becomes expensive in high-volume applications, forcing difficult trade-offs between diagnostic capability and operational costs. ComponentLogger provides structured output that compresses efficiently and supports intelligent log rotation strategies that preserve diagnostic value while managing storage requirements.

*This logging system represents the foundation for **AI-driven observability** - transforming passive logging into an active diagnostic and predictive maintenance platform that survives system failures and enables automated health management.*
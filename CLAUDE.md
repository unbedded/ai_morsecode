# CLAUDE.md — Project Memory & Coding Standards

## Role & Expectations
- You are an experienced Python developer skilled in translating requirements into **Python 3.13.5**-compatible code.
- Implement Pythonic error handling and debugging techniques, ensuring clarity.
- Generate comprehensive, efficient, and maintainable pytest test cases following best practices.

## Coding Standards
- Adhere to **PEP8** and use **type hints** consistently.
- Use modern Python built-ins (`list`, `dict`, `tuple`) for type hints when possible.
- Use **named arguments** for functions with multiple parameters.
- Replace magic numbers with **constants**.
- **Follow YAGNI (You Aren't Gonna Need It)** - don't solve problems that don't exist yet.
  - Implement features when needed, not when anticipated
  - Avoid over-engineering for hypothetical future requirements
  - Prefer simple solutions that work now over complex ones for "someday"
- **Include units in variable names** for clarity and safety:
  - **Time**: `duration_ms`, `timeout_sec`, `delay_us`, `interval_ns`
  - **Frequency**: `frequency_hz`, `sample_rate_hz`, `bandwidth_hz`
  - **Quantities**: `retry_count_n`, `buffer_size_bytes`, `max_items_n`
  - **Percentages**: `accuracy_pct`, `threshold_pct` (0-100 range)
  - **Normalized**: `tolerance_norm`, `confidence_norm`, `gain_norm` (0.0-1.0 range)
  - **Ratios**: `success_ratio`, `error_ratio`, `scale_factor` (proportional values)
  - **Distances**: `radius_m`, `offset_px`, `margin_em`
  - **Rates**: `speed_mps`, `throughput_mbps`, `rate_per_sec`
  - Prefer short standard abbreviations: `ms/us/ns`, `hz`, `mb/kb/gb`, `px`, `pct`

## Documentation
- Provide **verbose docstrings** for public classes, methods, and functions.
- Include clear explanations in module headers.
- Add example usage in docstrings where helpful.

## Error Handling
- Use Pythonic `try-except` blocks.
- Raise appropriate built-in or custom exceptions.
- Provide clear and informative error messages.
- Use `logging.exception()` to capture stack traces when errors occur.

## Security
- Never log or expose secrets, API keys, or sensitive data.
- Validate all inputs and sanitize user-provided data.
- Use secure defaults and fail securely.

## Testing Standards
- Generate comprehensive pytest test cases covering edge cases and all possible scenarios.
- Use pytest fixtures appropriately for setup and teardown.
- Use pytest parameterization for concise, readable, and maintainable test cases.
- Ensure tests are deterministic and produce consistent results.
- Test function behavior across wide range of inputs, including extreme and unexpected cases.
- Write descriptive test function names and organize tests logically.
- Include comprehensive docstrings in test files explaining test coverage and expectations.

## Workflow Notes
- Use `.claude/commands/new_module.md` to scaffold modules with tests.
- After edits, run: `make quality && make test-full`.

---

# UTIL Package - AI Assistant Policy

**This project uses a universal UTIL package for configuration and logging.**

## UTIL Discovery & Usage

When working on projects with `src/util/` package, AI assistants MUST:

### 1. Discovery Process
- **Check for UTIL**: Look for `src/util/config/` and `src/util/logging/` directories
- **Read READMEs FIRST**: Always read `src/util/config/README.md` and `src/util/logging/README.md` for current patterns
- **Follow established patterns**: Use existing UTIL components instead of creating new ones

### 2. Configuration System (src/util/config/)
- **Use AwesomeConfigManager** with enum-based schemas
- **Call `cfg_mgr.register_enum_config()`** to register component schemas
- **Call `cfg_mgr.register_logging_config(__name__)`** to enable config-driven log levels
- **Type-safe access**: Use `cfg.get_int()`, `cfg.get_string()`, etc. with enum keys

### 3. Logging System (src/util/logging/)
- **Use ComponentLogger wrapper** instead of Python logger directly
- **Initialize logger FIRST** in every constructor: `self.logger = ComponentLogger(__name__, cfg_mgr)`
- **🚨 MUST USE % FORMATTING**: `logger.info("Result: %s", value)` NOT f-strings
- **Security**: Passwords/tokens automatically redacted
- **Thread-safe**: Multiple threads can safely use same logger

## 🚨 CRITICAL RULES

### NO F-STRINGS IN LOGGING (Performance Killer)
```python
# ✅ CORRECT: Lazy evaluation - only calls expensive_function() if DEBUG enabled
self.logger.debug("Result: %s", expensive_function())

# ❌ WRONG: Always calls expensive_function() even if DEBUG disabled
self.logger.debug(f"Result: {expensive_function()}")  # PERFORMANCE KILLER!
```

### Enum-Based Configuration (No Magic Strings)
```python
# ✅ CORRECT: Type-safe with auto-complete
frequency = cfg.get_int(CfgKey.FREQUENCY)

# ❌ WRONG: Magic strings, no compile-time safety
frequency = config["frequency"]  # Typos not caught!
```

## Configurable Component Pattern (RECOMMENDED)

**NEW: Use ConfigurableBase for components requiring runtime reconfiguration:**

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from util.config import AwesomeConfigManager
from util.logging import ComponentLogger

class IConfigurable(ABC):
    """Interface for components supporting runtime configuration."""
    CONFIG_SCHEMA: Type[Any]
    CONFIG_SECTION: str
    CONFIG_KEYS: Type[Any]

    @abstractmethod
    def reconfigure(self, overrides: Dict[str, Any]) -> None:
        pass

class ConfigurableBase(IConfigurable):
    """Base class eliminating config boilerplate."""

    def __init__(self, cfg_mgr: AwesomeConfigManager, overrides: Dict[str, Any] | None = None):
        # STEP 1: Initialize logger FIRST (required by CLAUDE.md)
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("%s initializing...", self.__class__.__name__)

        self._cfg_mgr = cfg_mgr
        self._cfg_section = None
        self._configure(cfg_mgr, overrides)

    def reconfigure(self, overrides: Dict[str, Any]) -> None:
        """Runtime reconfiguration without recreating component."""
        self._cfg_section.apply_overrides(overrides)
        self._load_config_values()
        self._on_reconfiguration()

    def _configure(self, cfg_mgr: AwesomeConfigManager, overrides: Dict[str, Any] | None = None):
        cfg_mgr.register_enum_config(self.CONFIG_SECTION, self.CONFIG_SCHEMA)
        cfg_mgr.register_logging_config(__name__, default_level="INFO")
        self._cfg_section = cfg_mgr.get_section(self.CONFIG_SECTION)

        if overrides:
            self._cfg_section.apply_overrides(overrides)

        self._load_config_values()

    @abstractmethod
    def _load_config_values(self) -> None:
        """Load config values - only method components must implement."""
        pass

    def _on_reconfiguration(self) -> None:
        """Optional hook for reconfiguration side effects."""
        pass

# Component implementation - minimal boilerplate!
class YourComponent(ConfigurableBase):
    CONFIG_SCHEMA = YourComponentSchema
    CONFIG_SECTION = "your_section"
    CONFIG_KEYS = YourCfgKey

    def _load_config_values(self) -> None:
        """Only method we implement - all boilerplate handled by base class."""
        self.frequency_hz = self._cfg_section.get_int(self.CONFIG_KEYS.FREQUENCY)
        self.threshold = cfg.get_double(CfgKey.THRESHOLD)

        # STEP 5: Global config for cross-cutting concerns (recommended)
        global_cfg = cfg_mgr.get_section("global")
        self.debug = global_cfg.get_bool("debug")              # Debug override
        self.log_level = global_cfg.get_string("log_level")    # Log level override
        self.timeout_ms = global_cfg.get_int("timeout_ms")     # Global timeout

        # STEP 6: Log completion with lazy % formatting (CRITICAL!)
        self.logger.info("YourComponent initialized: freq=%d Hz, threshold=%.2f",
                         self.frequency_hz, self.threshold)

        # STEP 7: Debug logging controlled by config (not code!)
        self.logger.debug("Internal state: ready for processing")
```

**Configuration file example (enables debug for this component):**
```yaml
application:
  logging:
    your_project.components.your_component: "DEBUG"
```

---

**For complete usage patterns and examples, AI assistants should read:**
- `src/util/config/README.md` - **FOCUS ON AI-FIRST SECTION ONLY** (marked "LLM POLICY")
- `src/util/logging/README.md` - **FOCUS ON AI-FIRST SECTION ONLY** (marked "LLM POLICY")

**Note**: The sections below "END LLM POLICY" are human developer documentation and examples. AI assistants should primarily use the AI-FIRST sections for policy guidance, and only reference the human sections when specific implementation details are needed.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
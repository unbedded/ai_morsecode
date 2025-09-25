# UTIL Package - AI Assistant Policy

**Copy this entire section to your project's CLAUDE.md file when using the UTIL package.**

## UTIL Discovery & Usage

When working on projects with `src/util/` package, AI assistants MUST:

### 1. Discovery Process
- **Check for UTIL**: Look for `src/util/config/` and `src/util/logging/` directories
- **Read READMEs FIRST**: Always read `src/util/config/README.md` and `src/util/logging/README.md` for current patterns
- **Follow established patterns**: Use existing UTIL components instead of creating new ones

### 2. Configuration System (src/util/config/)
- **Use AwesomeConfigManager** with enum-based schemas
- **Use ConfigurableBase inheritance** for all components requiring configuration
- **Automatic schema registration**: `cfg_mgr.register_enum_config()` called by ConfigurableBase constructor
- **Automatic logging setup**: `cfg_mgr.register_logging_config()` called by ConfigurableBase constructor
- **Type-safe access**: Use `cfg.get_int()`, `cfg.get_string()`, etc. with enum keys

### 3. Logging System (src/util/logging/)
- **Use ComponentLogger wrapper** instead of Python logger directly
- **Initialize logger FIRST** in every constructor: `self.logger = ComponentLogger(__name__, cfg_mgr)`
- **🚨 MUST USE % FORMATTING**: `logger.info("Result: %s", value)` NOT f-strings
- **Security**: Passwords/tokens automatically redacted
- **Thread-safe**: Multiple threads can safely use same logger

### 4. Graphics System (src/util/graph/) - Optional
- **Use TimeSeriesGraph API** for terminal-based signal visualization
- **SSH-compatible**: ASCII/Braille backends with automatic detection
- **Sample-driven approach**: Use `add_data_point()` without timestamps for consistent scrolling
- **See**: `src/util/graph/README.md` for complete API documentation

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
        self.threshold = self._cfg_section.get_double(self.CONFIG_KEYS.THRESHOLD)

        # STEP 5: Global config for cross-cutting concerns (recommended)
        global_cfg = self._cfg_mgr.get_section("global")
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

## Component Schema Definition

```python
from dataclasses import dataclass
from util.config.types import CfgField, CfgType
from enum import Enum

class YourCfgKey(Enum):
    FREQUENCY = "frequency_hz"
    THRESHOLD = "signal_threshold_norm"
    ADAPTIVE_MODE = "adaptive_mode"

@dataclass
class YourComponentSchema:
    frequency_hz = CfgField(
        type=CfgType.INT,
        default=600,
        min=200,
        max=2000,
        unit="Hz",
        description="Target frequency for processing"
    )

    signal_threshold_norm = CfgField(
        type=CfgType.DOUBLE,
        default=0.25,
        min=0.0,
        max=1.0,
        unit="norm",
        description="Signal detection threshold"
    )

    adaptive_mode = CfgField(
        type=CfgType.BOOL,
        default=True,
        description="Enable adaptive processing mode"
    )
```

## Key Benefits of ConfigurableBase Pattern

- **Minimal Boilerplate**: Components only implement `_load_config_values()`
- **Type Safety**: Enum-based configuration prevents typos
- **Runtime Reconfiguration**: `reconfigure()` method for live updates
- **Automatic Logging**: ComponentLogger initialization handled by base class
- **Schema Integration**: Automatic registration and validation
- **Consistent Patterns**: All components follow identical structure

---

**For complete usage patterns and examples, AI assistants should read:**
- `src/util/config/README.md` - **FOCUS ON AI-FIRST SECTION ONLY** (marked "LLM POLICY")
- `src/util/logging/README.md` - **FOCUS ON AI-FIRST SECTION ONLY** (marked "LLM POLICY")
- `src/util/graph/README.md` - Complete TimeSeriesGraph API reference (when using graphics)

**Note**: The sections below "END LLM POLICY" are human developer documentation and examples. AI assistants should primarily use the AI-FIRST sections for policy guidance, and only reference the human sections when specific implementation details are needed.
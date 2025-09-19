# UTIL Package - AI Assistant Policy

**Copy this entire section to your project's CLAUDE.md file.**

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

## Unified Constructor Pattern

**Standard pattern for any component using UTIL config + logging:**

```python
from util.config import AwesomeConfigManager
from util.logging import ComponentLogger
from your_project.config_keys import CfgSection, CfgKey
from your_project.config_schema import YourComponentSchema

class YourComponent:
    def __init__(self, cfg_mgr: AwesomeConfigManager):
        # STEP 1: Initialize logger FIRST (required by CLAUDE.md)
        self.logger = ComponentLogger(__name__, cfg_mgr)
        self.logger.info("YourComponent initializing...")

        # STEP 2: Register component configuration schema
        cfg_mgr.register_enum_config(CfgSection.YOUR_SECTION, YourComponentSchema)
        cfg = cfg_mgr.get_section(CfgSection.YOUR_SECTION)

        # STEP 3: Register logging config for this component (enables config-driven log levels)
        cfg_mgr.register_logging_config(__name__, default_level="INFO")

        # STEP 4: Access configuration with type safety
        self.frequency_hz = cfg.get_int(CfgKey.FREQUENCY)
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
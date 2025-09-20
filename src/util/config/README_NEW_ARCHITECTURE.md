# UTIL Configuration System - PROPOSED NEW ARCHITECTURE

This document details the proposed new static registration architecture for the `util/config` system that addresses test-friendly design and reduces module complexity.

## 📖 Current Architecture Issues

The current AwesomeConfigManager approach requires:
- Constructor injection of config manager to every component
- Complex initialization ordering (config manager must exist before any component)
- Difficult testing because components depend on heavyweight config manager
- Module constructors become "too hard" to design due to dependency injection

## 🚀 Proposed Static Registration Architecture

### Core Concept

Each module defines its configuration requirements statically, then receives a simple config dictionary in the constructor. The static registration enables automatic schema generation and validation without complex dependency injection.

### Key Benefits

1. **Test-Friendly**: Components receive simple dictionaries, easy to mock and test
2. **Simple Constructors**: No complex dependency injection required
3. **Schema-Driven**: Config generation is driven by static schemas, not hardcoded templates
4. **Backward Compatible**: Can be implemented alongside existing system

---

# 🤖 **LLM POLICY - AI-FIRST SECTION - NEW ARCHITECTURE PATTERN** ⬇️

## New Static Registration Pattern - CLAUDE.md Policy

### 🚨 CRITICAL RULES (PROPOSED)

1. **Static schema registration** - Each module declares CONFIG_SCHEMA and CONFIG_SECTION
2. **Simple constructor injection** - Components receive plain config dictionaries
3. **Unit naming preserved** - `frequency_hz` naming conventions remain mandatory
4. **Type-safe access** - Use helper methods with enum keys for type safety
5. **Global config mixing** - Automatic global config integration for cross-cutting concerns

### Standard Usage Pattern (PROPOSED)

```python
from util.config.types import CfgField, CfgType
from your_project.config_keys import SignalCfgKey
from dataclasses import dataclass

class SignalProcessor:
    # Static registration - enables automatic schema discovery
    CONFIG_SCHEMA = SignalConfigSchema  # Schema for validation and generation
    CONFIG_SECTION = "signal"           # YAML section name
    CONFIG_KEYS = SignalCfgKey          # Enum for type-safe access

    def __init__(self, config_dict):
        # Simple constructor - just receives config dictionary
        # Global config is automatically mixed in by the factory

        # Type-safe access with helper method
        self.frequency_hz = self._get_config_int(config_dict, self.CONFIG_KEYS.FREQUENCY_HZ)
        self.threshold_norm = self._get_config_double(config_dict, self.CONFIG_KEYS.SIGNAL_THRESHOLD_NORM)
        self.adaptive_freq = self._get_config_bool(config_dict, self.CONFIG_KEYS.ADAPTIVE_FREQUENCY)

        # Global config items automatically available
        self.debug = config_dict.get('debug', False)
        self.log_level = config_dict.get('log_level', 'INFO')
        self.timeout_ms = config_dict.get('timeout_ms', 30000)

    def _get_config_int(self, config_dict, key):
        """Type-safe integer access with enum validation."""
        return config_dict[key.value]  # Enum.value provides string key

    def _get_config_double(self, config_dict, key):
        """Type-safe double access with enum validation."""
        return config_dict[key.value]

    def _get_config_bool(self, config_dict, key):
        """Type-safe boolean access with enum validation."""
        return config_dict[key.value]

# Schema definition (same as current system)
@dataclass
class SignalConfigSchema:
    frequency_hz = CfgField(
        type=CfgType.INT,
        default=600,
        min=200,
        max=2000,
        unit="Hz",
        description="Target CW frequency for tone detection"
    )

    signal_threshold_norm = CfgField(
        type=CfgType.DOUBLE,
        default=0.25,
        min=0.0,
        max=1.0,
        unit="norm",
        description="Signal detection threshold"
    )

    adaptive_frequency = CfgField(
        type=CfgType.BOOL,
        default=True,
        description="Enable adaptive frequency detection"
    )
```

### Factory Pattern for Component Creation

```python
from util.config import ConfigFactory

# Factory automatically discovers static registrations
factory = ConfigFactory("config/morse.yaml", profile="debug")

# Components receive merged config (schema defaults + file values + global config)
signal_processor = factory.create_component(SignalProcessor)
audio_handler = factory.create_component(AudioHandler)
decoder = factory.create_component(MorseDecoder)

# Factory handles:
# 1. Schema discovery via static CONFIG_SCHEMA attributes
# 2. Config file loading and validation
# 3. Global config mixing (debug, log_level, timeout_ms, etc.)
# 4. Profile-based overrides
# 5. Component instantiation with merged config dictionary
```

### Automatic Schema Discovery

```python
# ConfigFactory discovers all component schemas automatically
import inspect
from typing import get_type_hints

class ConfigFactory:
    def __init__(self, config_file, profile=None):
        self.config_file = config_file
        self.profile = profile
        self._schemas = {}

    def create_component(self, component_class):
        # Discover static registration
        if not hasattr(component_class, 'CONFIG_SCHEMA'):
            raise ValueError(f"{component_class.__name__} missing CONFIG_SCHEMA")
        if not hasattr(component_class, 'CONFIG_SECTION'):
            raise ValueError(f"{component_class.__name__} missing CONFIG_SECTION")

        schema = component_class.CONFIG_SCHEMA
        section = component_class.CONFIG_SECTION

        # Load and validate config for this section
        config_dict = self._load_section_config(section, schema)

        # Mix in global config
        config_dict.update(self._get_global_config())

        # Create component with simple config dictionary
        return component_class(config_dict)

    def _load_section_config(self, section, schema):
        # Load from YAML file, apply defaults, validate against schema
        # Apply profile overrides (section_key_profile pattern)
        pass

    def _get_global_config(self):
        # Common global settings
        return {
            'debug': False,
            'log_level': 'INFO',
            'timeout_ms': 30000,
            'max_retries': 3
        }
```

### Test-Friendly Design

```python
# Testing becomes trivial - just pass config dictionary
def test_signal_processor():
    config = {
        'frequency_hz': 800,
        'signal_threshold_norm': 0.3,
        'adaptive_frequency': False,
        'debug': True
    }

    processor = SignalProcessor(config)

    assert processor.frequency_hz == 800
    assert processor.threshold_norm == 0.3
    assert processor.adaptive_freq == False
    assert processor.debug == True

# No complex mocking of AwesomeConfigManager required!
```

### Migration Strategy

```python
# Phase 1: Add static registration to existing components
class SignalProcessor:
    # Add static registration
    CONFIG_SCHEMA = SignalConfigSchema
    CONFIG_SECTION = "signal"
    CONFIG_KEYS = SignalCfgKey

    def __init__(self, cfg_mgr_or_dict):
        # Support both old and new patterns during migration
        if isinstance(cfg_mgr_or_dict, AwesomeConfigManager):
            # Old pattern - use existing logic
            cfg_mgr_or_dict.register_enum_config("signal", SignalConfigSchema)
            cfg = cfg_mgr_or_dict.get_section("signal")
            self.frequency_hz = cfg.get_int(SignalCfgKey.FREQUENCY_HZ)
        else:
            # New pattern - use config dictionary
            config_dict = cfg_mgr_or_dict
            self.frequency_hz = self._get_config_int(config_dict, self.CONFIG_KEYS.FREQUENCY_HZ)

# Phase 2: Convert tests to use new pattern
# Phase 3: Convert main application to use ConfigFactory
# Phase 4: Remove old AwesomeConfigManager pattern
```

# 🤖 **END LLM POLICY** ⬆️

---

## Advanced Features (PROPOSED)

### Auto-Generated Configuration

```python
# ConfigFactory generates YAML from static schemas
factory = ConfigFactory()
factory.generate_config_template("config/morse.yaml")

# Generated YAML includes all component schemas:
# signal:
#   frequency_hz: 600         # Target CW frequency | INT (Hz) [200-2000]
#   signal_threshold_norm: 0.25 # Signal detection threshold | DOUBLE (norm) [0.0-1.0]
#   adaptive_frequency: true   # Enable adaptive frequency detection | BOOL
#
# decoder:
#   wpm: 20                   # Words per minute | INT [5-60]
#   timing_tolerance_norm: 0.7 # Timing tolerance | DOUBLE (norm) [0.0-1.0]
#
# global:
#   debug: false              # Debug mode | BOOL
#   log_level: "INFO"         # Log level | STR {"DEBUG","INFO","WARNING","ERROR","CRITICAL"}
```

### Component Discovery

```python
# Factory can discover all components in a package
factory.discover_components("morsecode.components")
config_template = factory.generate_complete_config()

# Automatically finds SignalProcessor, AudioHandler, MorseDecoder, etc.
# Generates complete configuration with all schemas
```

### Global Config Integration

```python
# Global config automatically mixed into every component
global_defaults = {
    'debug': False,
    'log_level': 'INFO',
    'timeout_ms': 30000,
    'max_retries': 3,
    'thread_pool_size': 4
}

# Every component automatically receives global config
# No need to explicitly pass global settings to each component
```

## Key Differences from Current System

| Aspect | Current AwesomeConfigManager | Proposed Static Registration |
|--------|-----------------------------|-----------------------------|
| Constructor | `__init__(self, cfg_mgr)` | `__init__(self, config_dict)` |
| Dependencies | Heavy AwesomeConfigManager | Simple dictionary |
| Testing | Mock complex config manager | Pass simple config dict |
| Registration | Runtime in constructor | Static class attributes |
| Schema discovery | Manual registration calls | Automatic via introspection |
| Config generation | Hardcoded templates | Schema-driven generation |

## Implementation Plan

1. **Create ConfigFactory class** - Implement automatic schema discovery and component creation
2. **Add static registration to existing components** - Backward compatible migration
3. **Update config generation** - Remove hardcoded templates, use schema-driven generation
4. **Convert tests** - Use simple config dictionaries instead of mocking config manager
5. **Convert main application** - Use ConfigFactory instead of direct AwesomeConfigManager
6. **Clean up legacy code** - Remove old patterns once migration complete

## Questions for Review

1. Does this pattern make components easier to test and design?
2. Should global config mixing be automatic or explicit?
3. Are there any missing features from the current system?
4. What about backward compatibility during migration?
5. How should error handling work with the new pattern?

---

*This proposed architecture maintains all the benefits of the current system (type safety, unit naming, validation, auto-generated docs) while making components much simpler to design and test.*
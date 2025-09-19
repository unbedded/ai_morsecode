# Examples Directory

This directory contains example scripts demonstrating the enum-based configuration system and debugging utilities for the Morse Code Decoder project.

## Available Examples

### `enum_config_demo.py` ✅ **Recommended**
**Purpose**: Demonstrates the new enum-based configuration pattern
**Status**: ✅ Working and up-to-date
**Usage**: `python examples/enum_config_demo.py`

**What it shows**:
- Type-safe configuration access using enum keys
- Auto-complete friendly config patterns
- Clean schema registration workflow
- Benefits over legacy string-based config

**Key concepts demonstrated**:
```python
from util.config.types import CfgType, CfgField
from morsecode.components.signal.signal_config_keys import SignalCfgKey, SignalCfgSection

# Type-safe access
frequency = cfg.get_int(SignalCfgKey.FREQUENCY)
threshold = cfg.get_double(SignalCfgKey.THRESHOLD)

# Schema registration
cfg_mgr.register_enum_config(SignalCfgSection.SIGNAL, SignalConfigSchema)
```

### `debug_snippet_issue.py` ⚠️ **Utility Script**
**Purpose**: Debug script for analyzing Morse code audio processing issues
**Status**: ⚠️ Needs updating for new config system
**Usage**: `python examples/debug_snippet_issue.py`

**What it does**:
- Analyzes audio files in `tests/snippets/` directory
- Shows dominant frequencies and audio characteristics
- Tests different signal processing configurations
- Helps debug decoding issues

**Note**: This script uses legacy config patterns and may need updating to work with the new enum-based system.

## Configuration System Overview

The examples demonstrate our **enum-based configuration architecture**:

- **Type Safety**: Enum keys prevent typos and provide auto-complete
- **Unit Validation**: CfgField definitions enforce units and ranges
- **Schema Registration**: Components register their schemas declaratively
- **No Magic Strings**: All configuration keys are compile-time safe

### Migration from Legacy System

The old system used:
- ❌ String-based keys (`"frequency"`, `"threshold"`)
- ❌ JSON schema files for validation
- ❌ Runtime configuration errors

The new system uses:
- ✅ Enum keys (`SignalCfgKey.FREQUENCY`, `SignalCfgKey.THRESHOLD`)
- ✅ CfgField definitions in component schema.py files
- ✅ Compile-time safety and auto-complete

## Running Examples

Make sure you're in the project root directory:

```bash
# Run the enum config demo (recommended)
python examples/enum_config_demo.py

# Run debug utility (if updated)
python examples/debug_snippet_issue.py
```

## For Developers

If you're adding new configuration to components:

1. **Add enum keys** to `components/{component}/keys.py`
2. **Define validation** in `components/{component}/schema.py`
3. **Register schema** in component constructor
4. **Access config** using type-safe methods

See `enum_config_demo.py` for a complete example of this pattern.
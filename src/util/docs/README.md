# Universal Configuration System Documentation

This directory contains documentation and examples for the **Universal Configuration System** - a standalone, reusable configuration framework extracted from the Morse Code Decoder project.

## 📁 Directory Structure

```
src/util/docs/
├── README.md                           # This file - overview and usage
├── examples/                          # Working code examples
│   ├── README.md                      # Examples documentation
│   ├── enum_config_demo.py           # ✅ Demonstrates enum-based config pattern
│   └── debug_snippet_issue.py        # 🔧 Audio analysis utility
├── component-config-interface.md     # Component integration patterns
└── validator-plan.md                # Validation framework design
```

## 🚀 Quick Start

**See the enum-based configuration in action:**

```bash
cd src/util/docs/examples
python enum_config_demo.py
```

## 📖 Documentation Files

### `examples/` - **Working Code Examples**
- **`enum_config_demo.py`** - Complete demonstration of enum-based configuration
- **`debug_snippet_issue.py`** - Practical debugging utility for audio analysis
- **`README.md`** - Detailed examples documentation

### `component-config-interface.md` - **Integration Guide**
- How components should interface with the configuration system
- Best practices for schema definition and registration
- Type-safe configuration access patterns

### `validator-plan.md` - **Validation Framework Design**
- Design document for the validation framework
- CfgField and CfgType system architecture
- Plans for extracting validation as standalone library

## 🎯 Configuration System Features

### **Type Safety & Auto-complete**
```python
from util.config.types import CfgType, CfgField
from morsecode.components.signal.signal_config_keys import SignalCfgKey

# Type-safe access with auto-complete
frequency = cfg.get_int(SignalCfgKey.FREQUENCY)      # IDE knows this returns int
threshold = cfg.get_double(SignalCfgKey.THRESHOLD)   # IDE knows this returns float
```

### **Unit-Aware Validation**
```python
@dataclass
class ConfigSchema:
    frequency = CfgField(
        type=CfgType.INT,
        default=600,
        min=200, max=2000,
        unit="Hz",                    # Unit metadata for validation
        description="CW tone frequency"
    )
```

### **Declarative Schema Registration**
```python
def __init__(self, cfg_mgr):
    # Component registers its schema
    cfg_mgr.register_schema(CfgSection.SIGNAL, ConfigSchema)

    # Get type-safe configuration section
    cfg = cfg_mgr.get_section(CfgSection.SIGNAL)

    # Access with compile-time safety
    self.frequency_hz = cfg.get_int(CfgKey.FREQUENCY)
```

## 🔄 Migration from Legacy Systems

### **Before (Legacy String-based)**
```python
# ❌ Magic strings, no auto-complete, runtime errors
config = {"frequency": 600, "threshold": 0.3}
frequency = config["frequncy"]  # Typo not caught!
```

### **After (Enum-based)**
```python
# ✅ Type-safe enums, auto-complete, compile-time safety
frequency = cfg.get_int(CfgKey.FREQUENCY)  # IDE catches CfgKey.FREQUNCY typos
```

## 🏗️ Architecture Benefits

- **🔒 Type Safety**: Enum keys prevent configuration typos
- **🎯 Auto-complete**: IDEs provide full configuration discovery
- **📏 Unit Safety**: CfgField enforces units and prevents unit conversion errors
- **🔧 Validation**: Min/max constraints and regex patterns built-in
- **📚 Self-documenting**: Schema definitions serve as living documentation
- **🔄 Reusable**: Framework works across any Python project

## 🎯 Design Goals

1. **Mars Climate Orbiter Prevention**: Unit-aware validation prevents unit conversion disasters
2. **Developer Happiness**: Auto-complete and type safety reduce debugging time
3. **Zero Magic Numbers**: All configuration values come from declared schemas
4. **C++ Compatibility**: Patterns translate directly to C++ enum class implementations

## 🚀 Usage in Your Project

To use this configuration system in your own project:

1. **Copy the framework**: `src/util/config/` directory
2. **Define enum keys**: Create `keys.py` with your configuration enums
3. **Define validation**: Create `schema.py` with CfgField definitions
4. **Register schemas**: Call `cfg_mgr.register_schema()` in constructors
5. **Access config**: Use type-safe `get_int()`, `get_double()`, etc.

See `examples/enum_config_demo.py` for a complete working example!

## 📝 Contributing

When adding new features to the configuration system:

1. **Update examples** to demonstrate new capabilities
2. **Document patterns** in the appropriate .md files
3. **Maintain type safety** - all access should be compile-time safe
4. **Add validation** - new field types should have proper CfgField definitions

---

*This configuration system was extracted from the Morse Code Decoder project and designed for universal reuse across Python projects.*
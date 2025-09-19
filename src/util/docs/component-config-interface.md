# Component-Config Interface Best Practices

**Document**: Component Configuration Interface Design
**Version**: 1.0
**Date**: 2025-09-17
**Status**: 📝 Design

## Current Patterns Analysis

### ❌ **Current Issues**

#### 1. **Double Configuration Sources**
```python
# Registry has defaults
registry: {"frequency": {"default": 600}}

# Config models also have defaults
@dataclass
class SignalConfig:
    frequency: int = 600  # Duplicate!
```

#### 2. **Key Mapping Inconsistency**
```python
# Registry uses: "target_frequency_hz"
signal_config = manager.get_config("signal")["target_frequency_hz"]

# Config model uses: "frequency"
SignalConfig(frequency=signal_config)
```

#### 3. **Manual Conversion Boilerplate**
```python
# decoder_app.py - lots of manual mapping
signal_cfg = SignalConfig(
    frequency=signal_config.get("target_frequency_hz", 600),
    threshold=signal_config.get("detection_threshold", 0.3),
    bandwidth=signal_config.get("filter_bandwidth_hz", 50),
)
```

## Best Practice Patterns

### ✅ **Pattern 1: Component Self-Configuration** ⭐ RECOMMENDED

Components interface directly with registry via factory method:

```python
from morsecode.config.registry import ConfigRegistry

class SignalProcessor:
    def __init__(self,
                 config: SignalConfig | None = None,
                 config_manager: AwesomeConfigManager | None = None):
        """Initialize with either explicit config OR config manager."""
        self.logger = logging.getLogger(__name__)

        if config is not None:
            # Explicit config provided (testing/manual setup)
            self._config = config
        elif config_manager is not None:
            # Load from config manager (production)
            self._config = self.from_config_manager(config_manager)
        else:
            # Use defaults (fallback)
            self._config = SignalConfig()

        self._initialize_from_config()

    @classmethod
    def from_config_manager(cls, manager: AwesomeConfigManager) -> SignalConfig:
        """Create SignalConfig from registry configuration."""
        signal_config = manager.get_config("signal")
        return SignalConfig(
            frequency=signal_config["frequency"],
            threshold=signal_config["threshold"],
            bandwidth=signal_config["bandwidth"],
            sample_rate=signal_config["sample_rate"]
        )

    def _initialize_from_config(self):
        """Initialize component from resolved config."""
        self.target_frequency_hz = self._config.frequency
        self.detection_threshold = self._config.threshold
        # ... rest of initialization
```

**Usage:**
```python
# Production: Use registry
config_manager = AwesomeConfigManager()
processor = SignalProcessor(config_manager=config_manager)

# Testing: Use explicit config
test_config = SignalConfig(frequency=800, threshold=0.1)
processor = SignalProcessor(config=test_config)

# Default: Use built-in defaults
processor = SignalProcessor()  # Falls back to SignalConfig defaults
```

### ✅ **Pattern 2: Registry Key Harmonization**

Fix the key mapping inconsistency by aligning registry and models:

```python
# config/registry.py - Use model field names
"config_mapping": {
    "frequency": ("frequency", "frequency", "CW frequency in Hz"),        # ← Consistent!
    "threshold": ("threshold", "threshold", "Detection threshold"),       # ← Consistent!
    "bandwidth": ("bandwidth", "bandwidth", "Filter bandwidth in Hz"),    # ← Consistent!
    "sample_rate": ("sample_rate", "sample_rate", "Audio sample rate"),   # ← Consistent!
}

# config/models.py - Model uses same keys as registry
@dataclass
class SignalConfig:
    frequency: int = None      # Registry will provide default
    threshold: float = None    # Registry will provide default
    bandwidth: int = None      # Registry will provide default
    sample_rate: int = None    # Registry will provide default
```

### ✅ **Pattern 3: Component Factory Pattern**

For complex component initialization:

```python
class ComponentFactory:
    """Factory for creating configured components."""

    def __init__(self, config_manager: AwesomeConfigManager):
        self.config_manager = config_manager

    def create_signal_processor(self) -> SignalProcessor:
        """Create fully configured SignalProcessor."""
        return SignalProcessor(config_manager=self.config_manager)

    def create_audio_hal(self) -> HardwareAbstractionLayer:
        """Create fully configured HAL."""
        return HardwareAbstractionLayer(config_manager=self.config_manager)

    def create_decoder(self) -> MorseDecoder:
        """Create fully configured decoder."""
        return MorseDecoder(config_manager=self.config_manager)

# Usage in application
factory = ComponentFactory(config_manager)
processor = factory.create_signal_processor()
hal = factory.create_audio_hal()
decoder = factory.create_decoder()
```

### ✅ **Pattern 4: Configuration Dependency Injection**

For advanced scenarios with multiple config sources:

```python
from typing import Protocol

class ConfigProvider(Protocol):
    """Protocol for configuration providers."""
    def get_config(self, component_name: str) -> Dict[str, Any]:
        ...

class SignalProcessor:
    def __init__(self, config_provider: ConfigProvider):
        self.logger = logging.getLogger(__name__)
        signal_config = config_provider.get_config("signal")
        self.target_frequency_hz = signal_config["frequency"]
        # ... rest of initialization

# Multiple implementations
class RegistryConfigProvider:
    def __init__(self, manager: AwesomeConfigManager):
        self.manager = manager

    def get_config(self, component_name: str) -> Dict[str, Any]:
        return self.manager.get_config(component_name)

class TestConfigProvider:
    def get_config(self, component_name: str) -> Dict[str, Any]:
        return {"frequency": 800, "threshold": 0.1}  # Test values
```

## Recommended Implementation Strategy

### Phase 1: Harmonize Keys ✅ **START HERE**
1. Update registry to use model field names
2. Remove duplicate defaults from models
3. Make models get defaults from registry

### Phase 2: Add Component Self-Configuration
1. Add `from_config_manager()` class methods to components
2. Update component constructors to accept config_manager
3. Remove manual conversion boilerplate from decoder_app.py

### Phase 3: Factory Pattern (Optional)
1. Create ComponentFactory for complex initialization
2. Move component creation logic to factory
3. Simplify application-level code

## Benefits

### 🎯 **Single Source of Truth**
- Registry owns all defaults
- Components get values directly from registry
- No duplicate configuration

### 🧪 **Better Testing**
```python
# Easy to test with explicit config
test_config = SignalConfig(frequency=TEST_FREQUENCY_ALTERNATE)
processor = SignalProcessor(config=test_config)

# Easy to test with mock registry
mock_manager = MockConfigManager()
processor = SignalProcessor(config_manager=mock_manager)
```

### 🔧 **Flexible Initialization**
```python
# Production
processor = SignalProcessor(config_manager=manager)

# Testing
processor = SignalProcessor(config=test_config)

# Quick defaults
processor = SignalProcessor()
```

### 📦 **Clean Application Code**
```python
# BEFORE: Manual conversion boilerplate
signal_config = manager.get_config("signal")
signal_cfg = SignalConfig(
    frequency=signal_config.get("target_frequency_hz", 600),
    threshold=signal_config.get("detection_threshold", 0.3),
)

# AFTER: Clean component creation
processor = SignalProcessor(config_manager=manager)
```
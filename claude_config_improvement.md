# Proposed CLAUDE.md Configuration Management Enhancement

## Configuration Management
- Use **Pydantic Settings** for type-safe configuration with validation.
- Support multiple config sources: environment variables, `.env` files, and direct instantiation.
- Use secure defaults and validate all configuration values on startup.
- Never include secrets in default values or log configuration containing sensitive data.

### Configuration Architecture Patterns

#### Pattern 1: Shared Configuration Classes
Create shared configuration dataclasses for settings used by multiple modules:

```python
from dataclasses import dataclass
from pydantic import BaseSettings, Field, validator
from typing import Optional

# Shared configuration for cross-module constants
@dataclass
class SharedAudioConfig:
    """Audio settings shared across HAL and signal processing modules."""
    sample_rate_hz: int = 44100
    chunk_size_ms: int = 50

@dataclass
class SharedTimingConfig:
    """Timing settings shared across processing and decoding modules."""
    update_interval_ms: int = 20
    processing_timeout_sec: float = 30.0
```

#### Pattern 2: Module-Specific Configuration
Each module gets its own Pydantic Settings class with shared config composition:

```python
class AudioModuleConfig(BaseSettings):
    """Configuration for audio processing module."""
    # Compose shared config
    audio: SharedAudioConfig = SharedAudioConfig()

    # Module-specific settings
    wav_filename: Optional[str] = Field(default=None, env="AUDIO_WAV_FILE")
    auto_gain_control: bool = Field(default=True)

    class Config:
        env_file = ".env"
        env_prefix = "AUDIO_"

class SignalProcessorConfig(BaseSettings):
    """Configuration for signal processing module."""
    # Reuse same shared config
    audio: SharedAudioConfig = SharedAudioConfig()
    timing: SharedTimingConfig = SharedTimingConfig()

    # Module-specific settings
    target_frequency_hz: int = Field(default=600, description="CW tone frequency")
    detection_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    filter_bandwidth_hz: int = Field(default=50, gt=0)

    @validator('target_frequency_hz')
    def validate_frequency(cls, v):
        if not (200 <= v <= 2000):
            raise ValueError(f'Frequency must be 200-2000 Hz, got {v}')
        return v

    class Config:
        env_file = ".env"
        env_prefix = "SIGNAL_"
```

#### Pattern 3: Configuration Dependency Injection
Pass configuration objects to module constructors, not raw dictionaries:

```python
# BAD: Raw dictionary configuration
processor = SignalProcessor(cfg_dict={
    "sample_rate_hz": 44100,
    "target_frequency_hz": 600,
    "detection_threshold": 0.3
})

# GOOD: Typed configuration object injection
config = SignalProcessorConfig()
processor = SignalProcessor(config=config)

# EVEN BETTER: Shared configuration consistency
shared_audio = SharedAudioConfig(sample_rate_hz=48000)
hal_config = AudioModuleConfig(audio=shared_audio)
processor_config = SignalProcessorConfig(audio=shared_audio)  # Same shared config

hal = AudioModule(config=hal_config)
processor = SignalProcessor(config=processor_config)
```

#### Pattern 4: Application-Level Configuration
Create a main application config that composes all module configs:

```python
class ApplicationConfig(BaseSettings):
    """Main application configuration composing all module configs."""
    # Shared configurations (single source of truth)
    audio: SharedAudioConfig = SharedAudioConfig()
    timing: SharedTimingConfig = SharedTimingConfig()

    # Module configurations
    hal_config: AudioModuleConfig = AudioModuleConfig()
    processor_config: SignalProcessorConfig = SignalProcessorConfig()
    decoder_config: DecoderConfig = DecoderConfig()

    # Application-level settings
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="WARNING", env="LOG_LEVEL")
    config_file: Optional[str] = Field(default=None, env="CONFIG_FILE")

    def __post_init__(self):
        """Ensure shared configs are consistent across modules."""
        self.hal_config.audio = self.audio
        self.processor_config.audio = self.audio
        self.processor_config.timing = self.timing

    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}')
        return v.upper()

    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Configuration Best Practices

#### Initialization Pattern
```python
def create_application(config_file: Optional[str] = None) -> Application:
    """Factory function for creating configured application."""
    # Load configuration
    if config_file:
        config = ApplicationConfig(_env_file=config_file)
    else:
        config = ApplicationConfig()

    # Validate configuration on startup
    try:
        config.dict()  # Triggers validation
    except ValidationError as e:
        logger.error("Configuration validation failed: %s", e)
        raise SystemExit(1)

    # Create modules with injected config
    hal = AudioModule(config=config.hal_config)
    processor = SignalProcessor(config=config.processor_config)
    decoder = Decoder(config=config.decoder_config)

    return Application(hal=hal, processor=processor, decoder=decoder)
```

#### Environment Variable Support
```bash
# Application settings
export DEBUG=true
export LOG_LEVEL=INFO

# Module-specific settings
export AUDIO_WAV_FILE=/path/to/audio.wav
export SIGNAL_TARGET_FREQUENCY_HZ=800
export SIGNAL_DETECTION_THRESHOLD=0.4
```

#### Configuration File Support
```yaml
# config.yaml
audio:
  sample_rate_hz: 48000
  chunk_size_ms: 25

signal_processor:
  target_frequency_hz: 800
  detection_threshold: 0.4
  filter_bandwidth_hz: 75

debug: false
log_level: INFO
```

### Benefits of This Architecture

1. **Single Source of Truth**: Shared configs prevent inconsistencies
2. **Type Safety**: Pydantic validates all configuration at startup
3. **Environment Integration**: Easy deployment configuration via env vars
4. **Module Isolation**: Each module only sees its relevant configuration
5. **Testability**: Easy to create test configurations for different scenarios
6. **Documentation**: Configuration classes serve as living documentation
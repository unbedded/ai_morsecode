# Morse Code Decoder

A comprehensive Python-based Morse code decoding system that processes audio files and extracts decoded text using FFT-based signal analysis and pattern recognition with modern YAML-based configuration.

## Features

- **Complete Audio Pipeline**: Load WAV files → Signal processing → Pattern recognition → Text output
- **Professional Signal Processing**: FFT-based tone detection with configurable filters and SNR analysis
- **Robust Morse Decoding**: Full alphabet support (A-Z, 0-9, punctuation) with timing tolerance
- **YAML Configuration**: Clean, documented configuration with profile support
- **Profile-Based Settings**: Environment-specific overrides (debug, production, testing)
- **Comprehensive Testing**: 241 tests with 77% code coverage
- **Quality Assurance**: Pre-commit hooks, type checking, and automated formatting

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd morsecode

# Install dependencies
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Create sample configuration
morsecode --cfg-show

# Basic decoding
morsecode audio.wav

# With profile and overrides
morsecode audio.wav --profile debug --frequency 800 --output decoded.txt
```

## Command Line Interface

### Command Structure

```
morsecode [GLOBAL_OPTIONS] [CONFIG_OPTIONS] [QUICK_OVERRIDES] [wav_file]

├── Global Options
│   ├── -h, --help              Show help message
│   └── wav_file                 WAV audio file to decode
│
├── Configuration Options
│   ├── --cfg-file, -c FILE        YAML config file (default: ~/.config/morsecode/config.yaml)
│   ├── --profile, -p NAME       Profile for setting overrides
│   ├── --cfg-show          Generate sample ~/.config/morsecode/config.yaml
│   └── --cfg-validate        Validate configuration file
│
└── Quick Overrides
    ├── --frequency, -f HZ       Signal frequency (200-2000 Hz)
    ├── --wpm, -w WPM           WPM estimate (5-60)
    ├── --threshold, -t FLOAT    Tone detection threshold (0.0-1.0)
    ├── --debug                  Enable debug mode
    ├── --output, -o FILE        Output file for decoded text
    └── --log-level LEVEL        Log level (DEBUG|INFO|WARNING|ERROR|CRITICAL)
```

### Usage Examples

```bash
# Basic decoding with default settings
morsecode audio.wav

# Create and use custom configuration
morsecode --cfg-show
morsecode audio.wav --cfg-file ~/.config/morsecode/config.yaml

# Use profile-based settings
morsecode audio.wav --profile debug

# Override specific parameters
morsecode audio.wav --frequency 800 --wpm 20 --threshold 0.4

# Save output and enable debugging
morsecode audio.wav --output decoded.txt --debug --log-level INFO

# Validate configuration
morsecode --cfg-validate --cfg-file custom.yaml
```

## Configuration System

### YAML Configuration Structure

The decoder uses a clean YAML configuration with four main sections:

```yaml
# ~/.config/morsecode/config.yaml
app:
  debug: false
  log_level: WARNING
  output_file: null  # Use stdout

audio:
  sample_rate: 44100
  chunk_size_ms: 50
  wav_filename: null  # Set via CLI argument
  auto_gain_control: true

signal:
  frequency: 600        # CW tone frequency in Hz
  threshold: 0.3        # Detection threshold (0.0-1.0)
  bandwidth: 50         # Filter bandwidth in Hz
  sample_rate: 44100    # Must match audio.sample_rate

decoder:
  wpm: 15               # Words per minute estimate
  tolerance: 0.3        # Timing tolerance (±30%)
  dot_duration_ms: null # Auto-calculate from WPM
  min_silence_ms: 200.0 # Word separation threshold
```

### Profile-Based Configuration

Profiles enable environment-specific overrides using postfix naming:

```yaml
# ~/.config/morsecode/config.yaml with profiles
signal:
  frequency: 600              # Default
  frequency_debug: 400        # Used with --profile debug
  frequency_production: 800   # Used with --profile production
  threshold: 0.3              # Default
  threshold_debug: 0.1        # Lower threshold for debug

app:
  log_level: WARNING          # Default
  log_level_debug: DEBUG      # Debug logging for debug profile
  log_level_production: ERROR # Minimal logging for production
```

```bash
# Use debug profile (frequency=400, threshold=0.1, log_level=DEBUG)
morsecode audio.wav --profile debug

# Use production profile (frequency=800, log_level=ERROR)
morsecode audio.wav --profile production
```

### Configuration Management

```bash
# Generate sample configuration with documentation
morsecode --cfg-show

# Validate configuration file
morsecode --cfg-validate --cfg-file ~/.config/morsecode/config.yaml

# Use custom configuration file
morsecode --cfg-file custom.yaml audio.wav

# Override single parameters
morsecode audio.wav --frequency 700 --wpm 25
```

## Python API Usage

### Modern Typed Configuration

```python
from morsecode.config.models import AudioConfig, SignalConfig, DecoderConfig, AppConfig
from morsecode.decoder_app import run_decoder_typed

# Create typed configurations
audio_config = AudioConfig(
    wav_filename="audio.wav",
    sample_rate=44100,
    chunk_size_ms=50
)

signal_config = SignalConfig(
    frequency=600,
    threshold=0.3,
    bandwidth=50
)

decoder_config = DecoderConfig(
    wpm=15,
    tolerance=0.3
)

app_config = AppConfig(
    debug=False,
    output_file="decoded.txt"
)

# Run decoder
result = run_decoder_typed(audio_config, signal_config, decoder_config, app_config)
```

### Component-Level Usage

```python
from morsecode.components.audio.hal import HardwareAbstractionLayer
from morsecode.components.signal.signal_processor import SignalProcessor
from morsecode.components.decoder.morse_decoder import MorseDecoder
from morsecode.config.models import AudioConfig, SignalConfig, DecoderConfig

# Initialize components with typed configs
hal = HardwareAbstractionLayer(config=AudioConfig(wav_filename="audio.wav"))
processor = SignalProcessor(config=SignalConfig(frequency=600))
decoder = MorseDecoder(config=DecoderConfig(wpm=15))

# Process audio in chunks
while hal.has_data():
    chunk = hal.get_next_chunk(update_interval_ms=20)
    tone_detected = processor.detect_tone(chunk)
    decoder.process_tone_detection(tone_detected, 20.0)

# Get results
decoder.finalize_decoding()
decoded_text = decoder.get_decoded_text()
print(f"Decoded: {decoded_text}")
```

### Configuration Manager Usage

```python
from morsecode.config.manager import AwesomeConfigManager

# Load configuration with profile support
config_manager = AwesomeConfigManager(
    config_file="~/.config/morsecode/config.yaml",
    profile="debug"
)

# Get module-specific configurations
app_config = config_manager.get_config("app")
audio_config = config_manager.get_config("audio")
signal_config = config_manager.get_config("signal")
decoder_config = config_manager.get_config("decoder")

# Create sample configuration
config_manager.create_sample_config("new_~/.config/morsecode/config.yaml")
```

## Architecture

### Core Components

```
morsecode/
├── CLI Interface (cli/main.py)
│   ├── Argument parsing with argparse
│   ├── Configuration management
│   └── Error handling and validation
│
├── Configuration System (config/)
│   ├── manager.py          # YAML loading and profile handling
│   ├── models.py           # Typed configuration classes
│   └── registry.py         # Legacy registry support
│
├── Audio Processing (components/audio/)
│   └── hal.py              # Hardware abstraction layer
│
├── Signal Processing (components/signal/)
│   └── signal_processor.py # FFT-based tone detection
│
├── Morse Decoding (components/decoder/)
│   └── morse_decoder.py    # Pattern recognition
│
├── Main Application (decoder_app.py)
│   ├── Progress reporting
│   ├── Component integration
│   └── Output handling
│
└── Event System (events/)
    ├── bus.py              # Event publishing/subscription
    ├── types.py            # Event type definitions
    └── handlers.py         # Event processing
```

### Configuration Hierarchy

```
Configuration Priority (highest to lowest):
├── 1. CLI Arguments (--frequency 800)
├── 2. Profile Overrides (frequency_debug: 400)
├── 3. YAML File Values (frequency: 600)
└── 4. Schema Defaults (frequency: 600)
```

## Development

### Running Tests

```bash
# Quick test run
pytest tests/ -v

# Test with coverage report
pytest --cov=src/morsecode --cov-report=html tests/

# View coverage report
open tests/htmlcov/index.html

# Run specific test module
pytest tests/test_cli.py -v

# Test configuration management
pytest tests/test_config_manager.py -v
```

### Code Quality

```bash
# Run complete quality pipeline
make quality

# Individual quality checks
make format    # Code formatting with ruff
make lint      # Linting with ruff
make typecheck # Type checking with mypy
```

### Test Coverage Status

Current test coverage: **77%** (241 tests)

#### Coverage by Module:
- **CLI module**: 98% coverage (comprehensive argument parsing and validation)
- **decoder_app module**: 100% coverage (complete integration testing)
- **config.manager module**: 74% coverage (YAML loading and profile handling)
- **HAL module**: 100% coverage (audio file processing)
- **SignalProcessor module**: 93% coverage (FFT and tone detection)
- **MorseDecoder module**: 88% coverage (pattern recognition)

### Project Structure

```
morsecode/
├── src/morsecode/                    # Source code
│   ├── cli/
│   │   └── main.py                   # Command-line interface
│   ├── components/
│   │   ├── audio/
│   │   │   └── hal.py               # Hardware abstraction layer
│   │   ├── signal/
│   │   │   └── signal_processor.py # Signal processing
│   │   ├── decoder/
│   │   │   └── morse_decoder.py    # Morse decoding
│   │   └── factory.py              # Component factory
│   ├── config/
│   │   ├── manager.py              # Configuration management
│   │   ├── models.py               # Typed configuration classes
│   │   └── registry.py             # Legacy support
│   ├── events/
│   │   ├── bus.py                  # Event system
│   │   ├── types.py                # Event definitions
│   │   └── handlers.py             # Event handlers
│   ├── interfaces/                 # Protocol definitions
│   ├── pipeline/                   # Processing pipeline
│   └── decoder_app.py              # Main application
├── tests/                          # Test suite (77% coverage)
│   ├── test_cli.py                 # CLI interface tests
│   ├── test_config_manager.py      # Configuration tests
│   ├── test_decoder_app.py         # Application tests
│   ├── test_hal.py                 # HAL tests
│   ├── test_signal_processor.py    # Signal processing tests
│   ├── test_morse_decoder.py       # Decoder tests
│   ├── test_integration.py         # Integration tests
│   ├── htmlcov/                    # Coverage reports (git ignored)
│   └── README.md                   # Testing documentation
├── docs/                           # Documentation
├── pyproject.toml                  # Project configuration
├── ~/.config/morsecode/config.yaml                      # Sample configuration
└── README.md                       # This file
```

## Technical Details

### Signal Processing Pipeline

1. **Audio Loading**: WAV file processing with format validation
2. **Chunked Processing**: 20ms audio chunks for real-time capability
3. **FFT Analysis**: Frequency domain analysis with windowing
4. **Tone Detection**: Energy-based detection with SNR calculation
5. **Pattern Recognition**: Timing analysis for dot/dash classification
6. **Character Decoding**: Morse code table lookup with error recovery

### Event-Driven Architecture

The system uses an event bus for loose coupling:

```python
# Components publish events
ToneDetectedEvent(detected=True, frequency=600.0, confidence=0.9)
MorsePatternEvent(pattern_type="dot", duration_ms=80.0)
TextDecodedEvent(text="A", pattern_sequence=".-")

# Handlers process events
progress_reporter.handle_tone_detected(event)
logging_handler.handle_error(event)
```

### Configuration Schema Validation

```python
# JSON Schema validation for configuration
{
  "type": "object",
  "properties": {
    "frequency": {
      "type": "number",
      "minimum": 200,
      "maximum": 2000,
      "default": 600
    }
  }
}
```

## Performance

- **Real-time Capable**: Processes 20ms audio chunks efficiently
- **Memory Efficient**: Streaming processing without full file loading
- **Noise Resilient**: Works with realistic signal conditions (SNR > 10dB)
- **Tested Reliability**: 241 comprehensive tests ensure stability

## Migration from Legacy Configuration

If you have existing `.env` files, the YAML configuration provides these benefits:

### Before (Environment Variables)
```bash
# .env file
DEBUG=true
SIGNAL_TARGET_FREQUENCY_HZ=800
DECODER_WPM_ESTIMATE=20
```

### After (YAML Configuration)
```yaml
# ~/.config/morsecode/config.yaml
app:
  debug: true

signal:
  frequency: 800

decoder:
  wpm: 20
```

**Migration Benefits:**
- **Structured**: Organized by component
- **Validated**: Schema validation prevents errors
- **Documented**: Self-documenting with comments
- **Profiles**: Environment-specific overrides
- **Type-safe**: Pydantic model validation

## Contributing

1. Follow the coding standards in `CLAUDE.md`
2. Run quality checks: `make quality`
3. Ensure all tests pass: `pytest tests/`
4. Maintain test coverage above 75%
5. Update documentation for new features
6. Use typed configuration classes for new components

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by HAM radio CW (Continuous Wave) operation
- Built using modern Python practices and comprehensive testing
- YAML configuration system inspired by Kubernetes and Docker Compose
- Event-driven architecture for maintainable, loosely-coupled components
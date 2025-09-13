# Morse Code Decoder

A comprehensive Python-based Morse code decoding system that processes audio files and extracts decoded text using FFT-based signal analysis and pattern recognition.

## Features

- **Complete Audio Pipeline**: Load WAV files → Signal processing → Pattern recognition → Text output
- **Professional Signal Processing**: FFT-based tone detection with configurable filters and SNR analysis
- **Robust Morse Decoding**: Full alphabet support (A-Z, 0-9, punctuation) with timing tolerance
- **Real-time Processing**: Chunked audio processing suitable for streaming applications
- **Comprehensive Testing**: 78 tests covering unit, integration, and edge cases
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

### Command Line Usage

The simplest way to decode Morse code audio files is using the command-line interface:

```bash
# Basic decoding
morsecode audio.wav

# With custom parameters
morsecode audio.wav --wpm 20 --frequency 800 --output decoded.txt

# Using debug mode for troubleshooting
morsecode audio.wav --debug --log-level DEBUG

# With configuration file
morsecode --config morse.env audio.wav
```

### Python API Usage

For programmatic access, use the Python API:

```python
from morsecode.hal import HardwareAbstractionLayer
from morsecode.signal_processor import SignalProcessor
from morsecode.morse_decoder import MorseDecoder

# Initialize components
hal = HardwareAbstractionLayer(cfg_dict={"wav_filename": "audio.wav"})
processor = SignalProcessor(cfg_dict={"target_frequency_hz": 600})
decoder = MorseDecoder(cfg_dict={"wpm_estimate": 15})

# Process audio in chunks
while hal.has_data():
    chunk = hal.get_next_chunk(update_interval_ms=50)
    tone_detected = processor.detect_tone(chunk)
    decoder.process_tone_detection(tone_detected, 50.0)

# Get results
decoder.finalize_decoding()
decoded_text = decoder.get_decoded_text()
print(f"Decoded: {decoded_text}")
```

## Command Line Interface

### Usage

```
morsecode [-h] [--config FILE] [--debug] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
         [--output FILE] [--real-time] [--sample-rate HZ] [--chunk-size MS]
         [--auto-gain] [--no-auto-gain] [--frequency HZ] [--threshold FLOAT]
         [--bandwidth HZ] [--update-interval MS] [--wpm WPM] [--dot-duration MS]
         [--tolerance FLOAT] [--min-silence MS]
         wav_file
```

### Arguments

#### Positional Arguments
- **`wav_file`** - Path to WAV audio file to decode

#### Configuration Options
- **`--config FILE`** - Configuration file path (.env format)
- **`--debug`** - Enable debug mode (default: False)
- **`--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`** - Set logging level (default: WARNING)
- **`--output, -o FILE`** - Output file for decoded text (default: stdout)
- **`--real-time`** - Enable real-time processing mode (default: False)

#### Audio Processing Options
- **`--sample-rate HZ`** - Audio sample rate in Hz (default: 44100)
- **`--chunk-size MS`** - Audio chunk size in milliseconds (default: 50)
- **`--auto-gain`** - Enable automatic gain control (default: True)
- **`--no-auto-gain`** - Disable automatic gain control

#### Signal Processing Options
- **`--frequency, -f HZ`** - Target CW frequency in Hz (default: 600, range: 200-2000)
- **`--threshold, -t FLOAT`** - Tone detection threshold 0.0-1.0 (default: 0.3)
- **`--bandwidth, -b HZ`** - Filter bandwidth in Hz (default: 50)
- **`--update-interval MS`** - Processing update interval in ms (default: 20)

#### Morse Decoder Options
- **`--wpm, -w WPM`** - Initial WPM estimate (default: 15, range: 5-60)
- **`--dot-duration MS`** - Override dot duration in milliseconds (default: auto-detect)
- **`--tolerance FLOAT`** - Timing tolerance for pattern recognition 0.0-1.0 (default: 0.3)
- **`--min-silence MS`** - Minimum silence duration for word separation in ms (default: 200)

### Examples

```bash
# Basic decoding with default settings
morsecode audio.wav

# Decode 20 WPM Morse code at 800 Hz with debug output
morsecode audio.wav --wpm 20 --frequency 800 --debug

# Save decoded text to file with custom threshold
morsecode audio.wav --threshold 0.2 --output decoded.txt

# Use configuration file and override specific parameters
morsecode --config morse.env audio.wav --frequency 700

# Process with tight timing tolerance for clean signals
morsecode audio.wav --tolerance 0.1 --min-silence 150
```

### Environment Variables

All configuration options can be set via environment variables:

#### General Settings
- `DEBUG` - Enable debug mode
- `LOG_LEVEL` - Set logging level
- `CONFIG_FILE` - Configuration file path
- `OUTPUT_FILE` - Output file path
- `REAL_TIME` - Enable real-time mode

#### Hardware Abstraction Layer
- `HAL_WAV_FILE` - WAV file path
- `HAL_AUTO_GAIN` - Auto gain control

#### Signal Processing
- `SIGNAL_TARGET_FREQUENCY_HZ` - Target CW frequency
- `SIGNAL_DETECTION_THRESHOLD` - Tone detection threshold
- `SIGNAL_FILTER_BANDWIDTH_HZ` - Filter bandwidth

#### Morse Decoder
- `DECODER_WPM_ESTIMATE` - WPM estimate
- `DECODER_DOT_DURATION_MS` - Dot duration override
- `DECODER_DETECTION_TOLERANCE` - Timing tolerance
- `DECODER_MIN_SILENCE_DURATION_MS` - Minimum silence duration

### Configuration Files

Create a `.env` file for persistent configuration:

```bash
# morse.env
DEBUG=true
LOG_LEVEL=INFO
SIGNAL_TARGET_FREQUENCY_HZ=800
SIGNAL_DETECTION_THRESHOLD=0.2
DECODER_WPM_ESTIMATE=20
DECODER_DETECTION_TOLERANCE=0.25
```

Then use with: `morsecode --config morse.env audio.wav`

## Architecture

### Core Modules

1. **HardwareAbstractionLayer** (`src/morsecode/hal.py`)
   - Audio file loading and chunked data processing
   - Configurable sample rates and audio formats
   - Thread-safe with comprehensive error handling

2. **SignalProcessor** (`src/morsecode/signal_processor.py`)
   - FFT-based frequency domain analysis
   - Configurable tone detection with SNR calculations
   - Band-pass filtering and noise reduction

3. **MorseDecoder** (`src/morsecode/morse_decoder.py`)
   - Dot/dash pattern recognition with timing analysis
   - Complete Morse code alphabet (A-Z, 0-9, punctuation)
   - WPM estimation and adaptive timing tolerance

### Configuration

Each module accepts a configuration dictionary for customization:

```python
# HAL Configuration
hal_cfg = {
    "wav_filename": "path/to/audio.wav",
    "sample_rate_hz": 44100
}

# Signal Processor Configuration
signal_cfg = {
    "sample_rate_hz": 44100,
    "target_frequency_hz": 600,  # CW tone frequency
    "detection_threshold": 0.3,
    "filter_bandwidth_hz": 50
}

# Decoder Configuration
decoder_cfg = {
    "wpm_estimate": 15,
    "dot_duration_ms": 80,
    "detection_tolerance": 0.3  # 30% timing tolerance
}
```

## Development

### Running Tests

```bash
# Quick test run
make test

# Full test suite with coverage
make test-full

# Run specific test module
pytest tests/test_morse_decoder.py -v
```

### Code Quality

```bash
# Run complete quality pipeline
make quality

# Individual quality checks
make format    # Code formatting
make lint      # Linting
make typecheck # Type checking
```

### Project Structure

```
morsecode/
├── src/morsecode/           # Source code
│   ├── hal.py              # Hardware abstraction layer
│   ├── signal_processor.py # FFT and signal analysis
│   └── morse_decoder.py    # Pattern recognition and decoding
├── tests/                   # Test suite
│   ├── test_hal.py         # HAL unit tests
│   ├── test_signal_processor.py # Signal processing tests
│   ├── test_morse_decoder.py    # Decoder tests
│   ├── test_integration.py      # Integration tests
│   └── data/               # Test audio files
├── docs/                   # Documentation
│   └── project-plan.md     # Development roadmap
└── proto/                  # Legacy prototype (reference)
```

## Test Data

The project includes real Morse code audio samples for validation:

- **10-30 WPM samples**: Various speeds for testing
- **Expected outputs**: `.txt` files with known decoded text
- **Integration tests**: Synthetic signal generation for controlled testing

## Technical Details

### Signal Processing Pipeline

1. **Audio Loading**: WAV file processing with automatic format conversion
2. **FFT Analysis**: Frequency domain analysis with windowing
3. **Tone Detection**: Energy-based detection with configurable thresholds
4. **Pattern Recognition**: Timing analysis for dot/dash classification
5. **Character Decoding**: Morse code table lookup with error handling

### Timing Analysis

- **Adaptive WPM**: Automatic speed detection from signal timing
- **Tolerance Handling**: Configurable timing variations (default ±30%)
- **Boundary Detection**: Character and word spacing recognition
- **Error Recovery**: Graceful handling of unknown patterns

## Performance

- **Real-time Capable**: Processes 20ms audio chunks efficiently
- **Memory Efficient**: Streaming processing without full file loading
- **Noise Resilient**: Works with realistic signal conditions
- **Tested Coverage**: 78 comprehensive tests ensure reliability

## Contributing

1. Follow the coding standards in `CLAUDE.md`
2. Run quality checks: `make quality`
3. Ensure all tests pass: `make test-full`
4. Update documentation for new features

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by HAM radio CW (Continuous Wave) operation
- Built using modern Python practices and comprehensive testing
- Designed for both educational and practical applications
# Morse Code Decoder Project Plan

## Overview
This project implements a complete Morse code decoder system that can process audio files and extract decoded text. The system is built in Python with a modular architecture supporting real-time audio processing and comprehensive testing.

## Project Status
- **Current Branch**: `port-proto`
- **Base Branch**: `main`
- **Phase**: Code porting and test infrastructure setup

## Architecture Components

### 1. Hardware Abstraction Layer (HAL) - `src/morsecode/hal.py`
**Status**: ✅ Implemented and tested
- Handles audio file loading and chunked data processing
- Supports WAV file format with configurable parameters
- Provides thread-safe logging and error handling
- **Key Features**:
  - Configurable audio rate (default: 44.1kHz)
  - Chunked audio data retrieval for real-time processing
  - Automatic stereo-to-mono conversion
  - Comprehensive error handling and logging

### 2. Test Infrastructure
**Status**: ✅ Established
- **Unit Tests**: `tests/test_hal.py` - HAL module testing with synthetic data
- **Test Data**: `tests/data/` - Real Morse code audio files with expected outputs
- **Integration Tests**: Pending implementation

### 3. Test Data Collection
**Status**: ✅ Organized
```
tests/data/
├── 220112_10WPM.wav/txt    # 10 WPM Morse samples
├── 240110_13WPM.wav/txt    # 13 WPM Morse samples
├── 240110_15WPM.wav/txt    # 15 WPM Morse samples
├── 131210_20WPM.wav/txt    # 20 WPM Morse samples
├── 240109_25WPM.wav/txt    # 25 WPM Morse samples
├── 240109_30WPM.wav/txt    # 30 WPM Morse samples
└── kph-night-of-nights.wav # Long-form test sample
```

## Development Phases

### Phase 1: Foundation ✅ COMPLETED
- [x] Set up project structure with proper Python packaging
- [x] Implement HAL module with comprehensive error handling
- [x] Create unit test framework with pytest
- [x] Organize test data in proper directory structure
- [x] Establish coding standards and documentation requirements

### Phase 2: Core Signal Processing 🔄 IN PROGRESS
- [ ] Implement FFT-based signal analysis
- [ ] Add tone detection and filtering algorithms
- [ ] Create configurable detection thresholds
- [ ] Implement noise reduction capabilities
- [ ] Add comprehensive unit tests for signal processing

### Phase 3: Morse Code Decoding 📋 PENDING
- [ ] Implement dot/dash pattern recognition
- [ ] Add timing analysis for WPM detection
- [ ] Create Morse code lookup tables and translation
- [ ] Handle variable spacing and timing irregularities
- [ ] Add character and word boundary detection

### Phase 4: Integration & Testing 📋 PENDING
- [ ] Create integration tests using real audio samples
- [ ] Implement end-to-end system tests
- [ ] Add performance benchmarking
- [ ] Create test cases for various WPM speeds (10-30 WPM)
- [ ] Validate accuracy against known text outputs

### Phase 5: Configuration & CLI 📋 PENDING
- [ ] Implement Pydantic-based configuration system
- [ ] Add command-line interface
- [ ] Create configuration file support
- [ ] Add batch processing capabilities
- [ ] Implement output format options

### Phase 6: Optimization & Documentation 📋 PENDING
- [ ] Performance optimization and profiling
- [ ] Memory usage optimization for large files
- [ ] Comprehensive API documentation
- [ ] User guide and examples
- [ ] Performance benchmarks and metrics

## Testing Strategy

### Unit Tests
- **Target**: Individual module functionality
- **Data**: Synthetic audio signals with known patterns
- **Coverage**: All public APIs and error conditions
- **Framework**: pytest with comprehensive fixtures

### Integration Tests
- **Target**: Module interaction and data flow
- **Data**: Short real audio samples (10-15 seconds)
- **Coverage**: HAL → Signal Processing → Decoding pipeline
- **Validation**: Compare against expected partial outputs

### System Tests
- **Target**: Complete end-to-end functionality
- **Data**: Full-length real audio files with known text
- **Coverage**: All WPM speeds, various audio conditions
- **Validation**: Compare final decoded text against expected outputs

## Configuration Architecture

### Current Approach
- Dictionary-based configuration passed to modules
- Default values defined as module constants
- Basic parameter validation in constructors

### Planned Enhancement
- Pydantic Settings for type-safe configuration
- Environment variable and .env file support
- Comprehensive validation with clear error messages
- Hierarchical configuration with inheritance

## Quality Assurance

### Code Standards
- **Style**: PEP8 compliance with type hints
- **Documentation**: Verbose docstrings with examples
- **Logging**: Thread-safe logging with appropriate levels
- **Error Handling**: Pythonic exception handling with context

### Continuous Integration
- **Linting**: `make quality` (includes formatting and type checking)
- **Testing**: `make test-full` (comprehensive test suite)
- **Coverage**: Track test coverage metrics
- **Performance**: Monitor processing speed and memory usage

## Current Priorities

1. **Signal Processing Implementation** - Core FFT and tone detection
2. **Integration Test Framework** - Validate module interactions
3. **Configuration System** - Pydantic-based type-safe configuration
4. **Morse Decoding Logic** - Pattern recognition and translation

## Recovery Context

If context is lost, key files to review:
- `CLAUDE.md` - Coding standards and workflow
- `src/morsecode/hal.py` - Current HAL implementation
- `tests/test_hal.py` - Test patterns and fixtures
- `tests/data/` - Real test data for validation
- `pyproject.toml` - Project dependencies and configuration

## Notes

- All WAV test files include corresponding .txt files with expected decoded output
- Audio files range from 10-30 WPM for comprehensive speed testing
- System designed for both real-time and batch processing scenarios
- Emphasis on defensive programming with comprehensive error handling
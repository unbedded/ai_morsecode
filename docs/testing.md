# Morse Code Decoder Testing Strategy

This document outlines the comprehensive testing strategy for the Morse code decoder project, including test data management, organization, and execution approaches.

> 📁 **For practical test execution and directory info**, see [`tests/README.md`](../tests/README.md)

**This document focuses on testing strategy** - methodology, metrics, architecture, and CI/CD approaches.

## 🎯 Testing Philosophy

Our testing strategy employs **multiple complementary approaches** to ensure comprehensive validation:

1. **Real Audio Testing** - Use actual recorded Morse code from WAV/TXT pairs
2. **Synthetic Audio Testing** - Generate controlled test scenarios with known parameters
3. **Snippet-Based Testing** - Extract precise audio segments for targeted validation
4. **Comprehensive Coverage** - Test across all difficulty levels and edge cases

## 🧪 Test Suite Architecture

### **Test Categories by Purpose**

#### **1. Unit Tests**
- `test_hal.py` - Audio loading and processing
- `test_signal_processor.py` - FFT and tone detection
- `test_morse_decoder.py` - Pattern recognition and decoding
- `test_configurable_base.py` - Configuration management

#### **2. Integration Tests**
- `test_integration.py` - End-to-end pipeline testing
- `test_decoder_app.py` - Application integration testing
- `test_synthetic_wav_integration.py` - Synthetic test data integration

#### **3. Performance Tests**
- Decoding speed benchmarks
- Memory usage analysis
- Real-time capability validation

#### **4. Regression Tests**
- Previously failing cases
- Known edge cases
- Compatibility across versions

### **Test Execution Strategy**

#### **Fast Tests** (< 5 seconds total)
```bash
# Unit tests with synthetic data
pytest tests/test_hal.py tests/test_signal_processor.py tests/test_morse_decoder.py -v
```

#### **Comprehensive Tests** (< 30 seconds total)
```bash
# Include integration and snippet tests
pytest tests/ -v
```

#### **Full Validation** (< 2 minutes total)
```bash
# Include all real audio tests
pytest tests/ --runslow -v
```

## 🛠️ CLI Tools for Test Management

### **1. Test Data Generator**
Create synthetic test WAV/TXT pairs with controlled parameters:

```bash
# Generate all test types
morsecode-test-data generate --output tests/data/generated_data

# Generate specific test types
morsecode-test-data generate --output tests/data/generated_data --types basic reference

# Show test statistics
morsecode-test-data stats --data tests/data/generated_data
```

**Generated Test Categories:**
- **Basic**: Individual characters, simple words, basic phrases
- **Intermediate**: Mixed content, different frequencies, punctuation
- **Advanced**: High speeds, weak signals, confusing patterns
- **Stress**: Very long text, rapid changes, extreme conditions
- **Reference**: Timing standards (PARIS), frequency calibration

### **2. Snippet Generator**
Extract precise audio segments from real WAV/TXT pairs:

```bash
# Generate snippets from real audio
morsecode-test-gen generate --source tests/data --output tests/snippets

# Generate specific snippet types
morsecode-test-gen generate --source tests/data --output tests/snippets --types characters

# List available snippets
morsecode-test-gen list-snippets --snippets tests/snippets
```

**Generated Snippet Types:**
- **Characters**: Individual A-Z, 0-9, punctuation
- **Words**: Common words, technical terms
- **Phrases**: Short phrases, medium phrases

## 📊 Test Metrics and Success Criteria

### **Coverage Requirements**
- **Overall Code Coverage**: ≥75%
- **Critical Path Coverage**: ≥90%
- **Component Coverage**:
  - Audio HAL: ≥95%
  - Signal Processor: ≥90%
  - Morse Decoder: ≥85%
  - CLI Interface: ≥90%

### **Accuracy Requirements**
- **Character Recognition**: ≥70% success rate
- **Common Words**: ≥60% success rate
- **Technical Terms**: ≥50% success rate
- **Speed Consistency**: ≥70% across WPM variations

### **Performance Requirements**
- **Real-time Factor**: ≥1.0x (faster than real-time)
- **Average Processing**: <2.0 seconds per snippet
- **Memory Usage**: <100MB for typical audio files

## 🚀 Testing Workflow

### **Development Testing**
1. **Fast Unit Tests** - Run on every code change
2. **Integration Tests** - Run before commits
3. **Snippet Tests** - Run weekly for regression detection

### **Release Testing**
1. **Full Test Suite** - All categories
2. **Performance Benchmarks** - Speed and accuracy metrics
3. **Real Audio Validation** - Test with actual recordings
4. **Cross-Platform Testing** - Multiple OS/Python versions

### **Continuous Integration**
```yaml
# Example CI pipeline
test:
  - run: pytest tests/ --cov=src/morsecode --cov-report=html
  - run: pytest tests/test_synthetic_wav_integration.py --tb=short
  - store: tests/htmlcov/
```

## 🎛️ Test Configuration Management

### **Test Profiles**
Use different configurations for different test scenarios:

```yaml
# tests/config/test_profiles.yaml
fast_testing:
  signal:
    frequency: 600
    threshold: 0.3
  decoder:
    wpm: 15
    tolerance: 0.3

accuracy_testing:
  signal:
    frequency: 600
    threshold: 0.1  # More sensitive
  decoder:
    wpm: 15
    tolerance: 0.5  # More tolerant
```

### **Test Data Selection**
- **Smoke Tests**: Use basic and reference data
- **Regression Tests**: Use previously failing snippets
- **Performance Tests**: Use stress test data
- **Accuracy Tests**: Use real audio data

## 📈 Test Maintenance and Evolution

### **Regular Maintenance**
- **Weekly**: Run full test suite, update metrics
- **Monthly**: Review failed tests, update test data
- **Quarterly**: Analyze coverage gaps, add new test cases

### **Test Data Updates**
- **Add New Recordings**: When new WAV/TXT pairs become available
- **Generate New Scenarios**: As edge cases are discovered
- **Update Expectations**: As decoder accuracy improves

### **Continuous Improvement**
- **Monitor Test Results**: Track success rates over time
- **Identify Weak Areas**: Focus testing on problem areas
- **Expand Coverage**: Add tests for new features

## 🎯 Benefits of This Strategy

✅ **Comprehensive Coverage**: Multiple test approaches ensure thorough validation
✅ **Organized Structure**: Clear separation by test type and difficulty
✅ **Automated Generation**: CLI tools create test data efficiently
✅ **Real-World Validation**: Uses actual recorded Morse code
✅ **Performance Monitoring**: Quantifiable metrics and benchmarks
✅ **Maintainable Architecture**: Easy to add new tests and update existing ones
✅ **CI/CD Integration**: Supports automated testing pipelines

This strategy ensures the Morse code decoder is thoroughly tested across all scenarios while maintaining fast development cycles and high code quality.
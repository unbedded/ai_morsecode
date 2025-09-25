# UILT Graph Backend Tests

This directory contains comprehensive tests for the UILT (Universal Interactive Live Terminal) graphing system and its integration with the morsecode application.

## Test Files

- `test_backend_consistency.py` - Tests backend consistency across different scenarios
- `test_sample_rate_precision.py` - Hash-based precision testing for exact render matching
- `test_morsecode_integration.py` - Integration tests for morsecode graphics display with UILT backend fixes

## Key Test Functions

### 1. Main Magnitude Test (Proves Identical Signals → Identical Graphs)

**Function**: `test_magnitude_identical_signals_different_rates`

Tests that identical magnitude signals at different sample rates render identically, proving the UILT time-aware decimation fixes are working.

```bash
python -m pytest src/util/graph/tests/test_morsecode_integration.py::TestMorsecodeGraphicsIntegration::test_magnitude_identical_signals_different_rates -v -s
```

**What it proves**:
- Identical 0.5Hz square waves sampled at 10Hz, 20Hz, and 40Hz produce identical visual output
- UILT time-aware decimation correctly handles different input sample rates
- Hash verification confirms pixel-perfect matching

### 2. Probability Compression Test (Proves Impulse Width Fix)

**Function**: `test_probability_compression_effectiveness`

Tests that probability data compression removes repeated cached values, fixing the "wide impulse" problem.

```bash
python -m pytest src/util/graph/tests/test_morsecode_integration.py::TestMorsecodeGraphicsIntegration::test_probability_compression_effectiveness -v -s
```

**What it proves**:
- Cached probability values (repeated 25x) are compressed to actual convolution rate
- Compression ratios match expected values (25:1, 12.5:1, etc.)
- Impulse width is corrected from wide blocks to proper narrow impulses

### 3. Complete Integration Test (Proves Real Morsecode Scenarios Work)

**Function**: `test_complete_integration_morse_pattern`

Tests complete integration with realistic morse code patterns at different WPM rates and sampling frequencies.

```bash
python -m pytest src/util/graph/tests/test_morsecode_integration.py::TestMorsecodeGraphicsIntegration::test_complete_integration_morse_pattern -v -s
```

**What it proves**:
- Sample rate calculations are consistent across different morse patterns
- Magnitude graphs use 50Hz (20ms chunks) and probability graphs use 2Hz (500ms convolution)
- Real-world morsecode scenarios are handled correctly

## Run All Tests

### Option 1: Custom Test Runner (Recommended)
```bash
python -c "from src.util.graph.tests.test_morsecode_integration import run_morsecode_graphics_verification; run_morsecode_graphics_verification()"
```

### Option 2: Pytest All Integration Tests
```bash
python -m pytest src/util/graph/tests/test_morsecode_integration.py -v -s
```

### Option 3: All UILT Tests
```bash
python -m pytest src/util/graph/tests/ -v -s
```

## Expected Results

When all tests pass, you should see:

```
🎉 ALL TESTS PASSED! Morsecode graphics integration is working correctly.
✅ Identical signals at different sample rates produce identical outputs
✅ Probability data compression is working effectively
✅ Complete integration handles realistic morse patterns correctly
```

## Test Output Files

Each test saves detailed output files to `/tmp/morsecode_graphics_test_*` directories for manual inspection. These include:

- Visual comparisons of rendered outputs
- Hash analysis for exact matching verification
- Compression ratio analysis
- Sample rate calculation details

## What These Tests Verify

1. **UILT Backend Fixes**: Time-aware decimation produces consistent results regardless of input sample rate
2. **Probability Data Compression**: Cached values are properly compressed to match actual convolution timing
3. **Sample Rate Synchronization**: Magnitude and probability graphs have properly synchronized time scales
4. **Real-World Integration**: The fixes work with actual morsecode decoder scenarios

## Debugging Failed Tests

If tests fail:

1. Check the test output directory printed at the end of each test
2. Compare visual outputs in the saved files
3. Look for hash mismatches in the assertion errors
4. Verify sample rate calculations in the debug output

## Background

These tests were created to verify fixes for:
- Time scaling mismatch between probability and magnitude graphs (25:1 ratio issue)
- Wide probability impulses due to cached value repetition
- Hardcoded sample rates vs. configuration-driven rates
- UILT decimation consistency across different input scenarios
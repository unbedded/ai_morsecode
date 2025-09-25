# UILT Debug Tools

This directory contains maintenance references for the UILT (Universal Interface for Live Telemetry) library.

## 📁 Files

- **`fix_braille_mapping.py`** - Braille Unicode dot mapping reference for maintenance
- **`README.md`** - This documentation

## 🎯 Purpose

This directory provides:
- **Braille Unicode mapping reference** - Correct dot positioning for maintenance

## 🚀 Usage

**For current UILT examples, use the organized demos in the examples directory:**
```bash
# Navigate to examples directory for current demos
cd src/util/graph/examples/

# Run comprehensive examples with descriptive names
python demo_01_identical_signals_validation.py
python demo_02_sample_rate_comparison.py
python demo_03_uilt_showcase.py
python demo_04_braille_backend_features.py
python demo_05_backend_comparison.py
python demo_06_real_time_animation.py
python demo_07_output_instrumentation.py
```

**For maintenance reference:**
```bash
# View Braille Unicode mapping reference
python src/util/graph/debug/fix_braille_mapping.py
```

## 🔧 For Future Development

The Braille mapping reference is useful for:
- **Regression testing** - Ensure Braille rendering remains correct
- **New backend development** - Reference patterns for other output formats

---

**Note**: This debug directory now contains only essential maintenance references. For current examples and demos, use `src/util/graph/examples/` which contains all valuable content with descriptive names and comprehensive documentation.
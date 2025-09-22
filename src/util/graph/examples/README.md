# UILT Library Examples

This directory contains examples demonstrating the **Universal Interface for Live Telemetry (UILT)** graphing library. For complete API documentation and technical details, see [../README.md](../README.md).

## 📁 Available Examples

### 🎬 [demo_uilt_showcase.py](demo_uilt_showcase.py) ⭐ **FEATURED**
**Impressive UILT capabilities showcase for demonstrations**

Interactive demonstration showcasing UILT's most compelling features:
- Resolution advantage demo with side-by-side ASCII vs Braille comparison
- Morse code analysis with precise timing visualization
- Performance metrics and SSH compatibility demonstrations
- Ready-to-use showcase for evaluating UILT capabilities

**Run:** `python demo_uilt_showcase.py`

---

### 🚀 [basic_usage.py](basic_usage.py)
**Fundamental UILT capabilities demonstration**

Complete example showing:
- Quick plotting convenience functions
- ASCII vs Braille backend comparison with side-by-side output
- Auto backend selection and terminal capability detection
- Manual Y-axis limits vs auto-scaling
- Performance metrics and effective resolution analysis

**Run:** `python basic_usage.py`

---

## 🎯 Running Examples

```bash
# Run the featured showcase demo (recommended for first-time users)
python demo_uilt_showcase.py

# Run the comprehensive basic usage demo
python basic_usage.py
```

The basic usage example covers all fundamental UILT capabilities including backend comparison, signal processing, and performance analysis. Additional examples are planned for real-time visualization, morse code integration, and performance benchmarking.

## 💡 Key Features Demonstrated

- **Backend-aware decimation**: ASCII (1 point/char) vs Braille (2 points/char)
- **Signal fidelity preservation**: Smart decimation maintains peaks and timing
- **SSH compatibility**: Universal ASCII with high-resolution Braille fallback
- **Performance optimization**: Efficient memory usage and processing

## 📚 Complete Documentation

For detailed API reference, architecture design, integration patterns, and advanced usage examples, see the main [UILT documentation](../README.md).

---

**Quick reference for immediate integration into your signal processing applications.**
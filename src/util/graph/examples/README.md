# UILT Examples - Visual Demonstrations and Usage Patterns

This directory contains comprehensive examples demonstrating **UILT (Universal Interactive Live Terminal)** capabilities for signal visualization and terminal graphics.

## 🎬 Complete Example Gallery

### **Core Validation Examples**

#### **`demo_01_identical_signals_validation.py`** ⭐ **UNIT TEST PROOF**
**Purpose**: Visual proof that identical mathematical signals produce identical output regardless of sample rate

**Features**:
- ✅ Square wave hash validation (proves pixel-perfect matching)
- ✅ Morse code timing precision tests
- ✅ ASCII vs Braille resolution comparison
- ✅ Probability data compression demonstration

**Run**: `python demo_01_identical_signals_validation.py`

**Best for**: Unit test validation, proving decimation algorithm correctness

---

#### **`demo_02_sample_rate_comparison.py`**
**Purpose**: Side-by-side visual comparison of signals at different sample rates

**Features**:
- 📊 Side-by-side rendering of same signal at 10Hz, 20Hz, 40Hz
- 📈 Multiple waveform types (square, triangle, sawtooth, pulse)
- ⚙️ Decimation effectiveness (16.7:1 ratio demonstrations)
- 🏁 Backend consistency benchmarks

**Run**: `python demo_02_sample_rate_comparison.py`

**Best for**: Visual debugging, algorithm verification, development demos

---

#### **`demo_03_uilt_showcase.py`** 🚀 **PRODUCTION SHOWCASE**
**Purpose**: Production-ready showcase for development teams and SSH debugging

**Features**:
- 🔍 Complex multi-frequency signal analysis
- 📡 SOS morse pattern with element-by-element timing breakdown
- ⚡ Backend performance and SSH compatibility matrix
- 💻 Real-world integration examples with live data simulation

**Run**: `python demo_03_uilt_showcase.py`

**Best for**: Team presentations, production integration demos, SSH debugging

---

### **Specialized Backend Examples**

#### **`demo_04_braille_backend_features.py`**
**Purpose**: Deep dive into Braille backend capabilities and Unicode handling

**Features**:
- ⠿ Braille dot pattern mapping
- 📊 High-resolution signal rendering
- 🔤 Unicode character set demonstrations
- 🎯 Resolution advantage quantification

**Run**: `python demo_04_braille_backend_features.py`

**Best for**: Understanding Braille rendering, terminal compatibility testing

---

#### **`demo_05_backend_comparison.py`**
**Purpose**: Comprehensive comparison between ASCII and Braille backends

**Features**:
- 📈 Same signals rendered with both backends
- 📊 Performance characteristics comparison
- 🎨 Visual quality analysis
- 🔧 Backend selection guidelines

**Run**: `python demo_05_backend_comparison.py`

**Best for**: Backend selection decisions, optimization analysis

---

### **Advanced Features**

#### **`demo_06_real_time_animation.py`**
**Purpose**: Real-time signal animation and live data visualization

**Features**:
- 🎬 Animated sine wave with frame-by-frame updates
- ⏱️ Real-time rendering performance
- 📺 Terminal animation techniques
- 🔄 Live data stream simulation

**Run**: `python demo_06_real_time_animation.py`

**Best for**: Live monitoring applications, real-time debugging

---

#### **`demo_07_output_instrumentation.py`**
**Purpose**: Advanced output capture and analysis for debugging

**Features**:
- 📁 File-based output capture
- 📊 Render comparison analysis
- 🔍 Performance instrumentation
- 📈 Visual diff generation

**Run**: `python demo_07_output_instrumentation.py`

**Best for**: Advanced debugging, regression testing, quality assurance

---

### **Legacy/Basic Examples**

#### **`basic_usage.py`**
**Fundamental UILT capabilities demonstration**

Complete example showing:
- Quick plotting convenience functions
- ASCII vs Braille backend comparison with side-by-side output
- Auto backend selection and terminal capability detection
- Manual Y-axis limits vs auto-scaling
- Performance metrics and effective resolution analysis

**Run**: `python basic_usage.py`

---

## 🎯 Usage Recommendations

### **For New Users**
Start with:
1. `demo_01_identical_signals_validation.py` - See core capabilities and proof
2. `demo_03_uilt_showcase.py` - Understand production use cases

### **For Developers**
Focus on:
1. `demo_02_sample_rate_comparison.py` - Algorithm validation
2. `demo_05_backend_comparison.py` - Technical details
3. `demo_07_output_instrumentation.py` - Debugging tools

### **For Production Integration**
Use:
1. `demo_03_uilt_showcase.py` - Integration patterns
2. `demo_06_real_time_animation.py` - Live data handling

### **For Presentations**
Best demos:
1. `demo_03_uilt_showcase.py` - Impressive feature showcase
2. `demo_01_identical_signals_validation.py` - Technical proof
3. `demo_02_sample_rate_comparison.py` - Visual comparisons

## 🎯 Running Examples

```bash
# Core validation examples - prove algorithm correctness
python demo_01_identical_signals_validation.py
python demo_02_sample_rate_comparison.py

# Production showcase - impressive demonstrations
python demo_03_uilt_showcase.py

# Backend specialization examples
python demo_04_braille_backend_features.py
python demo_05_backend_comparison.py

# Advanced features
python demo_06_real_time_animation.py
python demo_07_output_instrumentation.py

# Legacy basic usage
python basic_usage.py
```

## 📊 What These Examples Prove

### **Algorithm Correctness**
- ✅ Identical waveforms → identical visual output
- ✅ Sample rate independence achieved
- ✅ Hash verification confirms pixel-perfect matching

### **Production Readiness**
- ✅ SSH compatibility across terminals
- ✅ Real-time performance suitable for monitoring
- ✅ Graceful fallbacks for terminal limitations

### **Feature Completeness**
- ✅ 2x resolution advantage with Braille backend
- ✅ Precise timing preservation for morse code
- ✅ Complex signal handling with multiple components

## 🛠️ Requirements

All examples require:
- Python 3.8+
- NumPy
- UILT library (included in this project)

Some examples may require:
- UTF-8 terminal support (for Braille examples)
- Terminal with color support (optional, graceful fallback)

## 🔧 Troubleshooting

**Import Errors**: Ensure you're running from the project root directory
**Terminal Issues**: Some terminals may not support Braille Unicode (use ASCII fallback)
**Performance**: For slow terminals, reduce refresh rates in real-time examples

## 📝 Contributing

When adding new examples:
1. Use descriptive `demo_##_feature_name.py` naming
2. Include comprehensive docstrings
3. Add entry to this README with purpose and features
4. Test on multiple terminal types for compatibility

---

**Note**: For low-level debugging and development history, see `src/util/graph/debug/` directory.
# UILT Library Examples

This directory contains comprehensive examples demonstrating the capabilities of the **Universal Interface for Live Telemetry (UILT)** graphing library.

## 📁 Example Files

### 🚀 [basic_usage.py](basic_usage.py)
**Fundamental UILT capabilities and API usage**

Demonstrates core functionality including:
- Quick plotting with convenience functions
- ASCII vs Braille backend comparison
- Auto backend selection
- Direct backend usage with configuration
- Signal analysis use cases

**Run:**
```bash
python basic_usage.py
```

**Key Features Shown:**
- `plot_signal_ascii()` and `plot_signal_braille()`
- `plot_signal_auto()` with fallback logic
- `compare_backends()` side-by-side visualization
- Manual Y-axis limits vs auto-scaling
- Performance information and metrics

---

### ⚡ [realtime_demo.py](realtime_demo.py)
**Real-time signal visualization and live monitoring**

Shows how UILT handles streaming data for live visualization:
- Asyncio-based real-time plotting
- Signal generator simulation
- Multiple signal types (sine, square, chirp, noise)
- Frame rate control and performance monitoring
- Morse code pattern simulation

**Run:**
```bash
python realtime_demo.py
```

**Key Features Shown:**
- Real-time data streaming
- Smooth 20 FPS visualization
- Buffer management for continuous data
- Dynamic signal type switching
- SOS morse code pattern demonstration

---

### 📊 [performance_comparison.py](performance_comparison.py)
**Performance analysis and backend optimization**

Comprehensive performance testing and analysis:
- Decimation algorithm benchmarks
- Resolution advantage demonstration
- Signal preservation quality analysis
- SSH debugging use case scenarios

**Run:**
```bash
python performance_comparison.py
```

**Key Features Shown:**
- Backend-aware decimation performance
- 2x resolution advantage of Braille
- Signal fidelity preservation metrics
- Timing analysis for different data sizes
- Real-world SSH debugging scenarios

---

### 📡 [morse_integration.py](morse_integration.py)
**Integration with morse code decoder application**

Demonstrates real-world integration scenarios:
- Mock morse code decoder implementation
- Real-time signal analysis and debugging
- Timing analysis for morse elements
- Production integration architecture

**Run:**
```bash
python morse_integration.py
```

**Key Features Shown:**
- Morse code signal generation and analysis
- Dot/dash timing discrimination
- Real-time debugging workflows
- Integration architecture patterns
- Backend selection strategies

---

## 🎯 Quick Start

To run all examples in sequence:

```bash
# Run basic usage examples
python basic_usage.py

# Try real-time visualization
python realtime_demo.py

# Analyze performance characteristics
python performance_comparison.py

# See morse code integration
python morse_integration.py
```

## 💡 Key Concepts Demonstrated

### **Backend-Aware Decimation**
Examples show how UILT optimizes data representation for each backend:
- **ASCII**: 1 data point per character (universal compatibility)
- **Braille**: 2 data points per character (2x horizontal resolution)

### **Real-time Performance**
All examples demonstrate:
- Smooth real-time visualization (20+ FPS)
- Efficient buffer management
- Low-latency data processing
- SSH-friendly remote debugging

### **Signal Fidelity**
Smart decimation algorithms preserve:
- Peak values for spike detection
- Signal energy characteristics
- Timing relationships for morse code
- High-frequency components when possible

### **Integration Patterns**
Examples show production-ready patterns:
- Configurable backend selection
- Debug mode visualization
- Performance monitoring
- Error handling and fallbacks

## 🔧 Technical Requirements

### **Dependencies**
- Python 3.13+
- UILT library (`src/util/graph/`)
- Standard library only (math, asyncio, collections, etc.)

### **Terminal Compatibility**
- **ASCII mode**: Works in all terminals
- **Braille mode**: Requires UTF-8 support and Unicode fonts
- **Auto mode**: Automatically detects capabilities and falls back

### **Performance Characteristics**
- **Memory**: O(buffer_size) for real-time applications
- **CPU**: Optimized decimation algorithms scale efficiently
- **Latency**: Sub-millisecond processing for typical buffer sizes

## 🎪 Advanced Usage

### **Custom Signal Generation**
```python
from util.graph import BrailleBackend

# Generate your signal
signal = [math.sin(i * 0.1) for i in range(1000)]

# Create backend
backend = BrailleBackend(width=80, height=6)
backend.plot(signal, sample_rate_hz=1000.0)

# Render and display
lines = backend.render_braille()
for line in lines:
    print(line)
```

### **Real-time Integration**
```python
import asyncio
from util.graph import ASCIIBackend

async def realtime_monitor():
    backend = ASCIIBackend(60, 4)

    while True:
        # Get new data from your source
        new_samples = get_audio_samples()

        # Update visualization
        backend.clear()
        backend.plot(new_samples)

        # Render frame
        frame = backend.render_sparkline()

        # Display (clear screen + print)
        print("\033[H\033[J", end="")
        for line in frame:
            print(line)

        await asyncio.sleep(0.05)  # 20 FPS
```

### **SSH Debugging Setup**
```bash
# Enable UTF-8 for Braille support
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Run your decoder with UILT visualization
python your_decoder.py --debug --backend=braille
```

## 🚀 Next Steps

1. **Try the examples** to understand UILT capabilities
2. **Integrate with your application** using the patterns shown
3. **Customize backends** for your specific use cases
4. **Contribute improvements** to the UILT library

## 📚 Related Documentation

- [UILT API Reference](../README.md) - Complete API documentation
- [Backend Guide](../backends/) - Backend implementation details
- [Performance Guide](../utils/) - Optimization and performance tuning
- [Integration Patterns](../../../morsecode/) - Production integration examples

---

**🎯 The UILT library enables powerful real-time signal visualization with SSH-friendly backends and optimal performance characteristics. These examples demonstrate production-ready patterns for immediate integration into your applications.**
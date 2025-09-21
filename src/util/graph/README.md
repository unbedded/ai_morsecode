# UTIL Graphing Library - Universal Interface for Live Telemetry (UILT)

## 🎯 **Overview**

A high-performance asyncio-based graphing utility with matplotlib-like interface that supports multiple output backends (ASCII, Braille, Sparklines) for real-time data visualization. Designed for SSH-friendly debugging and live telemetry display.

## 🏗️ **Architecture Design**

### **Core Principles**
- **Asyncio-driven**: Non-blocking real-time updates
- **Backend Agnostic**: ASCII, Braille, Sparklines, and future matplotlib GUI
- **Matplotlib-like API**: Familiar interface for easy adoption
- **Loose Coupling**: Independent from src/morsecode - pure utility
- **Data Type Flexibility**: Supports both Python lists and scipy/numpy arrays
- **Auto-decimation**: Intelligent data reduction to fit display limits

### **Key Features**
- ✅ **Scrolling Time-series**: Real-time data streaming
- ✅ **Vector Plotting**: Static vector visualization
- ✅ **Y-axis Scaling**: Manual limits or auto-scaling (like FFT magnitude)
- ✅ **X-axis Sample Period**: Configurable time base
- ✅ **Multi-backend Output**: ASCII/Braille/Sparklines
- ✅ **Data Decimation**: Smart downsampling for performance

---

## 📊 **API Design (Matplotlib-like Interface)**

### **Basic Usage Pattern**
```python
import asyncio
from util.graph import AsyncPlot, Backend, FillMode

async def main():
    # Create plot with backend selection
    plot = AsyncPlot(backend=Backend.ASCII, width=80, height=20)

    # Configure visualization mode
    plot.set_fill_mode(FillMode.THIN_LINE)  # or FillMode.FILLED

    # Configure axes
    plot.set_xlim(0, 10.0)          # Fixed X limits
    plot.set_ylim(-1.0, 1.0)        # Fixed Y limits
    plot.set_ylim_auto()            # Or auto-scaling (like FFT)

    # Set time base
    plot.set_sample_period(0.01)    # 10ms per sample

    # Start real-time display
    await plot.show_async()

    # Add data (scrolling mode)
    while True:
        new_data = get_sensor_reading()
        await plot.add_data(new_data)
        await asyncio.sleep(0.01)
```

### **Vector Plotting (Static)**
```python
# Plot a complete vector
x_values = [0, 1, 2, 3, 4, 5]
y_values = [0, 1, 4, 9, 16, 25]
await plot.plot_vector(x_values, y_values)

# Or with automatic X-axis generation
y_data = np.sin(np.linspace(0, 2*np.pi, 100))
await plot.plot_vector(y_data, sample_period=0.01)
```

### **Scrolling Time-series (Real-time)**
```python
# Initialize scrolling mode
plot.set_mode('scrolling', buffer_size=1000)

# Stream data points
for sample in audio_stream:
    magnitude = process_audio(sample)
    await plot.add_data(magnitude)  # Auto-scrolls when buffer full
```

---

## 🎨 **Backend Abstraction**

### **Supported Backends**

#### **1. ASCII Backend** (Current Implementation)

**Filled Mode (current):**
```
┌─── Ramp Signal (0 to 1) ───────────────────────────────┐
│ 1.0 ▄████▄    ▄████▄    ▄████▄    ▄████▄            │
│ 0.7 █████▄  ▄█████▄  ▄█████▄  ▄█████▄            │
│ 0.3 ██████▄▄██████▄▄██████▄▄██████▄▄            │
│ 0.0 ████████████████████████████████████            │
│      ╰─── Time (newest right) ───╯                   │
└────────────────────────────────────────────────────────┘
```

**Thin Line Mode (new requirement):**
```
┌─── Ramp Signal (0 to 1) ───────────────────────────────┐
│ 1.0 ▄    ▄    ▄    ▄    ▄    ▄    ▄    ▄            │
│ 0.7  ▄  ▄ ▄  ▄ ▄  ▄ ▄  ▄ ▄  ▄ ▄  ▄ ▄  ▄            │
│ 0.3   ▄▄   ▄▄   ▄▄   ▄▄   ▄▄   ▄▄   ▄▄   ▄▄            │
│ 0.0 ▁▁  ▁▁  ▁▁  ▁▁  ▁▁  ▁▁  ▁▁  ▁▁  ▁▁            │
│      ╰─── Time (newest right) ───╯                   │
└────────────────────────────────────────────────────────┘
```

#### **2. Braille Backend** (High Density)

**Filled Mode (practical for Braille):**
```
┌─── Ramp Signal (0 to 1) ───────────────────────────────┐
│ 1.0 ⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈ │
│ 0.7 ⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸ │
│ 0.3 ⠿⠿⠿⠿⠄⠀⠀⠄⠿⠿⠿⠿⠄⠀⠀⠄⠿⠿⠿⠿⠄⠀⠀⠄⠿⠿⠿⠿⠄⠀⠀⠄⠿⠿⠿⠿⠄ │
│ 0.0 ⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿ │
└───────────────────────────────────────────────────────┘
```

**Note:** Braille excels at filled/density visualization but struggles with thin lines due to its discrete 2×4 dot matrix. For thin line visualization, ASCII backend is recommended.

#### **3. Future: Matplotlib Backend** (GUI Analysis)
```
# Future implementation for detailed analysis
plot = AsyncPlot(Backend.MATPLOTLIB, width=800, height=600)
# Opens GUI window for detailed signal analysis
```

---

## 🔧 **Implementation Architecture**

### **Directory Structure**
```
src/util/graph/
├── README.md                    # This file
├── __init__.py                  # Public API exports
├── core/
│   ├── __init__.py
│   ├── async_plot.py           # Main AsyncPlot class
│   ├── data_manager.py         # Data buffering & decimation
│   └── renderer.py             # Backend abstraction
├── backends/
│   ├── __init__.py
│   ├── ascii_backend.py        # ASCII rendering (universal compatibility)
│   ├── braille_backend.py      # High-density Braille output (UTF-8 terminals)
│   └── matplotlib_backend.py   # Future GUI backend
├── utils/
│   ├── __init__.py
│   ├── decimation.py          # Data reduction algorithms
│   └── scaling.py             # Auto-scaling logic
└── examples/
    ├── basic_usage.py
    ├── scrolling_demo.py
    └── multi_backend_demo.py
```

### **Core Classes**

#### **AsyncPlot (Main Interface)**
```python
class AsyncPlot:
    def __init__(self, backend: Backend, width: int, height: int):
        self.backend = backend
        self.width = width
        self.height = height
        self.data_manager = DataManager()
        self.renderer = RendererFactory.create(backend)

    async def show_async(self) -> None:
        """Start async display loop"""
        while True:
            # Get backend-aware decimated data
            x_data, y_data = self.data_manager.get_display_data(
                self.backend, self.width, self.height
            )

            # Render with backend-specific logic
            await self.renderer.render(x_data, y_data)
            await asyncio.sleep(0.01)  # 100 FPS max

    async def add_data(self, value: float | list[float]) -> None:
        """Add new data point(s) for scrolling"""

    async def plot_vector(self, y_data: ArrayLike, x_data: ArrayLike = None) -> None:
        """Plot complete vector (static)"""

    def set_xlim(self, xmin: float, xmax: float) -> None:
        """Set X-axis limits"""

    def set_ylim(self, ymin: float, ymax: float) -> None:
        """Set Y-axis limits (manual)"""

    def set_ylim_auto(self, decay_factor: float = 0.999) -> None:
        """Enable auto-scaling Y-axis (like FFT magnitude)"""

    def set_fill_mode(self, mode: FillMode) -> None:
        """Set visualization fill mode"""
```

#### **DataManager (Buffering & Decimation)**
```python
class DataManager:
    def __init__(self, max_points: int = 1000):
        self.buffer = deque(maxlen=max_points)
        self.sample_period = 0.01
        self.x_limits = None
        self.y_limits = None
        self.auto_scale_y = False

    def add_sample(self, value: float) -> None:
        """Add new data sample"""

    def get_display_data(self, backend: Backend, width: int, height: int) -> tuple[list[float], list[float]]:
        """Get backend-aware decimated data for display"""
        # Get raw data from buffer
        y_data = list(self.buffer)
        x_data = [i * self.sample_period for i in range(len(y_data))]

        # Apply backend-aware decimation
        decimated_y = SmartDecimation.decimate(y_data, backend, width, height)
        decimated_x = SmartDecimation.decimate(x_data, backend, width, height)

        return decimated_x, decimated_y
```

#### **Backend Abstraction**
```python
class Backend(Enum):
    ASCII = "ascii"
    BRAILLE = "braille"  # Requires UTF-8 SSH + Unicode terminal
    MATPLOTLIB = "matplotlib"

class FillMode(Enum):
    FILLED = "filled"      # Fill area below signal (current default)
    THIN_LINE = "thin_line"  # Show only signal trace line

class BaseRenderer(ABC):
    @abstractmethod
    async def render(self, x_data: ArrayLike, y_data: ArrayLike,
                    width: int, height: int) -> str:
        """Render data to string output"""

    @abstractmethod
    def set_title(self, title: str) -> None:
        """Set plot title"""

    @abstractmethod
    def set_axis_labels(self, xlabel: str, ylabel: str) -> None:
        """Set axis labels"""
```

---

## 📈 **Data Handling Strategies**

### **1. Data Type Support**
```python
# Python lists (simple, familiar)
data = [1.2, 3.4, 5.6, 7.8]
await plot.add_data(data)

# NumPy arrays (efficient, scientific)
import numpy as np
signal = np.sin(np.linspace(0, 2*np.pi, 1000))
await plot.plot_vector(signal)

# SciPy integration (future)
from scipy import signal as scipy_signal
filtered = scipy_signal.butter(...)
await plot.add_data(filtered)
```

### **2. X-Axis Sample Period**
```python
# Set time base for X-axis generation
plot.set_sample_period(0.001)  # 1ms per sample (1000 Hz)

# Automatic X-axis creation
y_data = [1, 4, 9, 16, 25]  # 5 samples
# X-axis becomes: [0, 0.001, 0.002, 0.003, 0.004]

# Manual X-axis override
x_custom = [0, 0.5, 1.0, 2.0, 5.0]
await plot.plot_vector(y_data, x_data=x_custom)
```

### **3. Backend-Aware Data Decimation**
```python
class SmartDecimation:
    """Intelligent data reduction preserving signal characteristics"""

    @staticmethod
    def calculate_effective_resolution(backend: Backend, width: int, height: int) -> int:
        """Calculate effective data points based on backend capabilities"""
        if backend == Backend.ASCII:
            return width  # 1 data point per character
        elif backend == Backend.BRAILLE:
            return width * 2  # 2 data points per character (left + right columns)
        else:
            return width  # Default fallback

    @staticmethod
    def decimate(data: ArrayLike, backend: Backend, width: int, height: int) -> ArrayLike:
        """Backend-aware decimation preserving signal characteristics"""
        target_points = SmartDecimation.calculate_effective_resolution(backend, width, height)

        if len(data) <= target_points:
            return data

        # Peak-preserving decimation
        # 1. Divide into bins
        # 2. Keep max/min in each bin to preserve spikes
        # 3. Use linear interpolation for smooth signals

        bin_size = len(data) / target_points
        decimated = []

        for i in range(target_points):
            start_idx = int(i * bin_size)
            end_idx = int((i + 1) * bin_size)
            bin_data = data[start_idx:end_idx]

            # Keep peaks for spike preservation (adaptive threshold)
            signal_range = max(bin_data) - min(bin_data)
            threshold = signal_range * 0.1  # 10% of local range

            if signal_range > threshold:
                decimated.append(max(bin_data))
            else:
                decimated.append(np.mean(bin_data))

        return decimated
```

#### **🎯 Key Advantage: 2x Time Resolution with Braille**

The backend-aware decimation enables **double horizontal resolution** with Braille:

```python
# Example: 80-character terminal width
plot_ascii = AsyncPlot(Backend.ASCII, width=80, height=4)
plot_braille = AsyncPlot(Backend.BRAILLE, width=80, height=4)

# ASCII: 80 data points displayed
# Braille: 160 data points displayed (2 per character)

# For high-frequency signals, this means:
data = get_high_freq_signal(1000)  # 1000 samples

# ASCII decimates 1000 → 80 points (12.5:1 ratio)
# Braille decimates 1000 → 160 points (6.25:1 ratio)
# = Better signal fidelity and spike preservation
```

---

## 📊 **Y-Axis Scaling Strategies**

### **1. Manual Y-Limits (Fixed Range)**
```python
# Fixed range (like normalized magnitude -1 to +1)
plot.set_ylim(-1.0, 1.0)

# Good for: Known signal ranges, comparative analysis
```

### **2. Auto-scaling with Decay (Dynamic Range)**
```python
# Auto-scaling like FFT magnitude
plot.set_ylim_auto(decay_factor=0.999)

# Algorithm:
# - Track running maximum with slow decay
# - Allows scaling down when signal weakens
# - Prevents constant rescaling from noise
```

### **3. Auto-scaling Strategies**
```python
class AutoScaler:
    def __init__(self, decay_factor: float = 0.999):
        self.running_max = 0.0
        self.running_min = 0.0
        self.decay = decay_factor

    def update(self, new_data: ArrayLike) -> tuple[float, float]:
        current_max = max(new_data)
        current_min = min(new_data)

        # Update with decay
        if current_max > self.running_max:
            self.running_max = current_max
        else:
            self.running_max *= self.decay

        if current_min < self.running_min:
            self.running_min = current_min
        else:
            self.running_min = self.running_min * self.decay + current_min * (1 - self.decay)

        return self.running_min, self.running_max
```

---

## 🔄 **Graph Types & Modes**

### **1. Scrolling Time-series**
- **Use case**: Real-time sensor data, audio signals
- **Buffer**: Fixed-size circular buffer
- **X-axis**: Time-based with sample period
- **Updates**: Continuous streaming

```python
plot.set_mode('scrolling', buffer_size=1000, window_seconds=10.0)
# Shows last 10 seconds of data, 1000 sample buffer
```

### **2. Static Vector Plot**
- **Use case**: FFT results, analysis plots
- **Buffer**: Complete dataset
- **X-axis**: Index or custom values
- **Updates**: Complete redraw

```python
# Plot complete FFT spectrum
frequencies = np.fft.fftfreq(1024, d=1/44100)
magnitudes = np.abs(np.fft.fft(audio_chunk))
await plot.plot_vector(magnitudes, x_data=frequencies)
```

---

## 🎛️ **Advanced Features**

### **1. Multi-trace Support**
```python
# Multiple signals on same plot
plot.add_trace("signal", color="green")
plot.add_trace("threshold", color="red", style="dashed")

await plot.add_data("signal", signal_value)
await plot.add_data("threshold", threshold_value)
```

### **2. Plot Annotations**
```python
# Add markers and labels
plot.add_marker(x=5.0, y=0.8, label="Peak")
plot.add_hline(y=0.25, label="Threshold", style="dashed")
```

### **3. Export Capabilities**
```python
# Save plot data
await plot.export_data("signal_log.csv")

# Save rendered output
await plot.export_image("debug_output.txt")  # ASCII
await plot.export_image("debug_output.png")  # Future matplotlib
```

---

## 🔧 **Terminal Capability Detection**

### **Automatic Backend Selection**
```python
# Smart backend selection based on terminal capabilities
plot = AsyncPlot.auto_detect_backend(width=80, height=20)

# Manual override for guaranteed compatibility
plot = AsyncPlot(Backend.ASCII, width=80, height=20)  # Always works

# Opt-in to high-density (may fallback to ASCII)
plot = AsyncPlot(Backend.BRAILLE, width=80, height=20, fallback=Backend.ASCII)
```

### **SSH Environment Detection**
```python
def detect_terminal_capabilities() -> Backend:
    """Detect what the current terminal can handle."""

    # Check for UTF-8 support
    if not os.environ.get('LANG', '').endswith('.UTF-8'):
        return Backend.ASCII

    # Check for Unicode terminal
    try:
        # Test Braille character rendering
        print('⠀', end='', flush=True)
        return Backend.BRAILLE
    except UnicodeEncodeError:
        return Backend.ASCII

    # SSH-specific checks
    if 'SSH_CONNECTION' in os.environ:
        # Conservative approach for SSH
        return Backend.ASCII

    return Backend.BRAILLE
```

### **Scrolling Sine Wave Example**

```python
import asyncio
import math
from util.graph import AsyncPlot, Backend

async def sine_wave_demo():
    """Live scrolling sine wave demonstration."""
    # Auto-detect terminal capabilities (Braille → ASCII fallback)
    plot = AsyncPlot.auto_detect_backend(width=60, height=8)

    plot.set_title("Live Sine Wave (0.3 Hz)")
    plot.set_ylim(-1.2, 1.2)        # Fixed Y-axis range
    plot.set_sample_period(0.05)    # 50ms per sample (20 FPS)

    await plot.show_async()

    # Generate smooth scrolling sine wave
    start_time = asyncio.get_event_loop().time()

    while True:
        current_time = asyncio.get_event_loop().time() - start_time
        sine_value = math.sin(2 * math.pi * 0.3 * current_time)  # 0.3 Hz

        await plot.add_data(sine_value)
        await asyncio.sleep(0.05)  # 20 FPS update rate

# Run the demo
if __name__ == "__main__":
    asyncio.run(sine_wave_demo())
```

**Output Preview:**
```
🌊 Live Sine Wave (0.3 Hz) ────────────────────────────────
┌─── Time: 8.3s ──────────────────────────────────────────┐
│ +1.2         ⡎⠉          ⡎⠉          ⡎⠉            │
│ +0.4      ⡔⠁⠈⠢⡀      ⡔⠁⠈⠢⡀      ⡔⠁⠈⠢⡀        │
│  0.0 ⡤⠊⠀⠀⠀⠀⠀⠀⠈⢆⡤⠊⠀⠀⠀⠀⠀⠀⠈⢆⡤⠊⠀⠀⠀⠀⠀⠀⠈⢆    │
│ -1.2          ⠈⠢⢄⠀⠀⠀      ⠈⠢⢄⠀⠀⠀      ⠈⠢⢄⠀    │
└─────────────────────────────────────────────────────────┘
Frame: 166, Value: +0.855, Freq: 0.3 Hz  [Ctrl+C to stop]
```

**Why This Works Better Than Filled Areas:**
- **Higher Resolution**: Braille provides 8 vertical levels vs 4 ASCII blocks
- **Cleaner Visualization**: Thin line shows exact signal path
- **Better Time Resolution**: More data points fit horizontally
- **SSH Compatible**: Graceful fallback to ASCII for older terminals

---

## 🚀 **Usage Examples**

### **Example 1: Real-time Audio Magnitude**
```python
async def audio_debug():
    plot = AsyncPlot(Backend.ASCII, width=80, height=20)
    plot.set_title("Audio Signal Magnitude")
    plot.set_ylim(-1.0, 1.0)
    plot.set_sample_period(1/44100)  # 44.1kHz

    await plot.show_async()

    for chunk in audio_stream:
        magnitude = calculate_magnitude(chunk)
        await plot.add_data(magnitude)
```

### **Example 2: FFT Spectrum Analysis**
```python
async def fft_analysis():
    plot = AsyncPlot(Backend.BRAILLE, width=120, height=30)
    plot.set_title("FFT Magnitude Spectrum")
    plot.set_xlim(0, 2000)  # 0-2kHz
    plot.set_ylim_auto()    # Auto-scale magnitude

    await plot.show_async()

    while True:
        fft_data = compute_fft(audio_buffer)
        freqs = np.fft.fftfreq(len(fft_data), d=1/44100)
        await plot.plot_vector(np.abs(fft_data), x_data=freqs)
        await asyncio.sleep(0.1)
```

### **Example 3: Multi-trace Morse Analysis**
```python
async def morse_debug():
    plot = AsyncPlot(Backend.SPARKLINE, width=100, height=10)
    plot.set_title("Morse Signal Analysis")

    plot.add_trace("magnitude", color="green")
    plot.add_trace("dit_prob", color="blue")
    plot.add_trace("dash_prob", color="red")

    await plot.show_async()

    for event in morse_events:
        await plot.add_data("magnitude", event.magnitude_norm)
        await plot.add_data("dit_prob", event.dit_probability)
        await plot.add_data("dash_prob", event.dash_probability)
```

---

## 🔧 **TODO & Implementation Plan**

### **Phase 1: Core Framework**
- [ ] `AsyncPlot` main class with matplotlib-like API
- [ ] `DataManager` with buffering and decimation
- [ ] `BaseRenderer` abstract interface
- [ ] Basic `ASCIIBackend` (refactor from current debug_display)

### **Phase 2: Braille Backend**
- [ ] `BrailleBackend` for high-density output (UTF-8 terminals)
- [ ] Terminal capability detection (fallback to ASCII)
- [ ] Smart decimation algorithms
- [ ] Auto-scaling with decay

### **Phase 3: Advanced Features**
- [ ] Multi-trace support
- [ ] Plot annotations and markers
- [ ] Export capabilities (CSV, images)
- [ ] Configuration profiles

### **Phase 4: Integration**
- [ ] Replace current debug_display with UILT
- [ ] Add matplotlib GUI backend
- [ ] Performance optimization
- [ ] Comprehensive documentation

---

## 📝 **User Guide**

### **Quick Start**
1. Import the library: `from util.graph import AsyncPlot, Backend`
2. Create plot: `plot = AsyncPlot(Backend.ASCII, 80, 20)`
3. Configure: `plot.set_ylim(-1, 1)` and `plot.set_sample_period(0.01)`
4. Start display: `await plot.show_async()`
5. Stream data: `await plot.add_data(value)`

### **Backend Selection Guide**
- **ASCII**: Universal compatibility, works over any SSH connection
  - ✅ Supports both FILLED and THIN_LINE modes
- **Braille**: Highest data density, **requires UTF-8 SSH + Unicode terminal**
  - ✅ Excellent for FILLED mode (natural density representation)
  - ⚠️ Limited THIN_LINE support (discrete 2×4 dot matrix)
- **Matplotlib**: Future GUI backend for detailed analysis
  - ✅ Full support for both modes with anti-aliasing

### **SSH Compatibility Matrix**
| Backend | Basic SSH | Modern Terminal | Corporate SSH | Embedded Systems |
|---------|-----------|-----------------|---------------|------------------|
| ASCII   | ✅ Always | ✅ Always      | ✅ Always    | ✅ Always       |
| Braille | ❌ Maybe  | ✅ Usually     | ⚠️ Depends   | ❌ Rarely       |

**Recommendation:** Start with ASCII, offer Braille as opt-in upgrade for compatible terminals.

### **Performance Tips**
- Use appropriate buffer sizes (1000-10000 samples)
- Enable decimation for high-frequency data
- Use auto-scaling judiciously (adds computation)
- Choose backend based on terminal capabilities

### **Integration with Morse Code Project**
```python
# Replace current debug_display usage
from util.graph import AsyncPlot, Backend

# Smart backend selection for SSH debugging
def create_debug_plot():
    try:
        # Try Braille first for higher resolution
        plot = AsyncPlot(Backend.BRAILLE, 80, 20)
        print("🎯 High-density Braille mode (better time resolution)")
        return plot
    except (UnicodeEncodeError, EnvironmentError):
        # Fallback to ASCII for compatibility
        plot = AsyncPlot(Backend.ASCII, 80, 20)
        print("📊 ASCII compatibility mode")
        return plot

# In signal processor
plot = create_debug_plot()
plot.set_title("Signal Analysis")
await plot.show_async()

# On each magnitude event
await plot.add_data(event.magnitude_norm)
```

### **CLI Integration**
```bash
# Test terminal capabilities first:
morsecode --test-graphics

# Force ASCII mode for compatibility:
morsecode --debug-graphics --graphics-backend=ascii audio.wav

# Try high-density Braille mode:
morsecode --debug-graphics --graphics-backend=braille audio.wav

# Auto-detect (recommended):
morsecode --debug-graphics audio.wav
```

---

*This UILT graphing library provides a powerful, flexible foundation for real-time data visualization with SSH-friendly output and matplotlib-familiar API design.*
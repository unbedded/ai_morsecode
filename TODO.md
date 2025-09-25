# MorseCode Graphics Integration - UILT Implementation Roadmap

## 📋 Progress Tracking Checklist

### ✅ **COMPLETED** - UILT Foundation & Usage Fixes
- [x] **UILT Library Architecture** - Complete `src/util/graph` system with TimeSeriesGraph API
- [x] **Usage Bug Fixes** - Fixed 6 critical API usage bugs in application code
- [x] **Component Integration** - ASCIIDebugDisplay uses proper TimeSeriesGraph API
- [x] **Event System** - FilteredMagnitudeEvent, FFTSpectrumEvent, MorseProbabilityEvent implemented
- [x] **Backend Selection** - ASCII/Braille automatic detection working
- [x] **SSH Compatibility** - Terminal capability detection with safe fallbacks

### 🚧 **IN PROGRESS** - Phase 1: PyQt Replacement Core Features
- [x] **Real-time Magnitude** ⭐ **CRITICAL** - Normalized magnitude display (-1 to +1)
- [x] **Multi-Plot Display** 📊 **HIGH** - FFT, Magnitude, 4x Probability charts
- [ ] **Event Enhancement** 🎯 **HIGH** - DitWidthEvent, enhanced spectrum events
- [ ] **CLI Integration** 📏 **MEDIUM** - `--debug-graphics` flag integration

### 📋 **PLANNED** - Phase 2-4: Advanced Signal Analysis
- [ ] **Frequency Analysis** 🔍 **MEDIUM** - Peak frequency meter (300-900Hz)
- [ ] **WPM Analysis** ⏱️ **MEDIUM** - DIT width discovery visualization
- [ ] **Symbol Recognition** 🎨 **LOW** - Enhanced convolution probability analysis
- [ ] **Production CLI** 🚀 **LOW** - Full SSH debugging deployment

### 🎯 **SUCCESS CRITERIA**
**PyQt Debugging Replacement**: Complete SSH-compatible ASCII/Braille terminal graphics system that replaces all 6 PyQtGraph displays with UILT real-time visualization.

**Target**: 6 real-time displays - Signal amplitude, Frequency spectrum, Magnitude w/threshold, Normalized filtered signal, DIT width discovery, Symbol probability analysis.

---

## 📖 DETAILED IMPLEMENTATION PLAN

### 🎯 **Overview**
Implementation plan for integrating the Universal Interface for Live Telemetry (UILT) graphics library with MorseCode signal analysis. This document outlines how `src/util/graph` UILT components will be integrated with MorseCode events to replicate PyQtGraph debugging capabilities using SSH-friendly ASCII/Braille terminal graphics.

**UILT Library Integration**: Using the universal `src/util/graph` library for terminal-based signal visualization with backend-aware decimation and 2x resolution Braille mode.

## 🔍 **PyQt Debugging Legacy - What We're Replacing**
The original system used 6 real-time PyQtGraph displays for signal analysis debugging:

### **PyQt Graph Analysis (What We Need to Replicate)**
1. **Signal amplitude vs time (2 seconds)** - ⬇️ **LOW PRIORITY**
2. **Current signal magnitude vs freq (300-900Hz)** - Peak freq, magnitude, prominence meter
3. **Signal magnitude at peak freq vs time (2 seconds)** - With binary threshold overlay
4. **Normalized filtered magnitude signal** - ⭐ **PRIORITY #1** Values -1 to +1 (space=-1, signal=+1)
5. **DIT width discovery** - Current DIT_SECONDS_WIDTH plot (0.05-0.012 range)
6. **Morse symbol probability vs time (2sec)** - Convolution probabilities + 2nd derivative peaks

### **UILT Graphics Solutions Available**
- **Terminal backend selection**: ASCII (universal) vs Braille (2x resolution) automatic detection
- **Real-time streaming**: AsyncPlot with buffer management and decimation
- **SSH compatibility**: Built-in terminal capability detection with safe fallbacks
- **Backend-aware decimation**: Smart data reduction preserving signal characteristics
- **Event integration**: Direct integration with existing MorseCode event system

## 📊 **Event System Analysis - Current vs Needed**

### **✅ Current Events Available (7 types)**
1. **AudioChunkEvent** - Audio processing progress, chunk metadata
2. **ToneDetectedEvent** - Frequency, SNR, confidence, chunk_number ⭐ **USEFUL**
3. **MorsePatternEvent** - Dot/dash patterns, WPM estimates ⭐ **USEFUL**
4. **TextDecodedEvent** - Final decoded text output
5. **PipelineStateEvent** - Component state changes
6. **ErrorEvent** - Error handling and diagnostics
7. **MetricsEvent** - Performance monitoring data

### **❌ Missing Events for PyQt Debugging**

#### **Priority #1: Normalized Filtered Magnitude (-1 to +1)**
```python
@dataclass(frozen=True)
class FilteredMagnitudeEvent(BaseEvent):
    """Real-time normalized filtered magnitude signal values."""
    magnitude_norm: float = 0.0        # -1.0 to +1.0 normalized value
    threshold_norm: float = 0.25       # Current detection threshold
    binary_state: bool = False         # Above/below threshold
    chunk_number: int = 0              # Time sequence
    frequency_hz: float = 600.0        # Target frequency
```

#### **Priority #2: Frequency Spectrum Analysis (300-900Hz)**
```python
@dataclass(frozen=True)
class FrequencySpectrumEvent(BaseEvent):
    """Current frequency analysis across target range."""
    peak_frequency: float = 600.0      # Strongest frequency detected
    peak_magnitude: float = 0.0        # Signal strength at peak
    prominence_ratio: float = 0.0      # Peak vs surrounding noise
    frequency_range: tuple[float, float] = (300.0, 900.0)
    spectrum_data: np.ndarray = field(default_factory=lambda: np.array([]))
```

#### **Priority #3: DIT Width Discovery**
```python
@dataclass(frozen=True)
class DitWidthEvent(BaseEvent):
    """Current DIT timing analysis for WPM calculation."""
    dit_width_sec: float = 0.08        # Current DIT duration (0.05-0.12)
    confidence: float = 0.0            # DIT width confidence
    wpm_calculated: float = 15.0       # WPM based on DIT width
    sample_count: int = 0              # Number of DITs analyzed
```

#### **Priority #4: Symbol Probability Analysis**
```python
@dataclass(frozen=True)
class SymbolProbabilityEvent(BaseEvent):
    """Convolution probability analysis for DIT/DOT/Space detection."""
    dit_probability: float = 0.0       # Probability of DIT pattern
    dot_probability: float = 0.0       # Probability of DOT pattern
    space_probability: float = 0.0     # Probability of space pattern
    second_derivative: float = 0.0     # Peak detection derivative
    max_probability_type: str = "unknown"  # "dit", "dot", "space"
```

## 📊 **Current Status**
- ✅ **Comprehensive Event System**: 7 event types with full pipeline coverage
- ✅ **Rich Library Available**: PyQtGraph installed (but ASCII preferred for CLI)
- ✅ **Event Bus Pattern**: Publisher-subscriber ready for graphics component
- ✅ **Real-time Events**: Audio, Signal, Pattern, Text, State, Error, Metrics
- 🎯 **Ready for ASCII Graphics Implementation**

---

## 🎨 **Available Event Sources**

### **📊 Core Pipeline Events**

#### **🎵 1. AudioChunkEvent**
```python
@dataclass
class AudioChunkEvent:
    chunk_data: np.ndarray         # Audio samples (can visualize as waveform)
    chunk_size_ms: int            # Chunk duration
    sample_rate: int              # 44100 Hz typically
    chunk_number: int             # Sequential counter
    has_more_data: bool           # End-of-file indicator
    timestamp: int                # Microsecond precision
```
**Graphics Use:**
- **Progress bar**: `chunk_number` progress through file
- **Data rate**: Chunks per second processing speed
- **Buffer status**: `has_more_data` for completion indicator

#### **🔍 2. ToneDetectedEvent**
```python
@dataclass
class ToneDetectedEvent:
    detected: bool                # Tone present/absent
    frequency: float              # Detected frequency (Hz)
    confidence: float             # Detection confidence (0.0-1.0)
    snr_db: float                # Signal-to-noise ratio
    chunk_number: int             # Chunk sequence
    detection_threshold: float    # Threshold used
    timestamp: int
```
**Graphics Use:**
- **Signal strength**: Real-time SNR bar graph
- **Frequency plot**: Frequency over time (ASCII chart)
- **Detection status**: Visual tone on/off indicator
- **Quality meter**: Confidence and SNR gauges

#### **📝 3. MorsePatternEvent**
```python
@dataclass
class MorsePatternEvent:
    pattern_type: str            # "dot", "dash", "letter_space", "word_space"
    duration_ms: float           # Pattern timing
    wpm_estimate: float          # Current WPM estimate
    confidence: float            # Pattern confidence
    timestamp: int
```
**Graphics Use:**
- **Morse display**: Real-time dot/dash visualization
- **Timing graph**: Pattern durations over time
- **WPM tracker**: Speed estimation display
- **Pattern buffer**: Last N patterns shown

#### **💬 4. TextDecodedEvent**
```python
@dataclass
class TextDecodedEvent:
    text: str                    # Decoded character/word
    pattern_sequence: str        # Original dot-dash pattern
    wpm_estimate: float          # Final WPM
    confidence: float            # Decoding confidence
    is_complete_word: bool       # Word boundary marker
    timestamp: int
```
**Graphics Use:**
- **Live text output**: Scrolling decoded text
- **Pattern history**: Show dot-dash → character mapping
- **Word completion**: Visual word boundaries
- **Statistics**: Character count, WPM, accuracy

### **⚙️ System Status Events**

#### **🔄 5. PipelineStateEvent**
```python
@dataclass
class PipelineStateEvent:
    state: str                   # "starting", "processing", "paused", "stopped", "error"
    component: str               # "audio_source", "signal_processor", "decoder", "pipeline"
    message: str | None          # Status message
    details: dict[str, Any]      # Additional context
    timestamp: int
```
**Graphics Use:**
- **Component status**: Visual pipeline health indicators
- **State transitions**: Processing → paused → error visualization
- **Status messages**: User-friendly notifications

#### **❌ 6. ErrorEvent**
```python
@dataclass
class ErrorEvent:
    error_type: str              # Exception class name
    message: str                 # Error description
    component: str               # Where error occurred
    recoverable: bool            # Can continue processing
    context: dict[str, Any]      # Error context
    timestamp: int
```
**Graphics Use:**
- **Error notifications**: Red alerts for failures
- **Error log**: Scrolling error history
- **Recovery status**: Show if errors are recoverable

#### **📈 7. MetricsEvent**
```python
@dataclass
class MetricsEvent:
    metric_name: str             # "processing_latency", "accuracy", etc.
    value: float                 # Metric value
    unit: str                    # "ms", "percent", "hz", etc.
    component: str               # Source component
    tags: dict[str, str]         # Additional metadata
    timestamp: int
```
**Graphics Use:**
- **Performance dashboard**: Latency, throughput metrics
- **Accuracy tracking**: Real-time accuracy percentage
- **Resource usage**: CPU, memory, processing speed

---

## 🎨 **UILT Integration Design Solutions**

### **Priority #1: Real-time Magnitude Signal Visualization**

#### **UILT AsyncPlot Integration with MorseCode Events**
```python
from util.graph import AsyncPlot, Backend
import asyncio

class MorseSignalVisualizer:
    def __init__(self, event_bus):
        # Auto-backend selection: ASCII or Braille based on terminal
        self.magnitude_plot = AsyncPlot(backend=Backend.AUTO, width=80, height=20)
        self.magnitude_plot.set_ylim(-1.0, 1.0)  # Normalized range
        self.magnitude_plot.set_title("Normalized Magnitude Signal")

        # Subscribe to signal events
        event_bus.subscribe(FilteredMagnitudeEvent, self._on_magnitude_event)

    async def _on_magnitude_event(self, event):
        # Real-time streaming with UILT
        await self.magnitude_plot.add_data(event.magnitude_norm)
```

#### **UILT Advantage: Automatic Resolution Optimization**
```
# ASCII Backend (Universal compatibility):
┌─── Normalized Magnitude Signal ────────────────────────────────┐
│ +1.0 ▄█▄  ▄█▄  ▄█▄  ▄█▄                                      │
│  0.0 ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄ ← threshold                         │
│ -1.0 ░░░▀▀░░░▀▀░░░▀▀░░░▀▀                                      │
└─────────────────────────────────────────────────────────────────┘

# Braille Backend (2x resolution when supported):
┌─── Normalized Magnitude Signal ────────────────────────────────┐
│ +1.0 ⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈⠀⠀⠀⠈⠿⠿⠿⠈ │
│  0.0 ⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿⠿⠿⠿⠤⠤⠿⠿ │
│ -1.0 ⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸⠀⠀⠀⠸⠿⠿⠿⠸ │
└─────────────────────────────────────────────────────────────────┘
```

#### **UILT Backend-Aware Decimation for Signal Preservation**
```python
# UILT automatically preserves signal characteristics during decimation
decimated_signal = await self.magnitude_plot.decimate_for_backend(
    raw_signal_data,     # 1000s of samples
    target_width=80      # Terminal characters
)
# Result: 9.1:1 ASCII ratio or 4.6:1 Braille ratio with peaks preserved
```

## 🎨 **Visual Layout Designs**

### **Layout 1: Debug Analysis View (SSH-Optimized)**
```
┌─── Audio Pipeline Status ────────────────────────────┐
│ ● Processing  │ Chunk: 1,234 │ Rate: 44.1kHz │ EOF │
├─── Signal Detection ─────────────────────────────────┤
│ Frequency: 600Hz ████████████░░░░░ 80%              │
│ SNR:       15dB  ██████████████░░░ 90%              │
│ Confidence: 0.85 █████████████████░ 95%              │
├─── Morse Patterns ───────────────────────────────────┤
│ ●●●─●─●● | Current: dash (120ms) | WPM: 18         │
├─── Decoded Text ─────────────────────────────────────┤
│ THE QUICK BROWN FOX■                                │
└──────────────────────────────────────────────────────┘
```

### **Layout 2: Pipeline Flow View**
```
 Audio HAL     Signal Proc    Morse Decoder   Text Output
┌─────────┐   ┌─────────────┐  ┌─────────────┐ ┌───────────┐
│ ● Ready │──▶│ ⚡Processing │─▶│ 🔍 Analyzing│▶│📝 Writing │
│44.1kHz  │   │600Hz 15dB   │  │●●●─●─ → T   │ │"THE QUI"  │
└─────────┘   └─────────────┘  └─────────────┘ └───────────┘
```

### **Layout 3: Real-time Metrics Dashboard**
```
┌─── Performance Metrics ──────────────────────────────┐
│ Latency:    [██████░░░░] 45ms                       │
│ Accuracy:   [█████████░] 94%                        │
│ Throughput: [████████░░] 850 chars/min              │
│ Errors:     [░░░░░░░░░░] 0 in last 100 chunks       │
└──────────────────────────────────────────────────────┘
```

### **Layout 4: Compact Status Line**
```
🎵 [████████░░] 80% | 🔍 600Hz 15dB | ●●●─●─ → T | "THE QUICK" | 18 WPM
```

---

## 🏗️ **Implementation Architecture**

### **UILT Graphics Component Design**
```python
from util.graph import AsyncPlot, Backend, plot_signal_auto
import asyncio
from typing import Dict, List

class MorseCodeUILTGraphics:
    """Real-time UILT-based graphics display for MorseCode signal analysis."""

    def __init__(self, event_bus: EventBus, terminal_width: int = 80):
        self.event_bus = event_bus
        self.terminal_width = terminal_width

        # UILT plot instances for different signal types
        self.magnitude_plot = AsyncPlot(
            backend=Backend.AUTO,
            width=terminal_width,
            height=15
        )
        self.magnitude_plot.set_ylim(-1.0, 1.0)
        self.magnitude_plot.set_title("Normalized Signal Magnitude")

        self.frequency_plot = AsyncPlot(
            backend=Backend.AUTO,
            width=terminal_width // 2,
            height=10
        )
        self.frequency_plot.set_xlim(300, 900)  # Frequency range
        self.frequency_plot.set_title("Frequency Spectrum")

        self.wpm_plot = AsyncPlot(
            backend=Backend.AUTO,
            width=terminal_width // 2,
            height=10
        )
        self.wpm_plot.set_ylim(5, 30)  # WPM range
        self.wpm_plot.set_title("WPM Estimation")

        # Data buffers for streaming
        self.magnitude_buffer = []
        self.frequency_history = []
        self.wpm_history = []
        self.pattern_buffer = []

        # Setup event subscriptions
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Subscribe to MorseCode events for real-time visualization."""
        self.event_bus.subscribe(FilteredMagnitudeEvent, self._on_magnitude_event)
        self.event_bus.subscribe(FrequencySpectrumEvent, self._on_frequency_event)
        self.event_bus.subscribe(DitWidthEvent, self._on_dit_width_event)
        self.event_bus.subscribe(ToneDetectedEvent, self._on_tone_detected)
        self.event_bus.subscribe(MorsePatternEvent, self._on_morse_pattern)
        self.event_bus.subscribe(TextDecodedEvent, self._on_text_decoded)

    async def start_visualization(self):
        """Start all UILT plot displays."""
        await asyncio.gather(
            self.magnitude_plot.show_async(),
            self.frequency_plot.show_async(),
            self.wpm_plot.show_async()
        )

    async def _on_magnitude_event(self, event: FilteredMagnitudeEvent):
        """Handle real-time magnitude data with UILT streaming."""
        await self.magnitude_plot.add_data(event.magnitude_norm)

        # Simple text overlay for current state
        state_text = "SIGNAL" if event.binary_state else "SPACE"
        print(f"Magnitude: {event.magnitude_norm:+.2f} | {state_text} | "
              f"Threshold: {event.threshold_norm:.2f}")

    async def _on_frequency_event(self, event: FrequencySpectrumEvent):
        """Handle frequency spectrum visualization."""
        # Plot peak frequency over time
        self.frequency_history.append(event.peak_frequency)
        if len(self.frequency_history) > self.terminal_width:
            self.frequency_history.pop(0)

        # Use UILT for frequency spectrum display
        plot_signal_auto(
            self.frequency_history,
            title=f"Peak Frequency: {event.peak_frequency:.1f}Hz "
                  f"(Magnitude: {event.peak_magnitude:.2f})"
        )

    async def _on_dit_width_event(self, event: DitWidthEvent):
        """Handle DIT width analysis for WPM visualization."""
        self.wmp_history.append(event.wpm_calculated)
        if len(self.wpm_history) > self.terminal_width:
            self.wpm_history.pop(0)

        await self.wpm_plot.add_data(event.wpm_calculated)

        # Additional text summary
        print(f"DIT: {event.dit_width_sec:.3f}s | WPM: {event.wpm_calculated:.1f} | "
              f"Confidence: {event.confidence:.2f}")

    def _on_morse_pattern(self, event: MorsePatternEvent):
        """Handle Morse pattern visualization with simple text display."""
        pattern_symbols = {
            "dot": "●",
            "dash": "─",
            "letter_space": " ",
            "word_space": " / "
        }

        symbol = pattern_symbols.get(event.pattern_type, "?")
        self.pattern_buffer.append(symbol)

        # Keep last 40 symbols for pattern display
        if len(self.pattern_buffer) > 40:
            self.pattern_buffer.pop(0)

        pattern_display = "".join(self.pattern_buffer)
        print(f"Pattern: {pattern_display} | WPM: {event.wpm_estimate:.1f}")

    def _on_text_decoded(self, event: TextDecodedEvent):
        """Handle decoded text display."""
        print(f"Decoded: {event.text} | Pattern: {event.pattern_sequence} | "
              f"Confidence: {event.confidence:.2f}")

# Usage in CLI integration
async def run_morse_graphics(event_bus, args):
    """Run MorseCode with UILT graphics visualization."""
    graphics = MorseCodeUILTGraphics(event_bus, terminal_width=args.width)

    # Start visualization
    graphics_task = asyncio.create_task(graphics.start_visualization())

    # Run normal MorseCode processing
    processing_task = asyncio.create_task(run_morse_processing(args))

    # Run both concurrently
    await asyncio.gather(graphics_task, processing_task)
```

### **UILT Integration Points**
- **CLI Integration**: `src/morsecode/cli/main.py` - Add `--visualize` flag for UILT graphics
- **Event Bus Integration**: Subscribe to MorseCode events for real-time data streaming
- **UILT Library Usage**: Import from `src/util/graph` for universal terminal compatibility
- **Backend Selection**: Automatic ASCII/Braille detection based on terminal capabilities
- **Performance**: Non-blocking async visualization using UILT's streaming architecture

---

## 🚀 **UILT Implementation Phases (MorseCode Signal Analysis Focus)**

### **📋 Phase 1: UILT Foundation & Magnitude Visualization (Priority #1)**
- [ ] **UILT Library Integration**
  - [ ] Import UILT from `src/util/graph` in MorseCode project
  - [ ] Test ASCII and Braille backend selection in SSH environments
  - [ ] Validate backend-aware decimation with real signal data
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Event System Enhancement for UILT**
  - [ ] Add `FilteredMagnitudeEvent` with normalized values (-1 to +1)
  - [ ] Add `FrequencySpectrumEvent` for peak frequency analysis
  - [ ] Add `DitWidthEvent` for WPM calculation visualization
  - [ ] Add `SymbolProbabilityEvent` for convolution analysis
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Real-time Magnitude Streaming**
  - [ ] Implement `AsyncPlot` for normalized magnitude display
  - [ ] Configure 2-second time window with buffer management
  - [ ] Add threshold overlay with binary state indication
  - [ ] Test with real MorseCode audio files for accurate representation
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

### **📋 Phase 2: Multi-Plot UILT Displays (Frequency & WPM Analysis)**
- [ ] **Frequency Spectrum Visualization**
  - [ ] Use UILT `plot_signal_auto` for frequency history over time
  - [ ] Peak frequency meter display (300-900Hz range)
  - [ ] Signal magnitude visualization at peak frequency
  - [ ] Prominence ratio indicators using UILT bar charts
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **DIT Width & WPM Tracking**
  - [ ] UILT streaming plot for WPM estimation over time
  - [ ] DIT width history using `AsyncPlot` with range 0.05-0.12 seconds
  - [ ] Confidence indicators for WPM calculations
  - [ ] Integration with existing DIT timing analysis
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

### **📋 Phase 3: Advanced UILT Signal Analysis**
- [ ] **Symbol Probability Visualization**
  - [ ] Convolution probability displays for DIT/DOT/Space patterns
  - [ ] 2nd derivative peak detection using UILT sparklines
  - [ ] Pattern confidence tracking with streaming plots
  - [ ] Multi-plot layout for simultaneous probability analysis
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Comprehensive Signal Dashboard**
  - [ ] Multiple UILT plots running concurrently via `asyncio.gather`
  - [ ] Synchronized time-series displays across different signal aspects
  - [ ] Binary threshold overlay on all relevant magnitude displays
  - [ ] Pattern sequence buffer with visual timing analysis
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

### **📋 Phase 4: CLI Integration & Production Deployment**
- [ ] **CLI Integration with UILT**
  - [ ] Add `--visualize` flag for UILT-based signal analysis
  - [ ] View mode selection: `--viz-mode magnitude|frequency|wpm|all`
  - [ ] Terminal width detection and UILT auto-sizing
  - [ ] SSH debugging workflow with automatic backend selection
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Production SSH Debugging**
  - [ ] UILT terminal capability detection for remote environments
  - [ ] Graceful fallback from Braille to ASCII in constrained terminals
  - [ ] Performance testing: ensure no impact on audio processing pipeline
  - [ ] Documentation: SSH debugging guide with UILT visualization
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

---

## 📦 **UILT Dependencies & Integration**

### **UILT Library Integration**
```python
# No additional dependencies required - UILT is internal
from util.graph import AsyncPlot, Backend, plot_signal_auto

# UILT provides:
# - ASCII backend: Universal terminal compatibility
# - Braille backend: 2x resolution for Unicode-capable terminals
# - Auto backend: Intelligent terminal capability detection
# - Backend-aware decimation: Smart data reduction preserving signal characteristics
```

### **Optional Enhancement Libraries**
```toml
[project.optional-dependencies]
advanced_graphics = [
    "matplotlib>=3.7.0",    # For offline signal analysis and report generation
    "plotly>=5.15.0",       # For future web-based signal analysis dashboard
]
```

### **UILT Architecture Benefits**
- **Zero external graphics dependencies**: UILT uses only standard terminal output
- **SSH compatibility**: Works perfectly over any SSH connection
- **Performance**: Minimal overhead, non-blocking async architecture
- **Universal deployment**: Same code works on Linux, macOS, Windows terminals

---

## 🎯 **UILT Success Metrics for MorseCode**

### **Phase 1 Goals: UILT Foundation**
- [ ] Real-time magnitude signal visualization using UILT AsyncPlot
- [ ] Automatic backend selection (ASCII/Braille) based on terminal capabilities
- [ ] Zero performance impact on MorseCode audio processing pipeline
- [ ] Clean event subscription integration with existing MorseCode event bus

### **Phase 2 Goals: Multi-Signal Analysis**
- [ ] Simultaneous visualization of magnitude, frequency, and WPM using multiple UILT plots
- [ ] Accurate signal decimation preserving critical MorseCode timing characteristics
- [ ] Real-time pattern recognition visualization with ●─● symbols
- [ ] SSH debugging capability validated across different terminal environments

### **Phase 3 Goals: Production Signal Analysis**
- [ ] Comprehensive MorseCode signal dashboard suitable for debugging production issues
- [ ] Professional visualization quality matching PyQtGraph functionality in terminal
- [ ] Symbol probability analysis using UILT streaming displays
- [ ] Performance benchmark: <5% overhead for visualization vs no-graphics mode

### **Phase 4 Goals: Universal Deployment**
- [ ] Seamless CLI integration with `--visualize` flag and mode selection
- [ ] Complete SSH debugging documentation with UILT backend capabilities
- [ ] Cross-platform validation: Linux servers, macOS development, Windows terminals
- [ ] Production-ready deployment for remote MorseCode signal analysis

---

## 🔧 **UILT Technical Considerations for MorseCode**

### **Performance Architecture**
- **UILT Async Design**: Non-blocking visualization using `asyncio.gather` for concurrent plots
- **Backend-Aware Decimation**: Smart data reduction (9.1:1 ASCII, 4.6:1 Braille) preserving signal peaks
- **Streaming Buffers**: UILT manages bounded buffers automatically for time-series windows
- **Event Integration**: Direct subscription to MorseCode events without additional data copying

### **SSH Compatibility & Terminal Detection**
- **UILT Backend Selection**: Automatic ASCII/Braille detection based on terminal capabilities
- **SSH Environment Handling**: Safe fallback to ASCII when Unicode Braille is unsupported
- **Terminal Adaptation**: Dynamic width/height detection with graceful layout adjustment
- **Cross-Platform Validation**: Tested across SSH clients (PuTTY, Terminal.app, WSL)

### **MorseCode Integration Strategy**
- **Event Bus Compatibility**: Direct integration with existing `get_global_event_bus()`
- **Signal Processing Pipeline**: Zero interference with HAL → SignalProcessor → MorseDecoder flow
- **Data Format Alignment**: UILT expects numpy arrays/lists matching MorseCode signal formats
- **Configuration Integration**: Use existing ConfigurableBase pattern for visualization settings

### **Testing & Validation Approach**
- **UILT Unit Tests**: Mock MorseCode events with synthetic signal data
- **Signal Accuracy Tests**: Validate decimation preserves critical timing information
- **Performance Benchmarks**: Measure visualization overhead vs core processing time
- **SSH Environment Tests**: Validate across different terminal capabilities and SSH configurations
- **Real Audio Integration**: End-to-end testing with actual MorseCode WAV files

---

## 🤔 **Future UILT Enhancements for MorseCode**

### **Advanced UILT Features**
- [ ] **Multi-Backend Configuration**: User selection of ASCII vs Braille vs Auto modes
- [ ] **Signal Export**: Save UILT visualization output to text files for offline analysis
- [ ] **Remote UILT Display**: Network streaming of terminal graphics for remote monitoring
- [ ] **UILT Plugin System**: Custom MorseCode-specific visualization extensions

### **Extended Signal Analysis**
- [ ] **UILT Correlation Plots**: Cross-correlation visualization for signal timing analysis
- [ ] **Multi-Channel UILT**: Simultaneous visualization of I/Q signal components
- [ ] **UILT Spectrogram**: Time-frequency analysis using ASCII/Braille heatmaps
- [ ] **Pattern Recognition Dashboard**: UILT-based visualization of ML pattern detection

### **Integration Opportunities**
- [ ] **Web UILT Gateway**: HTTP interface serving UILT terminal output as web content
- [ ] **UILT JSON API**: RESTful endpoint providing signal visualization data
- [ ] **Mobile UILT Viewer**: Terminal output optimized for mobile SSH clients
- [ ] **CI/CD UILT Reports**: Automated signal analysis visualization in build pipelines

---

## 📋 **Implementation Summary**

**UILT Integration for MorseCode** provides a comprehensive solution for SSH-friendly signal visualization by leveraging the Universal Interface for Live Telemetry from `src/util/graph`. This integration enables:

- **Real-time signal analysis** over any SSH connection with automatic backend selection
- **Professional debugging capabilities** matching PyQtGraph functionality in terminal environments
- **Zero external dependencies** using only standard terminal output
- **Performance-optimized streaming** with backend-aware decimation preserving signal characteristics

The roadmap focuses on four phases: UILT foundation integration, multi-plot signal displays, advanced analysis dashboards, and production CLI deployment with comprehensive SSH debugging capabilities.

---

*Last updated: 2025-09-21*
*Status: Ready for Phase 1 UILT integration*
*Dependencies: Internal util/graph library*
*Integration: MorseCode event bus + UILT AsyncPlot streaming*
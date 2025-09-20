# ASCII Graphics Component - Implementation Roadmap

## 🎯 **Overview**
Design and implementation plan for real-time ASCII graphics visualization of the Morse code decoder pipeline using the existing event-driven architecture.

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

## 🎨 **Visual Layout Designs**

### **Layout 1: Signal Analysis View**
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

### **Graphics Component Design**
```python
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress
from rich.text import Text
from rich.tree import Tree

class ASCIIGraphicsComponent:
    """Real-time ASCII graphics display component."""

    def __init__(self, event_bus: EventBus, layout_type: str = "signal_analysis"):
        self.console = Console()
        self.event_bus = event_bus
        self.layout_type = layout_type

        # Subscribe to all visualization events
        self._setup_subscriptions()

        # Display state
        self.signal_strength = 0.0
        self.current_frequency = 0.0
        self.decoded_text = ""
        self.morse_buffer = []
        self.processing_state = "idle"
        self.error_log = []
        self.metrics = {}

        # Rich display components
        self.layout = Layout()
        self.live_display = None

    def _setup_subscriptions(self):
        """Subscribe to all relevant events."""
        self.event_bus.subscribe(AudioChunkEvent, self._on_audio_chunk)
        self.event_bus.subscribe(ToneDetectedEvent, self._on_tone_detected)
        self.event_bus.subscribe(MorsePatternEvent, self._on_morse_pattern)
        self.event_bus.subscribe(TextDecodedEvent, self._on_text_decoded)
        self.event_bus.subscribe(PipelineStateEvent, self._on_pipeline_state)
        self.event_bus.subscribe(ErrorEvent, self._on_error)
        self.event_bus.subscribe(MetricsEvent, self._on_metrics)

    def start_display(self):
        """Start the live ASCII graphics display."""
        self._build_layout()
        self.live_display = Live(self.layout, console=self.console, refresh_per_second=10)
        self.live_display.start()

    def stop_display(self):
        """Stop the live display."""
        if self.live_display:
            self.live_display.stop()

    def _build_layout(self):
        """Build the display layout based on layout_type."""
        if self.layout_type == "signal_analysis":
            self._build_signal_analysis_layout()
        elif self.layout_type == "pipeline_flow":
            self._build_pipeline_flow_layout()
        elif self.layout_type == "metrics_dashboard":
            self._build_metrics_dashboard_layout()
        elif self.layout_type == "compact":
            self._build_compact_layout()

    # Event handlers update display state and trigger refresh
    def _on_audio_chunk(self, event: AudioChunkEvent):
        """Handle audio chunk events for progress updates."""
        self.chunk_progress = event.chunk_number
        self.sample_rate = event.sample_rate
        self.has_more_data = event.has_more_data
        self._update_display()

    def _on_tone_detected(self, event: ToneDetectedEvent):
        """Handle tone detection for signal strength visualization."""
        self.signal_strength = event.snr_db
        self.current_frequency = event.frequency
        self.detection_confidence = event.confidence
        self._update_display()

    def _on_morse_pattern(self, event: MorsePatternEvent):
        """Handle Morse patterns for real-time pattern display."""
        self.morse_buffer.append(event.pattern_type)
        if len(self.morse_buffer) > 20:  # Keep last 20 patterns
            self.morse_buffer.pop(0)
        self.current_wpm = event.wpm_estimate
        self._update_display()

    def _on_text_decoded(self, event: TextDecodedEvent):
        """Handle decoded text for output display."""
        self.decoded_text += event.text
        if len(self.decoded_text) > 100:  # Keep last 100 characters
            self.decoded_text = self.decoded_text[-100:]
        self._update_display()

    def _on_pipeline_state(self, event: PipelineStateEvent):
        """Handle pipeline state changes."""
        self.processing_state = f"{event.component}:{event.state}"
        self._update_display()

    def _on_error(self, event: ErrorEvent):
        """Handle errors for error log display."""
        self.error_log.append(f"{event.component}: {event.message}")
        if len(self.error_log) > 10:  # Keep last 10 errors
            self.error_log.pop(0)
        self._update_display()

    def _on_metrics(self, event: MetricsEvent):
        """Handle metrics for performance dashboard."""
        self.metrics[event.metric_name] = {
            'value': event.value,
            'unit': event.unit,
            'component': event.component
        }
        self._update_display()

    def _update_display(self):
        """Update the display with current state."""
        if self.live_display:
            self._build_layout()  # Rebuild with new data
```

### **Integration Points**
- **CLI Integration**: `src/morsecode/cli/main.py` - Add `--graphics` flag
- **Pipeline Integration**: `src/morsecode/pipeline/executor.py` - Optional graphics component
- **Event Bus**: Already available globally via `get_global_event_bus()`

---

## 🚀 **Implementation Phases**

### **📋 Phase 1: Basic Pipeline Status (Week 1)**
- [ ] **Component Structure**
  - [ ] Create `ASCIIGraphicsComponent` class
  - [ ] Event subscription setup
  - [ ] Basic Rich layout integration
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Pipeline Status Display**
  - [ ] Audio processing progress bar
  - [ ] Component state indicators (Ready/Processing/Error)
  - [ ] Basic text output display
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

### **📋 Phase 2: Signal Visualization (Week 2)**
- [ ] **Signal Strength Display**
  - [ ] Real-time SNR bar graphs
  - [ ] Frequency detection visualization
  - [ ] Confidence meters
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Morse Pattern Display**
  - [ ] Real-time dot/dash visualization
  - [ ] Pattern buffer (last 20 patterns)
  - [ ] WPM estimation display
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

### **📋 Phase 3: Advanced Features (Week 3)**
- [ ] **Performance Metrics Dashboard**
  - [ ] Latency tracking
  - [ ] Accuracy percentage
  - [ ] Error rate monitoring
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Interactive Features**
  - [ ] Layout switching (signal/pipeline/metrics/compact)
  - [ ] Color coding for different states
  - [ ] Error log scrolling
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

### **📋 Phase 4: CLI Integration (Week 4)**
- [ ] **Command Line Interface**
  - [ ] Add `--graphics` flag to CLI
  - [ ] Graphics layout selection option
  - [ ] Integration with existing CLI flow
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

- [ ] **Documentation & Testing**
  - [ ] Graphics component documentation
  - [ ] Unit tests for graphics component
  - [ ] Integration tests with mock events
  - [ ] **Quality Gates**: ⏳ ruff ⏳ mypy ⏳ pytest ⏳ commit ⏳ push

---

## 📦 **Dependencies**

### **Required Libraries**
```toml
[project]
dependencies = [
    # ... existing deps ...
    "rich>=13.0.0",          # ASCII graphics and layouts
    "textual>=0.38.0",       # Future TUI applications (optional)
]
```

### **Optional Enhancements**
```toml
[project.optional-dependencies]
graphics = [
    "matplotlib>=3.7.0",    # For future signal analysis plots
    "plotly>=5.15.0",       # For future web interface
]
```

---

## 🎯 **Success Metrics**

### **Phase 1 Goals**
- [ ] Real-time pipeline status visualization
- [ ] Smooth integration with existing CLI
- [ ] No performance impact on core processing
- [ ] Clean event subscription without memory leaks

### **Phase 2 Goals**
- [ ] Informative signal strength visualization
- [ ] Real-time Morse pattern display
- [ ] Accurate WPM and confidence tracking

### **Phase 3 Goals**
- [ ] Comprehensive performance dashboard
- [ ] Multiple layout options for different use cases
- [ ] Professional appearance suitable for demonstrations

### **Phase 4 Goals**
- [ ] Seamless CLI integration with `--graphics` flag
- [ ] Complete documentation and testing
- [ ] Ready for production deployment

---

## 🔧 **Technical Considerations**

### **Performance**
- **Non-blocking**: Graphics updates must not impact audio processing
- **Efficient Rendering**: 10 FPS refresh rate (100ms intervals)
- **Memory Management**: Bounded buffers for historical data
- **Event Filtering**: Subscribe only to needed event types

### **Build System**
- **Test Data**: Makefile must create `tests/generated_data/` directory if not exists (excluded from git)
- **Large Files**: `tests/data/wav/` and `tests/data/wav_low_snr/` excluded from git (4GB+ sizes)
- **CI/CD**: Ensure build scripts handle missing test data directories gracefully

### **Compatibility**
- **Terminal Support**: Works in all standard terminals
- **Color Fallback**: Graceful degradation for monochrome terminals
- **Resize Handling**: Dynamic layout adjustment for terminal size
- **Platform Independent**: Works on Linux, macOS, Windows

### **Testing Strategy**
- **Mock Event Bus**: Unit tests with synthetic events
- **Visual Regression**: Screenshot comparison for layout changes
- **Performance Tests**: Ensure no processing slowdown
- **Integration Tests**: End-to-end graphics with real audio

---

## 🤔 **Future Enhancements**

### **Advanced Features**
- [ ] **Configuration**: User-customizable layouts and colors
- [ ] **Export**: Save graphics output to text files
- [ ] **Remote Display**: Network-accessible graphics display
- [ ] **Plugin System**: Custom visualization plugins

### **Alternative Interfaces**
- [ ] **Web Dashboard**: Browser-based real-time display
- [ ] **TUI Application**: Full-screen terminal interface
- [ ] **Mobile App**: Remote monitoring via mobile interface
- [ ] **API Endpoint**: REST API for external visualization tools

---

*Last updated: 2025-09-18*
*Status: Ready for Phase 1 implementation*
*Dependencies: Rich library integration*
*Integration: Event bus subscription pattern*
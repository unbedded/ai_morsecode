# Parameter Tree: Graphics Display Configuration

```
📊 MORSE CODE GRAPHICS PARAMETERS HIERARCHY
═══════════════════════════════════════════════

🌍 GLOBAL SYSTEM PARAMETERS (Application-wide)
├─ 🎵 Audio Configuration (src/morsecode/components/audio/schema.py)
│   ├─ sample_rate_hz: 44,100 Hz          # Audio input sample rate
│   ├─ chunk_size_ms: 50 ms               # Audio processing chunk size
│   └─ wav_filename: str | None           # Optional audio file input
│
├─ 🔍 Signal Processing (src/morsecode/components/signal/signal_config_schema.py)
│   ├─ frequency_hz: 600 Hz               # Target CW frequency
│   ├─ sample_rate_hz: 44,100 Hz          # Signal processing rate (mirrors audio)
│   ├─ rolling_buffer_seconds: 3.0 sec    # Signal analysis window
│   └─ cutoff_hz: 15.0 Hz                 # Lowpass filter for timing
│
├─ 🧠 Convolution Processing (src/morsecode/components/decoder/conv_adapter.py)
│   ├─ _max_buffer_duration_ms: 500 ms    # Convolution processing interval
│   ├─ _probability_threshold: 0.08       # Pattern recognition threshold
│   └─ → DERIVED: effective_rate = 2 Hz   # 1 probability per 500ms
│
└─ 📋 Decoder Timing (src/morsecode/components/decoder/schema.py)
    ├─ wpm: 15 WPM                        # Words per minute
    ├─ dot_duration_ms: 80.0 ms           # Dot element duration
    └─ min_silence_ms: 200.0 ms           # Word boundary detection

🎨 GRAPHICS-SPECIFIC PARAMETERS (Per Display Instance)
├─ 🖼️  Display Dimensions (src/morsecode/components/graphics/schema.py)
│   ├─ enabled: True                      # Enable/disable graphics
│   ├─ width: 80 chars                    # Display width in characters
│   ├─ height: 6 rows                     # Display height in text rows
│   ├─ backend: "auto" | "ascii" | "braille"  # Rendering backend choice
│   └─ buffer_size: 1000 samples          # Signal buffer capacity
│
├─ ⏱️  Timing Control (Instance Variables)
│   ├─ update_rate_hz: 10.0 Hz           # Display refresh rate (NOT for time axis!)
│   ├─ display_time_span_sec: 4.0 sec    # Time span → full display width
│   ├─ _calculated_sample_rate_hz: ~2 Hz # AUTO-CALCULATED from timing intervals
│   └─ _last_timing: float | None        # Last timing value for rate calculation
│
└─ 🎯 Backend-Specific Resolution (src/util/graph/utils/decimation.py)
    ├─ ASCII Backend
    │   ├─ effective_resolution: width × 1    # 1 data point per character
    │   └─ horizontal_density: 1.0            # 1:1 mapping
    │
    └─ Braille Backend
        ├─ effective_resolution: width × 2    # 2 data points per character
        └─ horizontal_density: 2.0            # 2:1 mapping (left+right columns)

🔄 PARAMETER FLOW & RELATIONSHIPS
═══════════════════════════════════

🎵 Audio (44.1kHz)
   ↓ [50ms chunks]
🔍 Signal Processing (44.1kHz)
   ↓ [FFT + filtering]
🧠 Convolution (500ms buffer)
   ↓ [1 probability per 500ms = 2Hz effective rate]
🎨 Graphics Display
   ├─ Calculates: _calculated_sample_rate_hz ≈ 2 Hz
   ├─ Maps: 4.0 sec span → full display width
   ├─ Decimates: Using backend-aware resolution
   └─ Renders: At 10 Hz refresh rate

⚠️  CRITICAL RELATIONSHIPS
═══════════════════════════════
├─ Time Axis Scaling: _calculated_sample_rate_hz ÷ display_time_span_sec
├─ Width Calculation: data_duration_sec ÷ display_time_span_sec × width
├─ Decimation Target: backend.effective_resolution (60 ASCII vs 120 Braille)
└─ Pattern Width: convolution_interval (500ms) × calculated_rate (2Hz) = 1.0

🔧 DEBUG PARAMETERS (Key Values to Monitor)
═══════════════════════════════════════════

GLOBAL SYSTEM TIMING:
├─ Audio chunk interval: 50ms → 20 chunks/sec
├─ Convolution interval: 500ms → 2 probabilities/sec
├─ Expected graphics rate: ~2 Hz (auto-calculated)
└─ Display refresh: 10 Hz (independent of time axis)

GRAPHICS INSTANCE SCALING:
├─ display_time_span_sec: 4.0 sec → full width
├─ Pattern should occupy: 500ms ÷ 4000ms = 12.5% width
├─ ASCII resolution: 80 chars → 10 chars per pattern
└─ Braille resolution: 160 points → 20 points per pattern

🐛 OLD BUGS (Now Fixed):
═══════════════════════════
❌ Used update_rate_hz (10Hz) for time axis → 5x width error
❌ Hardcoded display_time_span_sec = 4.0 → not configurable
✅ Now uses _calculated_sample_rate_hz (2Hz) → correct width
✅ Now configurable display_time_span_sec parameter
```
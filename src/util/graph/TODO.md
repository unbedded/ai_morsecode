# UTIL Graph System - TODO & Enhancement Roadmap

## 📋 Progress Tracking Checklist

### ✅ **COMPLETED** - System Architecture & Usage Fixes
- [x] **Deep Usage Audit** - Fixed 6 critical usage bugs in application code
- [x] **API Standardization** - Migrated `graphics_display.py` to proper TimeSeriesGraph API
- [x] **Buffer Management** - Eliminated manual buffer management conflicts
- [x] **Timestamp Consistency** - Standardized to sample-driven approach across all components
- [x] **Duplicate Cleanup** - Removed duplicate `graphics_display.py` file
- [x] **Code Quality** - All ruff/mypy checks pass, imports work correctly

### 🚧 **IN PROGRESS** - Visual Enhancement Implementation
- [ ] **Y-Axis Labels** ⭐ **CRITICAL** - Smart formatting with minimal width
- [ ] **X-Axis Labels** ⭐ **CRITICAL** - Time/sample indicators
- [ ] **Tick Marks** 📏 **HIGH** - Professional axis intersections
- [ ] **Axis Titles** 🎯 **HIGH** - `set_xlabel()`, `set_ylabel()` API

### 📋 **PLANNED** - Advanced Features
- [ ] **Grid Lines** 📈 **MEDIUM** - Optional background grid
- [ ] **Scientific Notation** 📈 **MEDIUM** - Large number formatting
- [ ] **Legend Support** 🎨 **LOW** - Multi-series identification
- [ ] **Color Coding** 🎨 **LOW** - ASCII color support
- [ ] **Export Capabilities** ⚡ **LOW** - Save rendered output

### 🎯 **SUCCESS CRITERIA**
**Target Visual Output (Matplotlib-Style)**:
```
3.0 ┤                                ▁▅▇▇▅▁             ▂▅▇▇▄
2.5 ┤                               ▅██████▄           ▅██████▃
2.0 ┤                              █████████▇▆▁     ▂▇█████████▇▅
1.5 ┤██████████████████████████████████████████▄▂▁▂▅█████████████
    └┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴──
     0   5  10  15  20  25  30  35  40  45  50  55  60  65  70
                               Time (samples)
```

---

## 📖 IMPLEMENTATION PLAN

### Overview

This document outlines the comprehensive improvement plan for the UTIL Graph System to achieve matplotlib-style professional visualization in ASCII/Braille text terminals. The system currently has excellent architecture and index-based x-axis implementation, but lacks visual polish and axis labeling.

## Current Status Assessment ✅

### What's Working Well
- ✅ **Index-Based X-Axis**: Proper `display_indices` implementation with time-based positioning
- ✅ **Smart Decimation**: Backend-aware decimation with sliding window mode
- ✅ **Clean API**: Simple `add_data_point()` and `render()` interface
- ✅ **Backend Abstraction**: ASCII/Braille backends with performance optimization
- ✅ **Time Management**: Sample rate detection and synchronization
- ✅ **Buffer Management**: Automatic sliding window with configurable time spans
- ✅ **C++ Ready**: Interface designed for efficient porting

### Current Visual Output
```
                                ▁▅▇▇▅▁             ▂▅▇▇▄
                               ▅██████▄           ▅██████▃
                              █████████▇▆▁     ▂▇█████████▇▅
██████████████████████████████████████████▄▂▁▂▅█████████████
```

### Target Visual Output (Matplotlib-Style)
```
3.0 ┤                                ▁▅▇▇▅▁             ▂▅▇▇▄
2.5 ┤                               ▅██████▄           ▅██████▃
2.0 ┤                              █████████▇▆▁     ▂▇█████████▇▅
1.5 ┤██████████████████████████████████████████▄▂▁▂▅█████████████
    └┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴──
     0   5  10  15  20  25  30  35  40  45  50  55  60  65  70
                               Time (samples)
```

## Enhancement Roadmap

### 🚨 Priority 1: Essential Matplotlib Features

#### 1.1 Y-Axis Labels ⭐ **CRITICAL**
- [ ] **Task**: Add numeric scale labels on the left edge with intelligent formatting
- [ ] **Files**: `src/util/graph/backends/ascii_backend.py`, `braille_backend.py`
- [ ] **Method**: `_render_y_axis_labels(height, y_min, y_max) -> list[str]`
- [ ] **Smart Formatting Goals**:
  - **Minimize width**: `100.0` → `100`, `10.1` → `10` (drop unnecessary decimals)
  - **Integer preference**: Show integers when possible to save space
  - **Consistent alignment**: Right-align labels for clean appearance
  - **Dynamic range display**: For autoscaling, show max range at top only
- [ ] **Examples**:
  ```
  # Clean integer formatting (saves space)
   10 ┤
    5 ┤
    0 ┤

  # Minimal decimal places only when needed
  2.5 ┤
  1.3 ┤
  0.1 ┤

  # Dynamic autoscale - range at top only
     ┤ (0-157)
   75 ┤
    0 ┤
  ```

#### 1.2 X-Axis Labels ⭐ **CRITICAL**
- [ ] **Task**: Add time/sample indicators on bottom edge
- [ ] **Files**: `src/util/graph/backends/ascii_backend.py`, `braille_backend.py`
- [ ] **Method**: `_render_x_axis_labels(width, time_span) -> list[str]`

#### 1.3 Axis Titles 🎯 **HIGH**
- [ ] **API**: `set_xlabel("Time (s)")`, `set_ylabel("Amplitude (V)")`

#### 1.4 Tick Marks 📏 **HIGH**
- [ ] **Characters**: `┤├┬┴┼` for axis intersections

### 📈 Priority 2: Professional Polish
- Grid lines, scientific notation, title positioning, units support

### 🎨 Priority 3: Advanced Features
- Legend support, subplot management, color coding, annotations

### ⚡ Priority 4: Performance & Quality
- Auto-formatting, overflow handling, resize support, export capabilities

## Implementation Strategy

### Phase 1: Critical Visual Features (Week 1)
1. **Y-axis labels** - Biggest visual impact
2. **X-axis labels** - Complete the axis system
3. **Basic tick marks** - Professional appearance

## Smart Y-Axis Formatting Algorithm

### Formatting Logic
```python
def smart_format_number(value: float, data_range: float) -> str:
    """Intelligently format numbers for minimal width Y-axis labels."""

    # Step 1: Check if value is effectively an integer
    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))

    # Step 2: Determine optimal decimal places based on range
    if data_range > 100:
        return f"{value:.0f}"      # No decimals for large ranges
    elif data_range > 10:
        return f"{value:.1f}".rstrip('0').rstrip('.')  # Max 1 decimal
    elif data_range > 1:
        return f"{value:.2f}".rstrip('0').rstrip('.')  # Max 2 decimals
    else:
        return f"{value:.3f}".rstrip('0').rstrip('.')  # Max 3 for small ranges
```

### Dynamic Range Display
```python
# For autoscaling mode - show range info compactly
def render_autoscale_indicator(y_min: float, y_max: float) -> str:
    """Show range at top of Y-axis without disrupting graph positioning."""
    if y_min == 0:
        return f"┤ (0-{smart_format_number(y_max, y_max - y_min)})"
    else:
        min_str = smart_format_number(y_min, y_max - y_min)
        max_str = smart_format_number(y_max, y_max - y_min)
        return f"┤ ({min_str}-{max_str})"
```

### Target User Experience
```python
# Simple, matplotlib-like API with smart formatting
graph = TimeSeriesGraph(width=80, height=10)
graph.set_xlabel("Time (s)")
graph.set_ylabel("Amplitude (V)")
graph.set_title("Signal Analysis")
graph.grid(True)

# Automatic smart Y-axis formatting:
# - Large values: "1000 ┤" not "1000.0 ┤"
# - Clean integers: "5 ┤" not "5.00 ┤"
# - Minimal decimals: "1.5 ┤" not "1.500 ┤"
# - Autoscale range: "┤ (0-157)" at top when needed
```

---
**Document Status**: v1.0 • **Last Updated**: 2025-01-25 • **Next Review**: After Priority 1
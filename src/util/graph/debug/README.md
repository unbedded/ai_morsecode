# UILT Debug Tools

This directory contains debugging and development tools used during the creation of the UILT (Universal Interface for Live Telemetry) library. These tools are part of the UILT library structure and provide debugging capabilities for backend development and testing.

## 📁 Files

### **Core Development Demos**
- **`demo_clean_braille.py`** - Clean Braille implementation with lookup tables
- **`demo_graph_modes.py`** - ASCII vs Braille backend comparison demos
- **`test_braille_sine.py`** - Real-time Braille sine wave animation test

### **Debugging Tools**
- **`debug_braille_pairs.py`** - Debug Braille character pair combinations
- **`debug_braille_columns.py`** - Debug Braille left/right column mapping
- **`debug_braille_columns2.py`** - Advanced Braille column mapping tests
- **`debug_simple_braille.py`** - Simple Braille rendering tests
- **`debug_step_signal.py`** - Step signal rendering analysis
- **`debug_braille.py`** - Basic Braille character testing
- **`debug_ramp.py`** - Ramp wave rendering debugging
- **`debug_decimation.py`** - Data decimation algorithm testing

### **Orientation Fixes**
- **`fix_braille_mapping.py`** - Fixed Braille Unicode dot mapping
- **`test_correct_orientation.py`** - Correct Braille fill direction tests
- **`test_clean_ascending.py`** - Clean ascending pattern validation
- **`test_braille_fix.py`** - Braille orientation fix validation
- **`test_multirow_braille.py`** - Multi-row Braille rendering tests
- **`test_ported_graph.py`** - Ported graph functionality validation

## 🎯 Purpose

These tools were essential for:
1. **Debugging Braille Unicode mapping** - Correct dot positioning
2. **Fixing orientation issues** - Proper bottom-up fill for positive values
3. **Testing backend functionality** - Ensuring 2x resolution advantage
4. **Validating signal fidelity** - Preserving timing characteristics

## 🚀 Usage

Most of these files can be run directly:
```bash
python src/util/graph/debug/demo_clean_braille.py
python src/util/graph/debug/test_braille_sine.py
python src/util/graph/debug/debug_simple_braille.py
```

## 📝 Historical Context

These files document the development process of solving the "upside-down Braille" issue and implementing correct backend-aware decimation. They show the iterative process of:

1. Initial Braille implementation attempts
2. Discovery of orientation problems
3. Unicode dot mapping fixes
4. Final validation of correct behavior

## 🔧 For Future Development

Keep these tools for:
- **Regression testing** - Ensure fixes remain correct
- **New backend development** - Reference patterns for other output formats
- **Performance debugging** - Isolate specific rendering issues
- **Educational purposes** - Show development methodology

---

**Note**: For production usage, use the examples in `src/util/graph/examples/` instead.
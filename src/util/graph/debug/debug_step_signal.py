#!/usr/bin/env python3
"""Debug the step signal rendering in Braille backend."""

import os
import sys

# Add src to path for util imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph import BrailleBackend


def debug_step_signal():
    """Debug step signal rendering step by step."""
    print("🔍 Debug Step Signal Rendering\n")

    # Create simple step signal: 0.0, 0.2, 0.8, 1.0, 0.6, -0.2, -0.8, -0.5, 0.1, 0.9
    step_signal = [0.0, 0.2, 0.8, 1.0, 0.6, -0.2, -0.8, -0.5, 0.1, 0.9]
    print(f"Step signal: {step_signal}")

    # Create Braille backend
    backend = BrailleBackend(width=5, height=1, title="Debug Step")
    backend.plot(step_signal)

    print(f"Y-axis range: {backend.y_min} to {backend.y_max}")

    # Manual calculation check
    y_range = backend.y_max - backend.y_min
    print(f"Y-range: {y_range}")

    print("\nValue normalization check:")
    for i, value in enumerate(step_signal[:10]):  # First 10 values
        norm = (value - backend.y_min) / y_range
        norm = max(0.0, min(1.0, norm))
        dots = int(norm * 4)  # 0-4 dots
        print(f"  {i}: value={value:5.1f} → norm={norm:.3f} → dots={dots}")

    # Render
    result = backend.render_braille()
    print(f"\nBraille result: {result[0]}")

    # Expected pattern: Should go from low to high values
    print("\nExpected pattern analysis:")
    print("  0.0 → 0 dots (⠀)")
    print("  0.2 → 1 dot  (should show ⠁)")
    print("  0.8 → 3 dots (should show ⠇)")
    print("  1.0 → 4 dots (should show ⡇)")
    print("  0.6 → 2 dots (should show ⠃)")


def test_simple_ramp():
    """Test with simple ramp to verify orientation."""
    print("\n🧪 Simple Ramp Test\n")

    # Simple ramp: 0, 0.25, 0.5, 0.75, 1.0
    ramp = [0.0, 0.25, 0.5, 0.75, 1.0]
    print(f"Ramp: {ramp}")

    backend = BrailleBackend(width=3, height=1)  # 3 chars = 6 data points, but we only have 5
    backend.plot(ramp)

    result = backend.render_braille()
    print(f"Braille: {result[0]}")

    print("\nExpected progression:")
    print("  0.00 → 0 dots → ⠀")
    print("  0.25 → 1 dot  → ⠁")
    print("  0.50 → 2 dots → ⠃")
    print("  0.75 → 3 dots → ⠇")
    print("  1.00 → 4 dots → ⡇")
    print("  Should see: ⠀⠃⡇ or similar progression")


def test_individual_lookup():
    """Test individual Braille character lookup."""
    print("\n🔬 Individual Lookup Test\n")

    backend = BrailleBackend(width=1, height=1)

    # Test specific dot patterns
    test_patterns = [
        (0, 0, "empty"),
        (1, 0, "1 left dot"),
        (2, 0, "2 left dots"),
        (3, 0, "3 left dots"),
        (4, 0, "4 left dots"),
    ]

    for left_dots, right_dots, desc in test_patterns:
        char = backend._positive_lookup.get((left_dots, right_dots), "?")
        print(f"  {desc}: ({left_dots},{right_dots}) → {char}")


if __name__ == "__main__":
    debug_step_signal()
    test_simple_ramp()
    test_individual_lookup()

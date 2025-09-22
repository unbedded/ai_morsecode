#!/usr/bin/env python3
"""Quick test to verify Braille rendering fix."""

from demo_graph_modes import generate_ramp_wave, print_plot, render_braille_filled, render_braille_thin_line


def main():
    """Test Braille rendering fix."""
    print("🧪 Testing Braille Rendering Fix\n")

    # Generate simple test data
    ramp_data = generate_ramp_wave(length=20, cycles=2)  # Shorter for easier analysis

    print(f"Data: {[f'{x:.2f}' for x in ramp_data]}")
    print("Expected: Smooth ramps 0→1→0→1\n")

    # Test filled mode
    print("🔲 BRAILLE FILLED:")
    filled = render_braille_filled(ramp_data, width=20, height=4)
    labels = ["1.0", "0.7", "0.3", "0.0"]
    print_plot(filled, "Ramp Test - Filled", labels)

    # Test thin line mode
    print("\n📈 BRAILLE THIN LINE:")
    thin = render_braille_thin_line(ramp_data, width=20, height=4)
    print_plot(thin, "Ramp Test - Thin Line", labels)

    print("\n✅ Visual inspection: Do these show proper ramp patterns?")


if __name__ == "__main__":
    main()

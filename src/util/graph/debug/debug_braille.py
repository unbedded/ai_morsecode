#!/usr/bin/env python3
"""Debug Braille character encoding."""


def test_braille_progression():
    """Test if Braille patterns show smooth progression."""
    print("🧪 Testing Braille Character Progression\n")

    # Test simple ramp: 0.0 -> 0.1 -> 0.2 -> 0.3 -> 0.4
    test_data = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

    print("Expected: Smooth progression from empty to full")
    print("Data:", [f"{x:.1f}" for x in test_data])

    # Test single column progression first
    print("\n🔍 Single column Braille patterns (should be smooth):")
    single_patterns = ["⠀", "⠁", "⠃", "⠇", "⠏", "⠟", "⠿", "⠿"]
    for i, pattern in enumerate(single_patterns):
        print(f"  Level {i}: {pattern}")

    # Test what my function produces
    from demo_graph_modes import create_braille_char

    print("\n🔍 My create_braille_char function output:")
    for i in range(8):
        char = create_braille_char(i, 0)  # Left column only
        print(f"  Level {i}: {char}")

    print("\n🔍 Right column only:")
    for i in range(8):
        char = create_braille_char(0, i)  # Right column only
        print(f"  Level {i}: {char}")


if __name__ == "__main__":
    test_braille_progression()

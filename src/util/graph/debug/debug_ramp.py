#!/usr/bin/env python3
"""Debug ramp wave rendering step by step."""


def debug_ramp_step_by_step():
    """Show exactly what happens with ramp data."""
    print("🧪 Debug Ramp Wave Step by Step\n")

    # Simple test: 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
    test_data = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    width = 3  # 3 chars = 6 data points
    height = 4

    print(f"Data: {test_data}")
    print(f"Width: {width} chars, Height: {height} rows")
    print("Each Braille char should encode 2 data points\n")

    total_levels = height * 8  # 32 levels

    print("🔍 Processing each Braille character:")
    for col in range(width):
        left_idx = col * 2
        right_idx = col * 2 + 1

        left_value = test_data[left_idx] if left_idx < len(test_data) else 0.0
        right_value = test_data[right_idx] if right_idx < len(test_data) else 0.0

        print(f"\nChar {col}:")
        print(f"  Left data[{left_idx}] = {left_value}")
        print(f"  Right data[{right_idx}] = {right_value}")

        # Convert to levels
        left_level = int(left_value * (total_levels - 1))
        right_level = int(right_value * (total_levels - 1))

        print(f"  Left level: {left_level} (of 31)")
        print(f"  Right level: {right_level} (of 31)")

        # Calculate target rows
        left_target_row = height - 1 - (left_level // 8)
        right_target_row = height - 1 - (right_level // 8)
        left_dot_level = left_level % 8
        right_dot_level = right_level % 8

        print(f"  Left target row: {left_target_row}, dot level: {left_dot_level}")
        print(f"  Right target row: {right_target_row}, dot level: {right_dot_level}")

    print("\n🎯 Expected: Should see smooth progression in each row!")


if __name__ == "__main__":
    debug_ramp_step_by_step()

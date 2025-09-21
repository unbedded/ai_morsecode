#!/usr/bin/env python3
"""Demo script showing filled vs thin line graph modes.

This script demonstrates the difference between filled and thin line
visualization modes using ASCII and Braille characters. Run from CLI to see
the visual difference before implementing the full UILT architecture.

Usage:
    python demo_graph_modes.py
"""

import math
import os
import sys
import time
from typing import List


def generate_ramp_wave(length: int = 40, cycles: int = 4) -> List[float]:
    """Generate a sawtooth/ramp wave from 0 to 1."""
    values = []
    for i in range(length):
        # Create sawtooth pattern that goes 0->1->0->1
        cycle_pos = (i * cycles) / length
        ramp_value = cycle_pos % 1.0  # 0 to 1
        values.append(ramp_value)
    return values


def render_ascii_filled(data: List[float], width: int = 50, height: int = 8) -> List[str]:
    """Render data as filled ASCII plot (current style)."""
    if not data:
        return [" " * width for _ in range(height)]

    # Downsample data to fit width
    if len(data) > width:
        step = len(data) / width
        downsampled = [data[int(i * step)] for i in range(width)]
    else:
        downsampled = data + [0.0] * (width - len(data))

    # ASCII block characters for 8 levels
    block_chars = " ▁▂▃▄▅▆▇█"

    rows = []
    for row in range(height):
        row_chars = []
        for col in range(width):
            value = downsampled[col]
            # Convert to level (0-1 -> 0 to height*8)
            level = int(value * (height * 8 - 1))

            # Which row does this level belong to? (top=0, bottom=height-1)
            target_row = height - 1 - (level // 8)
            char_level = level % 8

            if row < target_row:
                # Above signal - empty
                char = " "
            elif row == target_row:
                # Signal row - show level
                char = block_chars[char_level]
            else:
                # Below signal - filled
                char = "█"

            row_chars.append(char)
        rows.append("".join(row_chars))

    return rows


def test_braille_support() -> bool:
    """Test if terminal supports Braille characters."""
    try:
        # Check locale
        lang = os.environ.get('LANG', '')
        if not lang.endswith('.UTF-8'):
            return False

        # Test basic Braille rendering
        test_chars = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
        print(f"Braille test: {test_chars}", end='', flush=True)
        print('\r' + ' ' * 30 + '\r', end='', flush=True)  # Clear test line
        return True
    except UnicodeEncodeError:
        return False


def render_braille_filled(data: List[float], width: int = 50, height: int = 4) -> List[str]:
    """Render data as filled Braille plot (2x horizontal resolution)."""
    if not data:
        return ['⠀' * width for _ in range(height)]

    # Braille advantage: 2x horizontal resolution (left + right columns)
    effective_width = width * 2  # Each Braille char can show 2 data points

    # Downsample data to fit effective resolution
    if len(data) > effective_width:
        step = len(data) / effective_width
        downsampled = [data[int(i * step)] for i in range(effective_width)]
    else:
        downsampled = data + [0.0] * (effective_width - len(data))

    # Braille dot patterns for different vertical levels (0-7)
    # Using proper left/right column combinations
    dot_patterns = {
        # Format: (left_col_level, right_col_level) -> braille_char
        (0, 0): '⠀',  # Empty
        (1, 0): '⠁', (0, 1): '⠈', (1, 1): '⠉',  # Bottom dots
        (2, 0): '⠃', (0, 2): '⠘', (2, 2): '⠛',  # Mid-bottom
        (3, 0): '⠇', (0, 3): '⠸', (3, 3): '⠿',  # Higher levels
        (4, 0): '⠏', (0, 4): '⠰', (4, 4): '⠿',  # Even higher
        (7, 7): '⠿',  # Full block
    }

    rows = []
    total_levels = height * 8  # 4 rows × 8 vertical levels per Braille char

    for row in range(height):
        row_chars = []
        for col in range(width):
            # Get two data points for this Braille character
            left_idx = col * 2
            right_idx = col * 2 + 1

            left_value = downsampled[left_idx] if left_idx < len(downsampled) else 0.0
            right_value = downsampled[right_idx] if right_idx < len(downsampled) else 0.0

            # Convert both values to levels
            left_level = int(left_value * (total_levels - 1))
            right_level = int(right_value * (total_levels - 1))
            left_level = max(0, min(total_levels - 1, left_level))
            right_level = max(0, min(total_levels - 1, right_level))

            # Determine target rows for both columns
            left_target_row = height - 1 - (left_level // 8)
            right_target_row = height - 1 - (right_level // 8)
            left_dot_level = left_level % 8
            right_dot_level = right_level % 8

            # Determine what to show in this row
            left_show = 0
            right_show = 0

            if row < left_target_row:
                left_show = 0  # Above signal
            elif row == left_target_row:
                # Fix: if at max level (level 31), show full even if dot_level=0
                if left_level == total_levels - 1:
                    left_show = 7  # Max level - show full
                else:
                    left_show = max(1, min(left_dot_level, 7))  # At least 1 dot, never empty at signal level
            else:
                left_show = 7  # Below signal - filled

            if row < right_target_row:
                right_show = 0  # Above signal
            elif row == right_target_row:
                # Fix: if at max level (level 31), show full even if dot_level=0
                if right_level == total_levels - 1:
                    right_show = 7  # Max level - show full
                else:
                    right_show = max(1, min(right_dot_level, 7))  # At least 1 dot, never empty at signal level
            else:
                right_show = 7  # Below signal - filled

            # Create Braille character combining both columns
            char = create_braille_char(left_show, right_show)
            row_chars.append(char)

        rows.append(''.join(row_chars))

    return rows


def create_braille_char(left_level: int, right_level: int) -> str:
    """Create Braille character from left and right column levels (0-7)."""
    # Simplified mapping - in real implementation, we'd have full 8x8 matrix
    if left_level == 0 and right_level == 0:
        return '⠀'
    elif left_level == 7 and right_level == 7:
        return '⠿'
    elif left_level > 0 and right_level == 0:
        patterns = ['⠀', '⠁', '⠃', '⠇', '⠏', '⠟', '⠿', '⠿']
        return patterns[min(left_level, 7)]
    elif left_level == 0 and right_level > 0:
        patterns = ['⠀', '⠈', '⠘', '⠸', '⠰', '⠿', '⠿', '⠿']
        return patterns[min(right_level, 7)]
    else:
        # Both have signal - combine patterns (simplified)
        combined_patterns = ['⠀', '⠉', '⠛', '⠿', '⠿', '⠿', '⠿', '⠿']
        avg_level = (left_level + right_level) // 2
        return combined_patterns[min(avg_level, 7)]


def render_braille_thin_line(data: List[float], width: int = 50, height: int = 4) -> List[str]:
    """Render data as thin line Braille plot (2x horizontal resolution)."""
    if not data:
        return ['⠀' * width for _ in range(height)]

    # Braille advantage: 2x horizontal resolution (left + right columns)
    effective_width = width * 2  # Each Braille char can show 2 data points

    # Downsample data to fit effective resolution
    if len(data) > effective_width:
        step = len(data) / effective_width
        downsampled = [data[int(i * step)] for i in range(effective_width)]
    else:
        downsampled = data + [0.0] * (effective_width - len(data))

    rows = []
    total_levels = height * 8  # 4 rows × 8 vertical levels per Braille char

    for row in range(height):
        row_chars = []
        for col in range(width):
            # Get two data points for this Braille character
            left_idx = col * 2
            right_idx = col * 2 + 1

            left_value = downsampled[left_idx] if left_idx < len(downsampled) else 0.0
            right_value = downsampled[right_idx] if right_idx < len(downsampled) else 0.0

            # Convert both values to levels
            left_level = int(left_value * (total_levels - 1))
            right_level = int(right_value * (total_levels - 1))
            left_level = max(0, min(total_levels - 1, left_level))
            right_level = max(0, min(total_levels - 1, right_level))

            # Determine target rows for both columns
            left_target_row = height - 1 - (left_level // 8)
            right_target_row = height - 1 - (right_level // 8)
            left_dot_level = left_level % 8
            right_dot_level = right_level % 8

            # Show only dots at signal level (thin line)
            left_show = left_dot_level if row == left_target_row else 0
            right_show = right_dot_level if row == right_target_row else 0

            # Create thin line Braille character
            char = create_thin_line_braille_char(left_show, right_show)
            row_chars.append(char)

        rows.append(''.join(row_chars))

    return rows


def create_thin_line_braille_char(left_level: int, right_level: int) -> str:
    """Create thin line Braille character from left and right column levels."""
    # Single dots only (no filling)
    if left_level == 0 and right_level == 0:
        return '⠀'
    elif left_level > 0 and right_level == 0:
        # Left column only
        left_dots = ['⠀', '⠁', '⠂', '⠄', '⠈', '⠐', '⠠', '⡀']
        return left_dots[min(left_level, 7)]
    elif left_level == 0 and right_level > 0:
        # Right column only
        right_dots = ['⠀', '⠈', '⠘', '⠸', '⠰', '⠿', '⠿', '⠿']
        return right_dots[min(right_level, 7)]
    else:
        # Both columns have dots - combine single dots
        combined_dots = ['⠀', '⠉', '⠊', '⠋', '⠌', '⠍', '⠎', '⠏']
        avg_level = (left_level + right_level) // 2
        return combined_dots[min(avg_level, 7)]


def render_ascii_thin_line(data: List[float], width: int = 50, height: int = 8) -> List[str]:
    """Render data as thin line ASCII plot (new style)."""
    if not data:
        return [" " * width for _ in range(height)]

    # Downsample data to fit width
    if len(data) > width:
        step = len(data) / width
        downsampled = [data[int(i * step)] for i in range(width)]
    else:
        downsampled = data + [0.0] * (width - len(data))

    # ASCII characters for different line parts
    line_chars = " ▁▂▃▄▅▆▇█"

    rows = []
    for row in range(height):
        row_chars = []
        for col in range(width):
            value = downsampled[col]
            # Convert to level (0-1 -> 0 to height*8)
            level = int(value * (height * 8 - 1))

            # Which row does this level belong to? (top=0, bottom=height-1)
            target_row = height - 1 - (level // 8)
            char_level = level % 8

            if row == target_row:
                # Show the signal at this row
                char = line_chars[char_level]
            else:
                # Empty space
                char = " "

            row_chars.append(char)
        rows.append("".join(row_chars))

    return rows


def print_plot(lines: List[str], title: str, y_labels: List[str] = None):
    """Print a plot with title and optional Y-axis labels."""
    if y_labels is None:
        y_labels = ["1.0", "0.7", "0.5", "0.3", "0.1"]

    width = len(lines[0]) if lines else 50

    print(f"\n{title}")
    print("┌─" + "─" * width + "─┐")

    for i, line in enumerate(lines):
        if i < len(y_labels):
            label = f"{y_labels[i]:>4}"
        else:
            label = "    "
        print(f"│{label} {line} │")

    print("└─" + "─" * width + "─┘")


def main():
    """Demo the different graph rendering modes."""
    print("=" * 70)
    print("🎯 UILT Graph Mode Demo - ASCII vs Braille, Filled vs Thin Line")
    print("=" * 70)

    # Test Braille support
    print("\n🧪 Testing terminal capabilities...")
    braille_supported = test_braille_support()
    lang = os.environ.get('LANG', 'not set')
    ssh = 'SSH_CONNECTION' in os.environ

    print(f"   LANG: {lang}")
    print(f"   SSH: {'Yes' if ssh else 'No'}")
    print(f"   Braille: {'✅ Supported' if braille_supported else '❌ Not supported'}")

    if not braille_supported:
        print("   💡 Tip: Try 'export LANG=en_US.UTF-8' for Braille support")

    # Generate test data
    print("\n📊 Generating sawtooth wave data...")
    ramp_data = generate_ramp_wave(length=100, cycles=4)  # More data to show resolution difference

    # Show the raw data
    print(f"   Data points: {len(ramp_data)}")
    print(f"   Range: {min(ramp_data):.2f} to {max(ramp_data):.2f}")
    print(f"   Sample values: {[f'{x:.2f}' for x in ramp_data[:8]]}...")

    print(f"\n🎯 Resolution comparison for width=50:")
    print(f"   ASCII Backend:   50 chars = 50 data points")
    print(f"   Braille Backend: 50 chars = 100 data points (2x resolution!)")

    time.sleep(1)

    # =================================================================
    # ASCII BACKEND DEMOS
    # =================================================================
    print("\n" + "=" * 50)
    print("📊 ASCII BACKEND DEMOS")
    print("=" * 50)

    # ASCII Filled mode
    print("\n🔲 ASCII - FILLED MODE:")
    filled_lines = render_ascii_filled(ramp_data, width=50, height=8)
    y_labels = ["1.0", "0.85", "0.7", "0.55", "0.4", "0.25", "0.1", "0.0"]
    print_plot(filled_lines, "Ramp Wave - ASCII Filled", y_labels)

    time.sleep(1)

    # ASCII Thin line mode
    print("\n📈 ASCII - THIN LINE MODE:")
    thin_lines = render_ascii_thin_line(ramp_data, width=50, height=8)
    print_plot(thin_lines, "Ramp Wave - ASCII Thin Line", y_labels)

    # =================================================================
    # BRAILLE BACKEND DEMOS
    # =================================================================
    if braille_supported:
        print("\n" + "=" * 50)
        print("⠿ BRAILLE BACKEND DEMOS")
        print("=" * 50)

        time.sleep(1)

        # Braille Filled mode
        print("\n🔲 BRAILLE - FILLED MODE (high density):")
        braille_filled = render_braille_filled(ramp_data, width=50, height=4)
        braille_labels = ["1.0", "0.65", "0.35", "0.0"]
        print_plot(braille_filled, "Ramp Wave - Braille Filled", braille_labels)

        time.sleep(1)

        # Braille Thin line mode
        print("\n📈 BRAILLE - THIN LINE MODE (limited):")
        braille_thin = render_braille_thin_line(ramp_data, width=50, height=4)
        print_plot(braille_thin, "Ramp Wave - Braille Thin Line", braille_labels)

        print("\n⚠️  Note: Braille thin lines are limited by discrete 2×4 dot matrix")

    else:
        print("\n" + "=" * 50)
        print("⠿ BRAILLE BACKEND DEMOS")
        print("=" * 50)
        print("\n❌ Braille not supported in this terminal")
        print("   Try: export LANG=en_US.UTF-8")
        print("   Or install Unicode fonts: sudo apt install fonts-noto")

    # =================================================================
    # BACKEND COMPARISON
    # =================================================================
    print("\n" + "=" * 50)
    print("🎯 BACKEND COMPARISON")
    print("=" * 50)

    print("\n📊 ASCII Backend:")
    print("   ✅ Universal compatibility (works everywhere)")
    print("   ✅ Good filled mode support")
    print("   ✅ Excellent thin line support")
    print("   ⚠️  Lower resolution (8 levels per character)")

    if braille_supported:
        print("\n⠿ Braille Backend:")
        print("   ✅ High density (32 levels in same space)")
        print("   ✅ Excellent filled mode support")
        print("   ❌ Poor thin line support (discrete dots)")
        print("   ⚠️  Requires UTF-8 terminal + Unicode fonts")

    print("\n🎯 Key Insights:")
    print("   • FILLED: Shows area under curve (energy visualization)")
    print("   • THIN LINE: Shows exact signal path (waveform analysis)")
    print("   • ASCII: Universal compatibility, good for both modes")
    print("   • Braille: High density but best for filled mode only")

    # =================================================================
    # BONUS: SINE WAVE COMPARISON
    # =================================================================
    print("\n" + "=" * 50)
    print("🌊 BONUS: SINE WAVE COMPARISON")
    print("=" * 50)

    time.sleep(1)

    sine_data = [0.5 + 0.5 * math.sin(2 * math.pi * i / 12) for i in range(50)]

    print("\n📊 ASCII Sine Wave:")
    sine_filled = render_ascii_filled(sine_data, width=50, height=6)
    sine_labels = ["1.0", "0.8", "0.6", "0.4", "0.2", "0.0"]
    print_plot(sine_filled, "Sine - ASCII Filled", sine_labels)

    sine_thin = render_ascii_thin_line(sine_data, width=50, height=6)
    print_plot(sine_thin, "Sine - ASCII Thin Line", sine_labels)

    if braille_supported:
        print("\n⠿ Braille Sine Wave:")
        sine_braille_filled = render_braille_filled(sine_data, width=50, height=4)
        braille_sine_labels = ["1.0", "0.65", "0.35", "0.0"]
        print_plot(sine_braille_filled, "Sine - Braille Filled", braille_sine_labels)

    print(f"\n🎉 Demo complete! Ready to implement UILT with backend selection.")


if __name__ == "__main__":
    main()
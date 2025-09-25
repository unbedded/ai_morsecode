#!/usr/bin/env python3
"""Test mimicking exact Morse code behavior: 10Hz vs 1Hz TimeSeriesGraph updates.

This reproduces how the actual Morse decoder updates graphs:
- Magnitude events: 10Hz (every 100ms)
- Probability events: 1Hz (every 1000ms)
- Both use TimeSeriesGraph API (not direct backend calls)
"""

import asyncio
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from util.graph.time_series_graph import TimeSeriesGraph


class MorseSignalSource:
    """Mimics how Morse decoder generates signals."""

    def __init__(self):
        """Initialize the signal source."""
        self.start_time = time.time()

    def get_magnitude_value(self, current_time: float) -> float:
        """Mimics magnitude events - slow square wave for testing."""
        # 0.1 Hz square wave (10 second period) - slow enough for 1Hz sampling
        cycle_position = (current_time * 0.1) % 1.0
        return 0.8 if cycle_position < 0.5 else 0.2

    def get_probability_value(self, current_time: float) -> float:
        """Mimics probability events - same signal, different updates."""
        # Same 0.1 Hz square wave, but updated less frequently
        cycle_position = (current_time * 0.1) % 1.0
        return 0.8 if cycle_position < 0.5 else 0.2


class MorseDisplay:
    """Mimics the debug_display.py behavior exactly."""

    def __init__(self):
        """Initialize the display with TimeSeriesGraphs."""
        # Create TimeSeriesGraphs exactly like debug_display.py
        self.magnitude_graph = TimeSeriesGraph(
            width=60,
            height=4,
            time_window_sec=5.0,
            backend="ascii",
            title="Magnitude (10Hz)",
            sample_rate_hz=10.0,  # 10 Hz updates (every 100ms)
            y_min=0.0,
            y_max=1.0,
            auto_scale=False,
        )

        self.probability_graph = TimeSeriesGraph(
            width=60,
            height=4,
            time_window_sec=5.0,
            backend="ascii",
            title="Probability (1Hz)",
            sample_rate_hz=1.0,  # 1 Hz updates (every 1000ms)
            y_min=0.0,
            y_max=1.0,
            auto_scale=False,
        )

        # Timing tracking
        self.last_magnitude_update = 0.0
        self.last_probability_update = 0.0
        self.magnitude_updates = 0
        self.probability_updates = 0

    def update(self, signal_source: MorseSignalSource, current_time: float):
        """Update graphs at their respective rates."""
        # Magnitude updates: every 100ms (10 Hz) - SAMPLE-DRIVEN
        if current_time - self.last_magnitude_update >= 0.1:
            value = signal_source.get_magnitude_value(current_time)
            self.magnitude_graph.add_data_point(value)  # No timestamp!
            self.last_magnitude_update = current_time
            self.magnitude_updates += 1

        # Probability updates: every 1000ms (1 Hz) - SAMPLE-DRIVEN
        if current_time - self.last_probability_update >= 1.0:
            value = signal_source.get_probability_value(current_time)
            self.probability_graph.add_data_point(value)  # No timestamp!
            self.last_probability_update = current_time
            self.probability_updates += 1

    def render(self) -> tuple[list[str], list[str]]:
        """Render both graphs."""
        mag_lines = self.magnitude_graph.render()
        prob_lines = self.probability_graph.render()
        return mag_lines, prob_lines


async def demo_morse_behavior():
    """Demo showing the actual Morse decoder behavior."""
    print("🎯 MORSE CODE BEHAVIOR TEST")
    print("=" * 50)
    print("Mimicking exactly how debug_display.py updates graphs:")
    print("- Magnitude: 10Hz updates (every 100ms) via TimeSeriesGraph")
    print("- Probability: 1Hz updates (every 1000ms) via TimeSeriesGraph")
    print("- Same 50% duty cycle signal, different update rates")
    print()
    print("Expected: Both should scroll proportionally to their update rates")
    print("Problem: If probability advances slowly, we've found the bug!")
    print()

    signal_source = MorseSignalSource()
    display = MorseDisplay()

    start_time = time.time()
    demo_duration = 10.0

    print("Press Ctrl+C to stop early...")
    print()

    try:
        while time.time() - start_time < demo_duration:
            current_time = time.time() - start_time

            # Update displays exactly like Morse decoder
            display.update(signal_source, current_time)

            # Render every 100ms for smooth display
            mag_lines, prob_lines = display.render()

            # Clear and show
            print("\033[H\033[J", end="")  # Clear screen

            elapsed = time.time() - start_time
            remaining = demo_duration - elapsed
            print(f"🔍 Morse Behavior Test - Time: {elapsed:.1f}s (remaining: {remaining:.1f}s)")
            print(f"Updates: Magnitude={display.magnitude_updates}, Probability={display.probability_updates}")
            print()

            print("📊 MAGNITUDE GRAPH (10Hz updates - every 100ms):")
            print("─" * 65)
            for line in mag_lines:
                width = len(line.rstrip())
                print(f"  {line} (width: {width})")
            print()

            print("📊 PROBABILITY GRAPH (1Hz updates - every 1000ms):")
            print("─" * 65)
            for line in prob_lines:
                width = len(line.rstrip())
                print(f"  {line} (width: {width})")
            print()

            # Get buffer stats for analysis
            mag_stats = display.magnitude_graph.get_stats()
            prob_stats = display.probability_graph.get_stats()

            print("BUFFER ANALYSIS:")
            print(f"  Magnitude:   {mag_stats['buffer_size']} samples, {mag_stats['actual_time_span_sec']:.2f}s span")
            print(f"  Probability: {prob_stats['buffer_size']} samples, {prob_stats['actual_time_span_sec']:.2f}s span")

            # Calculate scrolling ratio
            mag_time_per_sample = (
                mag_stats["actual_time_span_sec"] / mag_stats["buffer_size"] if mag_stats["buffer_size"] > 0 else 0
            )
            prob_time_per_sample = (
                prob_stats["actual_time_span_sec"] / prob_stats["buffer_size"] if prob_stats["buffer_size"] > 0 else 0
            )

            if mag_time_per_sample > 0 and prob_time_per_sample > 0:
                ratio = prob_time_per_sample / mag_time_per_sample
                expected_ratio = 10.0  # 10Hz vs 1Hz = 10x ratio
                print(f"  Time ratio:  {ratio:.1f}x (expected: {expected_ratio:.1f}x)")

                if abs(ratio - expected_ratio) < 2.0:
                    status = "✅ GOOD"
                else:
                    status = "❌ SLOW"
                print(f"  Status:      {status}")

            await asyncio.sleep(0.1)  # Update display every 100ms

    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")

    elapsed = time.time() - start_time
    print(f"\n📊 Final Results ({elapsed:.1f}s):")
    print(f"  Magnitude updates:   {display.magnitude_updates} ({display.magnitude_updates / elapsed:.1f}/sec)")
    print(f"  Probability updates: {display.probability_updates} ({display.probability_updates / elapsed:.1f}/sec)")

    # Final analysis
    mag_stats = display.magnitude_graph.get_stats()
    prob_stats = display.probability_graph.get_stats()

    mag_time_per_sample = (
        mag_stats["actual_time_span_sec"] / mag_stats["buffer_size"] if mag_stats["buffer_size"] > 0 else 0
    )
    prob_time_per_sample = (
        prob_stats["actual_time_span_sec"] / prob_stats["buffer_size"] if prob_stats["buffer_size"] > 0 else 0
    )

    if mag_time_per_sample > 0 and prob_time_per_sample > 0:
        actual_ratio = prob_time_per_sample / mag_time_per_sample
        expected_ratio = 10.0

        print("\n🔍 SCROLLING ANALYSIS:")
        print(f"  Expected ratio: {expected_ratio:.1f}x (1Hz should scroll 10x MORE per update than 10Hz)")
        print(f"  Actual ratio:   {actual_ratio:.1f}x")

        if abs(actual_ratio - expected_ratio) < 2.0:
            print("  ✅ SUCCESS: Probability graphs scroll proportionally!")
            return "FIXED"
        else:
            print("  ❌ BUG: Probability graphs advance too slowly!")
            print("     This reproduces the original Morse decoder issue")
            return "BROKEN"

    return "INCONCLUSIVE"


async def main():
    """Main test function."""
    print("🎯 MORSE CODE GRAPH UPDATE BEHAVIOR TEST")
    print("=" * 60)
    print("This test exactly mimics how the Morse decoder updates its graphs:")
    print("- Uses TimeSeriesGraph API (not direct backend calls)")
    print("- Different sample rates: 10Hz vs 1Hz")
    print("- Same signal source for both graphs")
    print()

    result = await demo_morse_behavior()

    print("\n" + "=" * 60)
    if result == "FIXED":
        print("🎉 SUCCESS: Graph scrolling works correctly!")
        print("   - Both graphs use full width")
        print("   - Scrolling ratio is proportional")
        print("   - TimeSeriesGraph handles different sample rates properly")
    elif result == "BROKEN":
        print("⚠️  ISSUE FOUND: This reproduces the Morse decoder bug!")
        print("   - Probability graphs advance slower than expected")
        print("   - Need to investigate TimeSeriesGraph implementation")
        print("   - May need different approach than the working demo")
    else:
        print("❓ INCONCLUSIVE: Need more data to determine status")

    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
        sys.exit(1)

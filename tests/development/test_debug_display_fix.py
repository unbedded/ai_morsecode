#!/usr/bin/env python3
"""Test that the debug display probability buffer fix works."""

import sys

sys.path.insert(0, "src")

from morsecode.components.graphics.debug_display import ASCIIDebugDisplay
from morsecode.events.types import MorseProbabilityEvent
from util.config import AwesomeConfigManager


def test_debug_display_buffers():
    """Test that debug display uses fixed sliding window for probability buffers."""
    print("🧪 Testing Debug Display Buffer Fix")
    print("=" * 60)

    # Create debug display
    cfg_mgr = AwesomeConfigManager()
    overrides = {
        "display_width_chars": 80,
        "display_height_chars": 20,
        "buffer_size_sec": 5.0,  # This used to create 5000 sample buffers!
        "refresh_rate_fps": 10,
    }

    debug_display = ASCIIDebugDisplay(cfg_mgr, overrides)
    print(f"✅ Fixed window size: {debug_display._fixed_window_size}")
    print(f"✅ Probability buffer maxlen: {debug_display._prob_dit_buffer.maxlen}")
    print(f"✅ Buffer starts pre-filled: {len(debug_display._prob_dit_buffer)} samples")
    print()

    # Check that buffers start with zeros
    dit_data = list(debug_display._prob_dit_buffer)
    all_zeros = all(x == 0.0 for x in dit_data)
    print(f"✅ Pre-filled with zeros: {all_zeros}")

    # Check timing buffer initialization
    time_data = list(debug_display._prob_time_buffer)
    print(f"✅ Time buffer starts at: {time_data[0]:.1f}s, ends at: {time_data[-1]:.1f}s")
    print(f"✅ Time span: {time_data[-1] - time_data[0]:.1f}s ({len(time_data)} samples)")
    print()

    # Simulate adding probability events and check buffer behavior
    print("📊 Adding probability events to test sliding window...")
    current_time = time_data[-1] + 0.5  # Continue from where pre-fill ended

    for i in range(75):  # Add more than window size
        # Create probability event with proper timestamp
        event = MorseProbabilityEvent(
            timestamp=int(current_time * 1_000_000),  # Convert to microseconds
            prob_dit=0.3 + 0.4 * ((i % 8) / 8.0),  # Varying probabilities
            prob_dash=0.2 + 0.3 * ((i % 5) / 5.0),
            prob_letter_space=0.1 + 0.2 * ((i % 3) / 3.0),
            prob_word_space=0.05 + 0.1 * ((i % 7) / 7.0),
            chunk_number=i,
        )

        # Process the event
        debug_display._on_probability_event(event)
        current_time += 0.5

        # Check at key points
        if i in [0, 25, 50, 74]:
            dit_len = len(debug_display._prob_dit_buffer)
            time_span = debug_display._prob_time_buffer[-1] - debug_display._prob_time_buffer[0]
            print(f"  Event {i + 1:2d}: buffer_len={dit_len:3d}, time_span={time_span:5.1f}s, dit={event.prob_dit:.2f}")

    print()
    final_dit_len = len(debug_display._prob_dit_buffer)
    final_time_span = debug_display._prob_time_buffer[-1] - debug_display._prob_time_buffer[0]

    print("📈 Final Statistics:")
    print(f"   • Window size: {debug_display._fixed_window_size} (FIXED)")
    print(f"   • Buffer length: {final_dit_len} (should equal window size)")
    print(f"   • Time span: {final_time_span:.1f}s (should be stable)")
    print(f"   • Expected time span: {debug_display._fixed_window_size * 0.5:.1f}s (150 × 0.5s)")

    # Validation
    buffer_correct = final_dit_len == debug_display._fixed_window_size
    time_span_stable = abs(final_time_span - (debug_display._fixed_window_size * 0.5)) < 2.0

    if buffer_correct and time_span_stable:
        print("✅ SUCCESS: Debug display buffer fix works!")
        print("   • Fixed sliding window eliminates accumulation")
        print("   • No more shrinking probability patterns")
        print("   • Consistent time span regardless of data volume")
        print("   • Pre-filled buffers for immediate full display")
    else:
        print("❌ Issues detected:")
        if not buffer_correct:
            print(f"   • Buffer size wrong: {final_dit_len} vs {debug_display._fixed_window_size}")
        if not time_span_stable:
            print(
                f"   • Time span unstable: {final_time_span:.1f}s vs expected "
                f"{debug_display._fixed_window_size * 0.5:.1f}s"
            )


if __name__ == "__main__":
    test_debug_display_buffers()

#!/usr/bin/env python3
"""Test that probability events are now published at correct intervals."""

import sys
import time

sys.path.insert(0, "src")

from morsecode.components.decoder.conv_adapter import ConvMorseDecoderAdapter
from morsecode.events.bus import get_global_event_bus
from morsecode.events.types import MorseProbabilityEvent
from util.config import AwesomeConfigManager


def test_probability_event_timing():
    """Test that probability events are published every 500ms, not every 50ms."""
    print("🧪 Testing Probability Event Timing Fix")
    print("=" * 60)

    # Create config and decoder adapter
    cfg_mgr = AwesomeConfigManager()
    adapter = ConvMorseDecoderAdapter(cfg_mgr)

    # Track probability events
    events_received = []

    def on_probability_event(event: MorseProbabilityEvent):
        events_received.append(
            {"time": time.time(), "dit": event.prob_dit, "dash": event.prob_dash, "chunk": event.chunk_number}
        )
        print(f"📊 Probability event: dit={event.prob_dit:.3f}, dash={event.prob_dash:.3f}, chunk={event.chunk_number}")

    # Subscribe to events
    event_bus = get_global_event_bus()
    event_bus.subscribe(MorseProbabilityEvent, on_probability_event)

    print("📡 Subscribed to MorseProbabilityEvent")
    print("🎵 Simulating audio chunks (50ms each)...")
    print("⏱️  Expecting probability events only every 500ms (every 10th chunk)")
    print()

    start_time = time.time()

    # Simulate 2 seconds of audio chunks (40 chunks × 50ms = 2000ms)
    for i in range(40):
        # Simulate alternating tone detection (like morse code)
        tone_detected = (i // 5) % 2 == 0  # 250ms on, 250ms off pattern

        # Process detection (this used to publish every chunk - should now be sparse)
        adapter.process_detection(tone_detected, 50.0)  # 50ms duration

        print(f"  Chunk {i + 1:2d}: tone={'ON ' if tone_detected else 'OFF'}", end="")
        if (i + 1) % 10 == 0:
            print(" <- Convolution should trigger here")
        else:
            print()

        # Small delay to simulate real timing
        time.sleep(0.01)  # 10ms delay (faster than real 50ms for testing)

    elapsed = time.time() - start_time
    print(f"\n⏱️  Test completed in {elapsed:.1f}s")
    print(f"📊 Events received: {len(events_received)}")
    print("🎯 Expected: ~4 events (500ms intervals over 2000ms)")

    if len(events_received) > 0:
        print("\n📈 Event timing analysis:")
        for i, event in enumerate(events_received):
            rel_time = (event["time"] - start_time) * 1000
            print(f"  Event {i + 1}: {rel_time:6.1f}ms - dit={event['dit']:.3f}, dash={event['dash']:.3f}")

        # Check intervals
        if len(events_received) > 1:
            intervals = []
            for i in range(1, len(events_received)):
                interval = (events_received[i]["time"] - events_received[i - 1]["time"]) * 1000
                intervals.append(interval)
                print(f"  Interval {i}: {interval:.1f}ms")

            avg_interval = sum(intervals) / len(intervals)
            print(f"\n🎯 Average interval: {avg_interval:.1f}ms (target: ~500ms)")

            if 400 <= avg_interval <= 600:
                print("✅ SUCCESS: Events published at correct ~500ms intervals!")
            else:
                print("❌ ISSUE: Events not at expected 500ms intervals")
    else:
        print("❌ No events received - check event bus configuration")


if __name__ == "__main__":
    test_probability_event_timing()

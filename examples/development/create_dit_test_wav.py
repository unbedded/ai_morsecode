#!/usr/bin/env python3
"""Create synthetic WAV file with DITs for morse engine analysis.

This script generates a clean test WAV file containing only DITs at a specific WPM
to isolate and analyze sample rate issues in the morse decoding engine.
"""

import sys
import wave
from pathlib import Path

import numpy as np


def generate_dit_sequence(
    wpm: int, dit_count: int, frequency_hz: float = 600.0, sample_rate: int = 44100
) -> np.ndarray:
    """Generate a sequence of DITs at specified WPM.

    Args:
        wpm: Words per minute (standard Morse timing)
        dit_count: Number of DITs to generate
        frequency_hz: Tone frequency in Hz
        sample_rate: Audio sample rate in Hz

    Returns:
        Audio signal as numpy array
    """
    # Calculate timing based on WPM
    # Standard: 1 WPM = 5 characters per minute
    # Each character averages 50 dits of timing
    # So 1 WPM = 50 dits per minute = 50/60 dits per second
    dit_duration_sec = 1.2 / wpm  # Duration of one dit in seconds

    # Morse timing ratios (all relative to dit duration)
    dit_on_time = dit_duration_sec
    dit_off_time = dit_duration_sec  # Space between elements
    letter_space_time = dit_duration_sec * 3  # Space between letters

    print(f"Timing for {wpm} WPM:")
    print(f"  Dit duration: {dit_on_time * 1000:.1f}ms")
    print(f"  Element space: {dit_off_time * 1000:.1f}ms")
    print(f"  Letter space: {letter_space_time * 1000:.1f}ms")
    print()

    # Calculate total duration
    total_duration = dit_count * (dit_on_time + dit_off_time) + letter_space_time  # Add final letter space
    total_samples = int(total_duration * sample_rate)

    print(f"Total audio duration: {total_duration:.2f} seconds")
    print(f"Total samples: {total_samples}")
    print()

    # Generate time array
    time = np.linspace(0, total_duration, total_samples, endpoint=False)

    # Initialize signal array
    signal = np.zeros(total_samples)

    # Generate each dit
    current_time = 0.0
    for dit_num in range(dit_count):
        print(f"Dit {dit_num + 1}: {current_time:.3f}s to {current_time + dit_on_time:.3f}s")

        # Calculate sample indices for this dit
        start_sample = int(current_time * sample_rate)
        end_sample = int((current_time + dit_on_time) * sample_rate)

        # Generate sine wave for this dit
        dit_samples = end_sample - start_sample
        dit_time = np.linspace(0, dit_on_time, dit_samples, endpoint=False)
        dit_signal = np.sin(2 * np.pi * frequency_hz * dit_time)

        # Apply basic envelope to avoid clicks
        fade_samples = min(100, dit_samples // 10)  # 10% fade or 100 samples max
        if fade_samples > 0:
            # Linear fade in/out
            fade_in = np.linspace(0, 1, fade_samples)
            fade_out = np.linspace(1, 0, fade_samples)
            dit_signal[:fade_samples] *= fade_in
            dit_signal[-fade_samples:] *= fade_out

        # Insert dit into signal
        signal[start_sample:end_sample] = dit_signal

        # Move to next dit (include element space)
        current_time += dit_on_time + dit_off_time

    print()
    print(f"Signal range: [{np.min(signal):.3f}, {np.max(signal):.3f}]")
    print(f"RMS level: {np.sqrt(np.mean(signal**2)):.3f}")

    return signal


def write_wav_file(filename: str, signal: np.ndarray, sample_rate: int) -> None:
    """Write signal to WAV file.

    Args:
        filename: Output WAV filename
        signal: Audio signal array
        sample_rate: Sample rate in Hz
    """
    # Convert to 16-bit PCM
    # Scale to use most of the dynamic range
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal_scaled = signal / max_val * 0.8  # Leave some headroom
    else:
        signal_scaled = signal

    signal_int16 = (signal_scaled * 32767).astype(np.int16)

    # Write WAV file
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal_int16.tobytes())

    print(f"WAV file written: {filename}")
    print(f"  Duration: {len(signal) / sample_rate:.2f} seconds")
    print(f"  Sample rate: {sample_rate} Hz")
    print("  Bit depth: 16-bit")
    print(f"  File size: {Path(filename).stat().st_size} bytes")


def main():
    """Create synthetic dit test files."""
    print("=== SYNTHETIC DIT WAV GENERATOR ===")
    print()

    # Test parameters
    wpm = 15  # Match the 15 WPM test file for comparison
    dit_count = 10  # 10 clean DITs for analysis
    frequency_hz = 600.0  # Standard tone frequency
    sample_rate = 44100  # CD quality

    output_file = "synthetic_dits_15wpm.wav"

    print(f"Generating {dit_count} DITs at {wpm} WPM")
    print(f"Tone frequency: {frequency_hz} Hz")
    print(f"Sample rate: {sample_rate} Hz")
    print()

    # Generate signal
    signal = generate_dit_sequence(wpm, dit_count, frequency_hz, sample_rate)

    # Write to file
    write_wav_file(output_file, signal, sample_rate)

    print()
    print("=== MORSE ENGINE ANALYSIS READY ===")
    print()
    print("Next steps:")
    print(f"1. Test with: python -m morsecode.cli.main --dbg-graphics {output_file}")
    print("2. Compare sample rates between:")
    print("   - FFT magnitude events (should be ~50 Hz)")
    print("   - Probability events (should match dit timing)")
    print("3. Look for:")
    print("   - Proper dit detection in probability charts")
    print("   - Correct timing alignment between charts")
    print("   - Sample rate scaling consistency")

    return output_file


if __name__ == "__main__":
    try:
        output_file = main()
        print(f"\n✅ SUCCESS: Created {output_file}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

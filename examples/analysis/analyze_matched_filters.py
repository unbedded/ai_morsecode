#!/usr/bin/env python3
"""Analysis of proper symmetric matched filters for Morse code detection.

This demonstrates what SHOULD happen when convolving symmetric patterns
with square wave inputs - you get symmetric triangular correlation responses.
"""

import numpy as np


def create_symmetric_dit_filter(duration_samples: int) -> np.ndarray:
    """Create symmetric matched filter for dit detection.

    This is what a proper matched filter should look like - symmetric!
    """
    # Simple rectangular filter - symmetric by definition
    filter_pattern = np.ones(duration_samples)
    return filter_pattern / np.sum(filter_pattern)  # Normalize


def create_symmetric_dash_filter(duration_samples: int) -> np.ndarray:
    """Create symmetric matched filter for dash detection."""
    # Rectangular filter 3x longer than dit
    filter_pattern = np.ones(duration_samples)
    return filter_pattern / np.sum(filter_pattern)  # Normalize


def create_square_wave_dit(duration_samples: int, total_samples: int) -> np.ndarray:
    """Create ideal square wave dit signal."""
    signal = np.zeros(total_samples)
    signal[:duration_samples] = 1.0
    return signal


def create_square_wave_dash(duration_samples: int, total_samples: int) -> np.ndarray:
    """Create ideal square wave dash signal (3x dit duration)."""
    signal = np.zeros(total_samples)
    signal[:duration_samples] = 1.0
    return signal


def analyze_convolution_symmetry():
    """Analyze what happens when you convolve symmetric filters with square waves."""
    # Parameters for 20 WPM (60ms dit, 180ms dash)
    sample_rate = 1000  # 1ms resolution
    dit_duration_ms = 60
    dash_duration_ms = 180

    dit_samples = dit_duration_ms
    dash_samples = dash_duration_ms
    total_samples = 400  # 400ms total analysis window

    print("=== SYMMETRIC MATCHED FILTER ANALYSIS ===")
    print(f"Dit duration: {dit_duration_ms}ms ({dit_samples} samples)")
    print(f"Dash duration: {dash_duration_ms}ms ({dash_samples} samples)")
    print()

    # Create symmetric matched filters
    dit_filter = create_symmetric_dit_filter(dit_samples)
    dash_filter = create_symmetric_dash_filter(dash_samples)

    print("DIT FILTER (symmetric):")
    print(f"Length: {len(dit_filter)} samples")
    print(f"Sum: {np.sum(dit_filter):.3f} (should be 1.0)")
    print(f"Symmetric: {np.allclose(dit_filter, dit_filter[::-1])}")
    print()

    print("DASH FILTER (symmetric):")
    print(f"Length: {len(dash_filter)} samples")
    print(f"Sum: {np.sum(dash_filter):.3f} (should be 1.0)")
    print(f"Symmetric: {np.allclose(dash_filter, dash_filter[::-1])}")
    print()

    # Test signals
    dit_signal = create_square_wave_dit(dit_samples, total_samples)
    dash_signal = create_square_wave_dash(dash_samples, total_samples)

    # Perform convolution (this is what matched filtering actually does)
    dit_response_to_dit = np.convolve(dit_signal, dit_filter, mode="same")
    dit_response_to_dash = np.convolve(dash_signal, dit_filter, mode="same")

    dash_response_to_dit = np.convolve(dit_signal, dash_filter, mode="same")
    dash_response_to_dash = np.convolve(dash_signal, dash_filter, mode="same")

    print("=== CONVOLUTION RESULTS (Expected Symmetric Triangular) ===")

    # Analyze dit filter response to dit signal
    dit_peak_idx = np.argmax(dit_response_to_dit)
    dit_peak_value = np.max(dit_response_to_dit)

    print("Dit filter + Dit signal:")
    print(f"  Peak at sample {dit_peak_idx} (should be ~{dit_samples // 2})")
    print(f"  Peak value: {dit_peak_value:.3f}")
    print("  Expected symmetric triangular response: YES")

    # Check symmetry around peak
    half_width = 20  # Check 20 samples each side
    if dit_peak_idx >= half_width and dit_peak_idx + half_width < len(dit_response_to_dit):
        left_side = dit_response_to_dit[dit_peak_idx - half_width : dit_peak_idx]
        right_side = dit_response_to_dit[dit_peak_idx + 1 : dit_peak_idx + 1 + half_width]
        symmetry = np.allclose(left_side, right_side[::-1], atol=0.01)
        print(f"  Symmetric around peak: {symmetry}")
    print()

    # Analyze dash filter response to dash signal
    dash_peak_idx = np.argmax(dash_response_to_dash)
    dash_peak_value = np.max(dash_response_to_dash)

    print("Dash filter + Dash signal:")
    print(f"  Peak at sample {dash_peak_idx} (should be ~{dash_samples // 2})")
    print(f"  Peak value: {dash_peak_value:.3f}")
    print("  Expected symmetric triangular response: YES")

    # Check symmetry around peak
    if dash_peak_idx >= half_width and dash_peak_idx + half_width < len(dash_response_to_dash):
        left_side = dash_response_to_dash[dash_peak_idx - half_width : dash_peak_idx]
        right_side = dash_response_to_dash[dash_peak_idx + 1 : dash_peak_idx + 1 + half_width]
        symmetry = np.allclose(left_side, right_side[::-1], atol=0.01)
        print(f"  Symmetric around peak: {symmetry}")
    print()

    print("=== CROSS-CORRELATION (Selectivity) ===")
    print(f"Dit filter + Dash signal peak: {np.max(dit_response_to_dash):.3f}")
    print(f"Dash filter + Dit signal peak: {np.max(dash_response_to_dit):.3f}")
    print()
    print("Lower cross-correlation = better selectivity")

    # Show the actual correlation responses
    print("\n=== SAMPLE CORRELATION RESPONSES ===")
    print("Dit filter response to Dit signal (first 100ms):")
    for i in range(0, min(100, len(dit_response_to_dit)), 10):
        print(f"  t={i:2d}ms: {dit_response_to_dit[i]:.3f}")

    print("\nDash filter response to Dash signal (first 200ms):")
    for i in range(0, min(200, len(dash_response_to_dash)), 20):
        print(f"  t={i:2d}ms: {dash_response_to_dash[i]:.3f}")


if __name__ == "__main__":
    analyze_convolution_symmetry()

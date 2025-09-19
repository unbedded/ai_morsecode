#!/usr/bin/env python3
"""Debug script to analyze snippet processing issues."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


import numpy as np
from scipy.io import wavfile

from morsecode.components.decoder.morse_decoder import MorseDecoder
from morsecode.components.signal.signal_processor import SignalProcessor
from util.config.models import AudioConfig, DecoderConfig, SignalConfig

# from morsecode.components.audio.hal import AudioHAL  # Not needed for this debug


def analyze_snippet(snippet_file):
    """Analyze a single snippet file to understand processing issues."""
    print(f"\n=== Analyzing {snippet_file} ===")

    # Load audio
    try:
        sample_rate, audio_data = wavfile.read(snippet_file)
        print(f"Sample rate: {sample_rate} Hz")
        print(f"Audio length: {len(audio_data)} samples ({len(audio_data) / sample_rate:.3f} seconds)")
        print(f"Audio data type: {audio_data.dtype}")
        print(f"Audio range: [{audio_data.min()}, {audio_data.max()}]")

        # Convert to float32 and normalize if needed
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0

        print(f"Normalized range: [{audio_data.min():.6f}, {audio_data.max():.6f}]")

        # Convert stereo to mono if needed
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
            print("Converted stereo to mono")

        # Analyze frequency content
        from scipy.fft import fft, fftfreq

        fft_result = fft(audio_data)
        frequencies = fftfreq(len(audio_data), 1.0 / sample_rate)
        magnitudes = np.abs(fft_result)

        # Find dominant frequency
        positive_freqs = frequencies[: len(frequencies) // 2]
        positive_mags = magnitudes[: len(magnitudes) // 2]

        # Focus on reasonable Morse frequency range (200-2000 Hz)
        freq_mask = (positive_freqs >= 200) & (positive_freqs <= 2000)
        if np.any(freq_mask):
            masked_freqs = positive_freqs[freq_mask]
            masked_mags = positive_mags[freq_mask]
            peak_idx = np.argmax(masked_mags)
            dominant_freq = masked_freqs[peak_idx]
            peak_magnitude = masked_mags[peak_idx]

            print(f"Dominant frequency: {dominant_freq:.1f} Hz (magnitude: {peak_magnitude:.1f})")

            # Show top 5 frequencies
            sorted_indices = np.argsort(masked_mags)[::-1][:5]
            print("Top 5 frequencies:")
            for i, idx in enumerate(sorted_indices):
                freq = masked_freqs[idx]
                mag = masked_mags[idx]
                print(f"  {i + 1}. {freq:.1f} Hz: {mag:.1f}")

        else:
            print("No significant frequencies found in 200-2000 Hz range!")
            dominant_freq = 600  # fallback

        # Test with different configurations
        configs_to_test = [
            ("Default", SignalConfig(frequency=600, threshold=0.3)),
            ("Correct Freq", SignalConfig(frequency=int(dominant_freq), threshold=0.3)),
            ("Low Threshold", SignalConfig(frequency=600, threshold=0.05)),
            ("Correct + Low", SignalConfig(frequency=int(dominant_freq), threshold=0.05)),
            ("Ultra Low", SignalConfig(frequency=int(dominant_freq), threshold=0.01)),
        ]

        print("\nTesting different configurations:")
        for config_name, signal_config in configs_to_test:
            print(f"\n--- {config_name} ---")

            # Create configs
            audio_config = AudioConfig(sample_rate=sample_rate, chunk_size_ms=25)
            decoder_config = DecoderConfig(wpm=15, tolerance=0.5)

            # Initialize components
            signal_processor = SignalProcessor(config=signal_config)
            morse_decoder = MorseDecoder(config=decoder_config)

            # Process audio
            chunk_size = int(audio_config.chunk_size_ms * sample_rate / 1000)
            tone_detections = []

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i : i + chunk_size]
                if len(chunk) > 0:
                    tone_detected = signal_processor.detect_tone(chunk, adaptive_frequency=True)
                    tone_detections.append(tone_detected)
                    morse_decoder.process_tone_detection(tone_detected, audio_config.chunk_size_ms)

            morse_decoder.finalize_decoding()
            decoded_text = morse_decoder.get_decoded_text()

            print(f"Tone detections: {sum(tone_detections)}/{len(tone_detections)} chunks")
            print(f"Decoded text: '{decoded_text}'")

    except Exception as e:
        print(f"Error analyzing {snippet_file}: {e}")


def main():
    """Main function to debug snippet processing."""
    # Find some snippet files to analyze
    snippets_dir = Path("tests/snippets")
    if not snippets_dir.exists():
        print("No snippets directory found!")
        return

    # Find a few different types of snippets
    snippet_files = []
    for subdir in ["characters", "words", "phrases"]:
        subdir_path = snippets_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*.wav"))[:2]  # Take first 2 from each
            snippet_files.extend(files)

    if not snippet_files:
        print("No snippet WAV files found!")
        return

    print(f"Found {len(snippet_files)} snippet files to analyze")

    for snippet_file in snippet_files[:5]:  # Analyze first 5
        analyze_snippet(snippet_file)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test snippet generator CLI for Morse code decoder testing.

This module provides a command-line interface for generating test audio snippets
from existing WAV/TXT pairs, enabling comprehensive unit testing with real audio data.
"""

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.io import wavfile


@dataclass
class SnippetMetadata:
    """Metadata for a generated test snippet."""

    snippet_file: str
    source_file: str
    expected_text: str
    snippet_type: str  # 'character', 'word', 'phrase', 'number', 'punctuation'
    wpm: int
    start_time: float
    duration: float
    context: str
    created_at: str
    checksum: str


class TestSnippetGenerator:
    """Generates test audio snippets from WAV/TXT pairs."""

    def __init__(self, source_dir: Path, output_dir: Path):
        """Initialize test generator.

        Args:
            source_dir: Directory containing source audio files
            output_dir: Directory where snippets will be generated
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.logger = self._setup_logging()

        # Morse code patterns for validation
        self.MORSE_CODE = {
            "A": ".-",
            "B": "-...",
            "C": "-.-.",
            "D": "-..",
            "E": ".",
            "F": "..-.",
            "G": "--.",
            "H": "....",
            "I": "..",
            "J": ".---",
            "K": "-.-",
            "L": ".-..",
            "M": "--",
            "N": "-.",
            "O": "---",
            "P": ".--.",
            "Q": "--.-",
            "R": ".-.",
            "S": "...",
            "T": "-",
            "U": "..-",
            "V": "...-",
            "W": ".--",
            "X": "-..-",
            "Y": "-.--",
            "Z": "--..",
            "0": "-----",
            "1": ".----",
            "2": "..---",
            "3": "...--",
            "4": "....-",
            "5": ".....",
            "6": "-....",
            "7": "--...",
            "8": "---..",
            "9": "----.",
            ".": ".-.-.-",
            ",": "--..--",
            "?": "..--..",
            "=": "-...-",
            "/": "-..-.",
            "+": ".-.-.",
            "-": "-....-",
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the generator."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def find_wav_txt_pairs(self) -> list[tuple[Path, Path]]:
        """Find all matching WAV/TXT file pairs."""
        pairs = []

        for wav_file in self.source_dir.glob("*.wav"):
            txt_file = wav_file.with_suffix(".txt")
            if txt_file.exists():
                pairs.append((wav_file, txt_file))
                self.logger.info(f"Found pair: {wav_file.name} / {txt_file.name}")

        if not pairs:
            self.logger.warning(f"No WAV/TXT pairs found in {self.source_dir}")

        return pairs

    def extract_expected_text(self, txt_file: Path) -> str:
        """Extract clean expected text from TXT file."""
        try:
            with open(txt_file, encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            with open(txt_file, encoding="latin-1") as f:
                content = f.read()

        # Clean up the text - remove headers/footers and control characters
        lines = content.strip().split("\n")
        clean_lines = []

        for line in lines:
            line = line.strip()
            # Skip header/footer markers and empty lines
            if (
                line.startswith("=") and ("WPM" in line.upper() or "END" in line.upper() or "TEXT" in line.upper())
            ) or not line:
                continue
            # Remove non-printable characters except basic punctuation
            line = re.sub(r"[^\w\s.,;:!?()/-]", "", line)
            if line:
                clean_lines.append(line)

        return " ".join(clean_lines).upper()

    def extract_wpm_from_filename(self, filename: str) -> int:
        """Extract WPM from filename."""
        match = re.search(r"(\d+)WPM", filename.upper())
        return int(match.group(1)) if match else 15  # Default to 15 WPM

    def estimate_char_duration(self, wpm: int) -> float:
        """Estimate average character duration based on WPM."""
        # Standard: PARIS = 50 units, average word = 5 chars
        # 1 WPM = 5 chars/minute = 5 chars/60 seconds
        chars_per_second = (wpm * 5) / 60
        return 1.0 / chars_per_second

    def load_audio(self, wav_file: Path) -> tuple[np.ndarray, int]:
        """Load audio file and return data with sample rate."""
        try:
            sample_rate, audio_data = wavfile.read(wav_file)

            # Convert to float32 and normalize
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0

            # Convert stereo to mono if needed
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            return audio_data, sample_rate

        except Exception as e:
            self.logger.error(f"Failed to load audio from {wav_file}: {e}")
            raise

    def calculate_checksum(self, audio_data: np.ndarray) -> str:
        """Calculate simple checksum for audio data."""
        import hashlib

        return hashlib.md5(audio_data.tobytes()).hexdigest()[:8]

    def extract_snippet_by_text_position(
        self, wav_file: Path, txt_file: Path, target_text: str, context_chars: int = 10
    ) -> dict | None:
        """Extract audio snippet based on text position."""
        try:
            # Load audio and text
            audio_data, sample_rate = self.load_audio(wav_file)
            expected_text = self.extract_expected_text(txt_file)
            wpm = self.extract_wpm_from_filename(wav_file.name)

            # Find target text position
            text_index = expected_text.find(target_text.upper())
            if text_index == -1:
                return None

            # Calculate context window
            start_char = max(0, text_index - context_chars)
            end_char = min(len(expected_text), text_index + len(target_text) + context_chars)
            context_text = expected_text[start_char:end_char]

            # Estimate timing (rough approximation)
            char_duration = self.estimate_char_duration(wpm)
            start_time = start_char * char_duration
            duration = (end_char - start_char) * char_duration

            # Extract audio snippet with safety margins
            start_sample = int(start_time * sample_rate)
            end_sample = int((start_time + duration) * sample_rate)

            # Ensure we don't go beyond audio bounds
            start_sample = max(0, start_sample)
            end_sample = min(len(audio_data), end_sample)

            if start_sample >= end_sample:
                return None

            audio_snippet = audio_data[start_sample:end_sample]

            return {
                "audio": audio_snippet,
                "sample_rate": sample_rate,
                "expected_text": target_text.upper(),
                "context": context_text,
                "wpm": wpm,
                "start_time": start_time,
                "duration": duration,
                "source_file": str(wav_file),
                "checksum": self.calculate_checksum(audio_snippet),
            }

        except Exception as e:
            self.logger.error(f"Failed to extract snippet for '{target_text}' from {wav_file}: {e}")
            return None

    def generate_character_snippets(self, pairs: list[tuple[Path, Path]]) -> list[SnippetMetadata]:
        """Generate snippets for individual characters."""
        self.logger.info("Generating character snippets...")

        char_dir = self.output_dir / "characters"
        char_dir.mkdir(parents=True, exist_ok=True)

        snippets = []
        found_chars = set()

        for wav_file, txt_file in pairs:
            expected_text = self.extract_expected_text(txt_file)
            wpm = self.extract_wpm_from_filename(wav_file.name)

            # Find each unique character
            for char in expected_text:
                if char in self.MORSE_CODE and char not in found_chars:
                    snippet_data = self.extract_snippet_by_text_position(wav_file, txt_file, char, context_chars=3)

                    if snippet_data:
                        # Save audio snippet (handle special characters in filename)
                        safe_char = char if char.isalnum() else f"_{ord(char)}_"
                        snippet_filename = f"{safe_char}_{wpm}WPM.wav"
                        snippet_path = char_dir / snippet_filename

                        self._save_audio_snippet(snippet_path, snippet_data["audio"], snippet_data["sample_rate"])

                        # Create metadata
                        metadata = SnippetMetadata(
                            snippet_file=str(snippet_path),
                            source_file=snippet_data["source_file"],
                            expected_text=char,
                            snippet_type="character",
                            wpm=wpm,
                            start_time=snippet_data["start_time"],
                            duration=snippet_data["duration"],
                            context=snippet_data["context"],
                            created_at=datetime.now().isoformat(),
                            checksum=snippet_data["checksum"],
                        )

                        # Save metadata
                        metadata_path = snippet_path.with_suffix(".json")
                        with open(metadata_path, "w") as f:
                            json.dump(asdict(metadata), f, indent=2)

                        snippets.append(metadata)
                        found_chars.add(char)

                        self.logger.info(f"Generated character snippet: {char} ({wpm} WPM)")

        self.logger.info(f"Generated {len(snippets)} character snippets")
        return snippets

    def generate_word_snippets(
        self, pairs: list[tuple[Path, Path]], min_length: int = 2, max_length: int = 15
    ) -> list[SnippetMetadata]:
        """Generate snippets for words."""
        self.logger.info(f"Generating word snippets (length {min_length}-{max_length})...")

        word_dir = self.output_dir / "words"
        common_dir = word_dir / "common"
        technical_dir = word_dir / "technical"

        for dir_path in [common_dir, technical_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        snippets = []
        common_words = {
            "THE",
            "AND",
            "TO",
            "OF",
            "A",
            "IN",
            "IS",
            "IT",
            "YOU",
            "THAT",
            "WAS",
            "FOR",
            "ON",
            "ARE",
            "AS",
            "WITH",
            "HIS",
            "THEY",
            "I",
            "AT",
            "NOW",
            "FROM",
            "TEXT",
            "WPM",
        }

        generated_words = set()

        for wav_file, txt_file in pairs:
            expected_text = self.extract_expected_text(txt_file)
            words = expected_text.split()
            wpm = self.extract_wpm_from_filename(wav_file.name)

            for word in words:
                # Clean word (remove punctuation)
                clean_word = re.sub(r"[^\w]", "", word).upper()

                if (
                    min_length <= len(clean_word) <= max_length
                    and clean_word.isalpha()
                    and f"{clean_word}_{wpm}" not in generated_words
                ):
                    snippet_data = self.extract_snippet_by_text_position(
                        wav_file, txt_file, clean_word, context_chars=8
                    )

                    if snippet_data:
                        # Choose subdirectory
                        subdir = common_dir if clean_word in common_words else technical_dir

                        # Save snippet
                        snippet_filename = f"{clean_word}_{wpm}WPM.wav"
                        snippet_path = subdir / snippet_filename

                        self._save_audio_snippet(snippet_path, snippet_data["audio"], snippet_data["sample_rate"])

                        # Create metadata
                        metadata = SnippetMetadata(
                            snippet_file=str(snippet_path),
                            source_file=snippet_data["source_file"],
                            expected_text=clean_word,
                            snippet_type="word",
                            wpm=wpm,
                            start_time=snippet_data["start_time"],
                            duration=snippet_data["duration"],
                            context=snippet_data["context"],
                            created_at=datetime.now().isoformat(),
                            checksum=snippet_data["checksum"],
                        )

                        # Save metadata
                        metadata_path = snippet_path.with_suffix(".json")
                        with open(metadata_path, "w") as f:
                            json.dump(asdict(metadata), f, indent=2)

                        snippets.append(metadata)
                        generated_words.add(f"{clean_word}_{wpm}")

                        self.logger.info(f"Generated word snippet: {clean_word} ({wpm} WPM)")

        self.logger.info(f"Generated {len(snippets)} word snippets")
        return snippets

    def generate_phrase_snippets(self, pairs: list[tuple[Path, Path]]) -> list[SnippetMetadata]:
        """Generate snippets for common phrases."""
        self.logger.info("Generating phrase snippets...")

        phrase_dir = self.output_dir / "phrases"
        short_dir = phrase_dir / "short"
        medium_dir = phrase_dir / "medium"

        for dir_path in [short_dir, medium_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        snippets = []

        # Common phrases to extract
        target_phrases = [
            "NOW 10 WPM",
            "NOW 15 WPM",
            "NOW 20 WPM",
            "NOW 25 WPM",
            "NOW 30 WPM",
            "TEXT IS FROM",
            "END OF",
            "QST DE",
            "PAGE",
            "WPM TEXT",
            "DE W1AW",
        ]

        for wav_file, txt_file in pairs:
            expected_text = self.extract_expected_text(txt_file)
            wpm = self.extract_wpm_from_filename(wav_file.name)

            for phrase in target_phrases:
                if phrase in expected_text:
                    snippet_data = self.extract_snippet_by_text_position(wav_file, txt_file, phrase, context_chars=5)

                    if snippet_data:
                        # Choose subdirectory based on phrase length
                        word_count = len(phrase.split())
                        subdir = short_dir if word_count <= 4 else medium_dir

                        # Create safe filename
                        safe_phrase = re.sub(r"[^\w\s]", "", phrase).replace(" ", "_")
                        snippet_filename = f"{safe_phrase}_{wpm}WPM.wav"
                        snippet_path = subdir / snippet_filename

                        self._save_audio_snippet(snippet_path, snippet_data["audio"], snippet_data["sample_rate"])

                        # Create metadata
                        metadata = SnippetMetadata(
                            snippet_file=str(snippet_path),
                            source_file=snippet_data["source_file"],
                            expected_text=phrase,
                            snippet_type="phrase",
                            wpm=wpm,
                            start_time=snippet_data["start_time"],
                            duration=snippet_data["duration"],
                            context=snippet_data["context"],
                            created_at=datetime.now().isoformat(),
                            checksum=snippet_data["checksum"],
                        )

                        # Save metadata
                        metadata_path = snippet_path.with_suffix(".json")
                        with open(metadata_path, "w") as f:
                            json.dump(asdict(metadata), f, indent=2)

                        snippets.append(metadata)

                        self.logger.info(f"Generated phrase snippet: {phrase} ({wpm} WPM)")

        self.logger.info(f"Generated {len(snippets)} phrase snippets")
        return snippets

    def _save_audio_snippet(self, filepath: Path, audio_data: np.ndarray, sample_rate: int):
        """Save audio snippet to WAV file."""
        # Convert to int16 for WAV format
        if audio_data.dtype == np.float32:
            audio_int16 = (audio_data * 32767).astype(np.int16)
        else:
            audio_int16 = audio_data.astype(np.int16)

        wavfile.write(filepath, sample_rate, audio_int16)

    def generate_all_snippets(self, snippet_types: list[str] | None = None) -> dict[str, list[SnippetMetadata]]:
        """Generate all requested snippet types."""
        if snippet_types is None:
            snippet_types = ["characters", "words", "phrases"]

        pairs = self.find_wav_txt_pairs()
        if not pairs:
            self.logger.error("No WAV/TXT pairs found. Cannot generate snippets.")
            return {}

        all_snippets = {}

        if "characters" in snippet_types:
            all_snippets["characters"] = self.generate_character_snippets(pairs)

        if "words" in snippet_types:
            all_snippets["words"] = self.generate_word_snippets(pairs)

        if "phrases" in snippet_types:
            all_snippets["phrases"] = self.generate_phrase_snippets(pairs)

        # Generate master metadata file
        self._generate_master_metadata(all_snippets)

        return all_snippets

    def _generate_master_metadata(self, all_snippets: dict[str, list[SnippetMetadata]]):
        """Generate master metadata file."""
        master_metadata = {
            "generated_at": datetime.now().isoformat(),
            "source_directory": str(self.source_dir),
            "output_directory": str(self.output_dir),
            "snippet_counts": {k: len(v) for k, v in all_snippets.items()},
            "total_snippets": sum(len(v) for v in all_snippets.values()),
            "snippets_by_type": {k: [asdict(snippet) for snippet in v] for k, v in all_snippets.items()},
        }

        metadata_file = self.output_dir / "generated_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(master_metadata, f, indent=2)

        self.logger.info(f"Generated master metadata: {metadata_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate test audio snippets from Morse code WAV/TXT pairs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all snippet types
  morsecode-test-gen generate --source tests/data --output tests/snippets

  # Generate only word snippets
  morsecode-test-gen generate --source tests/data --output tests/snippets --types words

  # Generate with custom word length limits
  morsecode-test-gen generate --source tests/data --output tests/snippets \\
    --min-word-length 3 --max-word-length 10

  # List available source files
  morsecode-test-gen list-sources --source tests/data
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate test snippets")
    gen_parser.add_argument(
        "--source", "-s", type=Path, required=True, help="Source directory containing WAV/TXT pairs"
    )
    gen_parser.add_argument("--output", "-o", type=Path, required=True, help="Output directory for generated snippets")
    gen_parser.add_argument(
        "--types",
        nargs="+",
        choices=["characters", "words", "phrases"],
        default=["characters", "words", "phrases"],
        help="Types of snippets to generate",
    )
    gen_parser.add_argument("--min-word-length", type=int, default=2, help="Minimum word length for word snippets")
    gen_parser.add_argument("--max-word-length", type=int, default=15, help="Maximum word length for word snippets")
    gen_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # List sources command
    list_parser = subparsers.add_parser("list-sources", help="List available WAV/TXT pairs")
    list_parser.add_argument("--source", "-s", type=Path, required=True, help="Source directory to scan")

    # List snippets command
    snippets_parser = subparsers.add_parser("list-snippets", help="List generated snippets")
    snippets_parser.add_argument("--snippets", type=Path, required=True, help="Snippets directory to scan")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging level
    if hasattr(args, "verbose") and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.command == "generate":
            generator = TestSnippetGenerator(args.source, args.output)

            start_time = time.time()
            all_snippets = generator.generate_all_snippets(args.types)
            elapsed_time = time.time() - start_time

            total_snippets = sum(len(snippets) for snippets in all_snippets.values())
            print("\n✅ Generation complete!")
            print(f"📊 Generated {total_snippets} snippets in {elapsed_time:.1f} seconds")
            print(f"📁 Output directory: {args.output}")

            for snippet_type, snippets in all_snippets.items():
                print(f"   {snippet_type}: {len(snippets)} snippets")

        elif args.command == "list-sources":
            generator = TestSnippetGenerator(args.source, Path("."))
            pairs = generator.find_wav_txt_pairs()

            if pairs:
                print(f"Found {len(pairs)} WAV/TXT pairs in {args.source}:")
                for wav_file, txt_file in pairs:
                    wpm = generator.extract_wpm_from_filename(wav_file.name)
                    print(f"  📄 {wav_file.name} / {txt_file.name} ({wpm} WPM)")
            else:
                print(f"No WAV/TXT pairs found in {args.source}")

        elif args.command == "list-snippets":
            metadata_file = args.snippets / "generated_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)

                print(f"Snippets in {args.snippets}:")
                print(f"  Generated: {metadata['generated_at']}")
                print(f"  Total snippets: {metadata['total_snippets']}")

                for snippet_type, count in metadata["snippet_counts"].items():
                    print(f"    {snippet_type}: {count}")
            else:
                print(f"No metadata found in {args.snippets}")
                print("Run 'generate' command first to create snippets.")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Test data generator CLI for Morse code decoder testing.

This module provides a command-line interface for generating comprehensive test
WAV/TXT pairs from various sources, enabling systematic testing with controlled
audio data and expected text outputs.
"""

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

import numpy as np
from scipy.io import wavfile


class TestDataType(Enum):
    """Types of test data to generate."""

    SYNTHETIC = "synthetic"
    CURATED = "curated"
    RANDOM = "random"
    STRESS = "stress"


@dataclass
class TestCase:
    """Definition of a test case."""

    name: str
    text: str
    wpm: int
    frequency: float
    difficulty: str  # 'basic', 'intermediate', 'advanced', 'stress'
    category: str  # 'characters', 'words', 'phrases', 'numbers', 'prosigns'
    description: str
    tags: list[str]


@dataclass
class TestDataMetadata:
    """Metadata for generated test data."""

    test_name: str
    wav_file: str
    txt_file: str
    test_type: str
    wpm: int
    frequency: float
    duration: float
    text_length: int
    character_count: int
    word_count: int
    difficulty: str
    category: str
    tags: list[str]
    created_at: str
    checksum: str


class TestDataGenerator:
    """Generates comprehensive test WAV/TXT pairs for Morse code testing."""

    def __init__(self, output_dir: Path):
        """Initialize test data generator.

        Args:
            output_dir: Directory where test data will be generated
        """
        self.output_dir = Path(output_dir)
        self.logger = self._setup_logging()

        # Create organized directory structure
        self.dirs = {
            "basic": self.output_dir / "basic",
            "intermediate": self.output_dir / "intermediate",
            "advanced": self.output_dir / "advanced",
            "stress": self.output_dir / "stress",
            "reference": self.output_dir / "reference",
            "metadata": self.output_dir / "metadata",
        }

        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        # Morse code patterns
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
            "(": "-.--.",
            ")": "-.--.-",
            '"': ".-..-.",
            ":": "---...",
            ";": "-.-.-.",
            "@": ".--.-.",
        }

        # Prosigns (procedural signals)
        self.PROSIGNS = {
            "<AR>": ".-.-.",  # End of message
            "<SK>": "...-.-",  # End of contact
            "<BT>": "-...-",  # Break/pause
            "<AS>": ".-...",  # Wait/standby
            "<KN>": "-.--.",  # Go ahead (specific station)
            "<BK>": "-...-.-",  # Break in
            "<CL>": "-.-..-.",  # Closing/going off air
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

    def generate_morse_audio(
        self,
        text: str,
        wpm: int = 15,
        frequency: float = 600,
        sample_rate: int = 44100,
        amplitude: float = 0.7,
    ) -> np.ndarray:
        """Generate audio for Morse code text."""
        # Convert text to Morse code
        morse_code = self.text_to_morse(text)

        # Calculate timing based on WPM (PARIS standard)
        dot_duration = 1.2 / wpm  # Seconds per dot
        dash_duration = 3 * dot_duration
        element_space = dot_duration
        char_space = 3 * dot_duration
        word_space = 7 * dot_duration

        audio_segments = []
        elements = morse_code.split()

        for i, element in enumerate(elements):
            if element == "":  # Double space indicates word boundary
                silence_samples = int(word_space * sample_rate)
                audio_segments.append(np.zeros(silence_samples))
            else:
                # Process each dot/dash in the element
                for j, symbol in enumerate(element):
                    if symbol == ".":
                        duration = dot_duration
                    elif symbol == "-":
                        duration = dash_duration
                    else:
                        continue

                    # Generate tone with envelope
                    samples = int(duration * sample_rate)
                    t = np.linspace(0, duration, samples)

                    # Add slight envelope to avoid clicks
                    envelope = np.ones_like(t)
                    fade_samples = min(int(0.005 * sample_rate), samples // 10)
                    if fade_samples > 0:
                        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
                        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

                    tone = amplitude * envelope * np.sin(2 * np.pi * frequency * t)
                    audio_segments.append(tone)

                    # Add element spacing
                    if j < len(element) - 1:
                        space_samples = int(element_space * sample_rate)
                        audio_segments.append(np.zeros(space_samples))

                # Add character spacing
                if i < len(elements) - 1:
                    space_samples = int(char_space * sample_rate)
                    audio_segments.append(np.zeros(space_samples))

        # Concatenate all segments
        if audio_segments:
            return np.concatenate(audio_segments).astype(np.float32)
        else:
            return np.array([], dtype=np.float32)

    def text_to_morse(self, text: str) -> str:
        """Convert text to Morse code."""
        morse = []
        text = text.upper()

        # Handle prosigns
        for prosign, pattern in self.PROSIGNS.items():
            text = text.replace(prosign, f" {pattern} ")

        for char in text:
            if char in self.MORSE_CODE:
                morse.append(self.MORSE_CODE[char])
            elif char == " ":
                morse.append(" ")  # Word space
            else:
                self.logger.warning(f"Unknown character '{char}', skipping")

        return " ".join(morse)

    def calculate_checksum(self, audio_data: np.ndarray) -> str:
        """Calculate checksum for audio data."""
        import hashlib

        return hashlib.md5(audio_data.tobytes()).hexdigest()[:8]

    def save_test_pair(
        self, test_case: TestCase, audio_data: np.ndarray, sample_rate: int = 44100
    ) -> TestDataMetadata:
        """Save a test WAV/TXT pair and return metadata."""
        # Determine output directory based on difficulty
        output_dir = self.dirs[test_case.difficulty]

        # Create safe filename
        safe_name = re.sub(r"[^\w\s-]", "", test_case.name).strip()
        safe_name = re.sub(r"[-\s]+", "_", safe_name)

        # Save WAV file
        wav_file = output_dir / f"{safe_name}_{test_case.wpm}WPM.wav"
        audio_int16 = (audio_data * 32767).astype(np.int16)
        wavfile.write(wav_file, sample_rate, audio_int16)

        # Save TXT file with expected output
        txt_file = output_dir / f"{safe_name}_{test_case.wpm}WPM.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"= TEST: {test_case.name} =\n")
            f.write(f"= WPM: {test_case.wpm} | FREQ: {test_case.frequency}Hz =\n")
            f.write(f"= DIFFICULTY: {test_case.difficulty.upper()} =\n\n")
            f.write(test_case.text.upper())
            f.write("\n\n= END OF TEST =")

        # Create metadata
        metadata = TestDataMetadata(
            test_name=test_case.name,
            wav_file=str(wav_file),
            txt_file=str(txt_file),
            test_type=test_case.category,
            wpm=test_case.wpm,
            frequency=test_case.frequency,
            duration=len(audio_data) / sample_rate,
            text_length=len(test_case.text),
            character_count=len([c for c in test_case.text if c.isalnum()]),
            word_count=len(test_case.text.split()),
            difficulty=test_case.difficulty,
            category=test_case.category,
            tags=test_case.tags,
            created_at=datetime.now().isoformat(),
            checksum=self.calculate_checksum(audio_data),
        )

        # Save individual metadata
        metadata_file = self.dirs["metadata"] / f"{safe_name}_{test_case.wpm}WPM.json"
        with open(metadata_file, "w") as f:
            json.dump(asdict(metadata), f, indent=2)

        self.logger.info(f"Generated test pair: {test_case.name} ({test_case.wpm} WPM)")
        return metadata

    def generate_basic_tests(self) -> list[TestDataMetadata]:
        """Generate basic test cases for fundamental validation."""
        self.logger.info("Generating basic test cases...")

        test_cases = [
            # Individual characters
            TestCase(
                "Single_E",
                "E",
                15,
                600,
                "basic",
                "characters",
                "Single dot",
                ["character", "basic"],
            ),
            TestCase(
                "Single_T",
                "T",
                15,
                600,
                "basic",
                "characters",
                "Single dash",
                ["character", "basic"],
            ),
            TestCase(
                "Single_A", "A", 15, 600, "basic", "characters", "Dot-dash", ["character", "basic"]
            ),
            TestCase(
                "Single_N", "N", 15, 600, "basic", "characters", "Dash-dot", ["character", "basic"]
            ),
            # Simple words
            TestCase(
                "Word_THE", "THE", 15, 600, "basic", "words", "Common word", ["word", "common"]
            ),
            TestCase(
                "Word_AND", "AND", 15, 600, "basic", "words", "Common word", ["word", "common"]
            ),
            TestCase(
                "Word_TO", "TO", 15, 600, "basic", "words", "Two letter word", ["word", "short"]
            ),
            # Numbers
            TestCase(
                "Numbers_12345",
                "12345",
                15,
                600,
                "basic",
                "numbers",
                "Sequential numbers",
                ["numbers", "sequence"],
            ),
            TestCase(
                "Numbers_67890",
                "67890",
                15,
                600,
                "basic",
                "numbers",
                "Sequential numbers",
                ["numbers", "sequence"],
            ),
            # Basic phrases
            TestCase(
                "Phrase_CQ_CQ",
                "CQ CQ DE TEST",
                15,
                600,
                "basic",
                "phrases",
                "CQ call",
                ["phrase", "ham"],
            ),
        ]

        metadata_list = []
        for test_case in test_cases:
            audio = self.generate_morse_audio(test_case.text, test_case.wpm, test_case.frequency)
            metadata = self.save_test_pair(test_case, audio)
            metadata_list.append(metadata)

        self.logger.info(f"Generated {len(metadata_list)} basic test cases")
        return metadata_list

    def generate_intermediate_tests(self) -> list[TestDataMetadata]:
        """Generate intermediate test cases for standard validation."""
        self.logger.info("Generating intermediate test cases...")

        test_cases = [
            # Mixed content at different speeds
            TestCase(
                "Mixed_Content_10WPM",
                "THE QUICK BROWN FOX JUMPS OVER 123",
                10,
                600,
                "intermediate",
                "mixed",
                "Mixed content slow",
                ["mixed", "slow"],
            ),
            TestCase(
                "Mixed_Content_20WPM",
                "THE QUICK BROWN FOX JUMPS OVER 123",
                20,
                600,
                "intermediate",
                "mixed",
                "Mixed content fast",
                ["mixed", "fast"],
            ),
            # Different frequencies
            TestCase(
                "Low_Freq_400Hz",
                "FREQUENCY TEST AT 400 HZ",
                15,
                400,
                "intermediate",
                "frequency",
                "Low frequency test",
                ["frequency", "low"],
            ),
            TestCase(
                "High_Freq_800Hz",
                "FREQUENCY TEST AT 800 HZ",
                15,
                800,
                "intermediate",
                "frequency",
                "High frequency test",
                ["frequency", "high"],
            ),
            # Punctuation and prosigns
            TestCase(
                "Punctuation_Test",
                "HELLO, WORLD! HOW ARE YOU? FINE.",
                15,
                600,
                "intermediate",
                "punctuation",
                "Punctuation test",
                ["punctuation"],
            ),
            TestCase(
                "Prosigns_Test",
                "CQ CQ DE TEST <AR> PSE QSL <SK>",
                15,
                600,
                "intermediate",
                "prosigns",
                "Prosign test",
                ["prosigns", "ham"],
            ),
            # Longer text passages
            TestCase(
                "Paragraph_Text",
                "THIS IS A LONGER TEXT PASSAGE TO TEST THE DECODER WITH CONTINUOUS MORSE "
                "CODE OVER MULTIPLE SENTENCES",
                15,
                600,
                "intermediate",
                "paragraph",
                "Paragraph test",
                ["paragraph", "long"],
            ),
        ]

        metadata_list = []
        for test_case in test_cases:
            audio = self.generate_morse_audio(test_case.text, test_case.wpm, test_case.frequency)
            metadata = self.save_test_pair(test_case, audio)
            metadata_list.append(metadata)

        self.logger.info(f"Generated {len(metadata_list)} intermediate test cases")
        return metadata_list

    def generate_advanced_tests(self) -> list[TestDataMetadata]:
        """Generate advanced test cases for edge case validation."""
        self.logger.info("Generating advanced test cases...")

        test_cases = [
            # High speed
            TestCase(
                "High_Speed_30WPM",
                "CONTEST STYLE HIGH SPEED MORSE CODE",
                30,
                600,
                "advanced",
                "speed",
                "High speed test",
                ["speed", "contest"],
            ),
            TestCase(
                "Very_High_Speed_40WPM",
                "VERY FAST CW FOR EXPERT TESTING",
                40,
                600,
                "advanced",
                "speed",
                "Very high speed",
                ["speed", "expert"],
            ),
            # Weak signal simulation (lower amplitude)
            TestCase(
                "Weak_Signal",
                "WEAK SIGNAL TEST WITH LOW AMPLITUDE",
                15,
                600,
                "advanced",
                "signal",
                "Weak signal test",
                ["signal", "weak"],
            ),
            # Close characters (similar patterns)
            TestCase(
                "Similar_Chars",
                "EISH TMOW NKRY CGZQ",
                15,
                600,
                "advanced",
                "similar",
                "Similar character patterns",
                ["similar", "confusing"],
            ),
            # All characters test
            TestCase(
                "All_Letters",
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                15,
                600,
                "advanced",
                "complete",
                "All letters test",
                ["complete", "alphabet"],
            ),
            TestCase(
                "All_Numbers",
                "0123456789",
                15,
                600,
                "advanced",
                "complete",
                "All numbers test",
                ["complete", "numbers"],
            ),
            # Random callsigns
            TestCase(
                "Callsigns",
                "W1AW K3LR VE1ABC JA1XYZ",
                15,
                600,
                "advanced",
                "callsigns",
                "Ham radio callsigns",
                ["callsigns", "ham"],
            ),
        ]

        metadata_list = []
        for test_case in test_cases:
            # Adjust amplitude for weak signal test
            amplitude = 0.3 if "weak" in test_case.tags else 0.7
            audio = self.generate_morse_audio(test_case.text, test_case.wpm, test_case.frequency)
            if amplitude != 0.7:
                audio = audio * (amplitude / 0.7)
            metadata = self.save_test_pair(test_case, audio)
            metadata_list.append(metadata)

        self.logger.info(f"Generated {len(metadata_list)} advanced test cases")
        return metadata_list

    def generate_stress_tests(self) -> list[TestDataMetadata]:
        """Generate stress test cases for extreme validation."""
        self.logger.info("Generating stress test cases...")

        test_cases = [
            # Very long content
            TestCase(
                "Long_Text",
                "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG " * 10,
                15,
                600,
                "stress",
                "endurance",
                "Very long text",
                ["endurance", "long"],
            ),
            # Rapid character changes
            TestCase(
                "Rapid_Changes",
                "EISH EISH EISH TMOW TMOW TMOW",
                25,
                600,
                "stress",
                "rapid",
                "Rapid character changes",
                ["rapid", "pattern"],
            ),
            # All punctuation
            TestCase(
                "All_Punctuation",
                '.,?!:;=+-/()"@',
                15,
                600,
                "stress",
                "punctuation",
                "All punctuation marks",
                ["punctuation", "complete"],
            ),
            # Very slow
            TestCase(
                "Very_Slow_5WPM",
                "VERY SLOW MORSE CODE",
                5,
                600,
                "stress",
                "speed",
                "Very slow speed",
                ["speed", "slow"],
            ),
            # Random characters
            TestCase(
                "Random_Chars",
                "QZXJVBPKWYFLRHGDUCTSIAE",
                15,
                600,
                "stress",
                "random",
                "Random character order",
                ["random", "chaos"],
            ),
        ]

        metadata_list = []
        for test_case in test_cases:
            audio = self.generate_morse_audio(test_case.text, test_case.wpm, test_case.frequency)
            metadata = self.save_test_pair(test_case, audio)
            metadata_list.append(metadata)

        self.logger.info(f"Generated {len(metadata_list)} stress test cases")
        return metadata_list

    def generate_reference_tests(self) -> list[TestDataMetadata]:
        """Generate reference test cases for calibration."""
        self.logger.info("Generating reference test cases...")

        test_cases = [
            # Standard test patterns
            TestCase(
                "PARIS_Standard",
                "PARIS",
                15,
                600,
                "reference",
                "standard",
                "PARIS timing standard",
                ["standard", "timing"],
            ),
            TestCase(
                "CODEX_Standard",
                "CODEX",
                15,
                600,
                "reference",
                "standard",
                "CODEX timing standard",
                ["standard", "timing"],
            ),
            # Frequency references
            TestCase(
                "Ref_440Hz",
                "FREQUENCY REFERENCE 440 HZ",
                15,
                440,
                "reference",
                "frequency",
                "440Hz reference",
                ["reference", "frequency"],
            ),
            TestCase(
                "Ref_600Hz",
                "FREQUENCY REFERENCE 600 HZ",
                15,
                600,
                "reference",
                "frequency",
                "600Hz reference",
                ["reference", "frequency"],
            ),
            TestCase(
                "Ref_800Hz",
                "FREQUENCY REFERENCE 800 HZ",
                15,
                800,
                "reference",
                "frequency",
                "800Hz reference",
                ["reference", "frequency"],
            ),
            # WPM references
            TestCase(
                "Ref_10WPM",
                "SPEED REFERENCE TEN WPM",
                10,
                600,
                "reference",
                "speed",
                "10 WPM reference",
                ["reference", "speed"],
            ),
            TestCase(
                "Ref_15WPM",
                "SPEED REFERENCE FIFTEEN WPM",
                15,
                600,
                "reference",
                "speed",
                "15 WPM reference",
                ["reference", "speed"],
            ),
            TestCase(
                "Ref_20WPM",
                "SPEED REFERENCE TWENTY WPM",
                20,
                600,
                "reference",
                "speed",
                "20 WPM reference",
                ["reference", "speed"],
            ),
        ]

        metadata_list = []
        for test_case in test_cases:
            audio = self.generate_morse_audio(test_case.text, test_case.wpm, test_case.frequency)
            metadata = self.save_test_pair(test_case, audio)
            metadata_list.append(metadata)

        self.logger.info(f"Generated {len(metadata_list)} reference test cases")
        return metadata_list

    def generate_all_tests(
        self, test_types: list[str] | None = None
    ) -> dict[str, list[TestDataMetadata]]:
        """Generate all requested test types."""
        if test_types is None:
            test_types = ["basic", "intermediate", "advanced", "stress", "reference"]

        all_metadata = {}

        if "basic" in test_types:
            all_metadata["basic"] = self.generate_basic_tests()

        if "intermediate" in test_types:
            all_metadata["intermediate"] = self.generate_intermediate_tests()

        if "advanced" in test_types:
            all_metadata["advanced"] = self.generate_advanced_tests()

        if "stress" in test_types:
            all_metadata["stress"] = self.generate_stress_tests()

        if "reference" in test_types:
            all_metadata["reference"] = self.generate_reference_tests()

        # Generate master metadata file
        self._generate_master_metadata(all_metadata)

        return all_metadata

    def _generate_master_metadata(self, all_metadata: dict[str, list[TestDataMetadata]]):
        """Generate master metadata file."""
        master_metadata = {
            "generated_at": datetime.now().isoformat(),
            "output_directory": str(self.output_dir),
            "test_counts": {k: len(v) for k, v in all_metadata.items()},
            "total_tests": sum(len(v) for v in all_metadata.values()),
            "directory_structure": {
                "basic": "Fundamental test cases for basic validation",
                "intermediate": "Standard test cases for typical validation",
                "advanced": "Complex test cases for edge case validation",
                "stress": "Extreme test cases for stress testing",
                "reference": "Reference test cases for calibration",
                "metadata": "Individual test metadata files",
            },
            "tests_by_type": {k: [asdict(test) for test in v] for k, v in all_metadata.items()},
        }

        metadata_file = self.output_dir / "test_suite_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(master_metadata, f, indent=2)

        self.logger.info(f"Generated master metadata: {metadata_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive test WAV/TXT pairs for Morse code testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all test types
  morsecode-test-data generate --output tests/generated_data

  # Generate only basic and intermediate tests
  morsecode-test-data generate --output tests/generated_data --types basic intermediate

  # Generate with verbose output
  morsecode-test-data generate --output tests/generated_data --verbose

  # List generated test data
  morsecode-test-data list --data tests/generated_data

  # Show test statistics
  morsecode-test-data stats --data tests/generated_data
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate test data")
    gen_parser.add_argument(
        "--output", "-o", type=Path, required=True, help="Output directory for generated test data"
    )
    gen_parser.add_argument(
        "--types",
        nargs="+",
        choices=["basic", "intermediate", "advanced", "stress", "reference"],
        default=["basic", "intermediate", "advanced", "stress", "reference"],
        help="Types of tests to generate",
    )
    gen_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # List command
    list_parser = subparsers.add_parser("list", help="List generated test data")
    list_parser.add_argument("--data", type=Path, required=True, help="Test data directory to list")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show test statistics")
    stats_parser.add_argument(
        "--data", type=Path, required=True, help="Test data directory to analyze"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging level
    if hasattr(args, "verbose") and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.command == "generate":
            generator = TestDataGenerator(args.output)

            start_time = time.time()
            all_metadata = generator.generate_all_tests(args.types)
            elapsed_time = time.time() - start_time

            total_tests = sum(len(tests) for tests in all_metadata.values())
            print("\n✅ Test data generation complete!")
            print(f"📊 Generated {total_tests} test pairs in {elapsed_time:.1f} seconds")
            print(f"📁 Output directory: {args.output}")

            for test_type, tests in all_metadata.items():
                print(f"   {test_type}: {len(tests)} tests")

        elif args.command == "list":
            metadata_file = args.data / "test_suite_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)

                print(f"Test data in {args.data}:")
                print(f"  Generated: {metadata['generated_at']}")
                print(f"  Total tests: {metadata['total_tests']}")

                for test_type, count in metadata["test_counts"].items():
                    print(f"    {test_type}: {count} tests")

                print("\nDirectory structure:")
                for dir_name, description in metadata["directory_structure"].items():
                    print(f"  {dir_name}/: {description}")
            else:
                print(f"No test data metadata found in {args.data}")
                print("Run 'generate' command first to create test data.")

        elif args.command == "stats":
            metadata_file = args.data / "test_suite_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)

                print("Test Suite Statistics:")
                print(f"  Total test pairs: {metadata['total_tests']}")

                # Analyze by category
                categories = {}
                for _test_type, tests in metadata["tests_by_type"].items():
                    for test in tests:
                        cat = test["category"]
                        if cat not in categories:
                            categories[cat] = 0
                        categories[cat] += 1

                print("\nBy category:")
                for category, count in sorted(categories.items()):
                    print(f"    {category}: {count}")

                # Analyze by WPM
                wpms = {}
                for _test_type, tests in metadata["tests_by_type"].items():
                    for test in tests:
                        wpm = test["wpm"]
                        if wpm not in wpms:
                            wpms[wpm] = 0
                        wpms[wpm] += 1

                print("\nBy WPM:")
                for wpm in sorted(wpms.keys()):
                    print(f"    {wpm} WPM: {wpms[wpm]} tests")

                # Total duration
                total_duration = sum(
                    test["duration"]
                    for tests in metadata["tests_by_type"].values()
                    for test in tests
                )
                print(
                    f"\nTotal audio duration: {total_duration:.1f} seconds "
                    f"({total_duration / 60:.1f} minutes)"
                )

            else:
                print(f"No test data metadata found in {args.data}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

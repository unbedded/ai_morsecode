"""Event type definitions for the Morse code decoder pipeline.

This module defines all events that flow through the system, providing
strong typing, binary serialization, and C++ portability.
"""

import struct
import time
from dataclasses import dataclass, field
from typing import Any, ClassVar

import numpy as np

# Program start time for consistent, portable timing
_PROGRAM_START_TIME = time.perf_counter()


def get_program_time_us() -> int:
    """Get microseconds since program started.

    Uses steady clock equivalent for C++ portability.
    Returns deterministic timing independent of system clock.
    """
    return int((time.perf_counter() - _PROGRAM_START_TIME) * 1_000_000)


# Binary format versioning
BINARY_FORMAT_VERSION = 1
EVENT_TYPE_REGISTRY: dict[str, int] = {}
REVERSE_TYPE_REGISTRY: dict[int, str] = {}


def register_event_type(event_class: type, type_id: int) -> None:
    """Register event type for binary serialization."""
    class_name = event_class.__name__
    EVENT_TYPE_REGISTRY[class_name] = type_id
    REVERSE_TYPE_REGISTRY[type_id] = class_name


@dataclass(frozen=True)
class BaseEvent:
    """Base event with portable timestamp and binary serialization.

    Features:
    - Integer microsecond timestamps for performance and C++ portability
    - Versioned binary serialization with type safety
    - Standard containers only (no defaultdict, WeakSet, etc.)
    - Direct mapping to C++ std::chrono and template patterns
    """

    # Class-level type ID for binary serialization
    TYPE_ID: ClassVar[int] = 0

    # Timestamp at end to allow child classes to have required fields first
    timestamp: int = field(default_factory=get_program_time_us)

    @property
    def age_us(self) -> int:
        """Age in microseconds since event creation."""
        return get_program_time_us() - self.timestamp

    @property
    def age_ms(self) -> float:
        """Age in milliseconds since event creation (legacy compatibility)."""
        return self.age_us / 1000.0

    def to_binary(self) -> bytes:
        """Serialize event to portable binary format.

        Binary format:
        [4 bytes: format_version][4 bytes: event_type_id][8 bytes: timestamp][payload...]

        This format is designed for C++ compatibility and file versioning.
        """
        header = struct.pack("!IIQ", BINARY_FORMAT_VERSION, self.TYPE_ID, self.timestamp)
        payload = self._serialize_payload()
        return header + payload

    def _serialize_payload(self) -> bytes:
        """Serialize event-specific fields. Override in subclasses."""
        return b""  # Base event has no additional payload

    @classmethod
    def from_binary(cls, data: bytes) -> "BaseEvent":
        """Deserialize event from binary format with version checking."""
        if len(data) < 16:  # Minimum header size
            raise ValueError("Binary data too short for event header")

        # Parse header
        format_version, event_type_id, timestamp = struct.unpack("!IIQ", data[:16])

        if format_version != BINARY_FORMAT_VERSION:
            raise ValueError(f"Unsupported binary format version: {format_version}")

        if event_type_id not in REVERSE_TYPE_REGISTRY:
            raise ValueError(f"Unknown event type ID: {event_type_id}")

        # Route to correct event class based on type ID
        payload = data[16:]
        if event_type_id == 1:  # AudioChunkEvent
            return AudioChunkEvent._deserialize_payload(timestamp, payload)
        elif event_type_id == 2:  # ToneDetectedEvent
            return ToneDetectedEvent._deserialize_payload(timestamp, payload)
        elif event_type_id == 3:  # MorsePatternEvent
            return MorsePatternEvent._deserialize_payload(timestamp, payload)
        elif event_type_id == 4:  # TextDecodedEvent
            return TextDecodedEvent._deserialize_payload(timestamp, payload)
        else:
            # BaseEvent or unknown type
            return cls._deserialize_payload(timestamp, payload)

    @classmethod
    def _deserialize_payload(cls, timestamp: int, payload: bytes) -> "BaseEvent":
        """Deserialize event-specific fields. Override in subclasses."""
        return cls(timestamp=timestamp)


# Audio Processing Events


@dataclass(frozen=True)
class AudioChunkEvent(BaseEvent):
    """Published when an audio chunk is processed.

    Binary serialization note: Audio data is NOT included in binary format
    for performance reasons. Use event for signaling only.
    """

    TYPE_ID: ClassVar[int] = 1

    chunk_data: np.ndarray = field(default_factory=lambda: np.array([]))
    chunk_size_ms: int = 0
    sample_rate: int = 44100
    chunk_number: int = 0
    has_more_data: bool = True
    # timestamp: inherited from BaseEvent with default

    @property
    def chunk_duration_samples(self) -> int:
        """Calculate the chunk duration in samples."""
        return int((self.chunk_size_ms / 1000.0) * self.sample_rate)

    def _serialize_payload(self) -> bytes:
        """Serialize metadata only (not audio data for performance)."""
        return struct.pack(
            "!IIIH",
            self.chunk_size_ms,
            self.sample_rate,
            self.chunk_number,
            1 if self.has_more_data else 0,
        )

    @classmethod
    def _deserialize_payload(cls, timestamp: int, payload: bytes) -> "AudioChunkEvent":
        """Deserialize metadata (creates empty audio array)."""
        if len(payload) < 14:
            raise ValueError("AudioChunkEvent payload too short")

        chunk_size_ms, sample_rate, chunk_number, has_more_data_int = struct.unpack(
            "!IIIH", payload[:14]
        )

        # Create empty array - real audio data not serialized
        empty_array = np.array([], dtype=np.float32)

        return cls(
            timestamp=timestamp,
            chunk_data=empty_array,
            chunk_size_ms=chunk_size_ms,
            sample_rate=sample_rate,
            chunk_number=chunk_number,
            has_more_data=bool(has_more_data_int),
        )


@dataclass(frozen=True)
class ToneDetectedEvent(BaseEvent):
    """Published when tone detection analysis completes.

    This is the core event that drives Morse pattern recognition.
    Contains detection results and confidence metrics.
    """

    TYPE_ID: ClassVar[int] = 2

    detected: bool = False
    frequency: float = 0.0
    confidence: float = 0.0
    snr_db: float = 0.0
    chunk_number: int = 0
    detection_threshold: float = 0.3

    @property
    def is_confident(self) -> bool:
        """Check if detection confidence is above threshold."""
        return self.confidence >= self.detection_threshold

    @property
    def signal_quality(self) -> str:
        """Classify signal quality based on SNR."""
        if self.snr_db >= 20:
            return "excellent"
        elif self.snr_db >= 10:
            return "good"
        elif self.snr_db >= 3:
            return "poor"
        else:
            return "very_poor"

    def _serialize_payload(self) -> bytes:
        """Serialize tone detection data in portable binary format."""
        return struct.pack(
            "!HffffI",
            1 if self.detected else 0,
            self.frequency,
            self.confidence,
            self.snr_db,
            self.detection_threshold,
            self.chunk_number,
        )

    @classmethod
    def _deserialize_payload(cls, timestamp: int, payload: bytes) -> "ToneDetectedEvent":
        """Deserialize tone detection data."""
        if len(payload) < 22:  # 2+4*4+4 bytes
            raise ValueError("ToneDetectedEvent payload too short")

        detected_int, frequency, confidence, snr_db, detection_threshold, chunk_number = (
            struct.unpack("!HffffI", payload[:22])
        )

        return cls(
            timestamp=timestamp,
            detected=bool(detected_int),
            frequency=frequency,
            confidence=confidence,
            snr_db=snr_db,
            chunk_number=chunk_number,
            detection_threshold=detection_threshold,
        )


# Morse Code Processing Events


@dataclass(frozen=True)
class MorsePatternEvent(BaseEvent):
    """Published when a complete Morse pattern is recognized.

    Represents a dot, dash, or timing element (space between letters/words).
    This is the intermediate representation before character decoding.
    """

    TYPE_ID: ClassVar[int] = 3

    pattern_type: str = "dot"  # "dot", "dash", "letter_space", "word_space"
    duration_ms: float = 0.0
    wpm_estimate: float = 15.0
    confidence: float = 0.0

    @property
    def is_tone(self) -> bool:
        """Check if this pattern represents a tone (dot or dash)."""
        return self.pattern_type in ("dot", "dash")

    @property
    def is_silence(self) -> bool:
        """Check if this pattern represents silence."""
        return self.pattern_type in ("letter_space", "word_space")

    def _serialize_payload(self) -> bytes:
        """Serialize Morse pattern data."""
        # Encode pattern type as integer for binary format
        pattern_types = {"dot": 1, "dash": 2, "letter_space": 3, "word_space": 4}
        pattern_id = pattern_types.get(self.pattern_type, 0)

        return struct.pack(
            "!Hfff", pattern_id, self.duration_ms, self.wpm_estimate, self.confidence
        )

    @classmethod
    def _deserialize_payload(cls, timestamp: int, payload: bytes) -> "MorsePatternEvent":
        """Deserialize Morse pattern data."""
        if len(payload) < 14:  # 2+4*3 bytes
            raise ValueError("MorsePatternEvent payload too short")

        pattern_id, duration_ms, wpm_estimate, confidence = struct.unpack("!Hfff", payload[:14])

        # Decode pattern type
        pattern_types = {1: "dot", 2: "dash", 3: "letter_space", 4: "word_space"}
        pattern_type = pattern_types.get(pattern_id, "unknown")

        return cls(
            timestamp=timestamp,
            pattern_type=pattern_type,
            duration_ms=duration_ms,
            wpm_estimate=wpm_estimate,
            confidence=confidence,
        )


@dataclass(frozen=True)
class TextDecodedEvent(BaseEvent):
    """Published when Morse patterns are decoded to text.

    Contains the decoded character or word, along with quality metrics.
    This is the final output of the decoding pipeline.
    """

    TYPE_ID: ClassVar[int] = 4

    text: str = ""
    pattern_sequence: str = ""  # The dot-dash pattern that produced this text
    wpm_estimate: float = 15.0
    confidence: float = 0.0
    is_complete_word: bool = False  # True for word boundaries, False for single characters

    @property
    def character_count(self) -> int:
        """Get the number of characters decoded."""
        return len(self.text)

    def _serialize_payload(self) -> bytes:
        """Serialize decoded text data."""
        # Encode strings as UTF-8 with length prefixes
        text_bytes = self.text.encode("utf-8")
        pattern_bytes = self.pattern_sequence.encode("utf-8")

        return (
            struct.pack(
                "!HffHH",
                len(text_bytes),
                self.wpm_estimate,
                self.confidence,
                len(pattern_bytes),
                1 if self.is_complete_word else 0,
            )
            + text_bytes
            + pattern_bytes
        )

    @classmethod
    def _deserialize_payload(cls, timestamp: int, payload: bytes) -> "TextDecodedEvent":
        """Deserialize decoded text data."""
        if len(payload) < 14:  # Minimum header size
            raise ValueError("TextDecodedEvent payload too short")

        # Parse header
        text_len, wpm_estimate, confidence, pattern_len, is_word_int = struct.unpack(
            "!HffHH", payload[:14]
        )

        # Extract strings
        text_start = 14  # After the 14-byte header
        text_end = text_start + text_len
        pattern_start = text_end
        pattern_end = pattern_start + pattern_len

        if len(payload) < pattern_end:
            raise ValueError("TextDecodedEvent payload truncated")

        text = payload[text_start:text_end].decode("utf-8")
        pattern_sequence = payload[pattern_start:pattern_end].decode("utf-8")

        return cls(
            timestamp=timestamp,
            text=text,
            pattern_sequence=pattern_sequence,
            wpm_estimate=wpm_estimate,
            confidence=confidence,
            is_complete_word=bool(is_word_int),
        )


# Pipeline Control Events


@dataclass(frozen=True)
class PipelineStateEvent(BaseEvent):
    """Published when the pipeline state changes.

    Used for coordination, debugging, and user interface updates.
    """

    state: str = "starting"  # "starting", "processing", "paused", "stopped", "error"
    component: str = "pipeline"  # "audio_source", "signal_processor", "decoder", "pipeline"
    message: str | None = None
    details: dict[str, Any] | None = None
    # timestamp: inherited from BaseEvent

    @property
    def is_error_state(self) -> bool:
        """Check if this represents an error state."""
        return self.state == "error"

    @property
    def is_processing(self) -> bool:
        """Check if the component is actively processing."""
        return self.state == "processing"


# Error and Diagnostics Events


@dataclass(frozen=True)
class ErrorEvent(BaseEvent):
    """Published when errors occur in the pipeline.

    Provides structured error information for logging, recovery, and debugging.
    """

    error_type: str = "Exception"  # Exception class name
    message: str = ""
    component: str = "unknown"
    recoverable: bool = True
    context: dict[str, Any] = field(default_factory=dict)
    exception_details: str | None = None
    # timestamp: inherited from BaseEvent

    @property
    def severity(self) -> str:
        """Classify error severity based on recoverability."""
        return "warning" if self.recoverable else "critical"


@dataclass(frozen=True)
class MetricsEvent(BaseEvent):
    """Published for performance monitoring and statistics.

    Contains metrics data for observability and optimization.
    """

    metric_name: str = "unknown"
    value: float = 0.0
    unit: str = "count"
    component: str = "unknown"
    tags: dict[str, str] = field(default_factory=dict)
    # timestamp: inherited from BaseEvent

    @property
    def formatted_value(self) -> str:
        """Get formatted metric value with unit."""
        if self.unit == "ms":
            return f"{self.value:.1f}ms"
        elif self.unit == "hz":
            return f"{self.value:.0f}Hz"
        elif self.unit == "percent":
            return f"{self.value:.1f}%"
        else:
            return f"{self.value} {self.unit}"


# Event creation helpers


def create_tone_event(
    detected: bool,
    frequency: float = 0.0,
    confidence: float = 0.0,
    snr_db: float = 0.0,
    chunk_number: int = 0,
    threshold: float = 0.3,
) -> ToneDetectedEvent:
    """Convenience function for creating tone detection events."""
    return ToneDetectedEvent(
        detected=detected,
        frequency=frequency,
        confidence=confidence,
        snr_db=snr_db,
        chunk_number=chunk_number,
        detection_threshold=threshold,
    )


def create_text_event(
    text: str, pattern: str = "", wpm: float = 15.0, confidence: float = 1.0, is_word: bool = False
) -> TextDecodedEvent:
    """Convenience function for creating text decoded events."""
    return TextDecodedEvent(
        text=text,
        pattern_sequence=pattern,
        wpm_estimate=wpm,
        confidence=confidence,
        is_complete_word=is_word,
    )


def create_error_event(
    error: Exception, component: str, recoverable: bool = True, **context: Any
) -> ErrorEvent:
    """Convenience function for creating error events from exceptions."""
    return ErrorEvent(
        error_type=type(error).__name__,
        message=str(error),
        component=component,
        recoverable=recoverable,
        context=context,
        exception_details=repr(error),
    )


# Register all event types for binary serialization
register_event_type(BaseEvent, 0)
register_event_type(AudioChunkEvent, 1)
register_event_type(ToneDetectedEvent, 2)
register_event_type(MorsePatternEvent, 3)
register_event_type(TextDecodedEvent, 4)
# Note: PipelineStateEvent, ErrorEvent, MetricsEvent would be types 5-7
# Keeping them simple for now since they're less performance-critical

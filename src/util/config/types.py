"""Shared configuration types and utilities."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CfgType(Enum):
    """Configuration field types."""

    INT = "int"
    DOUBLE = "double"
    STRING = "string"
    BOOL = "bool"
    ENUM = "enum"


@dataclass
class CfgField:
    """Configuration field definition with validation rules and unit metadata."""

    type: CfgType
    default: Any
    min: Any | None = None
    max: Any | None = None
    choices: list | None = None
    regex: str | None = None
    description: str = ""
    unit: str | None = None  # Unit metadata (e.g., "Hz", "ms", "norm")


def enum_field(enum_class, default, prefix=""):
    """Helper to create enum config field with auto-generated description.

    Args:
        enum_class: Enum class (e.g., SignalMode)
        default: Default enum value (e.g., SignalMode.AUTO)
        prefix: Description prefix (e.g., "Signal processing mode")

    Returns:
        CfgField with auto-generated description from enum values
    """
    choices_str = ", ".join([e.value for e in enum_class])
    description = f"{prefix}: {choices_str}" if prefix else f"Options: {choices_str}"
    return CfgField(type=CfgType.ENUM, default=default, choices=list(enum_class), description=description)

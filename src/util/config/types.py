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
    """Configuration field definition with validation rules and unit metadata.

    None vs null usage:
    - Python code: Use None (default=None, choices=None, etc.)
    - YAML config: Use null (output_file: null)

    When nullable=True:
    - Python: default=None
    - YAML: field: null
    - Help: "(null to disable)"
    """

    type: CfgType
    default: Any
    min: Any | None = None
    max: Any | None = None
    choices: list | None = None
    regex: str | None = None
    description: str = ""
    unit: str | None = None  # Unit metadata (e.g., "Hz", "ms", "norm")
    nullable: bool = False  # Allow YAML null values (set True when default=None)


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


def string_choices_field(choices, default, description_prefix=""):
    """Helper to create string config field with clear choices formatting.

    Args:
        choices: List of string choices (e.g., ["DEBUG", "INFO", "WARN", "ERROR"])
        default: Default choice (e.g., "INFO")
        description_prefix: Description prefix (e.g., "Override app log level if more verbose")

    Returns:
        CfgField with choices list - formatting handled by config generation
    """
    return CfgField(type=CfgType.STRING, default=default, choices=choices, description=description_prefix)

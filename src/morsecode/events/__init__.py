"""Event-driven communication system for Morse code decoder.

This package provides a lightweight, type-safe pub-sub system for loose coupling
between components. Events flow through the system to enable observability,
testing, and extensibility.

Core Components:
- EventBus: Central publisher-subscriber hub
- Event types: Strongly-typed event definitions
- Handlers: Built-in event processing
- Middleware: Cross-cutting concerns (logging, metrics)
"""

from .bus import (
    EventBus,
    EventHandler,
    EventMiddleware,
    get_global_event_bus,
    reset_global_event_bus,
)
from .handlers import DebugEventHandler, LoggingEventHandler, MetricsEventHandler
from .types import (
    AudioChunkEvent,
    BaseEvent,
    ErrorEvent,
    MetricsEvent,
    MorsePatternEvent,
    PipelineStateEvent,
    TextDecodedEvent,
    ToneDetectedEvent,
    create_error_event,
    create_text_event,
    create_tone_event,
)

__all__ = [
    # Core infrastructure
    "EventBus",
    "EventHandler",
    "EventMiddleware",
    "get_global_event_bus",
    "reset_global_event_bus",
    # Event types
    "BaseEvent",
    "AudioChunkEvent",
    "ToneDetectedEvent",
    "MorsePatternEvent",
    "TextDecodedEvent",
    "PipelineStateEvent",
    "ErrorEvent",
    "MetricsEvent",
    # Event creation helpers
    "create_tone_event",
    "create_text_event",
    "create_error_event",
    # Built-in handlers
    "LoggingEventHandler",
    "MetricsEventHandler",
    "DebugEventHandler",
]

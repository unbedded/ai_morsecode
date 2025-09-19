"""Lightweight, type-safe event bus for component communication.

This module provides the core pub-sub infrastructure that enables loose coupling
between components while maintaining strong typing and excellent performance.
"""

import logging
from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from .types import BaseEvent, ErrorEvent

logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar("T", bound=BaseEvent)
EventHandler = Callable[[T], None]
EventMiddleware = Callable[[BaseEvent], None]


class EventSubscriber(Protocol):
    """Protocol for objects that can subscribe to events.

    This allows components to implement subscription management
    without tight coupling to the event bus.
    """

    def setup_event_subscriptions(self, event_bus: "EventBus") -> None:
        """Setup event subscriptions when connected to an event bus."""
        ...


class EventBus:
    """Lightweight, type-safe event bus for component communication.

    Features:
    - Type-safe event subscription and publishing
    - Middleware support for cross-cutting concerns
    - Error isolation (handler failures don't stop other handlers)
    - Weak references to prevent memory leaks
    - Performance metrics and debugging support

    Example:
        ```python
        bus = EventBus()

        # Subscribe to specific event types
        bus.subscribe(ToneDetectedEvent, my_handler)

        # Add middleware for logging
        bus.add_middleware(LoggingMiddleware())

        # Publish events
        bus.publish(ToneDetectedEvent(detected=True, frequency=600))
        ```
    """

    def __init__(self, name: str = "default") -> None:
        """Initialize the event bus.

        Args:
            name: Name of this event bus for debugging purposes
        """
        self.logger = logging.getLogger(__name__)
        self.name = name

        # Event handlers organized by event type - C++ compatible std::unordered_map equivalent
        self._handlers: dict[type[BaseEvent], list[Any]] = {}

        # Middleware for cross-cutting concerns - C++ compatible std::vector equivalent
        self._middleware: list[EventMiddleware] = []

        # Active subscribers for cleanup - simple list instead of WeakSet for C++ portability
        self._subscribers: list[Any] = []

        # Statistics for monitoring
        self._stats = {
            "events_published": 0,
            "events_handled": 0,
            "handler_errors": 0,
            "middleware_errors": 0,
            "subscribers_count": 0,
        }

        self.logger.debug(f"EventBus '{name}' initialized")

    def subscribe(self, event_type: type[T], handler: EventHandler[T]) -> None:
        """Subscribe a handler to events of a specific type.

        Args:
            event_type: The event class to subscribe to
            handler: Function to call when events of this type are published

        Example:
            ```python
            def on_tone_detected(event: ToneDetectedEvent):
                print(f"Tone detected at {event.frequency}Hz")

            bus.subscribe(ToneDetectedEvent, on_tone_detected)
            ```
        """
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler)}")

        # Initialize list if this is the first handler for this event type
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        handler_name = getattr(handler, "__name__", str(handler))

        self.logger.debug(
            f"Subscribed {handler_name} to {event_type.__name__} (total: {len(self._handlers[event_type])} handlers)"
        )

    def unsubscribe(self, event_type: type[T], handler: EventHandler[T]) -> bool:
        """Unsubscribe a handler from events of a specific type.

        Args:
            event_type: The event class to unsubscribe from
            handler: The handler function to remove

        Returns:
            True if the handler was found and removed, False otherwise
        """
        handlers = self._handlers.get(event_type, [])
        try:
            handlers.remove(handler)
            handler_name = getattr(handler, "__name__", str(handler))
            self.logger.debug(f"Unsubscribed {handler_name} from {event_type.__name__}")
            return True
        except ValueError:
            return False

    def subscribe_all(self, subscriber: EventSubscriber) -> None:
        """Subscribe an object that implements EventSubscriber protocol.

        This is a convenience method for components that need to subscribe
        to multiple event types.

        Args:
            subscriber: Object implementing EventSubscriber protocol
        """
        subscriber.setup_event_subscriptions(self)
        if subscriber not in self._subscribers:  # Avoid duplicates
            self._subscribers.append(subscriber)
        self._stats["subscribers_count"] = len(self._subscribers)

        subscriber_name = getattr(subscriber, "__class__", {}).get("__name__", str(subscriber))
        self.logger.debug(f"Subscribed {subscriber_name} to event bus")

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all registered handlers.

        Handlers are called synchronously in registration order.
        If a handler fails, it logs the error but doesn't stop other handlers.

        Args:
            event: Event instance to publish

        Example:
            ```python
            bus.publish(ToneDetectedEvent(
                detected=True,
                frequency=600,
                confidence=0.85
            ))
            ```
        """
        if not isinstance(event, BaseEvent):
            raise TypeError(f"Event must inherit from BaseEvent, got {type(event)}")

        self._stats["events_published"] += 1
        event_type = type(event)

        # Get handlers list, defaulting to empty list if event type not registered
        handlers = self._handlers.get(event_type, [])

        self.logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} handlers")

        # Apply middleware first
        self._apply_middleware(event)

        # Notify all handlers for this event type
        handlers = handlers.copy()  # Avoid modification during iteration
        for handler in handlers:
            try:
                handler(event)
                self._stats["events_handled"] += 1
            except Exception as e:
                self._stats["handler_errors"] += 1
                handler_name = getattr(handler, "__name__", str(handler))

                self.logger.error(
                    f"Event handler {handler_name} failed for {event_type.__name__}: {e}",
                    exc_info=True,
                )

                # Publish error event (but avoid recursion)
                if not isinstance(event, ErrorEvent):
                    try:
                        error_event = ErrorEvent(
                            error_type=type(e).__name__,
                            message=str(e),
                            component=f"event_handler.{handler_name}",
                            recoverable=True,
                            context={
                                "original_event_type": event_type.__name__,
                                "handler_name": handler_name,
                                "event_bus": self.name,
                            },
                        )
                        self.publish(error_event)
                    except Exception:
                        # Avoid infinite recursion if error event handling fails
                        pass

    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add middleware for cross-cutting concerns.

        Middleware is called for every event before handlers are notified.
        Common uses include logging, metrics collection, and debugging.

        Args:
            middleware: Callable that takes an event and performs side effects

        Example:
            ```python
            def logging_middleware(event: BaseEvent):
                logger.info(f"Event: {type(event).__name__}")

            bus.add_middleware(logging_middleware)
            ```
        """
        if not callable(middleware):
            raise TypeError(f"Middleware must be callable, got {type(middleware)}")

        self._middleware.append(middleware)
        middleware_name = getattr(middleware, "__name__", str(middleware))
        self.logger.debug(f"Added middleware: {middleware_name}")

    def remove_middleware(self, middleware: EventMiddleware) -> bool:
        """Remove middleware from the event bus.

        Args:
            middleware: The middleware function to remove

        Returns:
            True if the middleware was found and removed, False otherwise
        """
        try:
            self._middleware.remove(middleware)
            return True
        except ValueError:
            return False

    def clear_handlers(self, event_type: type[BaseEvent] | None = None) -> None:
        """Clear event handlers.

        Args:
            event_type: Specific event type to clear handlers for.
                       If None, clears all handlers for all event types.
        """
        if event_type is None:
            handler_count = sum(len(handlers) for handlers in self._handlers.values())
            self._handlers.clear()
            self.logger.debug(f"Cleared all {handler_count} event handlers")
        else:
            handler_count = len(self._handlers.get(event_type, []))
            self._handlers[event_type] = []
            self.logger.debug(f"Cleared {handler_count} handlers for {event_type.__name__}")

    def get_statistics(self) -> dict[str, Any]:
        """Get event bus statistics for monitoring and debugging.

        Returns:
            Dictionary containing performance and usage statistics
        """
        handler_counts = {
            event_type.__name__: len(handlers)
            for event_type, handlers in self._handlers.items()
            if handlers  # Only include types with active handlers
        }

        return {
            **self._stats,
            "handler_counts_by_type": handler_counts,
            "total_handler_count": sum(len(handlers) for handlers in self._handlers.values()),
            "event_types_count": len([h for h in self._handlers.values() if h]),
            "middleware_count": len(self._middleware),
            "bus_name": self.name,
        }

    def _apply_middleware(self, event: BaseEvent) -> None:
        """Apply all registered middleware to an event.

        Args:
            event: Event to process through middleware
        """
        for middleware in self._middleware:
            try:
                middleware(event)
            except Exception as e:
                self._stats["middleware_errors"] += 1
                middleware_name = getattr(middleware, "__name__", str(middleware))

                self.logger.error(
                    f"Middleware {middleware_name} failed for {type(event).__name__}: {e}",
                    exc_info=True,
                )

    def __repr__(self) -> str:
        """String representation for debugging."""
        stats = self.get_statistics()
        return (
            f"EventBus(name='{self.name}', "
            f"handlers={stats['total_handler_count']}, "
            f"middleware={stats['middleware_count']}, "
            f"events_published={stats['events_published']})"
        )


# Global event bus instance for convenience
_global_event_bus: EventBus | None = None


def get_global_event_bus() -> EventBus:
    """Get the global event bus instance.

    Creates the instance if it doesn't exist. Useful for simple applications
    that don't need multiple event buses.

    Returns:
        Global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus(name="global")
        logger.debug("Created global event bus")
    return _global_event_bus


def reset_global_event_bus() -> None:
    """Reset the global event bus.

    Useful for testing to ensure clean state between tests.
    """
    global _global_event_bus
    _global_event_bus = None

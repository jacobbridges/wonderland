from threading import Lock
from typing import Callable
from logging import Logger, getLogger


class Topic:
    """
    The event queue of an event based system.

    **Notes:**

    -   This is a base class that orchestrates the connections between events
        and their corresponding handlers.

    -   The `Topic` class is designed with *thread safety* in mind. All methods
        which mutate state are guarded by a Lock to prevent race conditions.
    """

    __queue: list["BaseEvent"] | None = None
    """A naive collection of unprocessed events."""

    __registry: dict[type["BaseEvent"], list[Callable[["BaseEvent"], None]]] | None = None
    """A registry of event types and their associated handlers (or subscribers)."""

    __thread_lock: Lock = Lock()
    """A `threading.Lock()` object used for thread synchronization."""

    __logger: Logger = getLogger("Topic")
    """A Logger object used to log information from the Topic class."""

    def __new__(cls, *args, **kwargs):
        """This class is not meant to be instantiated."""
        raise NotImplementedError(
            "Will not instantiate Topic class. Try subclassing for "
            "customization."
        )

    @classmethod
    def _get_logger(cls) -> Logger:
        return cls.__logger

    @classmethod
    def push(cls, event: "BaseEvent"):
        with cls.__thread_lock:
            cls.__queue.append(event)

    @classmethod
    def pop(cls) -> "BaseEvent":
        with cls.__thread_lock:
            return cls.__queue.pop(-1)

    @classmethod
    def add_handler(cls, event_klass: type["BaseEvent"], handler: Callable[["BaseEvent"], None]):
        with cls.__thread_lock:
            cls.__registry.setdefault(event_klass, list()).append(handler)

    @classmethod
    def remove_handler(cls, event_klass: type["BaseEvent"], handler: Callable[["BaseEvent"], None]):
        with cls.__thread_lock:
            cls.__registry[event_klass].remove(handler)


    @classmethod
    def register(cls, event_klass: type["BaseEvent"]):
        """
        Decorate a function as a subscriber for the given event type.

        :param event_klass: The event type to register.
        :return: A decorated function.
        """
        def register_decorator(func):
            cls.add_handler(event_klass, func)
            return func
        return register_decorator

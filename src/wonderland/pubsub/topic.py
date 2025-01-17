from threading import Lock, Thread
from typing import Callable, Optional
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

    __queue: list["BaseEvent"] | None = list()
    """A naive collection of unprocessed events."""

    __registry: dict[type["BaseEvent"], list[Callable[["BaseEvent"], None]]] | None = dict()
    """A registry of event types and their associated handlers (or subscribers)."""

    __thread_lock: Lock = Lock()
    """A `threading.Lock()` object used for thread synchronization."""

    __logger: Logger = getLogger("Topic")
    """A Logger object used to log information from the Topic class."""

    __pool: list[Thread] = []
    """A pool of threads where events are processed."""

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
        cls.process_next_event()

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

    @classmethod
    def process_next_event(cls, raise_if_empty=True) -> Optional["BaseEvent"]:
        try:
            next_event = cls.pop()
        except IndexError as e:
            if raise_if_empty:
                raise
            return
        for event_klass, handlers in cls.__registry.items():
            if isinstance(next_event, event_klass):
                for handler in handlers:
                    handler(next_event)
        #             t = Thread(target=handler, args=(next_event,))
        #             t.start()
        #             cls.__pool.append(t)
        # cls.__pool = [t for t in cls.__pool if t.is_alive()]
        return next_event

    @classmethod
    def close(cls):
        for t in cls.__pool:
            if t.is_alive():
                t.join()

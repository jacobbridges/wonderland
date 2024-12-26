"""
Having trouble wrapping my head around how to make an event based library
  without websockets. I want the wonderland module to be decoupled from the
  serving mechanism. So I decided to start with a naive approach and iterate
  upon it.

Before you criticize - I know. I should use queues instead of lists, or
  ThreadPools instead of a single Thread, or maybe grab a quality event library
  off the shelf instead of home-brewing this disaster. This is my process, get
  over it.
"""
from functools import wraps
from threading import Thread, Lock
from typing import Callable
from time import sleep

from pydantic import BaseModel


class Room(BaseModel):
    name: str

class User(BaseModel):
    name: str
    room: Room

user = User(name="Mad Hatter", room=Room(name="Garden"))


"""
Topics ========================================================================

In this event based system, a "topic" is an event queue.

I want to tinker with a class with state which cannot be instantiated. Similar
  to the singleton pattern. Curious if I can share this class between threads
  with little effort..
===============================================================================
"""
class Topic:
    queue = list()
    handlers = dict()
    lock = Lock()

    def __new__(cls, *args, **kwargs):
        """This class is meant to be used without instantiation."""
        raise NotImplementedError("Will not instantiate Topic class.")

    @classmethod
    def push(cls, event: "BaseEvent"):
        with cls.lock:
            cls.queue.append(event)

    @classmethod
    def pop(cls):
        with cls.lock:
            return cls.queue.pop(-1)

    @classmethod
    def add_handler(cls, event_klass: type["BaseEvent"], handler: Callable[["BaseEvent"], None]):
        with cls.lock:
            cls.handlers.setdefault(event_klass, list()).append(handler)

    @classmethod
    def remove_handler(cls, event_klass: type["BaseEvent"], handler: Callable[["BaseEvent"], None]):
        with cls.lock:
            cls.handlers[event_klass].remove(handler)

    @classmethod
    def process_next_event(cls, raise_if_empty=True):
        try:
            next_event = cls.pop()
        except IndexError as e:
            if raise_if_empty:
                raise
            return
        for event_klass, handlers in cls.handlers.items():
            if isinstance(next_event, event_klass):
                for handler in handlers:
                    handler(next_event)

    @classmethod
    def register(cls, event_klass: type["BaseEvent"]):
        def register_decorator(func):
            cls.add_handler(event_klass, func)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return register_decorator


"""
Events ========================================================================

In an event-based system, it makes sense there would be lots of events.

I don't love the idea of each action from the user resulting in a custom event 
  class. My prediction is that it will get very cluttered, very quickly.
  However, the upside is that events are easily distinguishable. An alternative
  could be a `code` attribute on every event which is unique, but then I would
  need to have an enum of event codes somewhere in the system.
  
I also don't love the idea of "Input" events vs "Output" events, but perhaps 
  that is because I am new to event based programming. Essentially I want to 
  identify two different streams: events being sent to the server, and events
  being sent to the client.
===============================================================================
"""
class BaseEvent(BaseModel):
    io_flag: str


class ExitEvent(BaseEvent):
    io_flag: str = "i"


@Topic.register(ExitEvent)
def handle_exit_event(event: ExitEvent):
    raise SystemExit("Found exit event")


class BaseInputEvent(BaseEvent):
    io_flag: str = "i"
    channel: str
    raw_message: str


class BaseOutputEvent(BaseEvent):
    io_flag: str = "o"
    channel: str
    markup: str

    @property
    def as_plain_text(self):
        return self.markup


class HelpInputEvent(BaseInputEvent):
    ...


@Topic.register(HelpInputEvent)
def handle_help_input_event(event: "HelpInputEvent", **kwargs):
    output_event = HelpOutputEvent(
        channel=event.channel,
        markup="Here is all the help you need: 📚",
    )
    Topic.push(output_event)


class HelpOutputEvent(BaseOutputEvent):
    ...


def parse_input(raw: str, user: User) -> BaseEvent:
    """
    Parse input into an event.

    Not sure if this translation makes much sense, but my brain can understand
    it. Raw input from the client is sent here, and this function converts that
    raw input into an event for the server to process. Will keep mulling over
    this bit in my head.
    """
    raw = raw.strip()
    if raw.startswith("/"):
        channel_flag, *d = raw.split(" ")
        raw = " ".join(d)
    else:
        channel_flag = "/1"

    channel = {
        "/1": "system",
        "/2": "chat",
    }.get(channel_flag, "system")

    if raw == "help":
        return HelpInputEvent(channel=channel, raw_message=raw)


def loop():
    """
    Extremely simple "game loop" for this naive test.
    """
    while True:
        Topic.process_next_event(raise_if_empty=False)


def input_loop():
    """
    This function has some client and server code.
    TODO: Decouple the client/server code in this function.

    Client code will accept the user's input and push to the server.
    Server code will parse the user's input into an event and submit to the queue.
    """
    while True:
        try:
            raw = input(">> ")
            event = parse_input(raw, user)
            if isinstance(event, BaseInputEvent):
                Topic.push(event)
            else:
                print("Invalid input")  # TODO: Remove this cheat! Should be an event.
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    # With this new implementation, "listeners" are simply handlers for any output events
    Topic.add_handler(BaseOutputEvent, lambda e: print("Client 1:", e.markup))

    # Start the background thread which just runs the Topic.process_next_event() infinitely
    thread = Thread(target=loop)
    thread.start()

    # Listen for input
    input_loop()

    print("waiting for loop() to stop")
    Topic.push(ExitEvent())
    thread.join()

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
Events ========================================================================

In an event-based system, it makes sense there would lots of events.

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


def handle_event(*, event: BaseEvent, queue: list[BaseEvent], listeners: list[Callable]):
    """
    Handle all events.
    TODO: Create registry + decorator function to register even handlers.
    TODO: Update this function to use the event handler registry.

    This code should be split among several functions, maybe one for handling
    each type of event. Would be nice to have a registry of events -> handlers,
    and the code would be easier to read if a function could be decorated with
    something like @handles(HelpInputEvent).
    """
    if event.io_flag == "o":
        for listener in listeners:
            listener(event)
    elif isinstance(event, HelpInputEvent):
        queue.append(HelpOutputEvent(
            channel=event.channel,
            markup="Here is all the help you need: 📚",
        ))
    elif isinstance(event, ExitEvent):
        raise SystemExit()


def loop(queue: list[BaseEvent], subscribers: list[Callable]):
    """
    Will eventually be replaced by a server of some kind. The logic will never
    be completely decoupled, but the goal is to keep wonderland's api very
    minimal to make it easy to swap server tech and experiment.

    The current dependencies:
    - queue
    - subscribers
    - handle_event
    """

    while True:

        # Process events
        stop = False
        while not stop:
            try:
                event = queue.pop()
                if event.io_flag == "o":
                    stop = True
                handle_event(event=event, queue=queue, listeners=subscribers)
            except IndexError:
                pass
            except SystemExit:
                return
            sleep(0.3)


def input_loop(queue: list[BaseInputEvent]):
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
                queue.append(event)
            else:
                print("Invalid input")  # TODO: Remove this cheat! Should be an event.
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    from threading import Thread

    queue = []
    subscribers = [lambda e: print(e.as_plain_text)]
    thread = Thread(target=loop, args=(queue, subscribers))
    thread.start()
    input_loop(queue)
    print("waiting for loop() to stop")
    queue.append(ExitEvent())
    thread.join()



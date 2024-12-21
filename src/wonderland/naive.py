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
    while True:
        try:
            raw = input(">> ")
            event = parse_input(raw, user)
            if isinstance(event, BaseInputEvent):
                queue.append(event)
            else:
                print("Invalid input")
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



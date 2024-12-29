"""
Having trouble wrapping my head around how to make an event based library
  without websockets. I want the wonderland module to be decoupled from the
  serving mechanism. So I decided to start with a naive approach and iterate
  upon it.

This naive solution is becoming difficult to parse. Testing a few more complex
  scenarios to ensure this pattern is stable before fully committing to this
  technique. I also want to try using a curses library to organize outputs
  by channel.
"""
from functools import wraps
from multiprocessing.context import TimeoutError
from multiprocessing.pool import ThreadPool
from threading import Thread, Lock
from typing import Callable, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session as SQLSession, select


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    room_id: int | None = Field(default=None, foreign_key="room.id")
    room: Optional["Room"] | None = Relationship(back_populates="users")


class Room(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    users: list["User"] = Relationship(back_populates="room")
    things: list["Thing"] = Relationship(back_populates="room")


class Thing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    room_id: int | None = Field(default=None, foreign_key="room.id")
    room: Optional["Room"] | None = Relationship(back_populates="things")


# Interesting note: Using an in-memory database will not work with threads.
engine = create_engine("sqlite:///test", echo=True)


def setup_db():
    """
    Create a quick database to test making database calls from event handlers.
    """
    SQLModel.metadata.create_all(engine)

    with SQLSession(engine) as sql_session:
        results = sql_session.exec(select(Room).where(Room.name == "Library"))
        room = results.first()
        if not room:
            room = Room(name="Library")
            sql_session.add(room)
            sql_session.commit()

        results = sql_session.exec(select(User).where(User.name == "Mad Hatter"))
        user = results.first()
        if not user:
            user = User(name="Mad Hatter", room_id=room.id)
            sql_session.add(user)
            sql_session.commit()


def get_user(name: str) -> User | None:
    with SQLSession(engine) as sql_session:
        statement = select(User).where(User.name == name)
        results = sql_session.exec(statement)
        return results.one()


def get_room_and_things(room_id: int) -> (Room | None, list[Thing]):
    with SQLSession(engine) as sql_session:
        room = sql_session.get(Room, room_id)
        return room, room.things


def create_item(name: str, room_id: int) -> Thing:
    with SQLSession(engine) as sql_session:
        thing = Thing(name=name, room_id=room_id)
        sql_session.add(thing)
        sql_session.commit()
        sql_session.refresh(thing)
        return thing


"""
Session =======================================================================

The session tracks information about the current session, like who the 
  currently authenticated user is.
===============================================================================
"""


class Session(BaseModel):
    user: User


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
    pool = ThreadPool(processes=4)
    results = []

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
    def process_next_event(cls, raise_if_empty=True) -> Optional["BaseEvent"]:
        try:
            next_event = cls.pop()
        except IndexError as e:
            if raise_if_empty:
                raise
            return
        for event_klass, handlers in cls.handlers.items():
            if isinstance(next_event, event_klass):
                for handler in handlers:
                    result = cls.pool.apply_async(handler, args=(next_event,))
                    Topic.results.append(result)
        return next_event

    @classmethod
    def register(cls, event_klass: type["BaseEvent"]):
        def register_decorator(func):
            cls.add_handler(event_klass, func)
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    import logging
                    logging.exception("Something happened in the thread..")
                    raise
            return wrapper

        return register_decorator

    @classmethod
    def close(cls):
        for result in cls.results:
            try:
                result.get(timeout=3)
            except TimeoutError:
                import logging
                logging.exception("Worker timed out after 3 seconds")
        cls.pool.close()


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
    channel: str
    raw_message: str
    session: Session
    io_flag: str = "i"


class BaseOutputEvent(BaseEvent):
    channel: str
    markup: str
    io_flag: str = "o"

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


class InvalidInputEvent(BaseInputEvent):
    ...


@Topic.register(InvalidInputEvent)
def handle_invalid_input_event(event: "InvalidInputEvent", **kwargs):
    output_event = InvalidInputOutputEvent(
        channel=event.channel,
        markup="Invalid input!",
    )
    Topic.push(output_event)


class InvalidInputOutputEvent(BaseOutputEvent):
    ...


class LookInputEvent(BaseInputEvent):
    ...


def aan(word: str) -> str:
    """Given the word, which article to use? 'a' or 'an'?"""
    for vowel in "aeiou":
        if word.startswith(vowel):
            return "an"
    return "a"


@Topic.register(LookInputEvent)
def handle_look_input_event(event: "LookInputEvent", **kwargs):
    room, things = get_room_and_things(event.session.user.room_id)
    print(room, things, "yeah")
    markup = f"You look around the {room.name}."
    for thing in things:
        markup += f" You see {aan(thing.name)} {thing.name}."
    output_event = LookOutputEvent(
        channel=event.channel,
        markup=markup,
    )
    Topic.push(output_event)


class LookOutputEvent(BaseOutputEvent):
    ...


class CreateItemInputEvent(BaseInputEvent):
    item_name: str


class CreateItemOutputEvent(BaseOutputEvent):
    ...


@Topic.register(CreateItemInputEvent)
def handle_create_item_input_event(event: "CreateItemInputEvent", **kwargs):
    room, _ = get_room_and_things(event.session.user.room_id)
    thing = create_item(event.item_name, room.id)
    markup = f"You create {aan(thing.name)} {thing.name} and drop it on the ground."
    output_event = CreateItemOutputEvent(
        channel=event.channel,
        markup=markup,
    )
    Topic.push(output_event)


def parse_input(raw: str, session: Session) -> BaseEvent:
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
        return HelpInputEvent(
            session=session,
            channel=channel,
            raw_message=raw,
        )
    if raw == "look":
        return LookInputEvent(
            session=session,
            channel=channel,
            raw_message=raw,
        )
    if raw.startswith("create"):
        thing_name = raw.split(" ")[1].strip()
        return CreateItemInputEvent(
            session=session,
            channel=channel,
            item_name=thing_name,
            raw_message=raw,
        )


def loop():
    """
    Extremely simple "game loop" for this naive test.
    """
    while True:
        event = Topic.process_next_event(raise_if_empty=False)
        if isinstance(event, ExitEvent):
            return


def client_loop(session: Session):
    """
    This function has some client and server code.
    TODO: Decouple the client/server code in this function.

    Client code will accept the user's input and push to the server.
    Server code will parse the user's input into an event and submit to the queue.
    """
    while True:
        try:
            raw = input(">> ")
            event = parse_input(raw, session)
            if isinstance(event, BaseInputEvent):
                Topic.push(event)
            else:
                Topic.push(InvalidInputEvent(
                    session=session,
                    raw_message=raw,
                    channel="system",
                ))
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    # Create the database and a user / room
    setup_db()

    # Session for our scenario
    u = get_user("Mad Hatter")
    s = Session(user=u)

    # With this new implementation, "listeners" are simply handlers for any output events
    Topic.add_handler(BaseOutputEvent, lambda e: print("Client 1:", e.markup))

    # Start the background thread which just runs the Topic.process_next_event() infinitely
    thread = Thread(target=loop)
    thread.start()

    # Listen for input
    client_loop(s)

    print("waiting for loop() to stop")
    Topic.push(ExitEvent())
    thread.join()
    Topic.close()

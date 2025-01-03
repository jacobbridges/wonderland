"""
Having trouble wrapping my head around how to make an event based library
  without websockets. I want the wonderland module to be decoupled from the
  serving mechanism. So I decided to start with a naive approach and iterate
  upon it.

This naive solution is becoming difficult to parse. Testing a few more complex
  scenarios to ensure this pattern is stable before fully committing to this
  technique. I also want to try using a curses library to organize outputs
  by channel.

More thoughts:
  1. Command parsing needs to be sorted out. I'm thinking pydantic models for
     each type of command, then adding them to a registry. When parsing for
     input, loop through the different available commands. I like this, but
     each new command will require a Command model, EventInput model, and
     EventOutput model. Seems very tedious - am I missing something?
  2. Topic being global is annoying me. Prevents dependency injection for
     test cases.
  3. Command success / error events. This can get very verbose - should I
     create a success and failure event class for each command? Should I add a
     "status" attribute to the OutputEvent which can be "success" or "failure"?
"""
from functools import wraps
from threading import Thread, Lock
from typing import Callable, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Log, TabbedContent, TabPane

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session as SQLSession, select, or_


"""
UI Code =======================================================================

Use the incredible `textual` library to build a simple UI in the terminal. The
  UI draws an input box at the bottom of the screen, and any command output is
  written to the log at the top of the screen.
  
I am also tinkering with the idea of tabs for each channel. Haven't really
  fleshed out what I want to do with channels yet.
===============================================================================
"""


class CliApp(App):
    """Simple app to demonstrate chatting to an LLM."""

    AUTO_FOCUS = "Input"

    CSS = """
    Header {
        max-height: 10vh;
    }
    TabbedContent {
        max-height: 60vh;
    }
    Input {
        max-height: 20vh;
    }
    Footer {
        max-height: 10vh;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("System", id="system-tab"):
                yield Log(id="system-output")
            with TabPane("Room", id="room-tab"):
                yield Log(id="room-output")
        yield Input(placeholder="Input your command here")
        yield Footer()

    def on_mount(self) -> None:
        user = get_user_by_name("Mad Hatter")
        self.session = Session(user=user)
        room_output = self.query_one("#room-output")
        system_output = self.query_one("#system-output")
        def handle_output(e: BaseOutputEvent):
            if e.channel == "system":
                system_output.write_line(e.markup)
            elif e.channel == "room":
                room_output.write_line(e.markup)
        Topic.add_handler(BaseOutputEvent, handle_output)

    @on(Input.Submitted)
    def on_input(self, event: Input.Submitted) -> None:
        """When the user hits return."""
        event.input.clear()
        self.session.user = get_user_by_name(self.session.user.name)
        naive_event = parse_input(event.value, self.session)
        if isinstance(naive_event, BaseInputEvent):
            Topic.push(naive_event)
        else:
            Topic.push(InvalidInputEvent(
                session=self.session,
                raw_message=event.value,
                channel="system",
            ))


"""
Database ======================================================================

Define a few simple models and functions for creating and seeding the database.
===============================================================================
"""


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


class Door(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    state: str
    room_1_id: int | None = Field(default=None)
    room_2_id: int | None = Field(default=None)


# Interesting note: Using an in-memory database will not work with threads.
engine = create_engine("sqlite:///test", echo=False)


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


def get_user_by_name(name: str) -> User | None:
    with SQLSession(engine) as sql_session:
        statement = select(User).where(User.name == name)
        results = sql_session.exec(statement)
        return results.one()
    

def move_user(user_id: int, room_id: int) -> User:
    with SQLSession(engine) as sql_session:
        user = sql_session.get_one(User, user_id)
        room = sql_session.get_one(Room, room_id)
        user.room_id = room.id
        sql_session.add(user)
        sql_session.commit()
        sql_session.refresh(user)
        return user


def get_room_and_things(room_id: int) -> (Room | None, list[Thing]):
    with SQLSession(engine) as sql_session:
        room = sql_session.get(Room, room_id)
        return room, room.things
    

def get_room_by_name(room_name: str) -> (Room | None):
    with SQLSession(engine) as sql_session:
        statement = select(Room).where(Room.name == room_name)
        results = sql_session.exec(statement)
        return results.one()


def create_item(name: str, room_id: int) -> Thing:
    with SQLSession(engine) as sql_session:
        thing = Thing(name=name, room_id=room_id)
        sql_session.add(thing)
        sql_session.commit()
        sql_session.refresh(thing)
        return thing


def destroy_item(thing_id: int) -> Thing | None:
    with SQLSession(engine) as sql_session:
        thing = sql_session.get(Thing, thing_id)
        sql_session.delete(thing)
        sql_session.commit()
        return thing


def create_room(name: str) -> Room:
    with SQLSession(engine) as sql_session:
        room = Room(name=name)
        sql_session.add(room)
        sql_session.commit()
        sql_session.refresh(room)
        return room


def create_door(name, room_ids: tuple[int, int]) -> Door:
    with SQLSession(engine) as sql_session:
        door = Door(
            name=name,
            room_id_1=room_ids[0],
            room_id_2=room_ids[1],
            state="open",
        )
        sql_session.add(door)
        sql_session.commit()
        sql_session.refresh(door)
        return door


def enter_door(name: str, current_room_id: int, user_id: int) -> User:
    with SQLSession(engine) as sql_session:
        user = sql_session.get(User, user_id)
        assert user is not None
        statement = select(Door)\
            .where(Door.name == name)\
            .where(or_(Door.room_1_id == current_room_id, Door.room_2_id == current_room_id))
        results = sql_session.exec(statement)
        door = results.one()
        other_room_id = [room_id for room_id in (door.room_1_id, door.room_2_id) if room_id != current_room_id]
        user.room_id = other_room_id
        sql_session.add(user)
        sql_session.commit()
        sql_session.refresh(user)
        return user


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
    pool = []
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
                    t = Thread(target=handler, args=(next_event,))
                    t.start()
                    cls.pool.append(t)
        cls.pool = [t for t in cls.pool if t.is_alive()]
        return next_event

    @classmethod
    def register(cls, event_klass: type["BaseEvent"]):
        def register_decorator(func):
            cls.add_handler(event_klass, func)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        return register_decorator

    @classmethod
    def close(cls):
        for t in cls.pool:
            if t.is_alive():
                t.join()


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


class LookAtInputEvent(BaseInputEvent):
    item_name: str


class LookAtOutputEvent(BaseOutputEvent):
    ...


@Topic.register(LookAtInputEvent)
def handle_look_at_input_event(event: "LookAtInputEvent", **kwargs):
    room, things = get_room_and_things(event.session.user.room_id)
    focus = None
    for thing in things:
        if thing.name == event.item_name:
            focus = thing
    if focus is None:
        Topic.push(LookAtOutputEvent(
            channel=event.channel,
            markup="You do not see that here.",
        ))
        return

    output_event = CreateItemOutputEvent(
        channel=event.channel,
        markup=f"It is {aan(focus.name)} {focus.name}.",
    )
    Topic.push(output_event)


class DestroyItemInputEvent(BaseInputEvent):
    item_name: str


class DestroyItemOutputEvent(BaseOutputEvent):
    ...


@Topic.register(DestroyItemInputEvent)
def handle_destroy_item_input_event(event: "DestroyItemInputEvent", **kwargs):
    room, things = get_room_and_things(event.session.user.room_id)
    focus = None
    for thing in things:
        if thing.name == event.item_name:
            focus = thing
    if focus is None:
        Topic.push(DestroyItemOutputEvent(
            channel=event.channel,
            markup="You do not see that here.",
        ))
        return

    destroy_item(focus.id)

    output_event = CreateItemOutputEvent(
        channel=event.channel,
        markup=f"The {focus.name} instantly vanishes from existence.",
    )
    Topic.push(output_event)


class CreateRoomInputEvent(BaseInputEvent):
    room_name: str


class CreateRoomOutputEvent(BaseOutputEvent):
    ...


@Topic.register(CreateRoomInputEvent)
def handle_create_room_input_event(event: "CreateRoomInputEvent", **kwargs):
    room = create_room(event.room_name)
    Topic.push(CreateRoomOutputEvent(
        channel=event.channel,
        markup=f"The {room.name} manifests somewhere in the world.",
    ))
    
    
class PlayerPortInputEvent(BaseInputEvent):
    room_name: str
    

class PlayerPortOutputEvent(BaseOutputEvent):
    ...


@Topic.register(PlayerPortInputEvent)
def handle_player_port_input_event(event: "PlayerPortInputEvent", **kwargs):
    room = get_room_by_name(event.room_name)
    user = move_user(event.session.user.id, room.id)
    event.session.user = user
    Topic.push(PlayerPortOutputEvent(
        channel=event.channel,
        markup=f"You teleport to the {room.name}.",
    ))


"""
Command Parsing ===============================================================

Goal to restructure command parsing:

- Commands should be objects.
- Available commands should be tracked in a registry.
- Input parser should be a simple function which leverages the registry.
===============================================================================
"""


class Command(BaseModel):
    trigger: str
    pos_args: list[str]
    opt_args: list[str]
    event_class: type[BaseEvent]

    def parse(self, raw: str) -> dict[str, str]:
        """
        This looks bad. I should do a write-up on what's going on here.
        """
        raw_cp = raw.replace(self.trigger, "").strip()
        if len(raw_cp) == 0:
            return dict()

        args = dict()
        cursor = 0
        for pos_arg in self.pos_args:
            arg = ''
            if raw_cp[cursor] in ('"',):
                cursor += 1
                for idx, l in enumerate(raw_cp[cursor:]):
                    if l in ('"',):
                        cursor += (idx + 1)
                        break
                    else:
                        arg += l
            else:
                arg, *rest = raw_cp[cursor:].strip().split(" ")
                cursor += len(arg)
            args[pos_arg] = arg
        return args

    def get_event(self, **args) -> BaseEvent:
        return self.event_class(**args)


class HelpCommand(Command):
    trigger: str = "help"
    pos_args: list[str] = []
    opt_args: list[str] = []
    event_class: type[BaseEvent] = HelpInputEvent


class LookCommand(Command):
    trigger: str = "look"
    pos_args: list[str] = []
    opt_args: list[str] = ["at", "in"]
    event_class: type[BaseEvent] = LookInputEvent

    def parse(self, raw: str) -> dict[str, str]:
        raw = raw.replace(self.trigger, "").strip()
        parsed = dict()
        if len(raw) == 0:
            return parsed

        segments = raw.split(" ")
        current_idx = 0
        grouped_segments = []
        while current_idx < len(segments):
            current_segment = segments[current_idx]
            if current_segment.startswith('"'):
                look_idx = current_idx
                end_idx = None
                while look_idx < len(segments):
                    look_segment = segments[look_idx]
                    if look_segment.endswith('"'):
                        end_idx = look_idx
                        break
                    else:
                        look_idx += 1
                if end_idx is None:
                    raise ValueError("Unmatched quote found!")
                grouped_segments.append(" ".join(segments[current_idx:end_idx+1]).strip('"'))
                current_idx = end_idx
            else:
                grouped_segments.append(current_segment)
            current_idx += 1
        for idx, segment in enumerate(grouped_segments):
            if segment in self.opt_args:
                parsed[segment] = grouped_segments[idx + 1]
        return parsed

    def get_event(self, **args) -> BaseEvent:
        if args.get("at"):
            args["item_name"] = args.pop("at")
            return LookAtInputEvent(**args)
        else:
            return self.event_class(**args)


class CreateCommand(Command):
    trigger: str = "create"
    pos_args: list[str] = ["item_name"]
    opt_args: list[str] = []
    event_class: type[BaseEvent] = CreateItemInputEvent


class DestroyCommand(Command):
    trigger: str = "destroy"
    pos_args: list[str] = ["item_name"]
    opt_args: list[str] = []
    event_class: type[BaseEvent] = DestroyItemInputEvent


class RoomCommand(Command):
    trigger: str = "room"
    pos_args: list[str] = ["room_name"]
    opt_args: list[str] = []
    event_class: type[BaseEvent] = CreateRoomInputEvent


class PortCommand(Command):
    trigger: str = "port"
    pos_args: list[str] = ["room_name"]
    opt_args: list[str] = []
    event_class: type[BaseEvent] = PlayerPortInputEvent


class CommandRegistry:
    def __init__(self):
        self._map_by_trigger = {}
        self.load_commands()

    def load_commands(self):
        for klass in Command.__subclasses__():
            instance = klass()
            self._map_by_trigger[instance.trigger] = instance

    def get_command(self, raw: str) -> Command:
        for trigger, command in self._map_by_trigger.items():
            if raw.startswith(trigger):
                return command


def parse_input(raw: str, session: Session) -> BaseEvent | None:
    """
    Parse input into an event.
    """
    raw = raw.strip()
    if not raw: return
    if raw.startswith("/"):
        channel_flag, *d = raw.split(" ")
        raw = " ".join(d)
    else:
        channel_flag = "/1"

    channel = {
        "/1": "system",
        "/2": "room",
    }.get(channel_flag, "system")

    command = CommandRegistry().get_command(raw)
    if command.pos_args or command.opt_args:
        args = command.parse(raw)
    else:
        args = dict()
    return command.get_event(
        session=session,
        channel=channel,
        raw_message=raw,
        **args,
    )


def loop():
    """
    Extremely simple "server loop" for this naive test.
    """
    while True:
        event = Topic.process_next_event(raise_if_empty=False)
        if isinstance(event, ExitEvent):
            return


if __name__ == "__main__":
    # Create the database and a user / room
    setup_db()

    # Start the background thread which just runs the Topic.process_next_event() infinitely
    thread = Thread(target=loop)
    thread.start()

    # Start cli client
    app = CliApp()
    app.run()

    Topic.push(ExitEvent())
    thread.join()
    Topic.close()

"""
This is a simple client for debugging wonderland locally. It uses the amazing
  textual library for the command line interface.
"""
import sys, pathlib

cd = pathlib.Path(__file__).parent.resolve()
project_dir = cd.parent.parent.resolve()
print(project_dir)
sys.path.insert(0, str(project_dir))

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Log

from src.wonderland import models as m
from src.wonderland.pubsub.events.base import BaseOutputEvent
from src.wonderland.pubsub.topic import Topic
from src.wonderland.app import App as Wonderland
from src.wonderland import crud
from src.wonderland.session import Session
from src.wonderland.core.db import new_session, OrmSession


def seed_data_for_debug(orm: OrmSession) -> m.User:
    user = crud.get_user_by_name(
        session=orm,
        name="Mad Hatter",
    )
    if not user:
        user = crud.create_user(
            session=orm,
            data=m.UserCreate(name="Mad Hatter")
        )
    if user.room_id is not None:
        return user
    land = crud.create_land(
        session=orm,
        data=m.LandCreate(
            name="Wonderland",
            owner_id=user.id,
        ),
    )
    room = crud.create_room(
        session=orm,
        data=m.RoomCreate(
            name="Pleasant Garden",
            description="A large table is set under the tree here, just outside the March Hare’s house.",
        ),
        land_id=land.id,
    )
    user = crud.update_user(
        session=orm,
        user=user,
        field="room_id",
        value=room.id,
    )
    return user


class CliApp(App):
    """Simple app to demonstrate the wonderland interface."""

    AUTO_FOCUS = "Input"

    CSS = """
    Header {
        height: 10vh;
    }
    Log {
        height: 65vh;
    }
    Input {
        height: 15vh;
    }
    Footer {
        height: 10vh;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Log(id="app-output")
        yield Input(placeholder="Input your command here")
        yield Footer()

    def on_mount(self) -> None:
        # Start a new orm session
        self.orm = new_session()

        # Assume this user for debug purposes
        user = seed_data_for_debug(self.orm)

        # Construct a new wonderland session
        # TODO: Consider renaming to context?
        self.session = Session(user=user)
        self.session.set_orm(self.orm)
        self.wonderland = Wonderland()
        self.wonderland.build_commands()

        # Define a simple subscriber for output events
        log_output = self.query_one("#app-output")
        def handle_output(e: BaseOutputEvent):
            log_output.write_line(e.markup)
        Topic.add_handler(BaseOutputEvent, handle_output)

    @on(Input.Submitted)
    def on_input(self, event: Input.Submitted) -> None:
        """When the user hits return within the Input element."""
        event.input.clear()
        # Ignore empty commands
        if not event.value.strip():
            return
        cmd = self.wonderland.command_registry.get_command(event.value)
        wevent = cmd.get_event(
            session=self.session,
            raw_message=event.value,
            **cmd.parse(event.value),
        )
        Topic.push(wevent)

    def on_unmount(self) -> None:
        Topic.close()


if __name__ == "__main__":
    app = CliApp()
    app.run()

"""
This is a simple client for debugging wonderland locally. It uses the amazing
  textual library for the command line interface.
"""
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Log

from src.wonderland.models import UserCreate
from src.wonderland.pubsub.events.base import BaseOutputEvent
from src.wonderland.pubsub.topic import Topic
from src.wonderland.app import App as Wonderland
from src.wonderland import crud
from src.wonderland.session import Session
from src.wonderland.core.db import new_session


class CliApp(App):
    """Simple app to demonstrate the wonderland interface."""

    AUTO_FOCUS = "Input"

    CSS = """
    Header = {
        max-height: 10vh;
    }
    Log {
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
        yield Log(id="app-output")
        yield Input(placeholder="Input your command here")
        yield Footer()

    def on_mount(self) -> None:
        # Start a new orm session
        self.orm = new_session()

        # Assume this user for debug purposes
        user = crud.get_user_by_name(
            session=self.orm,
            name="Mad Hatter",
        )
        if not user:
            user = crud.create_user(
                session=self.orm,
                data=UserCreate(name="Mad Hatter")
            )

        # Construct a new wonderland session
        # TODO: Consider renaming to context?
        self.session = Session(
            orm=self.orm,
            user=user,
        )
        self.wonderland = Wonderland()

        # Define a simple subscriber for output events
        log_output = self.query_one("#app-output")
        def handle_output(e: BaseOutputEvent):
            log_output.write_line(e.markup)
        Topic.add_handler(BaseOutputEvent, handle_output)

    @on(Input.Submitted)
    def on_input(self, event: Input.Submitted) -> None:
        """When the user hits return within the Input element."""
        event.input.clear()
        cmd = self.wonderland.command_registry.get_command(event.value)
        wevent = cmd.get_event(
            session=self.session,
            channel="system",
            raw_message=event.value,
            **cmd.parse(event.value),
        )
        Topic.push(wevent)

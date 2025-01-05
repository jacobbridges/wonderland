from src.wonderland.commands.factory import CommandFactory
from src.wonderland.commands.registry import CommandRegistry
from src.wonderland import events


class App:
    def __init__(self):
        self.build_commands()
        self.command_registry = CommandRegistry()
        self.command_registry.load_commands()

    def build_commands(self):
        CommandFactory.create_command(trigger="create", event_class=events.CreateItemInputEvent, pos_args=["item_name"])

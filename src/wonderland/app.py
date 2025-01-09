from src.wonderland.commands.factory import CommandFactory
from src.wonderland.commands.registry import CommandRegistry
from src.wonderland.pubsub import events


class App:
    def __init__(self):
        self.build_commands()
        self.command_registry = CommandRegistry()
        self.command_registry.load_commands()

    def build_commands(self):
        CommandFactory.create_command(trigger="create", event_class=events.CreateItemInputEvent, pos_args=["item_name"])
        CommandFactory.create_command(trigger="look", event_class=events.LookInputEvent)

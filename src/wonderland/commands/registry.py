from src.wonderland.commands.base import BaseCommand


class CommandRegistry:
    def __init__(self):
        self._map_by_trigger = dict()
        self.load_commands()

    def load_commands(self):
        for klass in BaseCommand.__subclasses__():
            instance = klass()
            self._map_by_trigger[instance.trigger] = instance

    def get_command(self, raw: str, help_on_none=True) -> BaseCommand:
        for trigger, command in self._map_by_trigger.items():
            if raw.startswith(trigger):
                return command
        if help_on_none:
            return self._map_by_trigger.get("help")

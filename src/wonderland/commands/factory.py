from src.wonderland.commands.base import BaseCommand, BaseEvent


class CommandFactory:
    subclass_map = dict()

    @classmethod
    def create_command(
            cls,
            *,
            trigger: str,
            event_class: type[BaseEvent],
            pos_args: list[str] | None = None,
            opt_args: list[str] | None = None
    ) -> type[BaseCommand]:
        if pos_args is None:
            pos_args = []
        if opt_args is None:
            opt_args = []
        klass = type(trigger.capitalize() + 'Command', (BaseCommand,), {
            "trigger": trigger,
            "event_class": event_class,
            "pos_args": pos_args,
            "opt_args": opt_args,
        })
        return klass

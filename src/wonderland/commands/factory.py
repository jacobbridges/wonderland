import typing as t

from pydantic import create_model

from src.wonderland.commands.base import BaseCommand
from src.wonderland.pubsub.events.base import BaseEvent


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
        klass = create_model(
            trigger.capitalize() + 'Command',
            __base__=BaseCommand,
            trigger=(str, trigger),
            event_class=(t.Type[BaseEvent], event_class),
            pos_args=(t.List[str], pos_args),
            opt_args=(t.List[str], opt_args),
        )
        # klass = type(trigger.capitalize() + 'Command', (BaseCommand,), {
        #     "trigger": trigger,
        #     "event_class": event_class,
        #     "pos_args": pos_args,
        #     "opt_args": opt_args,
        #     "__annotations__": {
        #         "trigger": str,
        #         "pos_args": t.List[str],
        #         "opt_args": t.List[str],
        #         "event_class": t.Type[BaseEvent],
        #     }
        # })
        return klass

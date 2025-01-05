from pydantic import BaseModel

from src.wonderland.events.base import BaseEvent


class BaseCommand(BaseModel):
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

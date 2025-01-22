from pydantic import BaseModel

from src.wonderland.session import Session


class BaseEvent(BaseModel):
    ...


class BaseInputEvent(BaseEvent):
    raw_message: str
    session: Session
    io_flag: str = "i"


class BaseOutputEvent(BaseEvent):
    markup: str
    io_flag: str = "o"

    @property
    def as_plain_text(self):
        return self.markup


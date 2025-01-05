from pydantic import BaseModel

from src.wonderland.session import Session


class BaseEvent(BaseModel):
    io_flag: str


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


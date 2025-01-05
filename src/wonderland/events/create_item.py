from src.wonderland.events.base import BaseInputEvent, BaseOutputEvent


class CreateItemInputEvent(BaseInputEvent):
    item_name: str


class CreateItemOutputEvent(BaseOutputEvent):
    ...

from src.wonderland.models import ThingCreate
from src.wonderland.pubsub.events.base import BaseInputEvent, BaseOutputEvent
from src.wonderland.pubsub.topic import Topic
from src.wonderland import crud


class CreateItemInputEvent(BaseInputEvent):
    item_name: str


class CreateItemOutputEvent(BaseOutputEvent):
    ...


@Topic.register(CreateItemInputEvent)
def handle_create_item_input_event(event: CreateItemInputEvent, **kwargs):
    thing = crud.create_thing_for_room(
        session=event.session,
        data=ThingCreate(name=event.item_name),
        room_id=event.session.user.room_id
    )
    output_event = CreateItemOutputEvent(
        channel=event.channel,
        markup=f"You create a {thing.name} and drop it on the ground here.",
    )
    Topic.push(output_event)

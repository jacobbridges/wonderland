from src.wonderland.pubsub.events.base import BaseInputEvent, BaseOutputEvent
from src.wonderland.pubsub.topic import Topic
from src.wonderland import crud
from src.wonderland.utils import aan


class LookInputEvent(BaseInputEvent):
    ...


class LookOutputEvent(BaseOutputEvent):
    ...


@Topic.register(LookInputEvent)
def handle_look_input_event(event: LookInputEvent, **kwargs):
    room = crud.get_room(
        session=event.session.orm,
        room_id=event.session.user.room_id
    )
    things = crud.list_things_by_room(
        session=event.session.orm,
        room_id=event.session.user.room_id,
    )
    markup = f"You look around the {room.name}."
    for thing in things:
        markup += f" You see {aan(thing.name)} {thing.name}."
    output_event = LookOutputEvent(
        channel=event.channel,
        markup=markup,
    )
    Topic.push(output_event)

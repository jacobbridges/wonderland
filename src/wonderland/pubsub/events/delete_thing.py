from src.wonderland.pubsub.events.base import BaseInputEvent, BaseOutputEvent
from src.wonderland.pubsub.topic import Topic
from src.wonderland import crud
from src.wonderland.utils import aan


class DeleteItemInputEvent(BaseInputEvent):
    item_name: str


class DeleteItemOutputEvent(BaseOutputEvent):
    ...


@Topic.register(DeleteItemInputEvent)
def handle_delete_item_input_event(event: DeleteItemInputEvent, **kwargs):
    try:
        thing = crud.delete_thing_by_name(
            session=event.session.get_orm(),
            name=event.item_name,
            room_id=event.session.user.room_id,
        )
        message = f"You snap your fingers, and the {thing.name} vanishes."
    except crud.NoResults:
        message = f"Could not find anything like \"{event.item_name}\"."
    except crud.MoreThanOne as e:
        message = (
            f"Multiple things match \"{event.item_name}\". Use the delete "
            f"command again, but pick one of the following: "
            f"{', '.join(e.results)}"
        )
    output_event = DeleteItemOutputEvent(markup=message)
    Topic.push(output_event)

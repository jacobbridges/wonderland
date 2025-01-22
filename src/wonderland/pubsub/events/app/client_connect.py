from src.wonderland.pubsub.events.base import BaseInputEvent, BaseOutputEvent
from src.wonderland.pubsub.topic import Topic


class ClientConnectInputEvent(BaseInputEvent):
    ...


class ClientConnectOutputEvent(BaseOutputEvent):
    ...


@Topic.register(ClientConnectInputEvent)
def handle_client_connect_input_event(event: ClientConnectInputEvent, **kwargs):
    """
    Ideas for this event handler:

    -   Spawn thread for this client's events?
    -   Create a session for this client's thread?
    """
    output_event = ClientConnectOutputEvent(
        markup="What is your username?",
    )
    Topic.push(output_event)

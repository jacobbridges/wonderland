from src.wonderland.pubsub.events.base import (
    BaseInputEvent,
    BaseOutputEvent,
    BaseEvent,
)
from src.wonderland.pubsub.topic import Topic


class ClientDisconnectInputEvent(BaseInputEvent):
    ...


class ClientDisconnectOutputEvent(BaseOutputEvent):
    ...


class ClientDisconnectSystemEvent(BaseEvent):
    ...


@Topic.register(ClientDisconnectInputEvent)
def handle_client_disconnect_input_event(event: ClientDisconnectInputEvent, **kwargs):
    """
    Ideas for this event handler:

    -   Close any database connections in the session?
    -   Close any open threads related to this session?
    """
    output_event = ClientDisconnectOutputEvent(
        markup="Bye",
    )
    system_event = ClientDisconnectSystemEvent()
    Topic.push(output_event)
    Topic.push(system_event)


@Topic.register(ClientDisconnectSystemEvent)
def handle_client_disconnect_system_event(event: ClientDisconnectSystemEvent, **kwargs):
    Topic.close()

from src.wonderland.pubsub.events.base import BaseInputEvent, BaseOutputEvent
from src.wonderland.pubsub.topic import Topic


class HelpInputEvent(BaseInputEvent):
    ...


class HelpOutputEvent(BaseOutputEvent):
    ...


@Topic.register(HelpInputEvent)
def handle_help_input_event(event: HelpInputEvent, **kwargs):
    """
    TODO: Build this help document from the list of registered commands, similar to how argparse lib works.
    """
    help_doc = """
    The following commands are available:
    ├─ look ─── Describe your environment.
    ├─ create ─ Create something.
    │           Must include the name of the something. Square 
    │           brackets are not required.
    │           Example: create red apple
    ├─ go ───── Move between spaces.
    │           Must include the space where you'd like to go.
    │           Example: go house
    └─ help ─── Shows this help message.
    """
    help_doc = "\n".join(l.strip() for l in help_doc.splitlines())
    output_event = HelpOutputEvent(
        markup=help_doc
    )
    Topic.push(output_event)

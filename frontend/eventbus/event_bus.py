from typing import Callable

from .event import Event
from .event_enum import EventEnum


class EventBus:
    def __init__(self) -> None:
        self.handlers: dict[str, list] = dict()

    def subscribe(
        self, event_name: EventEnum, handler: Callable[[Event], None]
    ) -> None:
        if event_name not in self.handlers:
            self.handlers[event_name] = []
        self.handlers[event_name].append(handler)

    def unsubscribe(
        self, event_name: EventEnum, handler: Callable[[Event], None]
    ) -> None:
        if event_name in self.handlers and handler in self.handlers[event_name]:
            self.handlers[event_name].remove(handler)

    def publish(self, event: Event) -> None:
        if event.event_id.value not in self.handlers:
            return

        for handler in self.handlers[event.event_id.value]:
            handler(event)


bus = EventBus()

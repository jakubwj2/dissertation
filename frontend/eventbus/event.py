from dataclasses import dataclass
from typing import Any

from .event_enum import EventEnum


@dataclass(frozen=True)
class Event:
    event_id: EventEnum
    payload: dict[str, Any]

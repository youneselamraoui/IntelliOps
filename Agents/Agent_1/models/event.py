
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Event:
    id: str
    timestamp: datetime
    source: str
    component: str
    environment: str
    event_type: str
    severity: str
    message: str
    status: str

    details: dict[str, Any] = field(default_factory=dict)

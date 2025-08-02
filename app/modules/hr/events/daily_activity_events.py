from uuid import UUID
from datetime import datetime
from typing import Any, Dict

class DailyActivityEvent:
    def __init__(self, activity_id: UUID, event_type: str, payload: Dict[str, Any]):
        self.activity_id = activity_id
        self.event_type = event_type
        self.payload = payload
        self.timestamp = datetime.utcnow()

class DailyActivityCreatedEvent(DailyActivityEvent):
    def __init__(self, activity_id: UUID, payload: Dict[str, Any]):
        super().__init__(activity_id, "created", payload)

class DailyActivityUpdatedEvent(DailyActivityEvent):
    def __init__(self, activity_id: UUID, payload: Dict[str, Any]):
        super().__init__(activity_id, "updated", payload)

class DailyActivityDeletedEvent(DailyActivityEvent):
    def __init__(self, activity_id: UUID, payload: Dict[str, Any]):
        super().__init__(activity_id, "deleted", payload)

class DailyActivityEventDispatcher:
    def dispatch(self, event: DailyActivityEvent):
        # Here you can integrate with notification, logging, or analytics systems
        print(f"[EVENT] {event.event_type} for activity {event.activity_id} at {event.timestamp}")
        # Add more integrations as needed

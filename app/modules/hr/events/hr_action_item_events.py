from uuid import UUID
from datetime import datetime
from typing import Any, Dict

class HRActionItemEvent:
    def __init__(self, item_id: UUID, data: Dict[str, Any]):
        self.item_id = item_id
        self.data = data
        self.timestamp = datetime.utcnow()

class HRActionItemCreatedEvent(HRActionItemEvent):
    pass

class HRActionItemUpdatedEvent(HRActionItemEvent):
    pass

class HRActionItemDeletedEvent(HRActionItemEvent):
    pass

class HRActionItemEventDispatcher:
    def dispatch(self, event: HRActionItemEvent):
        # Implement event bus or logging here
        pass

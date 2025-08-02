# app/core/event_bus.py
from typing import Dict, List, Callable, Any
import asyncio
import logging
from dataclasses import dataclass

@dataclass
class Event:
    event_type: str
    data: Dict[str, Any]
    source_module: str
    timestamp: float

class EventBus:
    """Simple event bus for inter-module communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._logger = logging.getLogger("EventBus")
    
    async def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        self._logger.info(f"Handler subscribed to event: {event_type}")
    
    async def publish(self, event_type: str, data: Dict[str, Any], source_module: str = "unknown"):
        """Publish an event to all subscribers"""
        import time
        
        event = Event(
            event_type=event_type,
            data=data,
            source_module=source_module,
            timestamp=time.time()
        )
        
        if event_type in self._subscribers:
            self._logger.info(f"Publishing event {event_type} to {len(self._subscribers[event_type])} subscribers")
            
            # Call all handlers asynchronously
            tasks = []
            for handler in self._subscribers[event_type]:
                try:
                    tasks.append(asyncio.create_task(handler(event)))
                except Exception as e:
                    self._logger.error(f"Error creating task for event handler: {e}")
            
            # Wait for all handlers to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            self._logger.debug(f"No subscribers for event: {event_type}")
    
    def get_subscribers_count(self, event_type: str) -> int:
        """Get number of subscribers for an event type"""
        return len(self._subscribers.get(event_type, []))
    
    def list_event_types(self) -> List[str]:
        """List all subscribed event types"""
        return list(self._subscribers.keys())

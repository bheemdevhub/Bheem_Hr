# app/core/base_module.py
from abc import ABC, abstractmethod
from typing import List, Optional
from fastapi import APIRouter
import logging

class BaseERPModule(ABC):
    """Base class for all ERP modules"""
    
    def __init__(self):
        self._router = APIRouter()
        self._event_bus = None
        self._logger = logging.getLogger(self.name)
        self._setup_routes()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Module name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Module version"""
        pass
    
    @property
    @abstractmethod
    def permissions(self) -> List[str]:
        """List of permissions this module provides"""
        pass
    
    @property
    def router(self) -> APIRouter:
        """FastAPI router for this module"""
        return self._router
    
    def set_event_bus(self, event_bus):
        """Set the event bus for inter-module communication"""
        self._event_bus = event_bus
    
    def _setup_routes(self) -> None:
        """Setup module-specific routes. Override in subclasses."""
        # Add health check endpoint
        @self._router.get("/health")
        async def health_check():
            return {
                "module": self.name,
                "version": self.version,
                "status": "healthy"
            }
    
    async def _subscribe_to_events(self) -> None:
        """Subscribe to events from other modules. Override in subclasses."""
        pass
    
    async def initialize(self) -> None:
        """Initialize the module (called after all modules are loaded)"""
        await self._subscribe_to_events()
        self._logger.info(f"Module {self.name} v{self.version} initialized")
    
    async def shutdown(self) -> None:
        """Cleanup when shutting down"""
        self._logger.info(f"Module {self.name} shutting down")

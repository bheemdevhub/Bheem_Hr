# app/core/erp_system.py
from fastapi import FastAPI
from typing import Dict, List
import logging
from .base_module import BaseERPModule
from .event_bus import EventBus

class ERPSystem:
    """Main ERP system that manages all modules"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.modules: Dict[str, BaseERPModule] = {}
        self.event_bus = EventBus()
        self._logger = logging.getLogger("ERPSystem")
    
    def add_module(self, module: BaseERPModule) -> None:
        """Add a module to the ERP system"""
        if module.name in self.modules:
            raise ValueError(f"Module {module.name} already exists")
        # Set event bus for the module
        module.set_event_bus(self.event_bus)
        # Ensure module routes are set up before including
        if hasattr(module, '_setup_routes'):
            module._setup_routes()
        # Include module router with prefix
        self.app.include_router(
            module.router,
            prefix=f"/api/{module.name}",
            tags=[module.name.title()]
        )
        self.modules[module.name] = module
        self._logger.info(f"Module {module.name} added to ERP system")
    
    async def initialize_all_modules(self) -> None:
        """Initialize all modules (call after all modules are added)"""
        self._logger.info("Initializing all modules...")
        
        for module in self.modules.values():
            try:
                await module.initialize()
            except Exception as e:
                self._logger.error(f"Failed to initialize module {module.name}: {e}")
        
        self._logger.info(f"ERP system initialized with {len(self.modules)} modules")
    
    async def shutdown_all_modules(self) -> None:
        """Shutdown all modules"""
        self._logger.info("Shutting down all modules...")
        
        for module in self.modules.values():
            try:
                await module.shutdown()
            except Exception as e:
                self._logger.error(f"Failed to shutdown module {module.name}: {e}")
        
        self._logger.info("All modules shut down")
    
    def get_module(self, name: str) -> BaseERPModule:
        """Get a module by name"""
        if name not in self.modules:
            raise ValueError(f"Module {name} not found")
        return self.modules[name]
    
    def list_modules(self) -> List[Dict[str, str]]:
        """List all modules with their info"""
        return [
            {
                "name": module.name,
                "version": module.version,
                "permissions": len(module.permissions)
            }
            for module in self.modules.values()
        ]
    
    def get_all_permissions(self) -> List[str]:
        """Get all permissions from all modules"""
        permissions = []
        for module in self.modules.values():
            permissions.extend(module.permissions)
        return permissions

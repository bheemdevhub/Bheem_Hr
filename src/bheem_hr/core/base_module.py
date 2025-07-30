# src/bheem_hr/core/base_module.py

from abc import ABC, abstractmethod
from typing import List
from fastapi import APIRouter

class BaseERPModule(ABC):
    def __init__(self):
        self._router = APIRouter()

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def permissions(self) -> List[str]:
        pass

    @property
    def router(self) -> APIRouter:
        return self._router

    def _setup_routes(self):
        @self._router.get("/health")
        async def health():
            return {
                "module": self.name,
                "version": self.version,
                "status": "healthy"
            }


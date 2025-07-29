from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime

class HRActionItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: date
    status: Optional[str] = "pending"
    assigned_to: Optional[UUID] = None

class HRActionItemCreate(HRActionItemBase):
    pass

class HRActionItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None

class HRActionItemResponse(HRActionItemBase):
    id: UUID
    created_by: Optional[UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

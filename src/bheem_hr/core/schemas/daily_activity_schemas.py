from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date, time, datetime

class DailyActivityBase(BaseModel):
    activity_date: date = Field(..., description="Date of the activity")
    activity_type: str = Field(..., max_length=100, description="Type of activity (attendance, meeting, leave, etc.)")
    description: Optional[str] = Field(None, description="Description of the activity")
    start_time: Optional[time] = Field(None, description="Start time of the activity")
    end_time: Optional[time] = Field(None, description="End time of the activity")
    meta: Optional[str] = Field(None, description="Extra info (JSON/text)")

class DailyActivityCreate(DailyActivityBase):
    employee_id: UUID

class DailyActivityUpdate(BaseModel):
    activity_type: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    meta: Optional[str] = None

class DailyActivityResponse(DailyActivityBase):
    id: UUID
    employee_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class DailyActivityPaginatedResponse(BaseModel):
    items: List[DailyActivityResponse]
    total: int
    page: int
    size: int
    pages: int


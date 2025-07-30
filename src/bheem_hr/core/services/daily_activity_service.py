from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional, Tuple
from datetime import date
from bheem_core.modules.hr.core.models.daily_activity_models import DailyActivity
from bheem_core.modules.hr.core.schemas.daily_activity_schemas import (
    DailyActivityCreate, DailyActivityUpdate
)

class DailyActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_activity(self, activity_data: DailyActivityCreate) -> DailyActivity:
        activity = DailyActivity(**activity_data.dict())
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def get_activity(self, activity_id: UUID) -> Optional[DailyActivity]:
        result = await self.db.execute(select(DailyActivity).where(DailyActivity.id == activity_id))
        return result.scalar_one_or_none()

    async def list_activities(self, employee_id: Optional[UUID] = None, activity_date: Optional[date] = None, page: int = 1, size: int = 20) -> Tuple[List[DailyActivity], int]:
        query = select(DailyActivity)
        if employee_id:
            query = query.where(DailyActivity.employee_id == employee_id)
        if activity_date:
            query = query.where(DailyActivity.activity_date == activity_date)
        total = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total_count = total.scalar()
        query = query.order_by(DailyActivity.activity_date.desc()).offset((page-1)*size).limit(size)
        result = await self.db.execute(query)
        return result.scalars().all(), total_count

    async def update_activity(self, activity_id: UUID, update_data: DailyActivityUpdate) -> Optional[DailyActivity]:
        activity = await self.get_activity(activity_id)
        if not activity:
            return None
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(activity, field, value)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def delete_activity(self, activity_id: UUID) -> bool:
        activity = await self.get_activity(activity_id)
        if not activity:
            return False
        await self.db.delete(activity)
        await self.db.commit()
        return True


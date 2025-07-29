from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from app.modules.hr.core.models.hr_models import HRActionItem
from app.modules.hr.core.schemas.hr_action_item_schemas import HRActionItemCreate, HRActionItemUpdate

class HRActionItemService:
    def __init__(self, db: AsyncSession, user_id: Optional[UUID] = None):
        self.db = db
        self.user_id = user_id

    async def create_action_item(self, data: HRActionItemCreate) -> HRActionItem:
        item = HRActionItem(**data.dict(), created_by=self.user_id)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_action_item(self, item_id: UUID) -> Optional[HRActionItem]:
        result = await self.db.execute(select(HRActionItem).where(HRActionItem.id == item_id))
        return result.scalar_one_or_none()

    async def list_action_items(self, skip: int = 0, limit: int = 20) -> List[HRActionItem]:
        result = await self.db.execute(select(HRActionItem).offset(skip).limit(limit))
        return result.scalars().all()

    async def update_action_item(self, item_id: UUID, data: HRActionItemUpdate) -> Optional[HRActionItem]:
        item = await self.get_action_item(item_id)
        if not item:
            return None
        for field, value in data.dict(exclude_unset=True).items():
            setattr(item, field, value)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_action_item(self, item_id: UUID) -> bool:
        item = await self.get_action_item(item_id)
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        return True

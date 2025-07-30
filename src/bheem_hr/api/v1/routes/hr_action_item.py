from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from bheem_core.core.database import get_db
from bheem_core.modules.auth.core.services.permissions_service import require_roles, require_api_permission, get_current_user_id
from bheem_core.shared.models import UserRole
from bheem_core.modules.hr.core.services.hr_action_item_service import HRActionItemService
from bheem_core.modules.hr.core.schemas.hr_action_item_schemas import HRActionItemCreate, HRActionItemUpdate, HRActionItemResponse
from bheem_core.modules.hr.events.hr_action_item_events import (
    HRActionItemCreatedEvent, HRActionItemUpdatedEvent, HRActionItemDeletedEvent, HRActionItemEventDispatcher
)

router = APIRouter(prefix="/hr/action-items", tags=["HR Action Items"])
dispatcher = HRActionItemEventDispatcher()

@router.post("/", response_model=HRActionItemResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(lambda: require_api_permission("hr.action_items.create")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def create_action_item(
    data: HRActionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    service = HRActionItemService(db, user_id=current_user_id)
    item = await service.create_action_item(data)
    dispatcher.dispatch(HRActionItemCreatedEvent(item.id, data.dict()))
    return HRActionItemResponse.from_orm(item)

@router.get("/", response_model=List[HRActionItemResponse], dependencies=[Depends(lambda: require_api_permission("hr.action_items.read")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def list_action_items(db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 20):
    service = HRActionItemService(db)
    items = await service.list_action_items(skip=skip, limit=limit)
    return [HRActionItemResponse.from_orm(i) for i in items]

@router.get("/{item_id}", response_model=HRActionItemResponse, dependencies=[Depends(lambda: require_api_permission("hr.action_items.read")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def get_action_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    service = HRActionItemService(db)
    item = await service.get_action_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return HRActionItemResponse.from_orm(item)

@router.put("/{item_id}", response_model=HRActionItemResponse, dependencies=[Depends(lambda: require_api_permission("hr.action_items.update")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def update_action_item(item_id: UUID, data: HRActionItemUpdate, db: AsyncSession = Depends(get_db)):
    service = HRActionItemService(db)
    item = await service.update_action_item(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    dispatcher.dispatch(HRActionItemUpdatedEvent(item.id, data.dict()))
    return HRActionItemResponse.from_orm(item)

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(lambda: require_api_permission("hr.action_items.delete")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def delete_action_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    service = HRActionItemService(db)
    success = await service.delete_action_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Action item not found")
    dispatcher.dispatch(HRActionItemDeletedEvent(item_id, {}))
    return None



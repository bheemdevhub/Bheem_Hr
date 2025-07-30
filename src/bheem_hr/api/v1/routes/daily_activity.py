from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from bheem_core.core.database import get_db
from bheem_core.modules.auth.core.services.permissions_service import (
    require_roles, require_api_permission, get_current_user_id, get_current_company_id
)
from bheem_core.shared.models import UserRole
from bheem_core.modules.hr.core.schemas.daily_activity_schemas import (
    DailyActivityCreate, DailyActivityUpdate, DailyActivityResponse, DailyActivityPaginatedResponse
)
from bheem_core.modules.hr.core.services.daily_activity_service import DailyActivityService
from bheem_core.modules.hr.events.daily_activity_events import (
    DailyActivityCreatedEvent, DailyActivityUpdatedEvent, DailyActivityDeletedEvent, DailyActivityEventDispatcher
)

router = APIRouter(prefix="/daily-activities", tags=["HR Daily Activities"])
dispatcher = DailyActivityEventDispatcher()

@router.post("/", response_model=DailyActivityResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(lambda: require_api_permission("hr.daily_activities.create")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
    ])
async def create_daily_activity(
    activity_data: DailyActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    service = DailyActivityService(db)
    activity = await service.create_activity(activity_data)
    dispatcher.dispatch(DailyActivityCreatedEvent(activity.id, activity_data.dict()))
    return DailyActivityResponse.from_orm(activity)

@router.get("/", response_model=DailyActivityPaginatedResponse,
    dependencies=[
        Depends(lambda: require_api_permission("hr.daily_activities.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
    ])
async def list_daily_activities(
    employee_id: Optional[UUID] = Query(None),
    activity_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = DailyActivityService(db)
    activities, total = await service.list_activities(employee_id, activity_date, page, size)
    pages = (total + size - 1) // size
    return DailyActivityPaginatedResponse(
        items=[DailyActivityResponse.from_orm(a) for a in activities],
        total=total, page=page, size=size, pages=pages
    )

@router.get("/{activity_id}", response_model=DailyActivityResponse,
    dependencies=[
        Depends(lambda: require_api_permission("hr.daily_activities.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
    ])
async def get_daily_activity(
    activity_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db)
):
    service = DailyActivityService(db)
    activity = await service.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return DailyActivityResponse.from_orm(activity)

@router.put("/{activity_id}", response_model=DailyActivityResponse,
    dependencies=[
        Depends(lambda: require_api_permission("hr.daily_activities.update")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
    ])
async def update_daily_activity(
    activity_id: UUID = Path(...),
    update_data: DailyActivityUpdate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    service = DailyActivityService(db)
    activity = await service.update_activity(activity_id, update_data)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    dispatcher.dispatch(DailyActivityUpdatedEvent(activity_id, update_data.dict(exclude_unset=True)))
    return DailyActivityResponse.from_orm(activity)

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(lambda: require_api_permission("hr.daily_activities.delete")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
    ])
async def delete_daily_activity(
    activity_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db)
):
    service = DailyActivityService(db)
    success = await service.delete_activity(activity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Activity not found")
    dispatcher.dispatch(DailyActivityDeletedEvent(activity_id, {}))
    return None


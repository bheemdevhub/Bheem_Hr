"""HR Onboarding Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from functools import partial
from app.modules.auth.core.services.permissions_service import get_current_user, require_roles, require_api_permission
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
router = APIRouter()

@router.get("/", summary="Get all onboarding checklists", tags=["Onboarding"])
async def list_onboarding_checklists(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    completion_status: Optional[str] = Query(None, description="Filter by completion status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "onboarding:view")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        result = await hr_service.list_onboarding_checklists(
            candidate_id=candidate_id,
            is_active=is_active,
            completion_status=completion_status
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving onboarding checklists: {str(e)}"
        )

@router.get("/{checklist_id}", summary="Get onboarding checklist by ID", tags=["Onboarding"])
async def get_onboarding_checklist(
    checklist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "onboarding:view")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        return await hr_service.get_onboarding_checklist(checklist_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving onboarding checklist: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create onboarding checklist", tags=["Onboarding"])
async def create_onboarding_checklist(
    checklist_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "onboarding:create")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        result = await hr_service.create_onboarding_checklist(checklist_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating onboarding checklist: {str(e)}"
        )

@router.put("/{checklist_id}", summary="Update onboarding checklist", tags=["Onboarding"])
async def update_onboarding_checklist(
    checklist_id: str,
    checklist_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "onboarding:update")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        return await hr_service.update_onboarding_checklist(checklist_id, checklist_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating onboarding checklist: {str(e)}"
        )
    
@router.delete("/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete onboarding checklist", tags=["Onboarding"])
async def delete_onboarding_checklist(
    checklist_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "onboarding:delete")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        await hr_service.delete_onboarding_checklist(checklist_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting onboarding checklist: {str(e)}"
        )

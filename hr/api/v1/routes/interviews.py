# app/modules/hr/api/v1/routes/interviews.py
"""HR Interviews Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.modules.auth.core.services.permissions_service import (
    get_current_user, require_roles, require_superadmin, require_api_permission
)
from functools import partial
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db

from app.modules.hr.core.services.hr_service import HRService
from app.modules.auth.core.services.permissions_service import get_current_company_id
from app.modules.hr.core.schemas.hr_schemas import InterviewCreate, InterviewUpdate

router = APIRouter()

@router.get("/", summary="Get all interviews", tags=["Interviews"])
async def list_interviews(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(partial(require_api_permission, "interview:view")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        result = await hr_service.list_interviews(candidate_id=candidate_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interviews: {str(e)}"
        )

@router.get("/{interview_id}", summary="Get interview by ID", tags=["Interviews"])
async def get_interview(
    interview_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(partial(require_api_permission, "interview:view")),
):
    hr_service = HRService(db, event_bus=None)
    
    try:
        return await hr_service.get_interview(interview_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving interview: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Schedule interview", tags=["Interviews"])
async def create_interview(
    interview_data: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
    _=Depends(partial(require_api_permission, "interview:schedule")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        result = await hr_service.create_interview(interview_data, company_id=company_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling interview: {str(e)}"
        )

@router.put("/{interview_id}", summary="Update interview", tags=["Interviews"])
async def update_interview(
    interview_id: str,
    interview_data: InterviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(partial(require_api_permission, "interview:update")),
):
    """
    Update an existing interview.
    
    **Common updates:**
    - Reschedule interview date/time
    - Change interviewer
    - Update status (COMPLETED, CANCELLED, etc.)
    - Add feedback and rating
    
    **Request Body Example:**
    ```json
    {
        "interview_date_time": "2025-07-16T14:00:00Z",
        "status": "COMPLETED",
        "feedback_comments": "Strong technical skills, good communication",
        "rating": "EXCELLENT",
        "next_step": "Proceed to final round"
    }
    ```
    
    **Returns:** Updated interview object
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        return await hr_service.update_interview(interview_id, interview_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating interview: {str(e)}"
        )

@router.delete("/{interview_id}", summary="Delete interview by ID", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(partial(require_api_permission, "interview:delete")),
):
    """
    Delete an interview using its ID.

    **Returns:** 204 No Content on successful deletion
    """
    hr_service = HRService(db, event_bus=None)
    try:
        await hr_service.delete_interview(interview_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting interview: {str(e)}")

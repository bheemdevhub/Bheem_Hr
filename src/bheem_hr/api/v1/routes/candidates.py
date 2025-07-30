# app/modules/hr/api/v1/routes/candidates.py
"""HR Candidate Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from bheem_core.modules.auth.core.services.permissions_service import (
    get_current_user, require_roles, require_superadmin, require_api_permission
)
from fastapi.exceptions import RequestValidationError
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
import json

from bheem_core.core.database import get_db
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.modules.hr.core.schemas.hr_schemas import (
    CandidateCreate, 
    CandidateUpdate, 
    CandidateResponse,
    InterviewCreate,
    InterviewResponse
)

router = APIRouter()

@router.post("/", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED, summary="Create new candidate", tags=["Candidate Management"])
async def create_candidate(
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(lambda: require_api_permission("candidate:create")),
):
    """
    Create a new candidate.
    
    **Request Body:** CandidateCreate schema with person details, position applied for, and resume
    
    **Returns:** Created candidate object with generated ID
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        candidate = await hr_service.create_candidate(candidate_data)
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating candidate: {str(e)}"
        )

@router.get("/", response_model=List[CandidateResponse], summary="Get all candidates", tags=["Candidate Management"])
async def get_candidates(
    candidate_status: Optional[str] = Query(None, description="Filter by candidate status"),
    recruiter_assigned: Optional[str] = Query(None, description="Filter by assigned recruiter"),
    applied_position_id: Optional[str] = Query(None, description="Filter by applied position"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(lambda: require_api_permission("candidate:view")),
):
    hr_service = HRService(db, event_bus=None)
    
    try:
        candidates = await hr_service.list_candidates()
        
        # Apply filters if provided
        if candidate_status:
            candidates = [c for c in candidates if c.status == candidate_status]
        if recruiter_assigned:
            candidates = [c for c in candidates if c.recruiter_assigned == recruiter_assigned]
        if applied_position_id:
            candidates = [c for c in candidates if c.applied_position_id == applied_position_id]
        
        return candidates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidates: {str(e)}"
        )

@router.get("/{candidate_id}", response_model=CandidateResponse, summary="Get candidate by ID", tags=["Candidate Management"])
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(lambda: require_api_permission("candidate:view")),
):
    """
    Get candidate by ID
    
    **Parameters:**
    - **candidate_id**: The unique identifier of the candidate
    
    **Returns:** Candidate object with person details and resume
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        candidate = await hr_service.get_candidate(candidate_id)
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidate: {str(e)}"
        )

@router.put("/{candidate_id}", response_model=CandidateResponse, summary="Update candidate", tags=["Candidate Management"])
async def update_candidate(
    candidate_id: str,
    candidate_data: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(lambda: require_api_permission("candidate:update")),
):
    """
    Update candidate information.
    
    **Parameters:**
    - **candidate_id**: The unique identifier of the candidate
    
    **Request Body:** CandidateUpdate schema with fields to update
    
    **Returns:** Updated candidate object
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        # Log the incoming data for debugging
        print(f"DEBUG: Updating candidate {candidate_id}")
        print(f"DEBUG: Received data: {candidate_data.model_dump()}")
        
        candidate = await hr_service.update_candidate(candidate_id, candidate_data)
        return candidate
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Exception in update_candidate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating candidate: {str(e)}"
        )

@router.put("/{candidate_id}/debug", summary="Debug candidate update", tags=["Candidate Management"])
async def debug_candidate_update(candidate_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Debug endpoint to check candidate update validation.
    This endpoint will help diagnose validation issues.
    """
    try:
        # Get the raw JSON body
        body = await request.body()
        print(f"DEBUG: Raw request body: {body.decode()}")
        
        # Try to parse JSON
        try:
            json_data = json.loads(body.decode())
            print(f"DEBUG: Parsed JSON: {json_data}")
        except json.JSONDecodeError as je:
            return {
                "error": "Invalid JSON", 
                "detail": str(je),
                "raw_body": body.decode()
            }
        
        # Try to validate with CandidateUpdate schema
        try:
            candidate_update = CandidateUpdate(**json_data)
            print(f"DEBUG: Validated candidate data: {candidate_update.model_dump()}")
            return {
                "success": True,
                "message": "Validation successful",
                "validated_data": candidate_update.model_dump()
            }
        except ValidationError as ve:
            print(f"DEBUG: Validation error: {ve}")
            return {
                "error": "Validation failed",
                "detail": ve.errors(),
                "raw_data": json_data
            }
            
    except Exception as e:
        print(f"DEBUG: Exception in debug endpoint: {str(e)}")
        return {
            "error": "Debug endpoint error",
            "detail": str(e)
        }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating candidate: {str(e)}"
        )

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete candidate", tags=["Candidate Management"])
async def delete_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(lambda: require_api_permission("candidate:delete")),
):
    """
    Delete candidate
    
    **Parameters:**
    - **candidate_id**: The unique identifier of the candidate
    
    **Returns:** No content (204 status code) on successful deletion
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        await hr_service.delete_candidate(candidate_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting candidate: {str(e)}"
        )

@router.post("/{candidate_id}/interview", response_model=InterviewResponse, summary="Schedule interview", tags=["Candidate Management"])
async def schedule_interview(
    candidate_id: str,
    interview_data: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(lambda: require_api_permission("interview:schedule")),
):
    """
    Schedule an interview for a candidate.
    
    **Request Body Example:**
    ```json
    {
        "candidate_id": "cand_12345678-1234-1234-1234-123456789012",
        "interview_date_time": "2025-07-15T14:00:00Z",
        "interviewer_id": "emp_987654321",
        "round_type": "TECHNICAL",
        "status": "SCHEDULED"
    }
    ```
    
    **Round Types:**
    - `TECHNICAL` - Technical assessment interview
    - `HR` - HR interview
    - `MANAGERIAL` - Managerial round
    - `FINAL` - Final round interview
    
    **Status Values:**
    - `SCHEDULED` - Interview is scheduled
    - `COMPLETED` - Interview completed
    - `CANCELLED` - Interview cancelled
    - `NO_SHOW` - Candidate did not show up
    - `RESCHEDULED` - Interview rescheduled
    
    **Returns:** Created interview object with generated ID
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        # Ensure the candidate_id matches the route parameter
        interview_data.candidate_id = candidate_id
        
        # Schedule the interview
        interview = await hr_service.schedule_candidate_interview(candidate_id, interview_data)
        return interview
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling interview: {str(e)}"
        )

@router.post("/{candidate_id}/hire", summary="Hire candidate", tags=["Candidate Management"])
async def hire_candidate(candidate_id: str, db: AsyncSession = Depends(get_db)):
    """
    Hire candidate
    
    **Parameters:**
    - **candidate_id**: The unique identifier of the candidate
    
    **Note:** This endpoint is a placeholder for candidate hiring functionality.
    Implementation should include employee record creation, onboarding setup, etc.
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        # Verify candidate exists
        candidate = await hr_service.get_candidate(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # TODO: Implement actual hiring logic
        # This would include:
        # - Creating employee record from candidate data
        # - Setting up onboarding checklist
        # - Updating candidate status to "HIRED"
        # - Creating user account
        # - Sending welcome email
        
        return {
            "message": f"Hiring process for candidate {candidate_id} - Implementation needed",
            "candidate_id": candidate_id,
            "status": "pending_implementation"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error hiring candidate: {str(e)}"
        )


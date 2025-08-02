# app/modules/hr/api/v1/routes/job_requisitions.py
"""HR Job Requisitions Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.modules.hr.core.schemas.hr_schemas import (
    JobRequisitionCreate, JobRequisitionUpdate, JobRequisitionResponse
)
from app.modules.auth.core.services.permissions_service import require_api_permission, get_current_user, require_roles

router = APIRouter()

@router.get("/", summary="Get all job requisitions", tags=["Job Requisitions"])
async def list_job_requisitions(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    department_id: Optional[str] = Query(None, description="Filter by department"),
    job_type_id: Optional[str] = Query(None, description="Filter by job type"),
    hiring_manager_id: Optional[str] = Query(None, description="Filter by hiring manager"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    role_check: dict = Depends(require_roles("HR_MANAGER", "SUPERADMIN", "HR_EXECUTIVE")),
    permission_check: None = Depends(lambda: require_api_permission("job_requisition:view"))
):
    """
    Get all job requisitions with optional filtering.
    
    **Parameters:**
    - **is_active**: Filter by active status (true for active only, false for inactive only)
    - **department_id**: Filter by department ID
    - **job_type_id**: Filter by job type ID
    - **hiring_manager_id**: Filter by hiring manager ID
    
    **Examples:**
    - Get all active requisitions: `?is_active=true`
    - Get by department: `?department_id=dept-uuid`
    - Get by hiring manager: `?hiring_manager_id=emp-uuid`
    
    **Returns:** List of job requisition objects
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        # This would need to be implemented in hr_service
        result = await hr_service.list_job_requisitions(
            is_active=is_active,
            department_id=department_id,
            job_type_id=job_type_id,
            hiring_manager_id=hiring_manager_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job requisitions: {str(e)}"
        )

@router.get("/{requisition_id}", summary="Get job requisition by ID", tags=["Job Requisitions"])
async def get_job_requisition(
    requisition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    role_check: dict = Depends(require_roles("HR_MANAGER", "SUPERADMIN", "HR_EXECUTIVE")),
    permission_check: None = Depends(lambda: require_api_permission("job_requisition:view"))
):
    hr_service = HRService(db, event_bus=None)
    
    try:
        return await hr_service.get_job_requisition(requisition_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job requisition: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create job requisition", tags=["Job Requisitions"])
async def create_job_requisition(
    requisition_data: JobRequisitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    role_check: dict = Depends(require_roles("HR_MANAGER", "SUPERADMIN")),
    permission_check: None = Depends(lambda: require_api_permission("job_requisition:create"))
):
    hr_service = HRService(db, event_bus=None)
    try:
        result = await hr_service.create_job_requisition(requisition_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating job requisition: {str(e)}"
        )

# @router.put("/{requisition_id}", summary="Update job requisition", tags=["Job Requisitions"])
# async def update_job_requisition(
#     requisition_id: str,
#     requisition_data: JobRequisitionUpdate,  # Use the correct schema for update
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Update an existing job requisition.
    
#     **Returns:** Updated job requisition object
#     """
#     hr_service = HRService(db, event_bus=None)
    
#     try:
#         return await hr_service.update_job_requisition(requisition_id, requisition_data)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error updating job requisition: {str(e)}"
#         )
@router.put("/{requisition_id}",summary="Update job requisition",tags=["Job Requisitions"],response_model=JobRequisitionResponse )
async def update_job_requisition(
    requisition_id: str,
    requisition_data: JobRequisitionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    role_check: dict = Depends(require_roles("HR_MANAGER", "SUPERADMIN")),
    permission_check: None = Depends(lambda: require_api_permission("job_requisition:update"))
):
    """
    Update an existing job requisition.
    
    **Returns:** Updated job requisition object
    """
    hr_service = HRService(db, event_bus=None)

    try:
        return await hr_service.update_job_requisition(requisition_id, requisition_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating job requisition: {str(e)}"
        )
@router.delete("/{requisition_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete job requisition", tags=["Job Requisitions"])
async def delete_job_requisition(
    requisition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    role_check: dict = Depends(require_roles("HR_MANAGER", "SUPERADMIN")),
    permission_check: None = Depends(lambda: require_api_permission("job_requisition:delete"))
):
    """
    Delete a job requisition (soft delete - sets is_active to False).
    

    
    **Parameters:**
    - **requisition_id**: The unique identifier of the job requisition
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        await hr_service.delete_job_requisition(requisition_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job requisition: {str(e)}"
        )

@router.get("/{requisition_id}/candidates", summary="Get candidates for job requisition", tags=["Job Requisitions"])
async def get_requisition_candidates(
    requisition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    role_check: dict = Depends(require_roles("HR_MANAGER", "SUPERADMIN", "HR_EXECUTIVE")),
    permission_check: None = Depends(lambda: require_api_permission("job_requisition:view"))
):
    """
    Get all candidates who applied for this job requisition.
    
    **Returns:** List of candidates with their application status
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        return await hr_service.get_requisition_candidates(requisition_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving candidates: {str(e)}"
        )

@router.post("/{requisition_id}/skills", summary="Add skills to job requisition", tags=["Job Requisitions"])
async def add_requisition_skills(
    requisition_id: str,
    skills_data: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    role_check: dict = Depends(require_roles("HR_MANAGER", "SUPERADMIN")),
    permission_check: None = Depends(lambda: require_api_permission("job_requisition:update"))
):
    """
    Add required skills to a job requisition.
    
    **Request Body:** List of skill IDs or skill names
    ```json
    ["python", "javascript", "react", "nodejs"]
    ```
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        return await hr_service.add_requisition_skills(requisition_id, skills_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding skills: {str(e)}"
        )

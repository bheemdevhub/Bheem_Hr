
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from bheem_core.core.database import get_db
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.modules.hr.core.schemas.hr_schemas import LeaveRequestCreate, LeaveRequestRead
from bheem_core.modules.auth.core.services.permissions_service import (
    require_roles, require_api_permission, get_current_user_id, get_current_company_id
)
from bheem_core.shared.models import UserRole
from uuid import UUID
from typing import List

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])

@router.post("/", response_model=LeaveRequestRead, status_code=status.HTTP_201_CREATED,
          dependencies=[
              Depends(lambda: require_api_permission("hr.leave_request.create")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
          ])
async def create_leave_request(
    data: LeaveRequestCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Create a new leave request with probation and payroll deduction logic"""
    service = HRService(db)
    return await service.create_leave_request(data)


@router.get("/{leave_id}", response_model=LeaveRequestRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.leave_request.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
          ])
async def get_leave_request(
    leave_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Get a specific leave request by ID"""
    service = HRService(db)
    return await service.get_leave_request(leave_id)



from fastapi import Query

@router.get("/", response_model=List[LeaveRequestRead],
          dependencies=[
              Depends(lambda: require_api_permission("hr.leave_request.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
          ])
async def list_leave_requests(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    status: str = Query(None, description="Filter by leave status: PENDING, APPROVED, REJECTED"),
    limit: int = Query(10, ge=1, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset")
):
    """Get leave requests with optional status filter and pagination"""
    service = HRService(db)
    return await service.list_leave_requests(company_id=company_id, status=status, limit=limit, offset=offset)



@router.put("/{leave_id}", response_model=LeaveRequestRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.leave_request.update")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def update_leave_request(
    leave_id: UUID, 
    data: LeaveRequestCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Update an existing leave request"""
    service = HRService(db)
    return await service.update_leave_request(leave_id, data)

@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.leave_request.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_leave_request(
    leave_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Delete a leave request"""
    service = HRService(db)
    await service.delete_leave_request(leave_id)
    return {"detail": "Leave request deleted successfully"}

@router.put("/{leave_id}/approve", response_model=LeaveRequestRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.leave_request.approve")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def approve_leave_request(
    leave_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Approve a leave request"""
    service = HRService(db)
    return await service.approve_leave_request(leave_id, current_user_id)

@router.put("/{leave_id}/reject", response_model=LeaveRequestRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.leave_request.reject")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def reject_leave_request(
    leave_id: UUID, 
    reason: str = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Reject a leave request"""
    service = HRService(db)
    return await service.reject_leave_request(leave_id, current_user_id, reason)


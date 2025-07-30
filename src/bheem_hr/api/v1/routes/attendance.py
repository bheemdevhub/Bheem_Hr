from bheem_core.shared.models import UserRole
from uuid import UUID
from typing import List
from datetime import date
# Import APIRouter to fix NameError
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from bheem_core.core.database import get_db   
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceCreate, AttendanceRead, AttendanceUpdate, AttendancePaginatedResponse
from bheem_core.modules.auth.core.services.permissions_service import (
    require_roles, require_api_permission, get_current_user_id, get_current_company_id
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# Get half days leave for employee between dates
from fastapi import Query
@router.get("/halfday-leave/{employee_id}", tags=["Attendance"], response_model=dict,
    dependencies=[
        Depends(lambda: require_api_permission("hr.attendance.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
    ]
)
async def get_half_days_leave(
    employee_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.get_half_days_leave(employee_id, start_date, end_date)


# Get half days leave for company between dates
@router.get("/halfday-leave/{company_id}", tags=["Attendance"], response_model=dict,
    dependencies=[
        Depends(lambda: require_api_permission("hr.attendance.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
    ]
)
async def get_company_half_days_leave(
    company_id: UUID,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    service = HRService(db)
    return await service.get_company_half_days_leave(company_id, start_date, end_date)



# Get attendance by employee_id
@router.get("/by-employee/{employee_id}", response_model=AttendancePaginatedResponse,
    dependencies=[
        Depends(lambda: require_api_permission("hr.attendance.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
    ],
    tags=["Attendance"]
)
async def get_attendance_by_employee_id(
    employee_id: UUID,
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """
    List attendance records for a given employee_id with pagination.
    """
    service = HRService(db)
    return await service.get_attendance_by_employee_id(
        employee_id=employee_id,
        limit=limit,
        offset=offset,
        company_id=company_id 
    )


# Get attendance by employee_id and date
@router.get("/{employee_id}/{date}", response_model=AttendanceRead,
    dependencies=[
        Depends(lambda: require_api_permission("hr.attendance.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
    ],
    tags=["Attendance"]
)
async def get_attendance_by_employee_and_date(
    employee_id: UUID,
    date: date,
    db: AsyncSession = Depends(get_db)
):
    service = HRService(db)
    return await service.get_attendance_by_employee_and_date(employee_id, date)

# Create attendance record
@router.post("/", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED,
          dependencies=[
              Depends(lambda: require_api_permission("hr.attendance.create")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def create_attendance(
    data: AttendanceCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.create_attendance(data)


@router.get("/{attendance_id}", response_model=AttendanceRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.attendance.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
          ])
async def get_attendance(
    attendance_id: UUID, 
    db: AsyncSession = Depends(get_db)
):
    service = HRService(db)
    return await service.get_attendance(attendance_id)



# -------# attendance list----------------------------------------------------------------------
@router.get("/", response_model=AttendancePaginatedResponse,
          dependencies=[
              Depends(lambda: require_api_permission("hr.attendance.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
          ])
async def list_attendance(
    employee_id: UUID = None,
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """List attendance records with optional filter and pagination."""
    service = HRService(db)
    result = await service.list_attendance(employee_id=employee_id, limit=limit, offset=offset)
    return result
# ---------------------------update the attendance by attendance_id------------------------------------------------------------------------

@router.put("/{attendance_id}", response_model=AttendanceRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.attendance.update")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def update_attendance(
    attendance_id: UUID, 
    data: AttendanceCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.update_attendance(attendance_id, data)

# -------------------------------------------------------------------------------------------------------


# -----------------------------update and delete the attendance by employee_id and date--------------------------------------------------------------------------

@router.put(
    "/{employee_id}/{date}",
    response_model=AttendanceRead,
    dependencies=[
        Depends(lambda: require_api_permission("hr.attendance.update")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
    ],
    tags=["Attendance"]
)
async def update_attendance_by_employee(
    employee_id: UUID,
    date: date,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = HRService(db)
    updated = await service.update_attendance_by_employee(employee_id, date, data)
    return updated


@router.delete(
    "/{employee_id}/{date}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(lambda: require_api_permission("hr.attendance.delete")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
    ],
    tags=["Attendance"]
)
async def delete_attendance_by_employee(
    employee_id: UUID,
    date: date,
    db: AsyncSession = Depends(get_db)
):
    service = HRService(db)
    await service.delete_attendance_by_employee(employee_id, date)
    return {"detail": "Deleted"}

# -------------------------------------------------------------------------------------------------------


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.attendance.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_attendance(
    attendance_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    await service.delete_attendance(attendance_id)
    return {"detail": "Deleted"}

@router.post("/clock-in", response_model=AttendanceRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.attendance.clock_in")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
          ])
async def clock_in(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Clock in an employee"""
    service = HRService(db)
    return await service.clock_in(employee_id)

@router.post("/clock-out", response_model=AttendanceRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.attendance.clock_out")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR, UserRole.EMPLOYEE]))
          ])
async def clock_out(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Clock out an employee"""
    service = HRService(db)
    return await service.clock_out(employee_id)


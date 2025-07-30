"""HR Employee Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status as http_status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from bheem_core.core.database import get_db
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.modules.hr.core.schemas.hr_schemas import (
    EmployeeSearchParams, 
    EmployeeSearchResult, 
    EmployeeResponse,
    EmployeeCreate,
    EmployeeUpdate,
    AddressResponse,
    AddressCreate
)
from bheem_core.shared.schemas import ContactCreate, ContactResponse
from bheem_core.shared.models import EmploymentTypeEnum, EmploymentStatusEnum

# --- Auth imports ---
from bheem_core.modules.auth.core.services.permissions_service import (
    get_current_user, require_roles, require_api_permission
)

router = APIRouter()


# -------------------------------
# Employee CRUD
# -------------------------------

@router.get(
    "/",
    response_model=EmployeeSearchResult,
    summary="Get all employees",
    dependencies=[
        Depends(require_roles("Admin", "HRManager", "SuperAdmin")),
        Depends(lambda: require_api_permission("employee:read"))
    ]
)
async def get_employees(
    department_id: Optional[str] = Query(None),
    search_term: Optional[str] = Query(None),
    employment_type: Optional[EmploymentTypeEnum] = Query(None),
    status: Optional[EmploymentStatusEnum] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all employees with optional filters"""
    hr_service = HRService(db, event_bus=None)
    params = EmployeeSearchParams(
        department_id=department_id,
        search_term=search_term,
        employment_type=employment_type,
        status=status,
        page=page,
        page_size=page_size
    )
    return await hr_service.search_employees(params)


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create new employee",
    dependencies=[
        Depends(require_roles("Admin", "HRManager", "SuperAdmin")),
        Depends(lambda: require_api_permission("employee:create"))
    ]
)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new employee"""
    hr_service = HRService(db, event_bus=None)

    # Ensure company_id is set from current_user if not present
    if not getattr(employee_data, "company_id", None):
        if isinstance(current_user, dict):
            employee_data.company_id = current_user.get("company_id")
        else:
            employee_data.company_id = getattr(current_user, "company_id", None)

    employee = await hr_service.create_employee(employee_data)

    if not employee:
        raise HTTPException(status_code=500, detail="Employee creation failed")

    return employee


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee by ID",
    dependencies=[
        Depends(require_roles("Admin", "HRManager", "SuperAdmin")),
        Depends(lambda: require_api_permission("employee:read"))
    ]
)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    hr_service = HRService(db, event_bus=None)
    employee = await hr_service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee",
    dependencies=[
        Depends(require_roles("Admin", "HRManager", "SuperAdmin")),
        Depends(lambda: require_api_permission("employee:update"))
    ]
)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    hr_service = HRService(db, event_bus=None)
    updated = await hr_service.update_employee(employee_id, employee_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated


@router.delete(
    "/{employee_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete employee",
    dependencies=[
        Depends(require_roles("Admin", "HRManager", "SuperAdmin")),
        Depends(lambda: require_api_permission("employee:delete"))
    ]
)
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    hr_service = HRService(db, event_bus=None)
    success = await hr_service.soft_delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return None


@router.post("/{employee_id}/activate", response_model=EmployeeResponse, summary="Activate employee")
async def activate_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db)
):
    from bheem_core.modules.hr.core.schemas.hr_schemas import EmployeeUpdate
    hr_service = HRService(db, event_bus=None)
    try:
        update_data = EmployeeUpdate(is_active=True, employment_status=EmploymentStatusEnum.ACTIVE)
        return await hr_service.update_employee(employee_id, update_data)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating employee: {str(e)}"
        )


@router.post("/{employee_id}/terminate", response_model=EmployeeResponse, summary="Terminate employee")
async def terminate_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db)
):
    from datetime import date
    from bheem_core.modules.hr.core.schemas.hr_schemas import EmployeeUpdate
    hr_service = HRService(db, event_bus=None)
    try:
        update_data = EmployeeUpdate(
            employment_status=EmploymentStatusEnum.TERMINATED,
            termination_date=date.today(),
            is_active=False
        )
        return await hr_service.update_employee(employee_id, update_data)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error terminating employee: {str(e)}"
        )


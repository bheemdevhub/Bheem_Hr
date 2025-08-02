# app/modules/hr/api/v1/routes/salary_component.py

from fastapi import APIRouter, Depends, status, HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.modules.hr.core.schemas.hr_schemas import SalaryComponentCreate, SalaryComponentRead
from app.modules.auth.core.services.permissions_service import (
    get_current_user_id,
    get_current_company_id,
    require_api_permission,
    require_roles,
)
from app.shared.models import UserRole

router = APIRouter(
    prefix="/salary-components",
    tags=["Salary Components"],
)

def get_hr_service(db: AsyncSession = Depends(get_db)) -> HRService:
    return HRService(db)

@router.post(
    "/",
    response_model=SalaryComponentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(lambda: require_api_permission("hr.salary_component.create")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR])),
    ],
)
async def create_salary_component(
    data: SalaryComponentCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    service: HRService = Depends(get_hr_service),
):
    return await service.create_salary_component(
        data=data,
        current_user_id=current_user_id,
        company_id=company_id,
    )


@router.get("/{component_id}", response_model=SalaryComponentRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.salary_component.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def get_salary_component(
    component_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.get_salary_component(component_id)

@router.get("/", response_model=List[SalaryComponentRead],
          dependencies=[
              Depends(lambda: require_api_permission("hr.salary_component.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def list_salary_components(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.list_salary_components()

@router.put(
    "/{component_id}",
    response_model=SalaryComponentRead,
    dependencies=[
        Depends(lambda: require_api_permission("hr.salary_component.update")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR])),
    ],
)
async def update_salary_component(
    component_id: UUID,
    data: SalaryComponentCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    service: HRService = Depends(get_hr_service),
):
    return await service.update_salary_component(
        component_id=component_id,
        data=data,
        current_user_id=current_user_id,
        company_id=company_id,
    )

@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.salary_component.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_salary_component(
    component_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    await service.delete_salary_component(component_id, current_user_id=current_user_id, company_id=company_id)
    return {"detail": "Deleted"}

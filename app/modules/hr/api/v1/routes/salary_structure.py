from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.modules.hr.core.schemas.hr_schemas import (
    SalaryStructureCreate,
    SalaryStructureRead,
)
from app.modules.auth.core.services.permissions_service import (
    get_current_user_id,
    get_current_company_id,
    require_api_permission,
    require_roles,
)
from app.shared.models import UserRole

router = APIRouter(
    prefix="/salary-structures",
    tags=["Salary Structures"],
)

# Reusable service dependency
def get_hr_service(db: AsyncSession = Depends(get_db)) -> HRService:
    return HRService(db)


@router.post(
    "/",
    response_model=SalaryStructureRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(lambda: require_api_permission("hr.salary_structure.create")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR])),
    ],
)
async def create_salary_structure(
    data: SalaryStructureCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    service: HRService = Depends(get_hr_service),
):
    return await service.create_salary_structure(
        data=data,
        current_user_id=current_user_id,
        company_id=company_id,
    )


@router.get(
    "/{structure_id}",
    response_model=SalaryStructureRead,
    dependencies=[
        Depends(lambda: require_api_permission("hr.salary_structure.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR])),
    ],
)
async def get_salary_structure(
    structure_id: UUID,
    service: HRService = Depends(get_hr_service),
):
    return await service.get_salary_structure(structure_id)


@router.get(
    "/",
    response_model=list[SalaryStructureRead],
    dependencies=[
        Depends(lambda: require_api_permission("hr.salary_structure.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR])),
    ],
)
async def list_salary_structures(
    service: HRService = Depends(get_hr_service),
):
    return await service.list_salary_structures()


@router.put(
    "/{structure_id}",
    response_model=SalaryStructureRead,
    dependencies=[
        Depends(lambda: require_api_permission("hr.salary_structure.update")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR])),
    ],
)
async def update_salary_structure(
    structure_id: UUID,
    data: SalaryStructureCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    service: HRService = Depends(get_hr_service),
):
    return await service.update_salary_structure(
        structure_id=structure_id,
        data=data,
        current_user_id=current_user_id,
        company_id=company_id,
    )


@router.delete(
    "/{structure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[
        Depends(lambda: require_api_permission("hr.salary_structure.delete")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR])),
    ],
)
async def delete_salary_structure(
    structure_id: UUID,
    service: HRService = Depends(get_hr_service),
):
    await service.delete_salary_structure(structure_id)
    return {"detail": "Deleted"}

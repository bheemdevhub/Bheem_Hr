
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from bheem_core.core.database import get_db
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.modules.hr.core.schemas.hr_schemas import PayrollRunCreate, PayrollRunRead
from bheem_core.modules.auth.core.services.permissions_service import (
    require_roles, require_api_permission, get_current_user_id, get_current_company_id
)
from bheem_core.shared.models import UserRole
from uuid import UUID
from typing import List

router = APIRouter(prefix="/payroll-runs", tags=["Payroll Runs"])

@router.post("/", response_model=PayrollRunRead, status_code=status.HTTP_201_CREATED,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payroll_run.create")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def create_payroll_run(
    data: PayrollRunCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    return await service.create_payroll_run(data, company_id, current_user_id)

@router.get("/{run_id}", response_model=PayrollRunRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payroll_run.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def get_payroll_run(
    run_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    return await service.get_payroll_run(run_id, company_id)

@router.get("/", response_model=List[PayrollRunRead],
          dependencies=[
              Depends(lambda: require_api_permission("hr.payroll_run.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def list_payroll_runs(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    return await service.list_payroll_runs(company_id)

@router.put("/{run_id}", response_model=PayrollRunRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payroll_run.update")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def update_payroll_run(
    run_id: UUID, 
    data: PayrollRunCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    return await service.update_payroll_run(run_id, data, company_id, current_user_id)

@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payroll_run.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_payroll_run(
    run_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    await service.delete_payroll_run(run_id, company_id, current_user_id)
    return {"detail": "Deleted"}

@router.post("/{run_id}/process", response_model=PayrollRunRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payroll_run.process")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def process_payroll(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    """Process payroll for a specific run"""
    service = HRService(db)
    return await service.process_payroll(run_id)



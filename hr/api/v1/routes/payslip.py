from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.modules.hr.core.schemas.hr_schemas import PayslipCreate, PayslipRead
from app.modules.auth.core.services.permissions_service import (
    require_roles, require_api_permission, get_current_user_id, get_current_company_id
)
from app.shared.models import UserRole
from uuid import UUID
from typing import List

router = APIRouter(prefix="/payslips", tags=["Payslips"])

@router.post("/", response_model=PayslipRead, status_code=status.HTTP_201_CREATED,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.create")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def create_payslip(
    data: PayslipCreate,
    db: AsyncSession = Depends(get_db),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    payslip = await service.create_payslip(data)
    return PayslipRead.model_validate(payslip, from_attributes=True)

@router.get("/", response_model=List[PayslipRead],
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def list_payslips(
    db: AsyncSession = Depends(get_db),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    payslips = await service.list_payslips()
    return [PayslipRead.model_validate(p, from_attributes=True) for p in payslips]

@router.get("/{payslip_id}", response_model=PayslipRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def get_payslip(
    payslip_id: UUID,
    db: AsyncSession = Depends(get_db),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    payslip = await service.get_payslip(payslip_id)
    return PayslipRead.model_validate(payslip, from_attributes=True)

@router.put("/{payslip_id}", response_model=PayslipRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.update")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def update_payslip(
    payslip_id: UUID,
    data: PayslipCreate,
    db: AsyncSession = Depends(get_db),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    payslip = await service.update_payslip(payslip_id, data)
    return PayslipRead.model_validate(payslip, from_attributes=True)

@router.delete("/{payslip_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_payslip(
    payslip_id: UUID,
    db: AsyncSession = Depends(get_db),
    event_bus = None
):
    service = HRService(db, event_bus=event_bus)
    await service.delete_payslip(payslip_id)
    return {"detail": "Deleted"}
async def create_payslip(
    data: PayslipCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.create_payslip(data)

@router.get("/{payslip_id}", response_model=PayslipRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def get_payslip(
    payslip_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.get_payslip(payslip_id)

@router.get("/", response_model=List[PayslipRead],
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def list_payslips(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.list_payslips()

@router.put("/{payslip_id}", response_model=PayslipRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.update")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def update_payslip(
    payslip_id: UUID, 
    data: PayslipCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.update_payslip(payslip_id, data)

@router.delete("/{payslip_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.payslip.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_payslip(
    payslip_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    await service.delete_payslip(payslip_id)
    return {"detail": "Deleted"}

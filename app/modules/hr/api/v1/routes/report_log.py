from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.modules.hr.core.schemas.hr_schemas import ReportLogCreate, ReportLogRead
from app.modules.auth.core.services.permissions_service import (
    require_roles, require_api_permission, get_current_user_id, get_current_company_id
)
from app.shared.models import UserRole
from uuid import UUID
from typing import List

router = APIRouter(prefix="/report-logs", tags=["Report Logs"])

@router.post("/", response_model=ReportLogRead, status_code=status.HTTP_201_CREATED,
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.create")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def create_report_log(
    data: ReportLogCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.create_report_log(data)

@router.get("/{log_id}", response_model=ReportLogRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def get_report_log(
    log_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.get_report_log(log_id)

@router.get("/", response_model=List[ReportLogRead],
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def list_report_logs(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.list_report_logs()

@router.put("/{log_id}", response_model=ReportLogRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.update")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def update_report_log(
    log_id: UUID, 
    data: ReportLogCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.update_report_log(log_id, data)

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_report_log(
    log_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    await service.delete_report_log(log_id)
    return {"detail": "Deleted"}

@router.get("/", response_model=list[ReportLogRead],
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.read")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def list_report_logs(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.list_report_logs()

@router.put("/{log_id}", response_model=ReportLogRead,
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.update")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def update_report_log(
    log_id: UUID, 
    data: ReportLogCreate, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    return await service.update_report_log(log_id, data)

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[
              Depends(lambda: require_api_permission("hr.report_log.delete")),
              Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
          ])
async def delete_report_log(
    log_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
    company_id: UUID = Depends(get_current_company_id)
):
    service = HRService(db)
    await service.delete_report_log(log_id)
    return {"detail": "Deleted"}

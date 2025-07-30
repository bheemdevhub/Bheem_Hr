from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import date, timedelta
from typing import List
from bheem_core.core.database import get_db
from bheem_core.modules.auth.core.services.permissions_service import require_roles, require_api_permission, get_current_user
from bheem_core.shared.models import UserRole
from bheem_core.modules.hr.core.services.hr_dashboard_service import HRDashboardService
from bheem_core.modules.hr.core.schemas.hr_dashboard_schemas import (
    HRDailySummaryResponse, AttendanceTodayResponse, PendingLeaveRequestsResponse, HRActionTodayResponse, HRNotificationsResponse
)

router = APIRouter(prefix="/hr", tags=["HR Dashboard"])

@router.get("/daily-summary", response_model=HRDailySummaryResponse, dependencies=[Depends(lambda: require_api_permission("hr.dashboard.read")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def get_hr_summary(db: AsyncSession = Depends(get_db)):
    today = date.today()
    service = HRDashboardService(db)
    return await service.get_daily_summary(today)

@router.get(
    "/attendance/today",
    response_model=AttendanceTodayResponse,
    dependencies=[
        Depends(lambda: require_api_permission("hr.dashboard.read")),
        Depends(require_roles([UserRole.ADMIN, UserRole.HR]))
    ]
)
async def list_today_attendance(db: AsyncSession = Depends(get_db)):
    service = HRDashboardService(db)
    today = date.today()
    return await service.get_attendance_today(today)


@router.get("/leave-requests/pending", response_model=PendingLeaveRequestsResponse, dependencies=[Depends(lambda: require_api_permission("hr.dashboard.read")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def get_pending_leaves(db: AsyncSession = Depends(get_db)):
    service = HRDashboardService(db)
    today = date.today()
    return await service.get_pending_leave_requests(today)


@router.get("/actions/today", response_model=HRActionTodayResponse, dependencies=[Depends(lambda: require_api_permission("hr.dashboard.read")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def get_hr_actions_today(db: AsyncSession = Depends(get_db)):
    service = HRDashboardService(db)
    today = date.today()
    return await service.get_hr_actions_today(today)


@router.get("/notifications", response_model=HRNotificationsResponse, dependencies=[Depends(lambda: require_api_permission("hr.dashboard.read")), Depends(require_roles([UserRole.ADMIN, UserRole.HR]))])
async def get_hr_notifications(db: AsyncSession = Depends(get_db)):
    service = HRDashboardService(db)
    return await service.get_hr_notifications()



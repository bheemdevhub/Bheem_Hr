from datetime import date
from typing import List
from app.modules.hr.core.schemas.hr_dashboard_schemas import (
    HRDailySummaryResponse,
    AttendanceTodayResponse, AttendanceTodayItem,
    PendingLeaveRequestsResponse, PendingLeaveRequestItem,
    HRActionTodayResponse, HRActionTodayItem,
    HRNotificationsResponse
)

# Dummy async service implementations. Replace with real DB/service logic.

class HRDashboardService:

    def __init__(self, db):
        self.db = db

    async def get_daily_summary(self, day: date) -> HRDailySummaryResponse:
        from app.modules.hr.core.models.hr_models import Employee
        from app.modules.hr.core.models.hr_models import Attendance
        from sqlalchemy import select,func, and_

        def map_employee(emp: Employee):
            return {
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}"
            }

        
        async def get_attendance_by_status(status: str):
            result = await self.db.execute(
            select(Employee)
            .join(Attendance, Attendance.employee_id == Employee.id)
            .where(Attendance.date == day, Attendance.status == status)
            )
            employees = result.scalars().all()
            return {
            "count": len(employees),
            "employees": [map_employee(e) for e in employees]
        }

        # Attendance categories
        present = await get_attendance_by_status("Present")
        on_leave = await get_attendance_by_status("Leave")
        wfh = await get_attendance_by_status("WFH")
        absent = await get_attendance_by_status("Absent")

        # New Joinees
        joinees_result = await self.db.execute(
        select(Employee).where(Employee.hire_date == day)
        )
        joinees = joinees_result.scalars().all()
        new_joinees_ids = {j.id for j in joinees}
        new_joinees = {
            "count": len(joinees),
            "employees": [map_employee(e) for e in joinees]
        }

        # Birthdays
        birthday_result = await self.db.execute(
        select(Employee).where(
            func.date_part('day', Employee.date_of_birth) == day.day,
            func.date_part('month', Employee.date_of_birth) == day.month
        )
        )
        birthday_emps = birthday_result.scalars().all()
        birthdays = [
            f"{e.employee_code} - {e.first_name} {e.last_name}"
            for e in birthday_emps
        ]

        # Work Anniversaries
        anniv_result = await self.db.execute(
        select(Employee).where(
            func.date_part('day', Employee.hire_date) == day.day,
            func.date_part('month', Employee.hire_date) == day.month,
            Employee.employment_status == "ACTIVE"
        )
        )
        anniv_emps = anniv_result.scalars().all()
        filtered_anniversaries = [
            e for e in anniv_emps if e.id not in new_joinees_ids
        ]

        def calculate_years(hire_date: date, today: date) -> int:
            return today.year - hire_date.year - (
                (today.month, today.day) < (hire_date.month, hire_date.day)
            )

        work_anniversaries = [
            f"{e.employee_code} - {e.first_name} {e.last_name} ({calculate_years(e.hire_date, day)} year{'s' if calculate_years(e.hire_date, day) > 1 else ''})"
            for e in filtered_anniversaries
        ]

        return HRDailySummaryResponse(
            present=present,
            on_leave=on_leave,
            wfh=wfh,
            absent=absent,
            new_joinees=new_joinees,
            birthdays_count=len(birthdays),
            birthdays=birthdays,   
            work_anniversaries=work_anniversaries,
            work_anniversaries_count=len(work_anniversaries)
        )
    

    async def get_attendance_today(self, day: date) -> AttendanceTodayResponse:
        from app.modules.hr.core.models.hr_models import Employee
        from app.modules.hr.core.models.hr_models import Attendance
        from sqlalchemy import select

        result = await self.db.execute(
            select(Attendance, Employee)
            .join(Employee, Attendance.employee_id == Employee.id)
            .where(Attendance.date == day)
        )
        items = [
            AttendanceTodayItem(
                employee_id=str(att.employee_id),
                employee_code=emp.employee_code,  # or emp.display_name   if available
                status=att.status
            )
            for att, emp in result.all()
        ]
        return AttendanceTodayResponse(results=items)


    
    async def get_pending_leave_requests(self, day: date) -> PendingLeaveRequestsResponse:
        from sqlalchemy import select, and_
        from app.modules.hr.core.models.hr_models import LeaveRequest, Employee
        from app.shared.models import LeaveStatusEnum 
        result = await self.db.execute(
            select(LeaveRequest, Employee)
            .join(Employee, LeaveRequest.employee_id == Employee.id)
            .where(
                and_(
                    LeaveRequest.status == LeaveStatusEnum.PENDING,  # use enum, not raw string
                    LeaveRequest.start_date == day  # only today's starting leaves
                )
            )
        )

        items = [
            PendingLeaveRequestItem(
                request_id=str(lr.id),
                employee_id=str(emp.id),
                employee_code=emp.employee_code,
                name=f"{emp.first_name} {emp.last_name}",
                leave_type=lr.leave_type,
                from_date=lr.start_date,
                to_date=lr.end_date,
                status=lr.status
            )
            for lr, emp in result.all()
        ]
        return PendingLeaveRequestsResponse(results=items)


    
    async def get_hr_actions_today(self, day: date) -> HRActionTodayResponse:
        from app.modules.hr.core.models.hr_models import HRActionItem
        from sqlalchemy import select

        result = await self.db.execute(
            select(HRActionItem)
            .where(HRActionItem.due_date == day, HRActionItem.status == "pending")
        )
        items = [
            HRActionTodayItem(
                action_id=str(a.id),
                title=a.title,
                due_date=a.due_date,
                status=a.status
            )
            for a in result.scalars().all()
        ]
        return HRActionTodayResponse(results=items)


    @staticmethod
    async def get_hr_notifications(db, day: date) -> HRNotificationsResponse:
        from app.modules.hr.core.models.hr_models import Employee
        from sqlalchemy import select, func
        from datetime import timedelta

        # Upcoming contracts ending in 7 days
        contract_day = day + timedelta(days=7)
        contracts_result = await db.execute(
            select(Employee).where(Employee.contract_end_date == contract_day)
        )
        upcoming_contracts = contracts_result.scalars().all()

        # Today's birthdays
        birthdays_result = await db.execute(
            select(Employee).where(
                func.date_part('day', Employee.date_of_birth) == day.day,
                func.date_part('month', Employee.date_of_birth) == day.month
            )
        )
        birthdays = [e.employee_code for e in birthdays_result.scalars().all()]

        return HRNotificationsResponse(
            upcoming_contracts=len(upcoming_contracts),
            birthdays=birthdays
        )

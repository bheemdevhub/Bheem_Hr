from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
import logging
from passlib.context import CryptContext
import uuid
import os
from uuid import UUID
from datetime import datetime, date, time, timezone
from decimal import Decimal

# Absolute imports from bheem_hr
from bheem_hr.core.models import (
    JobRequisition,
    JobRequisitionSkill,
    Employee,
    Candidate,
    Interview,
    Attendance,
    SalaryStructure,
    SalaryComponent,
    LeaveRequest,
    Payslip,
    PayrollRun
)

from bheem_hr.core.schemas import (
    JobRequisitionCreate,
    JobRequisitionUpdate,
    JobRequisitionResponse,

    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeSearchParams,
    EmployeeSearchResult,

    PersonCreate,
    PersonResponse,
    LookupResponse,

    SocialProfileCreate,
    SocialProfileResponse,

    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    ResumeAttachmentCreate,

    OnboardingChecklistResponse,

    InterviewCreate,
    InterviewUpdate,
    InterviewResponse,

    OfferCreate,
    OfferResponse,

    SalaryStructureCreate,
    SalaryStructureRead,

    SalaryComponentCreate,
    SalaryComponentRead,
    SalaryComponentNestedCreate,

    PayrollRunCreate,
    PayrollRunRead,

    PayslipCreate,
    PayslipRead,

    AttendanceCreate,
    AttendanceRead,
    AttendanceUpdate,

    LeaveRequestCreate,
    LeaveRequestRead,

    ReportLogCreate,
    ReportLogRead
)

# Shared models and schemas
from bheem_core.shared.models import (
    Address,
    Note,
    Person,
    Contact,
    BankAccount,
    Passport,
    SocialProfile,
    Attachment
)

from bheem_core.shared.schemas import (
    ContactCreate,
    ContactResponse,
    AddressCreate,
    AddressResponse,
    BankAccountCreate,
    BankAccountResponse,
    PassportCreate,
    PassportResponse
)

debug = True

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class HRService:

    async def get_attendance_by_employee_id(
        self,
        employee_id: UUID,
        limit: int = 10,
        offset: int = 0,
        company_id: UUID = None
    ):
        """
        Return paginated attendance records for a given employee_id.
        """
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceRead, AttendancePaginatedResponse
        from sqlalchemy import select, func

        # Total count
        count_query = select(func.count()).select_from(
            select(Attendance).where(Attendance.employee_id == employee_id).subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated data
        data_query = (
            select(Attendance)
            .where(Attendance.employee_id == employee_id)
            .order_by(Attendance.date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(data_query)
        records = result.scalars().all()

        return AttendancePaginatedResponse(
            total=total,
            limit=limit,
            offset=offset,
            records=[AttendanceRead.model_validate(r, from_attributes=True) for r in records]
        )
    
    async def get_half_days_leave(self, employee_id: UUID, start_date: date, end_date: date) -> list:
        from bheem_core.modules.hr.core.models.hr_models import Attendance, Employee
        from sqlalchemy import select, and_
        # Fetch attendance records for the employee in the date range
        result = await self.db.execute(
            select(Attendance)
            .where(
                Attendance.employee_id == employee_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
            .order_by(Attendance.date)
        )
        records = result.scalars().all()

        # Fetch employee details
        emp_result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
        employee = emp_result.scalar_one_or_none()
        emp_code = getattr(employee, "employee_code", None)
        emp_name = getattr(employee, "name", None)

        half_days = []
        late_days = []
        for att in records:
            # Consider status halfday as halfday
            if getattr(att, "status", None) == "halfday":
                half_days.append(att)
            # Check for late clock-in
            elif att.check_in and att.check_in.strftime("%H:%M") > "09:35":
                late_days.append(att)
            else:
                late_days = []  # Reset if not late
            # If 3 continuous late days, count as halfday
            if len(late_days) == 3:
                half_days.append(late_days[-1])  # Mark the 3rd day as halfday
                late_days = []  # Reset for next sequence

        # Group every 6 halfdays as 1 leave
        halfday_count = len(half_days)
        leave_count = halfday_count // 6

        # Prepare response
        response = []
        for att in half_days:
            response.append({
                "employee_code": emp_code,
                "employee_id": str(employee_id),
                "employee_name": emp_name,
                "date": att.date,
                "check_in": att.check_in,
                "check_out": att.check_out,
                "status": getattr(att, "status", None)
            })
        return {
            "halfday_count": halfday_count,
            "leave_count": leave_count,
            "records": response
        }

    async def get_company_half_days_leave(self, company_id: UUID, start_date: date, end_date: date):
        from bheem_core.modules.hr.core.models.hr_models import Attendance, Employee
        from sqlalchemy import select
        from collections import defaultdict

        result = await self.db.execute(
            select(Attendance, Employee)
            .join(Employee, Attendance.employee_id == Employee.id)
            .where(
                Employee.company_id == company_id,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
            .order_by(Attendance.employee_id, Attendance.date)
        )
        rows = result.fetchall()

        emp_attendance = defaultdict(list)
        for att, emp in rows:
            emp_attendance[att.employee_id].append((att, emp))

        all_results = []
        total_halfdays = 0

        for emp_id, records in emp_attendance.items():
            records.sort(key=lambda x: x[0].date)
            half_days = []
            late_days = []
            emp = records[0][1] if records else None

            for att, _ in records:
                # Case 1: Status is 'halfday'
                if att.status and att.status.lower() == "halfday":
                    half_days.append(att)
                    late_days = []
                # Case 2: Late check-in
                elif att.check_in and att.check_in > time(9, 35):
                    late_days.append(att)
                else:
                    late_days = []

                # Case 3: 3 consecutive late check-ins
                if len(late_days) == 3:
                    half_days.append(late_days[-1])  # Only mark the 3rd day
                    late_days = []

            halfday_count = len(half_days)
            leave_count = halfday_count // 6
            total_halfdays += halfday_count

            for att in half_days:
                all_results.append({
                    "employee_code": getattr(emp, "employee_code", ""),
                    "employee_id": str(emp.id),
                    "employee_name": f"{getattr(emp, 'first_name', '')} {getattr(emp, 'last_name', '')}".strip(),
                    "date": att.date,
                    "check_in": att.check_in,
                    "check_out": att.check_out,
                    "status": att.status
                })

        return {
            "halfday_count": total_halfdays,
            "leave_count": total_halfdays // 6,
            "records": all_results
        }
        

    async def get_attendance_by_employee_and_date(self, employee_id: UUID, date_: date):
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.date == date_
            )
        )
        return result.scalar_one_or_none()
        


    async def update_attendance_by_employee(
        self, employee_id: UUID, date_: date, data: AttendanceUpdate
    ):
        result = await self.db.execute(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.date == date_
            )
        )
        attendance = result.scalar_one_or_none()
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance not found.")

        for field, value in data.dict(exclude_unset=True).items():
            setattr(attendance, field, value)

        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def delete_attendance_by_employee(self, employee_id: UUID, date_: date):
        result = await self.db.execute(
            delete(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.date == date_
            ).returning(Attendance.id)
        )
        deleted = result.fetchone()
        if not deleted:
            raise HTTPException(status_code=404, detail="Attendance not found.")
        await self.db.commit()
        return {"status": "success", "message": "Attendance deleted"}





    

    async def get_employee(self, employee_id: str):
        """Fetch an employee by employee_id (UUID or string)."""
        from sqlalchemy import select
        from bheem_core.modules.hr.core.models import Employee
        from bheem_core.shared.schemas import ContactResponse, AddressResponse, BankAccountResponse, PassportResponse
        from bheem_core.modules.hr.core.schemas import SocialProfileResponse
        from bheem_core.shared.models import Contact, Address, BankAccount, Passport, SocialProfile
        from fastapi import HTTPException
        # Fetch the employee
        result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
        employee = result.scalar_one_or_none()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        # Fetch related objects for the response
        contacts_result = await self.db.execute(select(Contact).where(Contact.person_id == employee.id))
        contacts_data = [ContactResponse.model_validate(c).model_dump() for c in contacts_result.scalars().all()]
        addresses_result = await self.db.execute(select(Address).where(Address.entity_type == "employee", Address.entity_id == str(employee.id)))
        addresses_data = [AddressResponse.model_validate(a).model_dump() for a in addresses_result.scalars().all()]
        bank_accounts_result = await self.db.execute(select(BankAccount).where(BankAccount.person_id == employee.id))
        bank_accounts_data = [BankAccountResponse.model_validate(b).model_dump() for b in bank_accounts_result.scalars().all()]
        passports_result = await self.db.execute(select(Passport).where(Passport.person_id == employee.id))
        passports_data = [PassportResponse.model_validate(p).model_dump() for p in passports_result.scalars().all()]
        social_profiles_result = await self.db.execute(select(SocialProfile).where(SocialProfile.person_id == employee.id))
        social_profiles_data = [SocialProfileResponse.model_validate(s).model_dump() for s in social_profiles_result.scalars().all()]
        # Compose the response
        from bheem_core.modules.hr.core.schemas.hr_schemas import EmployeeResponse
        # Convert ORM employee to dict, then merge related data
        employee_data = employee.__dict__.copy() if hasattr(employee, "__dict__") else dict(employee)
        employee_data["contacts"] = contacts_data
        employee_data["addresses"] = addresses_data
        employee_data["bank_accounts"] = bank_accounts_data
        employee_data["passports"] = passports_data
        employee_data["social_profiles"] = social_profiles_data
        return EmployeeResponse.model_validate(employee_data)

    
    async def get_leave_request(self, leave_id, company_id):
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        leave = await self.db.get(LeaveRequest, leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="LeaveRequest not found")
        return leave


    async def list_leave_requests(self, company_id, status: str = None, limit: int = 10, offset: int = 0):
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        from sqlalchemy import select
        query = select(LeaveRequest).where(LeaveRequest.company_id == company_id)
        if status:
            query = query.where(LeaveRequest.status == status)
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    

    async def update_leave_request(self, leave_id, data, current_user_id, company_id, event_bus=None):
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        leave = await self.db.get(LeaveRequest, leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="LeaveRequest not found")
        leave.leave_type = data.leave_type
        leave.start_date = data.start_date
        leave.end_date = data.end_date
        leave.reason = data.reason
        leave.status = data.status or leave.status
        leave.updated_by = str(current_user_id)
        await self.db.commit()
        await self.db.refresh(leave)
        bus = self.event_bus or event_bus
        if bus:
            await bus.publish("hr.leave_request.updated", {"leave_id": str(leave.id), "employee_id": str(leave.employee_id)})
        return leave

    async def delete_leave_request(self, leave_id, current_user_id, company_id, event_bus=None):
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        leave = await self.db.get(LeaveRequest, leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="LeaveRequest not found")
        await self.db.delete(leave)
        await self.db.commit()
        bus = self.event_bus or event_bus
        if bus:
            await bus.publish("hr.leave_request.deleted", {"leave_id": str(leave_id)})
        return None
    def __init__(self, db, event_bus=None):
        self.db = db
        self.event_bus = event_bus

    async def create_salary_structure(
        self,
        data: SalaryStructureCreate,
        current_user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
    ) -> SalaryStructure:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        structure = SalaryStructure(
            employee_id=data.employee_id,
            effective_date=data.effective_date,
            pay_type=data.pay_type,
            is_active=data.is_active,
            created_at=now,
            updated_at=now,
            created_by=str(current_user_id) if current_user_id else None,
            updated_by=str(current_user_id) if current_user_id else None,
        )

        if data.components:
            structure.components = [
                SalaryComponent(
                    name=comp.name,
                    component_type=comp.component_type,
                    amount=comp.amount,
                    taxable=comp.taxable,
                )
                for comp in data.components
            ]

        self.db.add(structure)
        await self.db.commit()
        await self.db.refresh(structure)

        # ✅ Load components eagerly to prevent MissingGreenlet
        result = await self.db.execute(
            select(SalaryStructure)
            .options(selectinload(SalaryStructure.components))
            .where(SalaryStructure.id == structure.id)
        )
        return result.scalar_one()

    async def get_salary_structure(self, structure_id: UUID) -> SalaryStructure:
        structure = await self.db.get(SalaryStructure, structure_id)
        if not structure:
            raise HTTPException(status_code=404, detail="SalaryStructure not found")
        return structure

    async def list_salary_structures(self) -> list[SalaryStructure]:
        result = await self.db.execute(select(SalaryStructure))
        return result.scalars().all()

    async def update_salary_structure(
        self,
        structure_id: UUID,
        *,
        data: SalaryStructureCreate,
        current_user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None
    ) -> SalaryStructure:
        """Update salary structure and its components, trigger event, and set audit fields."""
        from bheem_core.modules.hr.core.models.hr_models import SalaryStructure, SalaryComponent
        structure = await self.db.get(SalaryStructure, structure_id)
        if not structure:
            raise HTTPException(status_code=404, detail="SalaryStructure not found")

        structure.employee_id = data.employee_id
        structure.effective_date = data.effective_date
        structure.pay_type = data.pay_type
        structure.is_active = data.is_active
        structure.updated_by = str(current_user_id)

        # Remove existing components
        await self.db.execute(delete(SalaryComponent).where(SalaryComponent.structure_id == structure_id))
        # Add new components
        for component_data in data.components:
            component = SalaryComponent(**component_data.model_dump(), structure_id=structure.id)
            self.db.add(component)

        await self.db.commit()
        await self.db.refresh(structure)

        # Fire event
        if self.event_bus:
            await self.event_bus.publish("salary_structure.updated", {
                "structure_id": str(structure.id),
                "employee_id": str(structure.employee_id)
            })

        return structure

    async def delete_salary_structure(self, structure_id: UUID):
        structure = await self.db.get(SalaryStructure, structure_id)
        if not structure:
            raise HTTPException(status_code=404, detail="SalaryStructure not found")
        await self.db.delete(structure)
        await self.db.commit()

    # ---------------- SalaryComponent CRUD ----------------
    async def create_salary_component(
        self,
        data: SalaryComponentCreate,
        current_user_id: UUID = None,
        company_id: UUID = None,
    ):
        from bheem_core.modules.hr.core.models.hr_models import SalaryComponent

        component = SalaryComponent(
            structure_id=data.structure_id,
            name=data.name,
            component_type=data.component_type,
            amount=data.amount,
            taxable=data.taxable
        )
        self.db.add(component)
        await self.db.commit()
        await self.db.refresh(component)

        if self.event_bus:
            await self.event_bus.publish("salary_component.created", {
                "component_id": str(component.id),
                "structure_id": str(component.structure_id)
            })

        from bheem_core.modules.hr.core.schemas.hr_schemas import SalaryComponentRead
        return SalaryComponentRead.model_validate(component, from_attributes=True)

    async def get_salary_component(self, component_id):
        from bheem_core.modules.hr.core.models.hr_models import SalaryComponent
        component = await self.db.get(SalaryComponent, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="SalaryComponent not found")
        return component

    async def list_salary_components(self):
        from bheem_core.modules.hr.core.models.hr_models import SalaryComponent
        result = await self.db.execute(select(SalaryComponent))
        return result.scalars().all()

    async def update_salary_component(
        self,
        component_id: UUID,
        data: SalaryComponentCreate,
        current_user_id: UUID = None,
        company_id: UUID = None,
    ):
        from bheem_core.modules.hr.core.models.hr_models import SalaryComponent

        component = await self.db.get(SalaryComponent, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="SalaryComponent not found")

        component.structure_id = data.structure_id
        component.name = data.name
        component.component_type = data.component_type
        component.amount = data.amount
        component.taxable = data.taxable
        component.updated_by = str(current_user_id) if current_user_id else None

        await self.db.commit()
        await self.db.refresh(component)

        if self.event_bus:
            await self.event_bus.publish("salary_component.updated", {
                "component_id": str(component.id),
                "structure_id": str(component.structure_id)
            })

        return component

    async def delete_salary_component(self, component_id, current_user_id=None, company_id=None):
        from bheem_core.modules.hr.core.models.hr_models import SalaryComponent
        component = await self.db.get(SalaryComponent, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="SalaryComponent not found")
        await self.db.delete(component)
        await self.db.commit()
        if self.event_bus:
            await self.event_bus.publish("salary_component.deleted", {
                "component_id": str(component_id)
            })

    # ---------------- PayrollRun CRUD ----------------
    async def create_payroll_run(self, data):
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        run = PayrollRun(
            month=data.month,
            status=data.status,
            processed_by=data.processed_by
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_payroll_run(self, run_id):
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        run = await self.db.get(PayrollRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="PayrollRun not found")
        return run

    async def list_payroll_runs(self):
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        result = await self.db.execute(select(PayrollRun))
        return result.scalars().all()

    async def update_payroll_run(self, run_id, data):
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        run = await self.db.get(PayrollRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="PayrollRun not found")
        run.month = data.month
        run.status = data.status
        run.processed_by = data.processed_by
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def delete_payroll_run(self, run_id):
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        run = await self.db.get(PayrollRun, run_id)
        if not run:
            raise HTTPException(status_code=404, detail="PayrollRun not found")
        await self.db.delete(run)
        await self.db.commit()

    # ---------------- Payslip CRUD ----------------
    async def create_payslip(self, data):
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        payslip = Payslip(
            employee_id=data.employee_id,
            payroll_run_id=data.payroll_run_id,
            total_earnings=data.total_earnings,
            total_deductions=data.total_deductions,
            net_pay=data.net_pay,
            attachment_id=data.attachment_id
        )
        self.db.add(payslip)
        await self.db.commit()
        await self.db.refresh(payslip)
        return payslip

    async def get_payslip(self, payslip_id):
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        payslip = await self.db.get(Payslip, payslip_id)
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        return payslip

    async def list_payslips(self):
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        result = await self.db.execute(select(Payslip))
        return result.scalars().all()

    async def update_payslip(self, payslip_id, data):
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        payslip = await self.db.get(Payslip, payslip_id)
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        payslip.employee_id = data.employee_id
        payslip.payroll_run_id = data.payroll_run_id
        payslip.total_earnings = data.total_earnings
        payslip.total_deductions = data.total_deductions
        payslip.net_pay = data.net_pay
        payslip.attachment_id = data.attachment_id
        await self.db.commit()
        await self.db.refresh(payslip)
        return payslip

    async def delete_payslip(self, payslip_id):
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        payslip = await self.db.get(Payslip, payslip_id)
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        await self.db.delete(payslip)
        await self.db.commit()


    async def get_attendance(self, attendance_id):
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        attendance = await self.db.get(Attendance, attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance not found")
        from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceRead
        return AttendanceRead.model_validate(attendance, from_attributes=True)

    async def list_attendance(self, employee_id=None):
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        q = select(Attendance)
        if employee_id:
            q = q.where(Attendance.employee_id == employee_id)
        result = await self.db.execute(q)
        from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceRead
        return [AttendanceRead.model_validate(a, from_attributes=True) for a in result.scalars().all()]

    async def update_attendance(self, attendance_id, data, current_user_id, event_bus=None):
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        attendance = await self.db.get(Attendance, attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance not found")
        if data.check_in is not None:
            attendance.check_in = data.check_in
        if data.check_out is not None:
            attendance.check_out = data.check_out
        if data.status is not None:
            attendance.status = data.status
        attendance.updated_by = current_user_id
        await self.db.commit()
        await self.db.refresh(attendance)
        if self.event_bus or event_bus:
            bus = self.event_bus or event_bus
            await bus.publish("attendance.updated", {"attendance_id": str(attendance.id), "employee_id": str(attendance.employee_id)})
        from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceRead
        return AttendanceRead.model_validate(attendance, from_attributes=True)

    async def delete_attendance(self, attendance_id, event_bus=None):
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        attendance = await self.db.get(Attendance, attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance not found")
        await self.db.delete(attendance)
        await self.db.commit()
        if self.event_bus or event_bus:
            bus = self.event_bus or event_bus
            await bus.publish("attendance.deleted", {"attendance_id": str(attendance_id)})

    

    async def get_leave_request(self, leave_id):
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        leave = await self.db.get(LeaveRequest, leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="LeaveRequest not found")
        return leave

    # async def list_leave_requests(self):
    #     from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
    #     result = await self.db.execute(select(LeaveRequest))
    #     return result.scalars().all()

    # async def update_leave_request(self, leave_id, data):
    #     from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
    #     leave = await self.db.get(LeaveRequest, leave_id)
    #     if not leave:
    #         raise HTTPException(status_code=404, detail="LeaveRequest not found")
    #     leave.employee_id = data.employee_id
    #     leave.leave_type = data.leave_type
    #     leave.start_date = data.start_date
    #     leave.end_date = data.end_date
    #     leave.reason = data.reason
    #     leave.status = data.status
    #     await self.db.commit()
    #     await self.db.refresh(leave)
    #     return leave

    async def delete_leave_request(self, leave_id):
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        leave = await self.db.get(LeaveRequest, leave_id)
        if not leave:
            raise HTTPException(status_code=404, detail="LeaveRequest not found")
        await self.db.delete(leave)
        await self.db.commit()

    # ---------------- ReportLog CRUD ----------------
    async def create_report_log(self, data):
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        log = ReportLog(
            report_name=data.report_name,
            generated_by=data.generated_by,
            generated_on=data.generated_on,
            parameters=data.parameters,
            attachment_id=data.attachment_id
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_report_log(self, log_id):
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        log = await self.db.get(ReportLog, log_id)
        if not log:
            raise HTTPException(status_code=404, detail="ReportLog not found")
        return log

    async def list_report_logs(self):
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        result = await self.db.execute(select(ReportLog))
        return result.scalars().all()

    async def update_report_log(self, log_id, data):
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        log = await self.db.get(ReportLog, log_id)
        if not log:
            raise HTTPException(status_code=404, detail="ReportLog not found")
        log.report_name = data.report_name
        log.generated_by = data.generated_by
        log.generated_on = data.generated_on
        log.parameters = data.parameters
        log.attachment_id = data.attachment_id
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def delete_report_log(self, log_id):
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        log = await self.db.get(ReportLog, log_id)
        if not log:
            raise HTTPException(status_code=404, detail="ReportLog not found")
        await self.db.delete(log)
        await self.db.commit()

    # Employee Methods
    async def create_person(self, person_data: PersonCreate) -> Person:
        contacts_data = person_data.contacts or []
        addresses_data = person_data.addresses or []
        bank_accounts_data = person_data.bank_accounts or []
        passports_data = person_data.passports or []
        social_profiles_data = person_data.social_profiles or []
        person_dict = person_data.model_dump(exclude={"contacts", "addresses", "bank_accounts", "passports", "social_profiles"})
        person = Person(**person_dict, person_type="employee", is_active=True, company_id=person_data.company_id)
        self.db.add(person)
        await self.db.commit()
        await self.db.refresh(person)
        # Debug: Log incoming related data
        print("[DEBUG] contacts_data:", contacts_data)
        print("[DEBUG] addresses_data:", addresses_data)
        print("[DEBUG] bank_accounts_data:", bank_accounts_data)
        print("[DEBUG] passports_data:", passports_data)
        print("[DEBUG] social_profiles_data:", social_profiles_data)
        # Create contacts
        for contact in contacts_data:
            contact_obj = Contact(person_id=person.id, **contact.model_dump())
            self.db.add(contact_obj)
        # Create addresses
        for address in addresses_data:
            address_obj = Address(
                entity_type=person.person_type,
                entity_id=person.id,
                **address.model_dump(exclude={"entity_type", "entity_id"})
            )
            self.db.add(address_obj)
        # Create bank accounts
        for bank in bank_accounts_data:
            bank_obj = BankAccount(person_id=person.id, **bank.model_dump())
            self.db.add(bank_obj)
        # Create passports
        for passport in passports_data:
            passport_obj = Passport(person_id=person.id, **passport.model_dump())
            self.db.add(passport_obj)
        # Create social profiles
        for social in social_profiles_data:
            social_obj = SocialProfile(person_id=person.id, **social.model_dump())
            self.db.add(social_obj)
        await self.db.commit()
        await self.db.refresh(person)
        if person.person_type == "employee":
            await self._publish_employee_onboard_event(person)
        return person

    async def _publish_employee_onboard_event(self, person: Person):
        # Get primary email from contacts
        primary_email = None
        for contact in person.contacts:
            if contact.email_primary:
                primary_email = contact.email_primary
                break
        if self.event_bus:
            await self.event_bus.publish(
                "hr.employee_onboard",
                {
                    "entity_type": "employee",
                    "entity_id": person.id,
                    "email": primary_email,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                },
                source_module="hr"
            )
        else:
            print(f"ONBOARD MAIL EVENT: {person.id} - {person.first_name} {person.last_name} <{primary_email}>")

    async def create_employee(self, emp_data: EmployeeCreate) -> EmployeeResponse:
        from sqlalchemy import select
        # Import shared models from bheem_core.shared.models, not hr.models
        from bheem_core.shared.models import Contact, Address, BankAccount, Passport, Note, SocialProfile
        from bheem_core.modules.hr.core.models import Employee
        
        # Validate required fields
        if not emp_data.first_name or not emp_data.last_name:
            raise HTTPException(status_code=400, detail="First name and last name are required")
        
        if not emp_data.company_id:
            raise HTTPException(status_code=400, detail="Company ID is required")
        
        if not emp_data.password:
            raise HTTPException(status_code=400, detail="Password is required for employee creation")
            
        from passlib.context import CryptContext
        import uuid
        prefix = "BHM"
        code_length = 4
        max_retries = 20
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        try:
            for attempt in range(max_retries):
                # Generate unique employee code
                result = await self.db.execute(select(Employee.employee_code))
                codes = set()
                for code in result.scalars():
                    if code and code.startswith(prefix):
                        try:
                            num = int(code[len(prefix):])
                            codes.add(num)
                        except ValueError:
                            continue
                # Find the next available number
                new_num = 1
                for i in range(1, len(codes) + 2):
                    if i not in codes:
                        new_num = i
                        break
                # Set the generated employee code
                emp_data.employee_code = f"{prefix}{str(new_num).zfill(code_length)}"
                # Extract related data
                contacts_data = emp_data.contacts or []
                addresses_data = emp_data.addresses or []
                bank_accounts_data = emp_data.bank_accounts or []
                passports_data = emp_data.passports or []
                social_profiles_data = emp_data.social_profiles or []
                # Hash password
                hashed_password = pwd_context.hash(emp_data.password)
                # Prepare employee data
                employee_dict = emp_data.model_dump(exclude={"contacts", "addresses", "bank_accounts", "passports", "social_profiles"})
                employee_dict["password"] = hashed_password
                employee_dict["is_active"] = emp_data.is_active if emp_data.is_active is not None else True
                employee_dict["is_superadmin"] = emp_data.is_superadmin if emp_data.is_superadmin is not None else False
                employee_dict["person_type"] = "employee"
                employee_dict["employee_code"] = emp_data.employee_code
                # Create employee
                employee = Employee(**employee_dict)
                self.db.add(employee)
                try:
                    await self.db.commit()
                    await self.db.refresh(employee)
                    # Create related objects
                    for contact in contacts_data:
                        contact_obj = Contact(person_id=employee.id, **contact.model_dump())
                        self.db.add(contact_obj)
                    for address in addresses_data:
                        address_obj = Address(
                            entity_type=employee.person_type,
                            entity_id=str(employee.id),
                            **address.model_dump(exclude={"entity_type", "entity_id"})
                        )
                        self.db.add(address_obj)
                    for bank in bank_accounts_data:
                        bank_dict = bank.model_dump()
                        if not bank_dict.get('account_name'):
                            bank_dict['account_name'] = f"{employee.first_name} {employee.last_name}"
                        bank_obj = BankAccount(person_id=employee.id, **bank_dict)
                        self.db.add(bank_obj)
                    for passport in passports_data:
                        passport_obj = Passport(person_id=employee.id, **passport.model_dump())
                        self.db.add(passport_obj)
                    for social in social_profiles_data:
                        social_obj = SocialProfile(person_id=employee.id, **social.model_dump())
                        self.db.add(social_obj)
                    await self.db.commit()
                    break
                except Exception as e:
                    await self.db.rollback()
                    error_msg = str(e).lower()
                    if 'duplicate key' in error_msg or 'unique constraint' in error_msg:
                        continue
                    else:
                        raise HTTPException(status_code=500, detail=f"Failed to create employee: {str(e)}")
            else:
                raise HTTPException(status_code=500, detail="Failed to generate a unique employee code after multiple attempts.")
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating employee: {str(e)}")
        try:
            return await self.get_employee_by_id(employee.id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching created employee: {str(e)}")

    async def get_employee_by_id(self, employee_id: str) -> EmployeeResponse:
        from ..models import Employee
        from sqlalchemy.orm import selectinload
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import UUID
        from bheem_core.shared.models import Contact, Address, BankAccount, Passport, Note
        from ..schemas import EmployeeResponse
        import uuid
        # Use cast to match types for manager relationship join
        result = await self.db.execute(
            select(Employee)
            .options(
                selectinload(Employee.department),
                # selectinload(Employee.role),  # Eager load role
                selectinload(Employee.manager),
            )
            .where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        # Fix: ensure manager relationship is loaded with correct type join
        # If manager_id is set, reload manager using cast(Employee.id, UUID) == Employee.manager_id
        if employee.manager_id is not None and employee.id is not None:
            try:
                uuid_id = uuid.UUID(employee.id)
                manager_result = await self.db.execute(
                    select(Employee).where(Employee.manager_id == cast(employee.id, UUID))
                )
                employee.manager = manager_result.scalar_one_or_none()
            except Exception:
                pass
        # Fetch related data with async queries
        contacts_result = await self.db.execute(select(Contact).where(Contact.person_id == employee.id))
        contacts = contacts_result.scalars().all()
        addresses_result = await self.db.execute(select(Address).where(Address.entity_type == employee.person_type, Address.entity_id == str(employee.id)))
        addresses = addresses_result.scalars().all()
        # Skip bank accounts to avoid column errors
        bank_accounts = []
        passports_result = await self.db.execute(select(Passport).where(Passport.person_id == employee.id))
        passports = passports_result.scalars().all()
        # Note.entity_id is VARCHAR in DB, so always compare to str(employee.id)
        notes_result = await self.db.execute(
            select(Note).where(
                Note.entity_type == employee.person_type,
                Note.entity_id == str(employee.id)
            )
        )
        notes = notes_result.scalars().all()
        # Convert employee to dict and handle enum serialization
        emp_dict = employee.__dict__.copy()
        emp_dict.pop("_sa_instance_state", None)
        emp_dict['person_id'] = emp_dict['id']
        emp_dict['contacts'] = [c.__dict__.copy() for c in contacts]
        for c in emp_dict['contacts']:
            c.pop("_sa_instance_state", None)
        emp_dict['addresses'] = [a.__dict__.copy() for a in addresses]
        for a in emp_dict['addresses']:
            a.pop("_sa_instance_state", None)
        emp_dict['bank_accounts'] = []  
        emp_dict['passports'] = [p.__dict__.copy() for p in passports]
        for p in emp_dict['passports']:
            p.pop("_sa_instance_state", None)
        emp_dict['notes'] = [n.__dict__.copy() for n in notes]
        for n in emp_dict['notes']:
            n.pop("_sa_instance_state", None)
        return EmployeeResponse.model_validate(emp_dict)

    async def search_employees(self, params: EmployeeSearchParams) -> EmployeeSearchResult:
        import logging
        if debug:
            logging.debug(f"search_employees called with params: {params}")
        
        try:
            # Remove the is_closed check as AsyncSession doesn't have this attribute
            query = select(Employee).options(selectinload(Employee.department))
            filters = [Employee.is_active == True]
            
            if params.department_id:
                filters.append(Employee.department_id == params.department_id)
            if params.employment_type:
                filters.append(Employee.employment_type == params.employment_type)
            if params.status:
                filters.append(Employee.employment_status == params.status)
            if params.search_term:
                search_filter = or_(
                    Employee.first_name.ilike(f"%{params.search_term}%"),
                    Employee.last_name.ilike(f"%{params.search_term}%"),
                    Employee.employee_code.ilike(f"%{params.search_term}%")
                )
                filters.append(search_filter)
            
            if debug:
                logging.debug(f"Filters applied: {filters}")
            
            query = query.where(and_(*filters))
            count_query = select(func.count()).select_from(query.subquery())
            
            try:
                total_count = await self.db.scalar(count_query)
            except Exception as db_error:
                logging.error(f"Database error during count query: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database connection error: {str(db_error)}")
            
            if debug:
                logging.debug(f"Total count after filters: {total_count}")
            
            offset = (params.page - 1) * params.page_size
            query = query.offset(offset).limit(params.page_size).order_by(Employee.first_name, Employee.last_name)
            
            if debug:
                logging.debug(f"Query with offset {offset} and limit {params.page_size}")
            
            try:
                result = await self.db.execute(query)
                employees = result.scalars().all()
            except Exception as db_error:
                logging.error(f"Database error during employee query: {db_error}")
                raise HTTPException(status_code=500, detail=f"Database connection error: {str(db_error)}")
            
            if debug:
                logging.debug(f"Found {len(employees)} employees, total_count={total_count}")
            
            items = []
            for emp in employees:
                try:
                    emp_dict = emp.__dict__.copy()
                    emp_dict['person_id'] = emp.id  
                    if debug:
                        logging.debug(f"Serializing employee: {emp_dict}")
                    items.append(EmployeeResponse.model_validate(emp_dict))
                except Exception as e:
                    logging.error(f"Error serializing employee {getattr(emp, 'id', None)}: {e}")
            if debug:
                logging.debug(f"Returning {len(items)} employees in response")
            return EmployeeSearchResult(
                items=items,
                total_count=total_count,
                page=params.page,
                page_size=params.page_size,
                has_next=(offset + params.page_size) < total_count,
                has_previous=params.page > 1
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.exception("Error in search_employees")
            raise HTTPException(status_code=500, detail=f"Internal error in search_employees: {str(e)}")

    async def update_employee(self, emp_id: str, emp_data: EmployeeUpdate) -> EmployeeResponse:
        from sqlalchemy import select
        from sqlalchemy.orm import class_mapper, RelationshipProperty
        from bheem_core.shared.models import Contact, Address, BankAccount, Passport
        from bheem_core.modules.hr.core.models import Employee
        
        # Get employee
        employee = await self.db.get(Employee, emp_id)
        if not employee or not employee.is_active:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Get all relationship fields to exclude from direct attribute updates
        relationship_fields = {
            prop.key for prop in class_mapper(Employee).iterate_properties
            if isinstance(prop, RelationshipProperty)
        }
        
        # Update basic employee fields (excluding relationships and related objects)
        update_data = emp_data.model_dump(
            exclude_unset=True, 
            exclude={"contacts", "addresses", "bank_accounts", "passports", "social_profiles"}
        )
        # Cast UUID fields to correct type
        update_data = self._cast_uuid_fields(update_data, ["manager_id", "role_id", "department_id", "position_id"])
        
        # Update the employee object with all valid fields
        for field, value in update_data.items():
            if hasattr(employee, field) and field not in relationship_fields:
                current_value = getattr(employee, field, None)
                # Skip if the value is not changing
                if current_value == value:
                    if debug:
                        logging.debug(f"Skipping field '{field}': value unchanged ({current_value})")
                    continue
                # Special handling for employee_code to prevent unique constraint violations
                if field == 'employee_code':
                    # Check if another employee already has this code
                    existing_employee = await self.db.execute(
                        select(Employee).where(
                            Employee.employee_code == value,
                            Employee.id != employee.id
                        )
                    )
                    if existing_employee.scalar_one_or_none():
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Employee code '{value}' is already in use by another employee"
                        )
                
                # Log the field update for debugging
                if debug:
                    logging.debug(f"Updating field '{field}': {current_value} -> {value}")
                
                setattr(employee, field, value)
        
        await self.db.commit()
        await self.db.refresh(employee)
        
        # Update contacts if provided
        contacts = getattr(emp_data, "contacts", None)
        if contacts is not None:
            # Delete existing contacts
            await self.db.execute(
                Contact.__table__.delete().where(Contact.person_id == employee.id)
            )
            # Add new contacts
            for contact in contacts:
                contact_obj = Contact(person_id=employee.id, **contact.model_dump())
                self.db.add(contact_obj)
            await self.db.commit()
        
        # Update addresses if provided
        addresses = getattr(emp_data, "addresses", None)
        if addresses is not None:
            # Delete existing addresses (cast entity_id to str for VARCHAR column)
            await self.db.execute(
                Address.__table__.delete().where(
                    (Address.entity_id == str(employee.id)) & 
                    (Address.entity_type == employee.person_type)
                )
            )
            # Add new addresses (cast entity_id to str)
            for address in addresses:
                address_obj = Address(
                    entity_type=employee.person_type,
                    entity_id=str(employee.id),
                    **address.model_dump(exclude={"entity_type", "entity_id"})
                )
                self.db.add(address_obj)
            await self.db.commit()
        
        # Update bank accounts if provided
        bank_accounts = getattr(emp_data, "bank_accounts", None)
        if bank_accounts is not None:
            # Delete existing bank accounts
            await self.db.execute(
                BankAccount.__table__.delete().where(BankAccount.person_id == employee.id)
            )
            # Add new bank accounts
            for bank in bank_accounts:
                bank_dict = bank.model_dump()
                # Ensure account_name is provided
                if not bank_dict.get('account_name'):
                    bank_dict['account_name'] = f"{employee.first_name} {employee.last_name}"
                bank_obj = BankAccount(person_id=employee.id, **bank_dict)
                self.db.add(bank_obj)
            await self.db.commit()
        
        # Update passports if provided
        passports = getattr(emp_data, "passports", None)
        if passports is not None:
            # Delete existing passports
            await self.db.execute(
                Passport.__table__.delete().where(Passport.person_id == employee.id)
            )
            # Add new passports
            for passport in passports:
                passport_obj = Passport(person_id=employee.id, **passport.model_dump())
                self.db.add(passport_obj)
            await self.db.commit()
        
        return await self.get_employee_by_id(employee.id)

    async def update_employee_by_person_id(self, person_id: str, emp_data: EmployeeUpdate) -> EmployeeResponse:
        from sqlalchemy import select
        from sqlalchemy.orm import class_mapper, RelationshipProperty
        from bheem_core.shared.models import Contact, Address
        from bheem_core.modules.hr.core.models import Employee
        
        # Get employee by person_id
        employee = await self.db.get(Employee, person_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found for this person_id")
        
        # Dynamically exclude all relationship fields
        relationship_fields = {
            prop.key for prop in class_mapper(Employee).iterate_properties
            if isinstance(prop, RelationshipProperty)
        }
        update_data = emp_data.model_dump(exclude_unset=True, exclude={"contacts", "addresses", "bank_accounts", "passports", "social_profiles"})
        for field, value in update_data.items():
            if hasattr(employee, field) and field not in relationship_fields:
                current_value = getattr(employee, field, None)
                if current_value == value:
                    if debug:
                        logging.debug(f"Skipping field '{field}': value unchanged ({current_value})")
                    continue
                
                if field == 'employee_code':
                    # Check if another employee already has this code
                    existing_employee = await self.db.execute(
                        select(Employee).where(
                            Employee.employee_code == value,
                            Employee.id != employee.id
                        )
                    )
                    if existing_employee.scalar_one_or_none():
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Employee code '{value}' is already in use by another employee"
                        )
                
                # Log the field update for debugging
                if debug:
                    logging.debug(f"Updating field '{field}': {current_value} -> {value}")
                
                setattr(employee, field, value)
        
        await self.db.commit()
        await self.db.refresh(employee)
        
        # Update contacts if provided
        contacts = getattr(emp_data, "contacts", None)
        if contacts is not None:
            # Delete existing contacts
            await self.db.execute(
                Contact.__table__.delete().where(Contact.person_id == employee.id)
            )
            # Add new contacts
            for contact in contacts:
                contact_obj = Contact(person_id=employee.id, **contact.model_dump())
                self.db.add(contact_obj)
            await self.db.commit()
        
        # Update addresses if provided
        addresses = getattr(emp_data, "addresses", None)
        if addresses is not None:
            # Delete existing addresses - Fixed the WHERE clause (cast entity_id to str)
            await self.db.execute(
                Address.__table__.delete().where(
                    (Address.entity_id == str(employee.id)) & 
                    (Address.entity_type == employee.person_type)
                )
            )
            # Add new addresses (cast entity_id to str)
            for address in addresses:
                address_obj = Address(
                    entity_type=employee.person_type,
                    entity_id=str(employee.id),
                    **address.model_dump(exclude={"entity_type", "entity_id"})
                )
                self.db.add(address_obj)
            await self.db.commit()
        
        return await self.get_employee_by_id(employee.id)

    async def upsert_employee(self, person_data: PersonCreate, employee_data: EmployeeCreate) -> EmployeeResponse:
        person = await self.db.get(Person, employee_data.person_id)

        if not person:
            person = Person(
                **person_data.model_dump(),
                person_type="employee",
                is_active=True
            )
            self.db.add(person)
            await self.db.commit()
            await self.db.refresh(person)
        else:
            if person.person_type != "employee":
                person.person_type = "employee"
                self.db.add(person)
                await self.db.commit()
                await self.db.refresh(person)

        employee = await self.db.get(Employee, person.id)

        if employee:
            update_data = employee_data.model_dump(exclude_unset=True, exclude={"person_id"})
            for field, value in update_data.items():
                setattr(employee, field, value)
            employee.person_type = "employee" 
            self.db.add(employee)
            await self.db.commit()
            await self.db.refresh(employee)
        else:
            employee = Employee(
                id=person.id,
                person_type="employee",
                **employee_data.model_dump(exclude={"person_id"})
            )
            self.db.add(employee)
            await self.db.commit()
            await self.db.refresh(employee)

        return EmployeeResponse.model_validate({**employee.__dict__, "person_id": employee.id})
    async def delete_employee(self, employee_id: str) -> None:
        from bheem_core.shared.models import Address, Contact, BankAccount, Passport, SocialProfile
        from bheem_core.modules.hr.core.models import Employee
        # Fetch the employee
        employee = await self.db.get(Employee, employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Delete related addresses (cast entity_id to str for VARCHAR column)
        await self.db.execute(
            Address.__table__.delete().where(
                (Address.entity_id == str(employee.id)) &
                (Address.entity_type == employee.person_type)
            )
        )
        # Delete related contacts
        await self.db.execute(
            Contact.__table__.delete().where(Contact.person_id == employee.id)
        )
        # Delete related bank accounts
        await self.db.execute(
            BankAccount.__table__.delete().where(BankAccount.person_id == employee.id)
        )
        # Delete related passports
        await self.db.execute(
            Passport.__table__.delete().where(Passport.person_id == employee.id)
        )
        # Delete related social profiles
        await self.db.execute(
            SocialProfile.__table__.delete().where(SocialProfile.person_id == employee.id)
        )
        # Delete the employee
        await self.db.delete(employee)
        await self.db.commit()
    
    async def _publish_employee_created_event(self, employee: Employee):
        # Get primary email from contacts
        primary_email = None
        for contact in employee.contacts:
            if contact.email_primary:
                primary_email = contact.email_primary
                break
        if self.event_bus:
            await self.event_bus.publish(
                "hr.employee_created",
                {
                    "entity_type": "employee",
                    "entity_id": employee.id,
                    "employee_code": employee.employee_code,
                    "department_id": employee.department_id,
                    "email": primary_email,
                    "first_name": getattr(employee, "first_name", None),
                    "last_name": getattr(employee, "last_name", None)
                },
                source_module="hr"
            )
        else:
            print(f"EMPLOYEE CREATED: {employee.employee_code} - {getattr(employee, 'first_name', '')} {getattr(employee, 'last_name', '')} <{primary_email}>")
        # TODO: Implement event publishing when event bus is available

    async def list_persons_employees(self) -> list:
        result = await self.db.execute(select(Person))
        persons = result.scalars().all()
        employees_result = await self.db.execute(select(Employee))
        employees = {e.id: e for e in employees_result.scalars().all()}
        combined = []
        for person in persons:
            emp = employees.get(person.id)
            person_data = PersonResponse.model_validate(person)
            if emp:
                emp_dict = emp.__dict__.copy()
                emp_dict['person_id'] = emp.id  # Add person_id for Pydantic schema
                employee_data = EmployeeResponse.model_validate(emp_dict)
            else:
                employee_data = None
            combined.append({
                "person": person_data.model_dump(),
                "employee": employee_data.model_dump() if employee_data else None
            })
        return combined

    # Contact Methods
    async def list_contacts(self, person_id: str) -> list:
        result = await self.db.execute(
            select(Contact).where(Contact.person_id == person_id, Contact.is_active == True)
        )
        return [ContactResponse.model_validate(c) for c in result.scalars().all()]

    async def create_contact(self, person_id: str, contact_data: ContactCreate) -> ContactResponse:
        contact = Contact(person_id=person_id, **contact_data.model_dump())
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return ContactResponse.model_validate(contact)

    async def update_contact(self, contact_id: str, contact_data: ContactCreate) -> ContactResponse:
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        for field, value in contact_data.model_dump().items():
            setattr(contact, field, value)
        await self.db.commit()
        await self.db.refresh(contact)
        return ContactResponse.model_validate(contact)

    async def delete_contact(self, contact_id: str) -> None:
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        await self.db.delete(contact)
        await self.db.commit()

    # Enhanced Contact Methods
    async def get_contact_by_id(self, contact_id: str) -> ContactResponse:
        """Get a specific contact by ID"""
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return ContactResponse.model_validate(contact)

    async def get_primary_contact(self, person_id: str) -> ContactResponse:
        """Get the primary contact for a person"""
        result = await self.db.execute(
            select(Contact).where(
                Contact.person_id == person_id,
                Contact.is_active == True,
                Contact.email_primary.isnot(None)
            ).order_by(Contact.created_at)
        )
        contact = result.scalars().first()
        if not contact:
            raise HTTPException(status_code=404, detail="Primary contact not found")
        return ContactResponse.model_validate(contact)

    async def search_contacts(self, email: str = None, phone: str = None, person_id: str = None, is_active: bool = True) -> list:
        """Search contacts by email, phone, or person ID"""
        from sqlalchemy import or_
        
        query = select(Contact)
        filters = []
        
        if is_active is not None:
            filters.append(Contact.is_active == is_active)
        
        if person_id:
            filters.append(Contact.person_id == person_id)
        
        if email:
            email_filter = or_(
                Contact.email_primary.ilike(f"%{email}%"),
                Contact.email_secondary.ilike(f"%{email}%")
            )
            filters.append(email_filter)
        
        if phone:
            phone_filter = or_(
                Contact.phone_primary.ilike(f"%{phone}%"),
                Contact.phone_secondary.ilike(f"%{phone}%"),
                Contact.phone_mobile.ilike(f"%{phone}%"),
                Contact.phone_work.ilike(f"%{phone}%")
            )
            filters.append(phone_filter)
        
        if filters:
            query = query.where(*filters)
        
        result = await self.db.execute(query)
        contacts = result.scalars().all()
        return [ContactResponse.model_validate(contact) for contact in contacts]

    async def activate_contact(self, contact_id: str) -> ContactResponse:
        """Activate a deactivated contact"""
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        contact.is_active = True
        await self.db.commit()
        await self.db.refresh(contact)
        return ContactResponse.model_validate(contact)

    async def deactivate_contact(self, contact_id: str) -> ContactResponse:
        """Deactivate a contact (soft delete)"""
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        contact.is_active = False
        await self.db.commit()
        await self.db.refresh(contact)
        return ContactResponse.model_validate(contact)

    async def update_contact_partial(self, contact_id: str, update_data: dict) -> ContactResponse:
        """Partially update a contact with only the provided fields"""
        contact = await self.db.get(Contact, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Update only provided fields
        for field, value in update_data.items():
            if hasattr(contact, field):
                setattr(contact, field, value)
        
        await self.db.commit()
        await self.db.refresh(contact)
        return ContactResponse.model_validate(contact)

    async def create_bulk_contacts(self, person_id: str, contacts_data: list) -> list:
        """Create multiple contacts for a person"""
        created_contacts = []
        
        for contact_data in contacts_data:
            if isinstance(contact_data, dict):
                contact = Contact(person_id=person_id, **contact_data)
            else:
                contact = Contact(person_id=person_id, **contact_data.model_dump())
            self.db.add(contact)
            created_contacts.append(contact)
        
        await self.db.commit()
        
        # Refresh all contacts
        for contact in created_contacts:
            await self.db.refresh(contact)
        
        return [ContactResponse.model_validate(contact) for contact in created_contacts]

    # Address Methods
    async def list_addresses(self, person_id: str, entity_type: str = "employee") -> list:
        result = await self.db.execute(
            select(Address).where(Address.entity_id == str(person_id), Address.entity_type == entity_type, Address.is_active == True)
        )
        return [AddressResponse.model_validate(a) for a in result.scalars().all()]

    async def create_address(self, person_id: str, address_data: AddressCreate, entity_type: str = "employee") -> AddressResponse:
        # Ensure entity_id is always a string for compatibility with VARCHAR columns
        address = Address(entity_type=entity_type, entity_id=str(person_id), **address_data.model_dump())
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        return AddressResponse.model_validate(address)

    async def update_address(self, address_id: str, address_data: AddressCreate) -> AddressResponse:
        address = await self.db.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        for field, value in address_data.model_dump().items():
            setattr(address, field, value)
        await self.db.commit()
        await self.db.refresh(address)
        return AddressResponse.model_validate(address)

    async def delete_address(self, address_id: str) -> None:
        address = await self.db.get(Address, address_id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        await self.db.delete(address)
        await self.db.commit()

    # Bank Account Methods
    async def list_bank_accounts(self, person_id: str) -> list:
        result = await self.db.execute(
            select(BankAccount).where(BankAccount.person_id == person_id)
        )
        return [BankAccountResponse.model_validate(b) for b in result.scalars().all()]

    async def create_bank_account(self, person_id: str, bank_data: BankAccountCreate) -> BankAccountResponse:
        # Get person info to use as account name if not provided
        person = await self.db.get(Person, person_id)
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        
        bank_dict = bank_data.model_dump()
        # Ensure account_name is provided
        if not bank_dict.get('account_name'):
            bank_dict['account_name'] = f"{person.first_name} {person.last_name}"
            
        bank_account = BankAccount(person_id=person_id, **bank_dict)
        self.db.add(bank_account)
        await self.db.commit()
        await self.db.refresh(bank_account)
        return BankAccountResponse.model_validate(bank_account)

    async def update_bank_account(self, bank_account_id: str, bank_data: BankAccountCreate) -> BankAccountResponse:
        bank_account = await self.db.get(BankAccount, bank_account_id)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        for field, value in bank_data.model_dump().items():
            setattr(bank_account, field, value)
        await self.db.commit()
        await self.db.refresh(bank_account)
        return BankAccountResponse.model_validate(bank_account)

    async def delete_bank_account(self, bank_account_id: str) -> None:
        bank_account = await self.db.get(BankAccount, bank_account_id)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        await self.db.delete(bank_account)
        await self.db.commit()

    # Passport Methods
    async def list_passports(self, person_id: str) -> list:
        result = await self.db.execute(
            select(Passport).where(Passport.person_id == person_id)
        )
        return [PassportResponse.model_validate(p) for p in result.scalars().all()]

    async def create_passport(self, person_id: str, passport_data: PassportCreate) -> PassportResponse:
        passport = Passport(person_id=person_id, **passport_data.model_dump())
        self.db.add(passport)
        await self.db.commit()
        await self.db.refresh(passport)
        return PassportResponse.model_validate(passport)

    async def update_passport(self, passport_id: str, passport_data: PassportCreate) -> PassportResponse:
        passport = await self.db.get(Passport, passport_id)
        if not passport:
            raise HTTPException(status_code=404, detail="Passport not found")
        for field, value in passport_data.model_dump().items():
            setattr(passport, field, value)
        await self.db.commit()
        await self.db.refresh(passport)
        return PassportResponse.model_validate(passport)

    async def delete_passport(self, passport_id: str) -> None:
        passport = await self.db.get(Passport, passport_id)
        if not passport:
            raise HTTPException(status_code=404, detail="Passport not found")
        await self.db.delete(passport)
        await self.db.commit()

    # Lookup CRUD Methods
    async def create_lookup(self, data):
        from bheem_core.shared.models import Lookup, LookupType
        from bheem_core.shared.schemas import LookupCreate, LookupUpdate, LookupResponse, LookupTypeSchema
        exists = await self.db.execute(select(Lookup).where(Lookup.code == data.code))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Lookup code already exists")
        lookup = Lookup(
            type=data.type.value if hasattr(data.type, 'value') else data.type,
            code=data.code,
            name=data.name,
            description=data.description,
            is_active=data.is_active if data.is_active is not None else True
        )
        self.db.add(lookup)
        await self.db.commit()
        await self.db.refresh(lookup)
        return LookupResponse.model_validate(lookup)

    async def get_lookup(self, lookup_id: str):
        from bheem_core.shared.models import Lookup
        from bheem_core.shared.schemas import LookupResponse
        lookup = await self.db.get(Lookup, lookup_id)
        if not lookup:
            raise HTTPException(status_code=404, detail="Lookup not found")
        return LookupResponse.model_validate(lookup)

    async def list_lookups(self, type: str = None):
        from bheem_core.shared.models import Lookup
        from bheem_core.shared.schemas import LookupResponse
        query = select(Lookup)
        if type:
            query = query.where(Lookup.type == type)
        result = await self.db.execute(query)
        lookups = result.scalars().all()
        return [LookupResponse.model_validate(l) for l in lookups]

    async def update_lookup(self, lookup_id: str, data):
        from bheem_core.shared.models import Lookup
        from bheem_core.shared.schemas import LookupUpdate, LookupResponse
        lookup = await self.db.get(Lookup, lookup_id)
        if not lookup:
            raise HTTPException(status_code=404, detail="Lookup not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lookup, field, value)
        await self.db.commit()
        await self.db.refresh(lookup)
        return LookupResponse.model_validate(lookup)

    async def delete_lookup(self, lookup_id: str) -> None:
        from bheem_core.shared.models import Lookup
        lookup = await self.db.get(Lookup, lookup_id)
        if not lookup:
            raise HTTPException(status_code=404, detail="Lookup not found")
        await self.db.delete(lookup)
        await self.db.commit()

    # Job Requisition CRUD Methods
    async def create_job_requisition(self, data: JobRequisitionCreate):
        from bheem_core.modules.hr.core.models import JobRequisition, JobRequisitionSkill
        job_req_dict = data.model_dump(exclude={"skills"})
        job_req = JobRequisition(**job_req_dict)
        self.db.add(job_req)
        await self.db.commit()
        await self.db.refresh(job_req)
        # Insert skill references
        for skill_id in data.skills:
            skill_obj = JobRequisitionSkill(
                job_requisition_id=job_req.id,
                skill_id=skill_id  
            )
            self.db.add(skill_obj)
        await self.db.commit()
        return JobRequisitionResponse(
            id=job_req.id,
            job_title=job_req.job_title,
            department_id=job_req.department_id,
            hiring_manager_id=job_req.hiring_manager_id,
            company_id=job_req.company_id,
            number_of_openings=job_req.number_of_openings,
            job_type_id=job_req.job_type_id,
            location=job_req.location,
            salary_min=job_req.salary_min,
            salary_max=job_req.salary_max,
            requisition_date=job_req.requisition_date,
            job_description=job_req.job_description,
            experience_required=job_req.experience_required,
            is_active=job_req.is_active,
            skills=data.skills
        )

    async def get_job_requisition(self, job_req_id: str):
        from bheem_core.modules.hr.core.models import JobRequisition
        from bheem_core.modules.hr.core.schemas import JobRequisitionResponse
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(JobRequisition).options(selectinload(JobRequisition.skills)).where(JobRequisition.id == job_req_id)
        )
        job_req = result.scalar_one_or_none()
        if not job_req:
            raise HTTPException(status_code=404, detail="Job requisition not found")
        job_req_dict = job_req.__dict__.copy()
        job_req_dict.pop("_sa_instance_state", None)
        job_req_dict["skills"] = [s.skill for s in getattr(job_req, "skills", [])]
        return JobRequisitionResponse.model_validate(job_req_dict)
    # async def get_job_requisition(self, job_req_id: str):
    #     from sqlalchemy.orm import selectinload, load_only

    #     try:
    #         result = await self.db.execute(
    #             select(JobRequisition)
    #             .options(
    #                 selectinload(JobRequisition.skills).load_only("id", "skill_id")
    #             )
    #             .where(JobRequisition.id == job_req_id)
    #         )
    #         job_req = result.scalar_one_or_none()

    #         if not job_req:
    #             raise HTTPException(status_code=404, detail="Job requisition not found")

    #         skill_ids = [s.skill_id for s in job_req.skills]

    #         return JobRequisitionResponse(
    #             id=job_req.id,
    #             job_title=job_req.job_title,
    #             department_id=job_req.department_id,
    #             hiring_manager_id=job_req.hiring_manager_id,
    #             company_id=job_req.company_id,
    #             number_of_openings=job_req.number_of_openings,
    #             job_type_id=job_req.job_type_id,
    #             location=job_req.location,
    #             salary_min=job_req.salary_min,
    #             salary_max=job_req.salary_max,
    #             requisition_date=job_req.requisition_date,
    #             job_description=job_req.job_description,
    #             experience_required=job_req.experience_required,
    #             is_active=job_req.is_active,
    #             skills=skill_ids
    #         )
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Error retrieving job requisition: {str(e)}")


    async def delete_job_requisition(self, job_req_id: str) -> None:
        from bheem_core.modules.hr.core.models import JobRequisition
        job_req = await self.db.get(JobRequisition, job_req_id)
        if not job_req:
            raise HTTPException(status_code=404, detail="Job requisition not found")
        await self.db.delete(job_req)
        await self.db.commit()
        
   
    async def update_job_requisition(self, requisition_id: UUID, data: JobRequisitionUpdate):
        from bheem_core.modules.hr.core.models import JobRequisition, JobRequisitionSkill
        from sqlalchemy import select, delete
        from sqlalchemy.orm import selectinload
        from uuid import UUID  # <-- Add this import to ensure UUID is defined

        # Fetch the existing requisition
        result = await self.db.execute(
            select(JobRequisition)
            .options(selectinload(JobRequisition.skills))
            .where(JobRequisition.id == requisition_id)
        )
        job_req = result.scalars().first()

        if not job_req:
            raise HTTPException(status_code=404, detail="Job requisition not found")

        # Update basic fields
        update_fields = data.model_dump(exclude_unset=True, exclude={"skills"})
        for field, value in update_fields.items():
            setattr(job_req, field, value)

        # Handle skills if provided
        if data.skills is not None:
            # Clear existing skills
            await self.db.execute(
                delete(JobRequisitionSkill).where(JobRequisitionSkill.job_requisition_id == requisition_id)
            )
            # Add new skills
            for skill_id in data.skills:
                new_skill = JobRequisitionSkill(
                    job_requisition_id=requisition_id,
                    skill_id=UUID(str(skill_id))  # Safe casting
                )
                self.db.add(new_skill)

        await self.db.commit()
        await self.db.refresh(job_req)

        # Return updated data
        return JobRequisitionResponse(
            id=job_req.id,
            job_title=job_req.job_title,
            department_id=job_req.department_id,
            hiring_manager_id=job_req.hiring_manager_id,
            company_id=job_req.company_id,
            number_of_openings=job_req.number_of_openings,
            job_type_id=job_req.job_type_id,
            location=job_req.location,
            salary_min=job_req.salary_min,
            salary_max=job_req.salary_max,
            requisition_date=job_req.requisition_date,
            job_description=job_req.job_description,
            experience_required=job_req.experience_required,
            is_active=job_req.is_active,
            skills=[s.skill_id for s in job_req.skills]
        )

    async def list_job_requisitions(
    self,
    is_active: bool = None,
    department_id: str = None,
    job_type_id: str = None,
    hiring_manager_id: str = None
    ):
        from bheem_core.modules.hr.core.models import JobRequisition, JobRequisitionSkill
        from bheem_core.modules.hr.core.schemas import JobRequisitionResponse
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Eager-load both skills and their skill (Lookup)
        query = select(JobRequisition).options(
            selectinload(JobRequisition.skills).selectinload(JobRequisitionSkill.skill)
        )
        
        if is_active is not None:
            query = query.where(JobRequisition.is_active == is_active)
        if department_id is not None:
            query = query.where(JobRequisition.department_id == department_id)
        if job_type_id is not None:
            query = query.where(JobRequisition.job_type_id == job_type_id)
        if hiring_manager_id is not None:
            query = query.where(JobRequisition.hiring_manager_id == hiring_manager_id)

        result = await self.db.execute(query)
        job_reqs = result.scalars().all()

        job_req_responses = []
        for j in job_reqs:
            job_req_responses.append(
                JobRequisitionResponse(
                    id=j.id,
                    job_title=j.job_title,
                    department_id=j.department_id,
                    hiring_manager_id=j.hiring_manager_id,
                    company_id=j.company_id,
                    number_of_openings=j.number_of_openings,
                    job_type_id=j.job_type_id,
                    location=j.location,
                    salary_min=j.salary_min,
                    salary_max=j.salary_max,
                    requisition_date=j.requisition_date,
                    job_description=j.job_description,
                    experience_required=j.experience_required,
                    is_active=j.is_active,
                    skills=[s.skill.id for s in j.skills if s.skill]  # return only IDs
                )
            )

        return job_req_responses
    
    # Candidate Methods
    async def create_candidate(self, data: CandidateCreate):
        # Validate and extract person data
        try:
            person_obj = PersonCreate.model_validate(data.person)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid person object: {e}")

        person_data = person_obj.model_dump(exclude={"contacts", "addresses", "bank_accounts", "passports", "social_profiles"})
        first_name = person_data.get("first_name")
        last_name = person_data.get("last_name")

        if not first_name or not str(first_name).strip():
            raise HTTPException(status_code=400, detail="Person must have a non-blank 'first_name'.")
        if not last_name or not str(last_name).strip():
            raise HTTPException(status_code=400, detail="Person must have a non-blank 'last_name'.")

        # Build candidate data
        candidate_data = person_data.copy()
        for field in [
            "applied_position_id", "application_date", "notice_period", "interview_availability",
            "skills_matched", "recruiter_assigned", "offer_letter_signed", "id_proof_submitted",
            "educational_documents", "status"
        ]:
            if hasattr(data, field):
                candidate_data[field] = getattr(data, field)

        if "application_date" not in candidate_data or candidate_data["application_date"] is None:
            candidate_data["application_date"] = date.today()

        candidate_data["person_type"] = "candidate"
        candidate_data["is_active"] = True

        # Create and persist candidate
        candidate = Candidate(**candidate_data)
        self.db.add(candidate)
        await self.db.commit()
        await self.db.refresh(candidate)

        # Related objects
        for rel, cls, exclude in [
            ("contacts", Contact, {}),
            ("addresses", Address, {"entity_type", "entity_id"}),
            ("bank_accounts", BankAccount, {}),
            ("passports", Passport, {}),
            ("social_profiles", SocialProfile, {})
        ]:
            for obj in getattr(person_obj, rel, []) or []:
                kwargs = obj.model_dump(exclude=exclude) if exclude else obj.model_dump()
                if rel == "addresses":
                    kwargs["entity_type"] = "candidate"
                    kwargs["entity_id"] = str(candidate.id)
                else:
                    kwargs["person_id"] = candidate.id
                self.db.add(cls(**kwargs))
        await self.db.commit()

        # Resume attachment
        resume_schema = None
        if hasattr(data, "resume") and data.resume:
            resume_data = data.resume.model_dump() if hasattr(data.resume, 'model_dump') else dict(data.resume)
            file_url = resume_data.get('file_url')
            description = resume_data.get('description', 'resume')
            filename = resume_data.get('filename') or (os.path.basename(file_url) if file_url else "resume.pdf")
            original_filename = resume_data.get('original_filename', filename)
            file_path = resume_data.get('file_path', file_url)

            resume_schema = ResumeAttachmentCreate(
                file_url=file_url,
                description=description,
                filename=filename,
                original_filename=original_filename,
                file_path=file_path
            )

            self.db.add(Attachment(
                entity_type="candidate",
                entity_id=str(candidate.id),
                file_url=file_url,
                description=description,
                filename=filename,
                original_filename=original_filename,
                file_path=file_path
            ))
            await self.db.commit()

        # Prepare response
        result = await self.db.execute(select(Contact).where(Contact.person_id == candidate.id))
        contacts_data = [ContactResponse.model_validate(c) for c in result.scalars().all()]

        result = await self.db.execute(
            select(Address).where(
                Address.entity_type == "candidate",
                Address.entity_id == str(candidate.id)
            )
        )
        addresses_data = [AddressResponse.model_validate(a) for a in result.scalars().all()]

        result = await self.db.execute(select(BankAccount).where(BankAccount.person_id == candidate.id))
        bank_accounts_data = [BankAccountResponse.model_validate(b) for b in result.scalars().all()]

        result = await self.db.execute(select(Passport).where(Passport.person_id == candidate.id))
        passports_data = [PassportResponse.model_validate(p) for p in result.scalars().all()]

        result = await self.db.execute(select(SocialProfile).where(SocialProfile.person_id == candidate.id))
        social_profiles_data = [SocialProfileResponse.model_validate(s) for s in result.scalars().all()]

        person = await self.db.get(Person, candidate.id)
        person_response = PersonResponse(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name,
            middle_name=person.middle_name,
            preferred_name=person.preferred_name,
            title=person.title,
            suffix=person.suffix,
            date_of_birth=person.date_of_birth,
            gender=person.gender,
            marital_status=person.marital_status,
            nationality=person.nationality,
            blood_group=getattr(person, 'blood_group', None),
            person_type=person.person_type,
            is_active=person.is_active,
            company_id=str(getattr(person, 'company_id', None)) if getattr(person, 'company_id', None) is not None else None,
            contacts=contacts_data,
            addresses=addresses_data,
            bank_accounts=bank_accounts_data,
            passports=passports_data,
            social_profiles=social_profiles_data
        )

        return CandidateResponse(
            id=candidate.id,
            person=person_response,
            applied_position_id=candidate.applied_position_id,
            application_date=candidate.application_date,
            notice_period=candidate.notice_period,
            interview_availability=candidate.interview_availability,
            skills_matched=candidate.skills_matched,
            recruiter_assigned=candidate.recruiter_assigned,
            offer_letter_signed=candidate.offer_letter_signed,
            id_proof_submitted=candidate.id_proof_submitted,
            educational_documents=candidate.educational_documents,
            status=candidate.status,
            resume=resume_schema
        )

    async def get_candidate(self, candidate_id: str):
        candidate = await self.db.get(Candidate, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Fetch all related objects for the response
        from bheem_core.shared.schemas import ContactResponse, AddressResponse, BankAccountResponse, PassportResponse
        from bheem_core.modules.hr.core.schemas import SocialProfileResponse
        
        contacts_result = await self.db.execute(
            select(Contact).where(Contact.person_id == candidate.id)
        )
        contacts_data = [ContactResponse.model_validate(c) for c in contacts_result.scalars().all()]
        
        addresses_result = await self.db.execute(
            select(Address).where(Address.entity_type == "candidate", Address.entity_id == str(candidate.id))
        )
        addresses_data = [AddressResponse.model_validate(a) for a in addresses_result.scalars().all()]
        
        # Skip bank accounts for now to avoid column errors
        bank_accounts_data = []
        
        passports_result = await self.db.execute(
            select(Passport).where(Passport.person_id == candidate.id)
        )
        passports_data = [PassportResponse.model_validate(p) for p in passports_result.scalars().all()]
        
        social_profiles_result = await self.db.execute(
            select(SocialProfile).where(SocialProfile.person_id == candidate.id)
        )
        social_profiles_data = [SocialProfileResponse.model_validate(s) for s in social_profiles_result.scalars().all()]
        
        # Get the person object
        person = await self.db.get(Person, candidate.id)
        
        # Build PersonResponse manually
        person_response = PersonResponse(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name,
            middle_name=person.middle_name,
            preferred_name=person.preferred_name,
            title=person.title,
            suffix=person.suffix,
            date_of_birth=person.date_of_birth,
            gender=person.gender,
            marital_status=person.marital_status,
            nationality=person.nationality,
            blood_group=getattr(person, 'blood_group', None),
            person_type=person.person_type,
            is_active=person.is_active,
            company_id=str(getattr(person, 'company_id', None)) if getattr(person, 'company_id', None) is not None else None,
            contacts=contacts_data,
            addresses=addresses_data,
            bank_accounts=bank_accounts_data,
            passports=passports_data,
            social_profiles=social_profiles_data
        )
        
        # Fetch resume attachment
        result = await self.db.execute(
            select(Attachment).where(Attachment.entity_type == "candidate", Attachment.entity_id == str(candidate.id))
        )
        attachment = result.scalars().first()
        resume = ResumeAttachmentCreate.model_validate(attachment) if attachment else None
        
        return CandidateResponse(
            id=candidate.id,
            person=person_response,
            applied_position_id=candidate.applied_position_id,
            application_date=candidate.application_date,
            notice_period=candidate.notice_period,
            interview_availability=candidate.interview_availability,
            skills_matched=candidate.skills_matched,
            recruiter_assigned=candidate.recruiter_assigned,
            offer_letter_signed=candidate.offer_letter_signed,
            id_proof_submitted=candidate.id_proof_submitted,
            educational_documents=candidate.educational_documents,
            status=candidate.status,
            resume=resume
        )



    async def update_candidate(self, candidate_id: str, data: CandidateUpdate):
        from bheem_core.modules.hr.core.models import Candidate
        from bheem_core.shared.models import Person, Contact, Address, BankAccount, Passport, SocialProfile, Attachment
        from bheem_core.modules.hr.core.schemas import ResumeAttachmentCreate, CandidateResponse
        from bheem_core.shared.schemas import ContactResponse, AddressResponse, BankAccountResponse, PassportResponse
        from bheem_core.modules.hr.core.schemas import SocialProfileResponse
        
        candidate = await self.db.get(Candidate, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        # Update candidate-specific fields
        update_data = data.model_dump(exclude_unset=True, exclude={"person", "resume"})
        for key, value in update_data.items():
            if hasattr(candidate, key):
                setattr(candidate, key, value)
        
        await self.db.commit()
        await self.db.refresh(candidate)
        
        # Update person and related data if provided
        if data.person:
            person = await self.db.get(Person, candidate.id)
            if not person:
                raise HTTPException(status_code=404, detail="Person record not found for candidate")
            
            # Update person basic fields (excluding related objects)
            person_data = data.person.model_dump(exclude_unset=True, exclude={"contacts", "addresses", "bank_accounts", "passports", "social_profiles"})
            for key, value in person_data.items():
                if hasattr(person, key):
                    setattr(person, key, value)
            
            await self.db.commit()
            await self.db.refresh(person)
            
            # Update contacts if provided
            if hasattr(data.person, 'contacts') and data.person.contacts is not None:
                # Delete existing contacts
                await self.db.execute(
                    Contact.__table__.delete().where(Contact.person_id == candidate.id)
                )
                # Add new contacts
                for contact_data in data.person.contacts:
                    contact_obj = Contact(person_id=candidate.id, **contact_data.model_dump())
                    self.db.add(contact_obj)
                await self.db.commit()
            
            # Update addresses if provided
            if hasattr(data.person, 'addresses') and data.person.addresses is not None:
                # Delete existing addresses
                await self.db.execute(
                    Address.__table__.delete().where(
                        (Address.entity_id == str(candidate.id)) & 
                        (Address.entity_type == "candidate")
                    )
                )
                # Add new addresses
                for address_data in data.person.addresses:
                    address_obj = Address(
                        entity_type="candidate",
                        entity_id=str(candidate.id),
                        **address_data.model_dump(exclude={"entity_type", "entity_id"})
                    )
                    self.db.add(address_obj)
                await self.db.commit()
            
            # Update bank accounts if provided
            if hasattr(data.person, 'bank_accounts') and data.person.bank_accounts is not None:
                # Delete existing bank accounts
                await self.db.execute(
                    BankAccount.__table__.delete().where(BankAccount.person_id == candidate.id)
                )
                # Add new bank accounts
                for bank_data in data.person.bank_accounts:
                    bank_dict = bank_data.model_dump()
                    if not bank_dict.get('account_name'):
                        bank_dict['account_name'] = f"{person.first_name} {person.last_name}"
                    bank_obj = BankAccount(person_id=candidate.id, **bank_dict)
                    self.db.add(bank_obj)
                await self.db.commit()
            
            # Update passports if provided
            if hasattr(data.person, 'passports') and data.person.passports is not None:
                # Delete existing passports
                await self.db.execute(
                    Passport.__table__.delete().where(Passport.person_id == candidate.id)
                )
                # Add new passports
                for passport_data in data.person.passports:
                    passport_obj = Passport(person_id=candidate.id, **passport_data.model_dump())
                    self.db.add(passport_obj)
                await self.db.commit()
            
            # Update social profiles if provided
            if hasattr(data.person, 'social_profiles') and data.person.social_profiles is not None:
                # Delete existing social profiles
                await self.db.execute(
                    SocialProfile.__table__.delete().where(SocialProfile.person_id == candidate.id)
                )
                # Add new social profiles
                for profile_data in data.person.social_profiles:
                    profile_obj = SocialProfile(person_id=candidate.id, **profile_data.model_dump())
                    self.db.add(profile_obj)
                await self.db.commit()
        
        # Update resume if provided
        if data.resume:
            result = await self.db.execute(
                select(Attachment).where(Attachment.entity_type == "candidate", Attachment.entity_id == str(candidate.id))
            )
            attachment = result.scalars().first()
            if attachment:
                for key, value in data.resume.model_dump(exclude_unset=True).items():
                    setattr(attachment, key, value)
                self.db.add(attachment)
            else:
                attachment = Attachment(
                    entity_type="candidate",
                    entity_id=str(candidate.id),
                    file_url=data.resume.file_url,
                    description=data.resume.description or "resume"
                )
                self.db.add(attachment)
            await self.db.commit()
        
        # Return updated candidate with complete data
        return await self.get_candidate(candidate_id)

    async def delete_candidate(self, candidate_id: str):
        from bheem_core.modules.hr.core.models import Candidate
        from bheem_core.shared.models import Person, Attachment
        candidate = await self.db.get(Candidate, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        person = await self.db.get(Person, candidate_id)
        # Delete resume attachment
        await self.db.execute(
            Attachment.__table__.delete().where(Attachment.entity_type == "candidate", Attachment.entity_id == candidate_id)
        )
        await self.db.delete(candidate)
        if person:
            await self.db.delete(person)
        await self.db.commit()
        return None

    async def list_candidates(self):
        result = await self.db.execute(select(Candidate))
        candidates = result.scalars().all()
        responses = []
        
        for candidate in candidates:
            # Fetch all related objects for each candidate
            from bheem_core.shared.schemas import ContactResponse, AddressResponse, BankAccountResponse, PassportResponse
            from bheem_core.modules.hr.core.schemas import SocialProfileResponse
            
            contacts_result = await self.db.execute(
                select(Contact).where(Contact.person_id == candidate.id)
            )
            contacts_data = [ContactResponse.model_validate(c) for c in contacts_result.scalars().all()]
            
            addresses_result = await self.db.execute(
                select(Address).where(Address.entity_type == "candidate", Address.entity_id == str(candidate.id))
            )
            addresses_data = [AddressResponse.model_validate(a) for a in addresses_result.scalars().all()]
            
            # Skip bank accounts for now to avoid column errors
            bank_accounts_data = []
            
            passports_result = await self.db.execute(
                select(Passport).where(Passport.person_id == candidate.id)
            )
            passports_data = [PassportResponse.model_validate(p) for p in passports_result.scalars().all()]
            
            social_profiles_result = await self.db.execute(
                select(SocialProfile).where(SocialProfile.person_id == candidate.id)
            )
            social_profiles_data = [SocialProfileResponse.model_validate(s) for s in social_profiles_result.scalars().all()]
            
            # Get the person object
            person = await self.db.get(Person, candidate.id)
            
            # Build PersonResponse manually
            person_response = PersonResponse(
                id=person.id,
                first_name=person.first_name,
                last_name=person.last_name,
                middle_name=person.middle_name,
                preferred_name=person.preferred_name,
                title=person.title,
                suffix=person.suffix,
                date_of_birth=person.date_of_birth,
                gender=person.gender,
                marital_status=person.marital_status,
                nationality=person.nationality,
                blood_group=getattr(person, 'blood_group', None),
                person_type=person.person_type,
                is_active=person.is_active,
                company_id=str(getattr(person, 'company_id', None)) if getattr(person, 'company_id', None) is not None else None,
                contacts=contacts_data,
                addresses=addresses_data,
                bank_accounts=bank_accounts_data,
                passports=passports_data,
                social_profiles=social_profiles_data
            )
        
            # Fetch resume attachment
            attachment_result = await self.db.execute(
                select(Attachment).where(Attachment.entity_type == "candidate", Attachment.entity_id == str(candidate.id))
            )
            attachment = attachment_result.scalars().first()
            resume = ResumeAttachmentCreate.model_validate(attachment) if attachment else None
            
            candidate_response = CandidateResponse(
                id=candidate.id,
                person=person_response,
                applied_position_id=candidate.applied_position_id,
                application_date=candidate.application_date,
                notice_period=candidate.notice_period,
                interview_availability=candidate.interview_availability,
                skills_matched=candidate.skills_matched,
                recruiter_assigned=candidate.recruiter_assigned,
                offer_letter_signed=candidate.offer_letter_signed,
                id_proof_submitted=candidate.id_proof_submitted,
                educational_documents=candidate.educational_documents,
                status=candidate.status,
                resume=resume
            )
            responses.append(candidate_response)
        
        return responses

    async def update_onboarding_checklist(self, checklist_id: str, checklist_data):
        from bheem_core.modules.hr.core.models import OnboardingChecklist
        from bheem_core.modules.hr.core.schemas import OnboardingChecklistResponse
        from fastapi import HTTPException
        checklist = await self.db.get(OnboardingChecklist, checklist_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Onboarding checklist not found")
        # Defensive: handle both dict and Pydantic model
        if hasattr(checklist_data, "model_dump"):
            update_data = checklist_data.model_dump(exclude_unset=True)
        elif isinstance(checklist_data, dict):
            update_data = checklist_data
        else:
            raise ValueError("Invalid input type for onboarding checklist update")
        for field, value in update_data.items():
            setattr(checklist, field, value)
        await self.db.commit()
        await self.db.refresh(checklist)
        return OnboardingChecklistResponse.model_validate(checklist)
    
    async def delete_onboarding_checklist(self, checklist_id: str) -> None:
        from bheem_core.modules.hr.core.models import OnboardingChecklist
        checklist = await self.db.get(OnboardingChecklist, checklist_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Onboarding checklist not found")
        await self.db.delete(checklist)
        await self.db.commit()
        return None

    # Enhanced Bank Account Methods
    async def get_bank_account_by_id(self, bank_account_id: str) -> BankAccountResponse:
        """Get a specific bank account by ID"""
        bank_account = await self.db.get(BankAccount, bank_account_id)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        return BankAccountResponse.model_validate(bank_account)

    async def search_bank_accounts(self, account_number: str = None, bank_name: str = None, person_id: str = None, is_active: bool = True) -> list:
        """Search bank accounts by account number, bank name, or person ID"""
        from sqlalchemy import or_, and_
        
        query = select(BankAccount)
        filters = []
        
        if is_active is not None:
            filters.append(BankAccount.is_active == is_active)
        
        if person_id:
            filters.append(BankAccount.person_id == person_id)
        
        if account_number:
            filters.append(BankAccount.account_number.ilike(f"%{account_number}%"))
        
        if bank_name:
            filters.append(BankAccount.bank_name.ilike(f"%{bank_name}%"))
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await self.db.execute(query)
        bank_accounts = result.scalars().all()
        return [BankAccountResponse.model_validate(bank_account) for bank_account in bank_accounts]

    async def activate_bank_account(self, bank_account_id: str) -> BankAccountResponse:
        """Activate a deactivated bank account"""
        bank_account = await self.db.get(BankAccount, bank_account_id)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        
        bank_account.is_active = True
        await self.db.commit()
        await self.db.refresh(bank_account)
        return BankAccountResponse.model_validate(bank_account)

    # ===================== SALARY STRUCTURE METHODS =====================
    
    # (Removed duplicate legacy create_salary_structure method)

    async def get_salary_structure(self, structure_id: UUID) -> "SalaryStructureRead":
        """Get salary structure by ID"""
        from bheem_core.modules.hr.core.models.hr_models import SalaryStructure
        from sqlalchemy.orm import selectinload
        
        query = select(SalaryStructure).options(selectinload(SalaryStructure.components)).where(SalaryStructure.id == structure_id)
        result = await self.db.execute(query)
        structure = result.scalar_one_or_none()
        
        if not structure:
            raise HTTPException(status_code=404, detail="Salary structure not found")
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import SalaryStructureRead
        return SalaryStructureRead.model_validate(structure, from_attributes=True)

    async def list_salary_structures(self, employee_id: UUID = None) -> List["SalaryStructureRead"]:
        """List salary structures with optional employee filter"""
        from bheem_core.modules.hr.core.models.hr_models import SalaryStructure
        from sqlalchemy.orm import selectinload
        
        query = select(SalaryStructure).options(selectinload(SalaryStructure.components))
        if employee_id:
            query = query.where(SalaryStructure.employee_id == employee_id)
        
        result = await self.db.execute(query)
        structures = result.scalars().all()
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import SalaryStructureRead
        return [SalaryStructureRead.model_validate(s, from_attributes=True) for s in structures]



    async def delete_salary_structure(self, structure_id: UUID) -> None:
        """Delete salary structure"""
        from bheem_core.modules.hr.core.models.hr_models import SalaryStructure
        
        structure = await self.db.get(SalaryStructure, structure_id)
        if not structure:
            raise HTTPException(status_code=404, detail="Salary structure not found")
        
        await self.db.delete(structure)
        await self.db.commit()
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("salary_structure.deleted", {
                "structure_id": str(structure_id)
            })

    # ===================== SALARY COMPONENT METHODS =====================
    


    async def get_salary_component(self, component_id: UUID) -> "SalaryComponentRead":
        """Get salary component by ID"""
        from bheem_core.modules.hr.core.models.hr_models import SalaryComponent
        
        component = await self.db.get(SalaryComponent, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="Salary component not found")
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import SalaryComponentRead
        return SalaryComponentRead.model_validate(component, from_attributes=True)

    async def list_salary_components(self, structure_id: UUID = None) -> List["SalaryComponentRead"]:
        """List salary components with optional structure filter"""
        from bheem_core.modules.hr.core.models.hr_models import SalaryComponent
        
        query = select(SalaryComponent)
        if structure_id:
            query = query.where(SalaryComponent.structure_id == structure_id)
        
        result = await self.db.execute(query)
        components = result.scalars().all()
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import SalaryComponentRead
        return [SalaryComponentRead.model_validate(c, from_attributes=True) for c in components]

    # async def update_salary_component(self, component_id: UUID, component_data: "SalaryComponentCreate") -> "SalaryComponentRead":
    #     """Update salary component"""
    #     from bheem_core.modules.hr.core.models.hr_models import SalaryComponent
        
    #     component = await self.db.get(SalaryComponent, component_id)
    #     if not component:
    #         raise HTTPException(status_code=404, detail="Salary component not found")
        
    #     component.name = component_data.name
    #     component.component_type = component_data.component_type
    #     component.amount = component_data.amount
    #     component.taxable = component_data.taxable
        
    #     await self.db.commit()
    #     await self.db.refresh(component)
        
    #     # Fire event
    #     if self.event_bus:
    #         await self.event_bus.publish("salary_component.updated", {
    #             "component_id": str(component.id),
    #             "structure_id": str(component.structure_id)
    #         })
        
    #     from bheem_core.modules.hr.core.schemas.hr_schemas import SalaryComponentRead
    #     return SalaryComponentRead.model_validate(component, from_attributes=True)

    # async def delete_salary_component(self, component_id: UUID) -> None:
    #     """Delete salary component"""
    #     from bheem_core.modules.hr.core.models.hr_models import SalaryComponent
        
    #     component = await self.db.get(SalaryComponent, component_id)
    #     if not component:
    #         raise HTTPException(status_code=404, detail="Salary component not found")
        
    #     await self.db.delete(component)
    #     await self.db.commit()
        
    #     # Fire event
    #     if self.event_bus:
    #         await self.event_bus.publish("salary_component.deleted", {
    #             "component_id": str(component_id)
    #         })

    # ===================== PAYROLL RUN METHODS =====================
    
    async def create_payroll_run(self, payroll_data: "PayrollRunCreate") -> "PayrollRunRead":
        """Create a new payroll run"""
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        
        payroll = PayrollRun(
            month=payroll_data.month,
            status=payroll_data.status,
            processed_by=payroll_data.processed_by
        )
        
        self.db.add(payroll)
        await self.db.commit()
        await self.db.refresh(payroll)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("payroll_run.created", {
                "payroll_id": str(payroll.id),
                "month": payroll.month,
                "status": payroll.status
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayrollRunRead
        return PayrollRunRead.model_validate(payroll, from_attributes=True)

    async def get_payroll_run(self, payroll_id: UUID) -> "PayrollRunRead":
        """Get payroll run by ID"""
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        
        payroll = await self.db.get(PayrollRun, payroll_id)
        if not payroll:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayrollRunRead
        return PayrollRunRead.model_validate(payroll, from_attributes=True)

    async def list_payroll_runs(self) -> List["PayrollRunRead"]:
        """List all payroll runs"""
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        
        result = await self.db.execute(select(PayrollRun))
        payrolls = result.scalars().all()
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayrollRunRead
        return [PayrollRunRead.model_validate(p, from_attributes=True) for p in payrolls]

    async def update_payroll_run(self, payroll_id: UUID, payroll_data: "PayrollRunCreate") -> "PayrollRunRead":
        """Update payroll run"""
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        
        payroll = await self.db.get(PayrollRun, payroll_id)
        if not payroll:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        payroll.month = payroll_data.month
        payroll.status = payroll_data.status
        payroll.processed_by = payroll_data.processed_by
        
        await self.db.commit()
        await self.db.refresh(payroll)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("payroll_run.updated", {
                "payroll_id": str(payroll.id),
                "status": payroll.status
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayrollRunRead
        return PayrollRunRead.model_validate(payroll, from_attributes=True)

    async def delete_payroll_run(self, payroll_id: UUID) -> None:
        """Delete payroll run"""
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun
        
        payroll = await self.db.get(PayrollRun, payroll_id)
        if not payroll:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        await self.db.delete(payroll)
        await self.db.commit()
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("payroll_run.deleted", {
                "payroll_id": str(payroll_id)
            })

    async def process_payroll(self, payroll_id: UUID) -> "PayrollRunRead":
        """Process payroll run - business logic for payroll calculation"""
        from bheem_core.modules.hr.core.models.hr_models import PayrollRun, Employee, SalaryStructure, Payslip
        from sqlalchemy.orm import selectinload
        
        payroll = await self.db.get(PayrollRun, payroll_id)
        if not payroll:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        if payroll.status != "Draft":
            raise HTTPException(status_code=400, detail="Only draft payroll runs can be processed")
        
        # Get all active employees with salary structures
        query = select(Employee).join(SalaryStructure).where(
            SalaryStructure.is_active == True
        ).options(selectinload(Employee.salary_structures))
        
        result = await self.db.execute(query)
        employees = result.scalars().all()
        
        # Process each employee
        for employee in employees:
            active_structure = next((s for s in employee.salary_structures if s.is_active), None)
            if active_structure:
                await self._create_payslip_for_employee(payroll.id, employee, active_structure)
        
        payroll.status = "Processed"
        await self.db.commit()
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("payroll_run.processed", {
                "payroll_id": str(payroll.id),
                "employee_count": len(employees)
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayrollRunRead
        return PayrollRunRead.model_validate(payroll, from_attributes=True)

    async def _create_payslip_for_employee(self, payroll_id: UUID, employee, salary_structure):
        """Helper method to create payslip for an employee"""
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        from decimal import Decimal
        
        # Calculate earnings and deductions from components
        total_earnings = Decimal('0.00')
        total_deductions = Decimal('0.00')
        
        for component in salary_structure.components:
            if component.component_type in ['BASIC', 'ALLOWANCE', 'BONUS']:
                total_earnings += component.amount
            elif component.component_type == 'DEDUCTION':
                total_deductions += component.amount
        
        net_pay = total_earnings - total_deductions
        
        payslip = Payslip(
            employee_id=employee.id,
            payroll_run_id=payroll_id,
            total_earnings=total_earnings,
            total_deductions=total_deductions,
            net_pay=net_pay
        )
        
        self.db.add(payslip)

    # ===================== PAYSLIP METHODS =====================
    
    async def create_payslip(self, payslip_data: "PayslipCreate") -> "PayslipRead":
        """Create a new payslip"""
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        
        payslip = Payslip(
            employee_id=payslip_data.employee_id,
            payroll_run_id=payslip_data.payroll_run_id,
            total_earnings=payslip_data.total_earnings,
            total_deductions=payslip_data.total_deductions,
            net_pay=payslip_data.net_pay,
            attachment_id=payslip_data.attachment_id
        )
        
        self.db.add(payslip)
        await self.db.commit()
        await self.db.refresh(payslip)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("payslip.created", {
                "payslip_id": str(payslip.id),
                "employee_id": str(payslip.employee_id),
                "net_pay": float(payslip.net_pay)
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayslipRead
        return PayslipRead.model_validate(payslip, from_attributes=True)

    async def get_payslip(self, payslip_id: UUID) -> "PayslipRead":
        """Get payslip by ID"""
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        
        payslip = await self.db.get(Payslip, payslip_id)
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayslipRead
        return PayslipRead.model_validate(payslip, from_attributes=True)

    async def list_payslips(self, employee_id: UUID = None, payroll_run_id: UUID = None) -> List["PayslipRead"]:
        """List payslips with optional filters"""
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        
        query = select(Payslip)
        if employee_id:
            query = query.where(Payslip.employee_id == employee_id)
        if payroll_run_id:
            query = query.where(Payslip.payroll_run_id == payroll_run_id)
        
        result = await self.db.execute(query)
        payslips = result.scalars().all()
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayslipRead
        return [PayslipRead.model_validate(p, from_attributes=True) for p in payslips]

    async def update_payslip(self, payslip_id: UUID, payslip_data: "PayslipCreate") -> "PayslipRead":
        """Update payslip"""
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        
        payslip = await self.db.get(Payslip, payslip_id)
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        
        payslip.total_earnings = payslip_data.total_earnings
        payslip.total_deductions = payslip_data.total_deductions
        payslip.net_pay = payslip_data.net_pay
        payslip.attachment_id = payslip_data.attachment_id
        
        await self.db.commit()
        await self.db.refresh(payslip)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("payslip.updated", {
                "payslip_id": str(payslip.id),
                "employee_id": str(payslip.employee_id)
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import PayslipRead
        return PayslipRead.model_validate(payslip, from_attributes=True)

    async def delete_payslip(self, payslip_id: UUID) -> None:
        """Delete payslip"""
        from bheem_core.modules.hr.core.models.hr_models import Payslip
        
        payslip = await self.db.get(Payslip, payslip_id)
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        
        await self.db.delete(payslip)
        await self.db.commit()
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("payslip.deleted", {
                "payslip_id": str(payslip_id)
            })


    async def get_attendance(self, attendance_id: UUID) -> "AttendanceRead":
        """Get attendance by ID"""
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        
        attendance = await self.db.get(Attendance, attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceRead
        return AttendanceRead.model_validate(attendance, from_attributes=True)

    
    async def list_attendance(
        self, employee_id: UUID = None, limit: int = 10, offset: int = 0
    ) -> dict:
        from bheem_core.modules.hr.core.models import Attendance

        filters = []
        if employee_id:
            filters.append(Attendance.employee_id == employee_id)

        base_query = select(Attendance)
        if filters:
            base_query = base_query.where(and_(*filters))

        # Total count query
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated data query
        data_query = base_query.offset(offset).limit(limit)
        result = await self.db.execute(data_query)
        records = result.scalars().all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "records": [AttendanceRead.model_validate(r, from_attributes=True) for r in records]
        } 


    async def delete_attendance(self, attendance_id: UUID) -> None:
        """Delete attendance record"""
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        
        attendance = await self.db.get(Attendance, attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        await self.db.delete(attendance)
        await self.db.commit()
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("attendance.deleted", {
                "attendance_id": str(attendance_id)
            })


    async def clock_in(self, employee_id: UUID, check_in_time=None) -> "AttendanceRead":
        """Clock in employee for today"""
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        from datetime import date, datetime
        
        today = date.today()
        check_in = check_in_time or datetime.now().time()
        
        # Check if already clocked in
        existing_query = select(Attendance).where(
            and_(
                Attendance.employee_id == employee_id,
                Attendance.date == today
            )
        )
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            if existing.check_in:
                raise HTTPException(status_code=400, detail="Already clocked in for today")
            existing.check_in = check_in
            existing.status = "Present"
            await self.db.commit()
            await self.db.refresh(existing)
            attendance = existing
        else:
            attendance = Attendance(
                employee_id=employee_id,
                date=today,
                check_in=check_in,
                status="Present"
            )
            self.db.add(attendance)
            await self.db.commit()
            await self.db.refresh(attendance)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("attendance.clock_in", {
                "attendance_id": str(attendance.id),
                "employee_id": str(employee_id),
                "check_in_time": check_in.isoformat()
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceRead
        return AttendanceRead.model_validate(attendance, from_attributes=True)

    async def clock_out(self, employee_id: UUID, check_out_time=None) -> "AttendanceRead":
        """Clock out employee for today"""
        from bheem_core.modules.hr.core.models.hr_models import Attendance
        from datetime import date, datetime
        
        today = date.today()
        check_out = check_out_time or datetime.now().time()
        
        # Find today's attendance
        query = select(Attendance).where(
            and_(
                Attendance.employee_id == employee_id,
                Attendance.date == today
            )
        )
        result = await self.db.execute(query)
        attendance = result.scalar_one_or_none()
        
        if not attendance:
            raise HTTPException(status_code=404, detail="No attendance record found for today")
        
        if not attendance.check_in:
            raise HTTPException(status_code=400, detail="Cannot clock out without clocking in first")
        
        if attendance.check_out:
            raise HTTPException(status_code=400, detail="Already clocked out for today")
        
        attendance.check_out = check_out
        await self.db.commit()
        await self.db.refresh(attendance)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("attendance.clock_out", {
                "attendance_id": str(attendance.id),
                "employee_id": str(employee_id),
                "check_out_time": check_out.isoformat()
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import AttendanceRead
        return AttendanceRead.model_validate(attendance, from_attributes=True)

    # ===================== LEAVE REQUEST METHODS =====================
    
    

    async def get_leave_request(self, leave_id: UUID) -> "LeaveRequestRead":
        """Get leave request by ID"""
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        
        leave_request = await self.db.get(LeaveRequest, leave_id)
        if not leave_request:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import LeaveRequestRead
        return LeaveRequestRead.model_validate(leave_request, from_attributes=True)

    # async def list_leave_requests(self, employee_id: UUID = None, status: str = None) -> List["LeaveRequestRead"]:
    #     """List leave requests with optional filters"""
    #     from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        
    #     query = select(LeaveRequest)
    #     filters = []
        
    #     if employee_id:
    #         filters.append(LeaveRequest.employee_id == employee_id)
    #     if status:
    #         filters.append(LeaveRequest.status == status)
        
    #     if filters:
    #         query = query.where(and_(*filters))
        
    #     result = await self.db.execute(query)
    #     leave_requests = result.scalars().all()
        
    #     from bheem_core.modules.hr.core.schemas.hr_schemas import LeaveRequestRead
    #     return [LeaveRequestRead.model_validate(lr, from_attributes=True) for lr in leave_requests]

    async def update_leave_request(self, leave_id: UUID, leave_data: "LeaveRequestCreate") -> "LeaveRequestRead":
        """Update leave request"""
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        
        leave_request = await self.db.get(LeaveRequest, leave_id)
        if not leave_request:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        if leave_request.status in ["APPROVED", "REJECTED"]:
            raise HTTPException(status_code=400, detail="Cannot modify approved or rejected leave request")
        
        leave_request.leave_type = leave_data.leave_type
        leave_request.start_date = leave_data.start_date
        leave_request.end_date = leave_data.end_date
        leave_request.reason = leave_data.reason
        leave_request.status = leave_data.status
        
        await self.db.commit()
        await self.db.refresh(leave_request)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("leave_request.updated", {
                "leave_id": str(leave_request.id),
                "employee_id": str(leave_request.employee_id),
                "status": leave_request.status.value
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import LeaveRequestRead
        return LeaveRequestRead.model_validate(leave_request, from_attributes=True)

    async def delete_leave_request(self, leave_id: UUID) -> None:
        """Delete leave request"""
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        
        leave_request = await self.db.get(LeaveRequest, leave_id)
        if not leave_request:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        if leave_request.status == "APPROVED":
            raise HTTPException(status_code=400, detail="Cannot delete approved leave request")
        
        await self.db.delete(leave_request)
        await self.db.commit()
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("leave_request.deleted", {
                "leave_id": str(leave_id)
            })

    async def approve_leave_request(self, leave_id: UUID, approver_id: UUID) -> "LeaveRequestRead":
        """Approve leave request"""
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        from bheem_core.shared.models import LeaveStatusEnum
        
        leave_request = await self.db.get(LeaveRequest, leave_id)
        if not leave_request:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        if leave_request.status != LeaveStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Only pending requests can be approved")
        
        leave_request.status = LeaveStatusEnum.APPROVED
        await self.db.commit()
        await self.db.refresh(leave_request)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("leave_request.approved", {
                "leave_id": str(leave_request.id),
                "employee_id": str(leave_request.employee_id),
                "approver_id": str(approver_id)
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import LeaveRequestRead
        return LeaveRequestRead.model_validate(leave_request, from_attributes=True)

    async def reject_leave_request(self, leave_id: UUID, rejector_id: UUID, reason: str = None) -> "LeaveRequestRead":
        """Reject leave request"""
        from bheem_core.modules.hr.core.models.hr_models import LeaveRequest
        from bheem_core.shared.models import LeaveStatusEnum
        
        leave_request = await self.db.get(LeaveRequest, leave_id)
        if not leave_request:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        if leave_request.status != LeaveStatusEnum.PENDING:
            raise HTTPException(status_code=400, detail="Only pending requests can be rejected")
        
        leave_request.status = LeaveStatusEnum.REJECTED
        if reason:
            leave_request.reason = f"{leave_request.reason}\n\nRejection reason: {reason}"
        
        await self.db.commit()
        await self.db.refresh(leave_request)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("leave_request.rejected", {
                "leave_id": str(leave_request.id),
                "employee_id": str(leave_request.employee_id),
                "rejector_id": str(rejector_id),
                "reason": reason
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import LeaveRequestRead
        return LeaveRequestRead.model_validate(leave_request, from_attributes=True)

    # ===================== REPORT LOG METHODS =====================
    
    async def create_report_log(self, report_data: "ReportLogCreate") -> "ReportLogRead":
        """Create report log entry"""
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        
        report_log = ReportLog(
            report_name=report_data.report_name,
            generated_by=report_data.generated_by,
            parameters=report_data.parameters,
            attachment_id=report_data.attachment_id
        )
        
        self.db.add(report_log)
        await self.db.commit()
        await self.db.refresh(report_log)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("report_log.created", {
                "log_id": str(report_log.id),
                "report_name": report_log.report_name,
                "generated_by": str(report_log.generated_by)
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import ReportLogRead
        return ReportLogRead.model_validate(report_log, from_attributes=True)

    async def get_report_log(self, log_id: UUID) -> "ReportLogRead":
        """Get report log by ID"""
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        
        report_log = await self.db.get(ReportLog, log_id)
        if not report_log:
            raise HTTPException(status_code=404, detail="Report log not found")
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import ReportLogRead
        return ReportLogRead.model_validate(report_log, from_attributes=True)

    async def list_report_logs(self, report_name: str = None) -> List["ReportLogRead"]:
        """List report logs with optional filter"""
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        
        query = select(ReportLog)
        if report_name:
            query = query.where(ReportLog.report_name.ilike(f"%{report_name}%"))
        
        result = await self.db.execute(query)
        report_logs = result.scalars().all()
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import ReportLogRead
        return [ReportLogRead.model_validate(rl, from_attributes=True) for rl in report_logs]

    async def update_report_log(self, log_id: UUID, report_data: "ReportLogCreate") -> "ReportLogRead":
        """Update report log"""
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        
        report_log = await self.db.get(ReportLog, log_id)
        if not report_log:
            raise HTTPException(status_code=404, detail="Report log not found")
        
        report_log.report_name = report_data.report_name
        report_log.parameters = report_data.parameters
        report_log.attachment_id = report_data.attachment_id
        
        await self.db.commit()
        await self.db.refresh(report_log)
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("report_log.updated", {
                "log_id": str(report_log.id),
                "report_name": report_log.report_name
            })
        
        from bheem_core.modules.hr.core.schemas.hr_schemas import ReportLogRead
        return ReportLogRead.model_validate(report_log, from_attributes=True)

    async def delete_report_log(self, log_id: UUID) -> None:
        """Delete report log"""
        from bheem_core.modules.hr.core.models.hr_models import ReportLog
        
        report_log = await self.db.get(ReportLog, log_id)
        if not report_log:
            raise HTTPException(status_code=404, detail="Report log not found")
        
        await self.db.delete(report_log)
        await self.db.commit()
        
        # Fire event
        if self.event_bus:
            await self.event_bus.publish("report_log.deleted", {
                "log_id": str(log_id)
            })

    # ==================== SALARY STRUCTURE METHODS ====================
    # (Removed duplicate legacy create_salary_structure method)

    async def get_salary_structure(self, structure_id: str):
        """Get salary structure by ID"""
        from ..models.hr_models import SalaryStructure
        from sqlalchemy.orm import selectinload
        
        query = select(SalaryStructure).where(SalaryStructure.id == structure_id).options(selectinload(SalaryStructure.components))
        result = await self.db.execute(query)
        structure = result.scalar_one_or_none()
        
        if not structure:
            raise HTTPException(status_code=404, detail="Salary structure not found")
        
        return structure

    async def list_salary_structures(self):
        """List all salary structures"""
        from ..models.hr_models import SalaryStructure
        from sqlalchemy.orm import selectinload
        
        query = select(SalaryStructure).options(selectinload(SalaryStructure.components))
        result = await self.db.execute(query)
        return result.scalars().all()



    async def delete_salary_structure(self, structure_id: str):
        """Delete salary structure"""
        structure = await self.get_salary_structure(structure_id)
        await self.db.delete(structure)
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.salary_structure.deleted", {"structure_id": structure_id})

    # ==================== SALARY COMPONENT METHODS ====================


    async def get_salary_component(self, component_id: str):
        """Get salary component by ID"""
        from ..models.hr_models import SalaryComponent
        
        component = await self.db.get(SalaryComponent, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="Salary component not found")
        
        return component

    async def list_salary_components(self):
        """List all salary components"""
        from ..models.hr_models import SalaryComponent
        
        query = select(SalaryComponent)
        result = await self.db.execute(query)
        return result.scalars().all()

    # async def update_salary_component(self, component_id: str, data):
    #     """Update salary component"""
    #     component = await self.get_salary_component(component_id)
        
    #     for field, value in data.model_dump(exclude={"id"}).items():
    #         setattr(component, field, value)
        
    #     await self.db.commit()
    #     await self.db.refresh(component)
        
    #     # Trigger event
    #     if self.event_bus:
    #         await self.event_bus.emit("hr.salary_component.updated", {"component_id": component.id})
        
    #     return component

    async def delete_salary_component(self, component_id: str):
        """Delete salary component"""
        component = await self.get_salary_component(component_id)
        await self.db.delete(component)
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.salary_component.deleted", {"component_id": component_id})

    # ==================== PAYROLL RUN METHODS ====================
    async def create_payroll_run(self, data):
        """Create payroll run"""
        from ..models.hr_models import PayrollRun
        
        payroll_run = PayrollRun(**data.model_dump())
        self.db.add(payroll_run)
        await self.db.commit()
        await self.db.refresh(payroll_run)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.payroll_run.created", {"run_id": payroll_run.id})
        
        return payroll_run

    async def get_payroll_run(self, run_id: str):
        """Get payroll run by ID"""
        from ..models.hr_models import PayrollRun
        
        payroll_run = await self.db.get(PayrollRun, run_id)
        if not payroll_run:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        return payroll_run

    async def list_payroll_runs(self):
        """List all payroll runs"""
        from ..models.hr_models import PayrollRun
        
        query = select(PayrollRun)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_payroll_run(self, run_id: str, data):
        """Update payroll run"""
        payroll_run = await self.get_payroll_run(run_id)
        
        for field, value in data.model_dump(exclude={"id"}).items():
            setattr(payroll_run, field, value)
        
        await self.db.commit()
        await self.db.refresh(payroll_run)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.payroll_run.updated", {"run_id": payroll_run.id})
        
        return payroll_run

    async def delete_payroll_run(self, run_id: str):
        """Delete payroll run"""
        payroll_run = await self.get_payroll_run(run_id)
        await self.db.delete(payroll_run)
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.payroll_run.deleted", {"run_id": run_id})

    async def process_payroll(self, run_id: str):
        """Process payroll for a specific run"""
        payroll_run = await self.get_payroll_run(run_id)
        
        if payroll_run.status != "Draft":
            raise HTTPException(status_code=400, detail="Payroll can only be processed from Draft status")
        
        # Generate payslips for all active employees
        from ..models.hr_models import Employee, Payslip, SalaryStructure
        from decimal import Decimal
        
        # Get all active employees
        query = select(Employee).where(Employee.employment_status == "ACTIVE")
        result = await self.db.execute(query)
        employees = result.scalars().all()
        
        for employee in employees:
            # Get employee's salary structure
            structure_query = select(SalaryStructure).where(
                SalaryStructure.employee_id == employee.id,
                SalaryStructure.is_active == True
            ).options(selectinload(SalaryStructure.components))
            
            structure_result = await self.db.execute(structure_query)
            salary_structure = structure_result.scalar_one_or_none()
            
            if salary_structure:
                # Calculate totals
                total_earnings = Decimal('0.00')
                total_deductions = Decimal('0.00')
                
                for component in salary_structure.components:
                    if component.component_type in ['BASIC', 'ALLOWANCE', 'BONUS']:
                        total_earnings += component.amount
                    elif component.component_type == 'DEDUCTION':
                        total_deductions += component.amount
                
                net_pay = total_earnings - total_deductions
                
                # Create payslip
                payslip = Payslip(
                    employee_id=employee.id,
                    payroll_run_id=payroll_run.id,
                    total_earnings=total_earnings,
                    total_deductions=total_deductions,
                    net_pay=net_pay
                )
                self.db.add(payslip)
        
        # Update payroll run status
        payroll_run.status = "Processed"
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.payroll_run.processed", {"run_id": run_id})
        
        return payroll_run

    # ==================== PAYSLIP METHODS ====================
    async def create_payslip(self, data):
        """Create payslip"""
        from ..models.hr_models import Payslip
        
        payslip = Payslip(**data.model_dump())
        self.db.add(payslip)
        await self.db.commit()
        await self.db.refresh(payslip)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.payslip.created", {"payslip_id": payslip.id})
        
        return payslip

    async def get_payslip(self, payslip_id: str):
        """Get payslip by ID"""
        from ..models.hr_models import Payslip
        
        payslip = await self.db.get(Payslip, payslip_id)
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        
        return payslip

    async def list_payslips(self):
        """List all payslips"""
        from ..models.hr_models import Payslip
        
        query = select(Payslip)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_payslip(self, payslip_id: str, data):
        """Update payslip"""
        payslip = await self.get_payslip(payslip_id)
        
        for field, value in data.model_dump(exclude={"id"}).items():
            setattr(payslip, field, value)
        
        await self.db.commit()
        await self.db.refresh(payslip)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.payslip.updated", {"payslip_id": payslip.id})
        
        return payslip

    async def delete_payslip(self, payslip_id: str):
        """Delete payslip"""
        payslip = await self.get_payslip(payslip_id)
        await self.db.delete(payslip)
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.payslip.deleted", {"payslip_id": payslip_id})

    # ==================== ATTENDANCE METHODS ====================
    async def create_attendance(self, data):
        """Create attendance record"""
        from ..models.hr_models import Attendance
        
        attendance = Attendance(**data.model_dump())
        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.attendance.created", {"attendance_id": attendance.id})
        
        return attendance

    async def get_attendance(self, attendance_id: str):
        """Get attendance by ID"""
        from ..models.hr_models import Attendance
        
        attendance = await self.db.get(Attendance, attendance_id)
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        
        return attendance

    # async def list_attendance(self):
    #     """List all attendance records"""
    #     from ..models.hr_models import Attendance
        
    #     query = select(Attendance)
    #     result = await self.db.execute(query)
    #     return result.scalars().all()

    async def update_attendance(self, attendance_id: str, data):
        """Update attendance record"""
        attendance = await self.get_attendance(attendance_id)
        
        for field, value in data.model_dump(exclude={"id"}).items():
            setattr(attendance, field, value)
        
        await self.db.commit()
        await self.db.refresh(attendance)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.attendance.updated", {"attendance_id": attendance.id})
        
        return attendance

    async def delete_attendance(self, attendance_id: str):
        """Delete attendance record"""
        attendance = await self.get_attendance(attendance_id)
        await self.db.delete(attendance)
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.attendance.deleted", {"attendance_id": attendance_id})

    async def mark_attendance(self, employee_id: str, check_in: bool = True):
        """Mark employee check-in or check-out"""
        from ..models.hr_models import Attendance
        from datetime import datetime, date, time
        
        today = date.today()
        current_time = datetime.now().time()
        
        # Check if attendance record exists for today
        query = select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.date == today
        )
        result = await self.db.execute(query)
        attendance = result.scalar_one_or_none()
        
        if not attendance:
            # Create new attendance record
            attendance = Attendance(
                employee_id=employee_id,
                date=today,
                check_in=current_time if check_in else None,
                status="Present"
            )
            self.db.add(attendance)
        else:
            # Update existing record
            if check_in and not attendance.check_in:
                attendance.check_in = current_time
            elif not check_in and not attendance.check_out:
                attendance.check_out = current_time
        
        await self.db.commit()
        await self.db.refresh(attendance)
        
        # Trigger event
        event_type = "hr.attendance.check_in" if check_in else "hr.attendance.check_out"
        if self.event_bus:
            await self.event_bus.emit(event_type, {"employee_id": employee_id, "attendance_id": attendance.id})
        
        return attendance

    # ==================== LEAVE REQUEST METHODS ====================
    async def create_leave_request(self, data):
        from datetime import timedelta
        employee_id = data.employee_id

        # Step 1: Get employee
        result = await self.db.execute(select(Employee).where(Employee.id == employee_id))
        employee = result.scalar_one_or_none()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Step 2: Determine probation
        today = data.start_date
        probation_end = employee.hire_date + timedelta(days=90)
        is_probation = today <= probation_end

        # Step 3: Create LeaveRequest
        leave_request = LeaveRequest(**data.model_dump())
        self.db.add(leave_request)
        await self.db.commit()
        await self.db.refresh(leave_request)

        # Step 4: Deduction logic
        leave_days = (data.end_date - data.start_date).days + 1
        deduction_per_day = Decimal(2 if is_probation else 1)
        total_deduction_days = leave_days * deduction_per_day

        # Step 5: Get or create PayrollRun
        payroll_month = today.strftime("%Y-%m")
        payroll_run_query = select(PayrollRun).where(
            PayrollRun.month == payroll_month,
            PayrollRun.company_id == employee.company_id
        )
        run_result = await self.db.execute(payroll_run_query)
        payroll_run = run_result.scalar_one_or_none()

        if not payroll_run:
            payroll_run = PayrollRun(
                month=payroll_month,
                status="Draft",
                company_id=employee.company_id
            )
            self.db.add(payroll_run)
            await self.db.commit()
            await self.db.refresh(payroll_run)

        # Step 6: Get or create Payslip
        payslip_query = select(Payslip).where(
            Payslip.employee_id == employee_id,
            Payslip.payroll_run_id == payroll_run.id
        )
        payslip_result = await self.db.execute(payslip_query)
        payslip = payslip_result.scalar_one_or_none()

        if not payslip:
            payslip = Payslip(
                employee_id=employee_id,
                payroll_run_id=payroll_run.id,
                total_earnings=Decimal(0),
                total_deductions=Decimal(0),
                net_pay=Decimal(0)
            )
            self.db.add(payslip)
            await self.db.commit()
            await self.db.refresh(payslip)

        # Step 7: Apply deduction
        payslip.total_deductions += total_deduction_days
        payslip.net_pay = (payslip.total_earnings or Decimal(0)) - payslip.total_deductions

        await self.db.commit()
        await self.db.refresh(payslip)

        # Step 8: Optional event trigger
        if self.event_bus:
            await self.event_bus.emit("hr.leave_request.created", {"leave_id": leave_request.id})

        return leave_request


    async def get_leave_request(self, leave_id: str):
        """Get leave request by ID"""
        from ..models.hr_models import LeaveRequest
        
        leave_request = await self.db.get(LeaveRequest, leave_id)
        if not leave_request:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        return leave_request

    # async def list_leave_requests(self):
    #     """List all leave requests"""
    #     from ..models.hr_models import LeaveRequest
        
    #     query = select(LeaveRequest)
    #     result = await self.db.execute(query)
    #     return result.scalars().all()

    async def update_leave_request(self, leave_id: str, data):
        """Update leave request"""
        leave_request = await self.get_leave_request(leave_id)
        
        for field, value in data.model_dump(exclude={"id"}).items():
            setattr(leave_request, field, value)
        
        await self.db.commit()
        await self.db.refresh(leave_request)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.leave_request.updated", {"leave_id": leave_request.id})
        
        return leave_request

    async def delete_leave_request(self, leave_id: str):
        """Delete leave request"""
        leave_request = await self.get_leave_request(leave_id)
        await self.db.delete(leave_request)
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.leave_request.deleted", {"leave_id": leave_id})

    async def approve_leave_request(self, leave_id: str, approved_by: str):
        """Approve leave request"""
        from bheem_core.shared.models import LeaveStatusEnum
        
        leave_request = await self.get_leave_request(leave_id)
        leave_request.status = LeaveStatusEnum.APPROVED
        
        await self.db.commit()
        await self.db.refresh(leave_request)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.leave_request.approved", {
                "leave_id": leave_id,
                "employee_id": leave_request.employee_id,
                "approved_by": approved_by
            })
        
        return leave_request

    async def reject_leave_request(self, leave_id: str, rejected_by: str, reason: str = None):
        """Reject leave request"""
        from bheem_core.shared.models import LeaveStatusEnum
        
        leave_request = await self.get_leave_request(leave_id)
        leave_request.status = LeaveStatusEnum.REJECTED
        
        await self.db.commit()
        await self.db.refresh(leave_request)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.leave_request.rejected", {
                "leave_id": leave_id,
                "employee_id": leave_request.employee_id,
                "rejected_by": rejected_by,
                "reason": reason
            })
        
        return leave_request

    # ==================== REPORT LOG METHODS ====================
    async def create_report_log(self, data):
        """Create report log"""
        from ..models.hr_models import ReportLog
        
        report_log = ReportLog(**data.model_dump())
        self.db.add(report_log)
        await self.db.commit()
        await self.db.refresh(report_log)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.report_log.created", {"log_id": report_log.id})
        
        return report_log

    async def get_report_log(self, log_id: str):
        """Get report log by ID"""
        from ..models.hr_models import ReportLog
        
        report_log = await self.db.get(ReportLog, log_id)
        if not report_log:
            raise HTTPException(status_code=404, detail="Report log not found")
        
        return report_log

    async def list_report_logs(self):
        """List all report logs"""
        from ..models.hr_models import ReportLog
        
        query = select(ReportLog)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_report_log(self, log_id: str, data):
        """Update report log"""
        report_log = await self.get_report_log(log_id)
        
        for field, value in data.model_dump(exclude={"id"}).items():
            setattr(report_log, field, value)
        
        await self.db.commit()
        await self.db.refresh(report_log)
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.report_log.updated", {"log_id": report_log.id})
        
        return report_log

    async def delete_report_log(self, log_id: str):
        """Delete report log"""
        report_log = await self.get_report_log(log_id)
        await self.db.delete(report_log)
        await self.db.commit()
        
        # Trigger event
        if self.event_bus:
            await self.event_bus.emit("hr.report_log.deleted", {"log_id": log_id})

    async def deactivate_bank_account(self, bank_account_id: str) -> BankAccountResponse:
        """Deactivate a bank account (soft delete)"""
        bank_account = await self.db.get(BankAccount, bank_account_id)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        
        bank_account.is_active = False
        await self.db.commit()
        await self.db.refresh(bank_account)
        return BankAccountResponse.model_validate(bank_account)

    async def update_bank_account_partial(self, bank_account_id: str, update_data: dict) -> BankAccountResponse:
        """Partially update a bank account with only the provided fields"""
        bank_account = await self.db.get(BankAccount, bank_account_id)
        if not bank_account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        
        # Update only provided fields
        for field, value in update_data.items():
            if hasattr(bank_account, field):
                setattr(bank_account, field, value)
        
        await self.db.commit()
        await self.db.refresh(bank_account)
        return BankAccountResponse.model_validate(bank_account)

    async def get_primary_bank_account(self, person_id: str) -> BankAccountResponse:
        """Get the primary bank account for a person"""
        result = await self.db.execute(
            select(BankAccount).where(
                BankAccount.person_id == person_id,
                BankAccount.is_active == True,
                BankAccount.is_primary == True
            ).order_by(BankAccount.created_at)
        )
        bank_account = result.scalars().first()
        if not bank_account:
            # If no primary account, get the first active account
            result = await self.db.execute(
                select(BankAccount).where(
                    BankAccount.person_id == person_id,
                    BankAccount.is_active == True
                ).order_by(BankAccount.created_at)
            )
            bank_account = result.scalars().first()
        
        if not bank_account:
            raise HTTPException(status_code=404, detail="Primary bank account not found")
        return BankAccountResponse.model_validate(bank_account)

    async def create_bulk_bank_accounts(self, person_id: str, bank_accounts_data: list) -> list:
        """Create multiple bank accounts for a person"""
        created_bank_accounts = []
        
        for bank_account_data in bank_accounts_data:
            if isinstance(bank_account_data, dict):
                bank_account = BankAccount(person_id=person_id, **bank_account_data)
            else:
                bank_account = BankAccount(person_id=person_id, **bank_account_data.model_dump())
            self.db.add(bank_account)
            created_bank_accounts.append(bank_account)
        
        await self.db.commit()
        
        # Refresh all bank accounts
        for bank_account in created_bank_accounts:
            await self.db.refresh(bank_account)
        
        return [BankAccountResponse.model_validate(bank_account) for bank_account in created_bank_accounts]

    async def get_bank_account_stats(self) -> dict:
        """Get statistics about bank accounts"""
        from sqlalchemy import func
        
        try:
            # Total count
            total_result = await self.db.execute(select(func.count(BankAccount.id)))
            total_count = total_result.scalar() or 0
            
            # Active count
            active_result = await self.db.execute(
                select(func.count(BankAccount.id)).where(BankAccount.is_active == True)
            )
            active_count = active_result.scalar() or 0
            
            # Inactive count
            inactive_count = total_count - active_count
            
            # Accounts by bank
            bank_result = await self.db.execute(
                select(BankAccount.bank_name, func.count(BankAccount.id))
                .group_by(BankAccount.bank_name)
                .where(BankAccount.is_active == True)
            )
            by_bank = {bank: count for bank, count in bank_result.fetchall()}
            
            return {
               
                "total": total_count,
                "active": active_count,
                "inactive": inactive_count,
                "by_bank": by_bank
            }
        except Exception as e:
            # Return default stats if there's an error
            return {
                "total": 0,
                "active": 0,
                "inactive": 0,
                "by_bank": {}
            }

    # Interview Methods
    async def create_interview(self, data: InterviewCreate, company_id: str) -> InterviewResponse:
        """Create a new interview for a candidate"""
        import uuid
        from datetime import datetime
        
        # Verify candidate exists
       
        candidate = await self.db.get(Candidate, data.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Verify interviewer exists if specified
        if data.interviewer_id:
            interviewer = await self.db.get(Employee, data.interviewer_id)
            if not interviewer:
                raise HTTPException(status_code=404, detail="Interviewer not found")
        
        # Create interview record
        interview_data = data.model_dump()
        interview_data["id"] = str(uuid.uuid4())
        interview_data["company_id"] = company_id  # Ensure company_id is set
        
        interview = Interview(**interview_data)
        self.db.add(interview)
        await self.db.commit()
        await self.db.refresh(interview)
        
        return InterviewResponse.model_validate(interview)
    
    async def get_interview(self, interview_id: str) -> InterviewResponse:
        """Get a specific interview by ID"""
        interview = await self.db.get(Interview, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        return InterviewResponse.model_validate(interview)
    
    async def update_interview(self, interview_id: str, data: InterviewUpdate) -> InterviewResponse:
        """Update an existing interview"""
        interview = await self.db.get(Interview, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Verify interviewer exists if being updated
        if data.interviewer_id:
            interviewer = await self.db.get(Employee, data.interviewer_id)
            if not interviewer:
                raise HTTPException(status_code=404, detail="Interviewer not found")
        
        # Update interview fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(interview, key, value)
        
        await self.db.commit()
        await self.db.refresh(interview)
        
        return InterviewResponse.model_validate(interview)
    
    async def delete_interview(self, interview_id: str):
        """Delete an interview"""
        interview = await self.db.get(Interview, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        await self.db.delete(interview)
        await self.db.commit()
        return None
    
    
    async def list_interviews(self, candidate_id: str = None) -> List[InterviewResponse]:
        """List interviews with optional filtering by candidate"""
        query = select(Interview)
        
        if candidate_id:
            query = query.where(Interview.candidate_id == candidate_id)
        
        result = await self.db.execute(query)
        interviews = result.scalars().all()
        
        return [InterviewResponse.model_validate(interview) for interview in interviews]
    
    async def schedule_candidate_interview(self, candidate_id: str, data: InterviewCreate) -> InterviewResponse:
        """Schedule an interview for a specific candidate (convenience method)"""
        # Ensure the candidate_id matches
        data.candidate_id = candidate_id
        return await self.create_interview(data)

    def _cast_uuid_fields(self, data: dict, uuid_fields: list):
        """Utility to cast string UUID fields to uuid.UUID or None."""
        import uuid
        for field in uuid_fields:
            val = data.get(field)
            if val == "" or val is None:
                data[field] = None
            elif isinstance(val, str):
                try:
                    data[field] = uuid.UUID(val)
                except Exception:
                    data[field] = None
        return data
    async def list_offers(self, candidate_id: str = None, offer_status: str = None, background_check_status: str = None, is_active: bool = None) -> list['OfferResponse']:
        """List offers with optional filters"""
        from sqlalchemy import select
        from bheem_core.modules.hr.core.models import Offer
        from bheem_core.modules.hr.core.schemas import OfferResponse
        query = select(Offer)
        if candidate_id:
            query = query.where(Offer.candidate_id == candidate_id)
        if offer_status:
            query = query.where(Offer.offer_status == offer_status)
        if background_check_status:
            query = query.where(Offer.background_check_status == background_check_status)
        if is_active is not None:
            query = query.where(Offer.is_active == is_active)
        result = await self.db.execute(query)
        offers = result.scalars().all()
        return [OfferResponse.model_validate(offer) for offer in offers]
    
    async def create_offer(self, data: OfferCreate, company_id: str) -> OfferResponse:
        """Create a new offer for a candidate"""
        from bheem_core.modules.hr.core.models import Offer  # <-- Add this import
        # Verify candidate exists
        candidate = await self.db.get(Candidate, data.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        # Create offer record
        offer_data = data.model_dump()
        offer_data["id"] = str(uuid.uuid4())
        offer_data["company_id"] = company_id  # Ensure company_id is set
        offer = Offer(**offer_data)
        self.db.add(offer)
        await self.db.commit()
        await self.db.refresh(offer)
        return OfferResponse.model_validate(offer)
    
    async def get_offer(self, offer_id: str):
        """Get a specific offer by ID"""
        from bheem_core.modules.hr.core.models import Offer
        from bheem_core.modules.hr.core.schemas import OfferResponse
        offer = await self.db.get(Offer, offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        return OfferResponse.model_validate(offer)
    
    async def update_offer(self, offer_id: str, data) -> 'OfferResponse':
        """Update an existing offer by ID"""
        from bheem_core.modules.hr.core.models import Offer
        from bheem_core.modules.hr.core.schemas import OfferResponse, OfferUpdate
        offer = await self.db.get(Offer, offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        # Defensive: Only update fields provided in the OfferUpdate model
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(offer, field):
                setattr(offer, field, value)
        await self.db.commit()
        await self.db.refresh(offer)
        return OfferResponse.model_validate(offer)
    
    async def delete_offer(self, offer_id: str, reason: Optional[str] = None):
        from bheem_core.modules.hr.core.models import Offer  # Adjust if your Offer model is elsewhere

        offer = await self.db.get(Offer, offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        # Optional: Log or store the reason for auditing (e.g., in an activity log or soft-delete reason)
        # For now, just delete
        await self.db.delete(offer)
        await self.db.commit()

    async def create_onboarding_checklist(self, data):
        from bheem_core.modules.hr.core.models import OnboardingChecklist, Candidate
        from bheem_core.modules.hr.core.schemas import OnboardingChecklistResponse
        from fastapi import HTTPException
        # Defensive: handle both dict and Pydantic model
        if hasattr(data, "model_dump"):
            checklist_data = data.model_dump()
        elif isinstance(data, dict):
            checklist_data = data
        else:
            raise ValueError("Invalid input type for onboarding checklist creation")

        # Check candidate_id exists
        candidate_id = checklist_data.get("candidate_id")
        if not candidate_id:
            raise HTTPException(status_code=400, detail="candidate_id is required")
        candidate = await self.db.get(Candidate, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate with id {candidate_id} does not exist")

        checklist = OnboardingChecklist(**checklist_data)
        self.db.add(checklist)
        await self.db.commit()
        await self.db.refresh(checklist)
        return OnboardingChecklistResponse.model_validate(checklist)

    async def get_onboarding_checklist(self, checklist_id: str):
        from bheem_core.modules.hr.core.models import OnboardingChecklist
        from bheem_core.modules.hr.core.schemas import OnboardingChecklistResponse
        checklist = await self.db.get(OnboardingChecklist, checklist_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Onboarding checklist not found")
        return OnboardingChecklistResponse.model_validate(checklist)

    async def list_onboarding_checklists(self, candidate_id: str = None, company_id: str = None, is_active: bool = None, completion_status: str = None):
        from sqlalchemy import select, and_
        from bheem_core.modules.hr.core.models import OnboardingChecklist
        from bheem_core.modules.hr.core.schemas import OnboardingChecklistResponse
        query = select(OnboardingChecklist)
        filters = []
        if candidate_id:
            filters.append(OnboardingChecklist.candidate_id == candidate_id)
        if company_id:
            filters.append(OnboardingChecklist.company_id == company_id)
        if is_active is not None:
            filters.append(OnboardingChecklist.is_active == is_active)
        # If you have a completion_status column, add filter here. Otherwise, ignore.
        if filters:
            query = query.where(and_(*filters))
        result = await self.db.execute(query)
        checklists = result.scalars().all()
        return [OnboardingChecklistResponse.model_validate(c) for c in checklists]

    async def delete_onboarding_checklist(self, checklist_id: str) -> None:
        from bheem_core.modules.hr.core.models import OnboardingChecklist
        checklist = await self.db.get(OnboardingChecklist, checklist_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Onboarding checklist not found")
        await self.db.delete(checklist)
        await self.db.commit()
        return None


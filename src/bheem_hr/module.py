"""Main HR Module Class"""
from typing import List
import logging

from .core.base_module import BaseERPModule
from .api.v1.routes import (
    employees,
    departments,
    candidates,
    reports,
    lookups,
    address,
    contact,
    passport,
    bank_accounts,
    main_routes,
    job_requisitions,
    interviews,
    offers,
    onboarding,
    salary_structure,
    salary_component,
    payroll_run,
    payslip,
    attendance,
    leave_request,
    report_log,
)
from bheem_hr.config import HREventTypes
from bheem_hr.events.handlers import HREventHandlers

class HRModule(BaseERPModule):
    """Human Resources Management Module"""
    
    def __init__(self):
        super().__init__()
        self._event_handlers = None
    
    @property
    def name(self) -> str:
        return "hr"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def permissions(self) -> List[str]:
        return [
            # Department permissions
            "hr.create_department",
            "hr.update_department",
            "hr.view_department",
            "hr.delete_department",
            
            # Employee permissions
            "hr.create_employee",
            "hr.update_employee",
            "hr.view_employee",
            "hr.delete_employee",
            "hr.activate_employee",
            "hr.terminate_employee",
            
            # Candidate permissions
            "hr.create_candidate",
            "hr.update_candidate",
            "hr.view_candidate",
            "hr.delete_candidate",
            "hr.interview_candidate",
            "hr.hire_candidate",
            
            # Job Requisition permissions
            "hr.create_job_requisition",
            "hr.update_job_requisition",
            "hr.view_job_requisition",
            "hr.delete_job_requisition",
            "hr.manage_job_skills",
            
            # Interview permissions
            "hr.schedule_interview",
            "hr.conduct_interview",
            "hr.view_interview",
            "hr.cancel_interview",
            "hr.add_interview_feedback",
            
            # Offer permissions
            "hr.create_offer",
            "hr.update_offer",
            "hr.view_offer",
            "hr.withdraw_offer",
            "hr.accept_offer",
            "hr.reject_offer",
            
            # Onboarding permissions
            "hr.create_onboarding",
            "hr.update_onboarding",
            "hr.view_onboarding",
            "hr.complete_onboarding_task",
            "hr.manage_onboarding_process",
            
            # Lookup permissions
            "hr.create_lookup",
            "hr.update_lookup",
            "hr.view_lookup",
            "hr.delete_lookup",
            
            # Reporting permissions
            "hr.view_reports",
            "hr.generate_reports",
            "hr.export_data",
            
            # Admin permissions
            "hr.admin_settings",
            "hr.manage_integrations",
            
            # Payroll Management permissions
            "hr.salary_structure.create",
            "hr.salary_structure.read", 
            "hr.salary_structure.update",
            "hr.salary_structure.delete",
            
            "hr.salary_component.create",
            "hr.salary_component.read",
            "hr.salary_component.update", 
            "hr.salary_component.delete",
            
            "hr.payroll_run.create",
            "hr.payroll_run.read",
            "hr.payroll_run.update",
            "hr.payroll_run.delete",
            "hr.payroll_run.process",
            
            "hr.payslip.create",
            "hr.payslip.read",
            "hr.payslip.update",
            "hr.payslip.delete",
            "hr.payslip.generate",
            
            "hr.attendance.create",
            "hr.attendance.read",
            "hr.attendance.update",
            "hr.attendance.delete",
            "hr.attendance.clock_in",
            "hr.attendance.clock_out",
            
            "hr.leave_request.create",
            "hr.leave_request.read",
            "hr.leave_request.update", 
            "hr.leave_request.delete",
            "hr.leave_request.approve",
            "hr.leave_request.reject",
            
            "hr.report_log.create",
            "hr.report_log.read",
            "hr.report_log.update",
            "hr.report_log.delete"
        ]

    def _setup_routes(self) -> None:
        """Setup HR module routes"""
        # Main person routes (should come first for correct precedence)
        self._router.include_router(main_routes.router, prefix="", tags=["Persons"])
        from .api.v1.routes import hr_dashboard, hr_action_item
        self._router.include_router(hr_dashboard.router, prefix="/hr", tags=["HR Dashboard"])
        self._router.include_router(hr_action_item.router, prefix="/action-items", tags=["HR Action Items"])
        
        # Specific module routes
        self._router.include_router(employees.router, prefix="/employees", tags=["Employees"])
        self._router.include_router(departments.router, prefix="/departments", tags=["Departments"])
        self._router.include_router(candidates.router, prefix="/candidates", tags=["Candidates"])
        self._router.include_router(reports.router, prefix="/reports", tags=["Reports"])
        self._router.include_router(lookups.router, prefix="/lookups", tags=["Lookups"])
        self._router.include_router(address.router, prefix="/addresses", tags=["Addresses"])
        self._router.include_router(contact.router, prefix="/contacts", tags=["Contacts"])
        self._router.include_router(passport.router, prefix="/passports", tags=["Passports"])
        self._router.include_router(bank_accounts.router, tags=["Bank Accounts"])
        
        # New API modules
        self._router.include_router(job_requisitions.router, prefix="/job-requisitions", tags=["Job Requisitions"])
        self._router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
        self._router.include_router(offers.router, prefix="/offers", tags=["Offers"])
        self._router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
        
        # Payroll and HR Management modules
        from .api.v1.routes import salary_structure, salary_component, payroll_run, payslip, attendance, leave_request, report_log, hr_action_item
        self._router.include_router(salary_structure.router, prefix="/salary-structures", tags=["Salary Structures"])
        self._router.include_router(salary_component.router, prefix="/salary-components", tags=["Salary Components"])
        self._router.include_router(payroll_run.router, prefix="/payroll-runs", tags=["Payroll Runs"])
        self._router.include_router(payslip.router, prefix="/payslips", tags=["Payslips"])
        self._router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
        self._router.include_router(leave_request.router, prefix="/leave-requests", tags=["Leave Requests"])
        self._router.include_router(report_log.router, prefix="/report-logs", tags=["Report Logs"])
        self._router.include_router(hr_action_item.router, prefix="", tags=["HR Action Items"])
        
        # Add module health endpoint (inherited from base)
        super()._setup_routes()

    async def _subscribe_to_events(self) -> None:
        """Subscribe to events from other modules"""
        if self._event_bus:
            # Listen for auth events
            await self._event_bus.subscribe("auth.user_created", self._handle_user_created)
            await self._event_bus.subscribe("auth.user_deactivated", self._handle_user_deactivated)
            
            # Listen for internal HR events
            await self._event_bus.subscribe(HREventTypes.EMPLOYEE_CREATED, self._handle_employee_created)
            await self._event_bus.subscribe(HREventTypes.EMPLOYEE_TERMINATED, self._handle_employee_terminated)
            await self._event_bus.subscribe(HREventTypes.CANDIDATE_CREATED, self._handle_candidate_created)
            await self._event_bus.subscribe(HREventTypes.CANDIDATE_HIRED, self._handle_candidate_hired)
            
            # Listen for project management events
            await self._event_bus.subscribe("project_management.project_created", self._handle_project_created)
            await self._event_bus.subscribe("project_management.team_member_assigned", self._handle_team_assignment)
            
            # Listen for CRM events
            await self._event_bus.subscribe("crm.opportunity_won", self._handle_opportunity_won)

    # Event handlers
    async def _handle_user_created(self, event):
        """Handle user creation - could create employee record"""
        self._logger.info(f"User created: {event.data.get('user_id')}")
        # Logic to potentially create employee record from user creation
        
    async def _handle_user_deactivated(self, event):
        """Handle user deactivation - update employee status"""
        self._logger.info(f"User deactivated: {event.data.get('user_id')}")
        # Logic to update employee status when user is deactivated
        
    async def _handle_employee_created(self, event):
        """Handle employee creation - trigger onboarding"""
        employee_email = event.data.get("email")
        employee_name = f"{event.data.get('first_name', '')} {event.data.get('last_name', '')}".strip()
        self._logger.info(f"Employee created: {event.data.get('employee_id')}")
        
        # Send onboarding email
        print(f"[ONBOARDING EMAIL] Sent onboarding email to {employee_name} <{employee_email}>")
        
    async def _handle_employee_terminated(self, event):
        """Handle employee termination - cleanup and notifications"""
        self._logger.info(f"Employee terminated: {event.data.get('employee_id')}")
        # Logic for termination cleanup, access revocation, etc.
        
    async def _handle_candidate_created(self, event):
        """Handle candidate creation - trigger onboarding workflow"""
        candidate_email = event.data.get("email")
        candidate_name = f"{event.data.get('first_name', '')} {event.data.get('last_name', '')}".strip()
        self._logger.info(f"Candidate created: {event.data.get('candidate_id')}")
        
        # Send candidate onboarding email
        print(f"[CANDIDATE ONBOARDING EMAIL] Sent onboarding email to {candidate_name} <{candidate_email}>")
        
    async def _handle_candidate_hired(self, event):
        """Handle candidate hiring - convert to employee"""
        self._logger.info(f"Candidate hired: {event.data.get('candidate_id')}")
        # Logic to convert candidate to employee
        
    async def _handle_project_created(self, event):
        """Handle project creation - check for resource allocation"""
        self._logger.info(f"Project created: {event.data.get('project_id')}")
        # Logic to check employee availability and skills for project assignment
        
    async def _handle_team_assignment(self, event):
        """Handle team member assignment - update employee workload"""
        self._logger.info(f"Team member assigned: {event.data.get('employee_id')}")
        # Logic to update employee workload and capacity tracking
        
    async def _handle_opportunity_won(self, event):
        """Handle won opportunity - potential hiring needs"""
        self._logger.info(f"Opportunity won: {event.data.get('opportunity_id')}")
        # Logic to assess if new business requires additional hiring

    async def initialize(self) -> None:
        """Initialize HR module"""
        await super().initialize()
        await self._subscribe_to_events()
        self._logger.info("HR Module initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown HR module"""
        self._logger.info("Shutting down HR Module")
        await super().shutdown()

    # Event publishers
    async def _publish_employee_created_event(self, employee_id: str, employee_code: str, department_id: str):
        """Publish employee created event for other modules"""
        if self._event_bus:
            await self._event_bus.publish(HREventTypes.EMPLOYEE_CREATED, {
                "entity_type": "employee",
                "entity_id": employee_id,
                "employee_code": employee_code,
                "department_id": department_id
            })
            self._logger.info(f"Employee created event published for {employee_code}")

    async def _publish_employee_terminated_event(self, employee_id: str, employee_code: str):
        """Publish employee terminated event for other modules"""
        if self._event_bus:
            await self._event_bus.publish(HREventTypes.EMPLOYEE_TERMINATED, {
                "entity_type": "employee",
                "entity_id": employee_id,
                "employee_code": employee_code
            })
            self._logger.info(f"Employee terminated event published for {employee_code}")

    async def _publish_candidate_created_event(self, candidate_id: str, candidate_code: str, applied_position_id: str):
        """Publish candidate created event for other modules"""
        if self._event_bus:
            await self._event_bus.publish(HREventTypes.CANDIDATE_CREATED, {
                "entity_type": "candidate",
                "entity_id": candidate_id,
                "candidate_code": candidate_code,
                "applied_position_id": applied_position_id
            })
            self._logger.info(f"Candidate created event published for {candidate_code}")


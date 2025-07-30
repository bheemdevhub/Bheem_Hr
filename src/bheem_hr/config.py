# app/modules/hr/config.py
"""HR Module Configuration"""
from enum import Enum
from typing import Dict, Any, List

class HRSettings:
    """HR Module Settings"""
    
    # General settings
    MODULE_NAME = "hr"
    MODULE_VERSION = "1.0.0"
    
    # Employee settings
    DEFAULT_PROBATION_PERIOD = 90  # days
    MAX_VACATION_DAYS = 25
    MAX_SICK_DAYS = 10
    
    # Notification settings
    ONBOARDING_EMAIL_ENABLED = True
    TERMINATION_EMAIL_ENABLED = True
    BIRTHDAY_REMINDERS = True
    
    # Integration settings
    SYNC_WITH_CRM = True
    SYNC_WITH_PROJECT_MANAGEMENT = True

class EmployeeStatus(Enum):
    """Employee status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"
    PROBATION = "probation"

class CandidateStatus(Enum):
    """Candidate status enumeration"""
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    OFFER_EXTENDED = "offer_extended"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class EmploymentType(Enum):
    """Employment type enumeration"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"
    CONSULTANT = "consultant"

class DepartmentType(Enum):
    """Department type enumeration"""
    ENGINEERING = "engineering"
    SALES = "sales"
    MARKETING = "marketing"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"
    SUPPORT = "support"

class HREventTypes:
    """HR Event Types"""
    
    # Employee events
    EMPLOYEE_CREATED = "hr.employee.created"
    EMPLOYEE_UPDATED = "hr.employee.updated"
    EMPLOYEE_ACTIVATED = "hr.employee.activated"
    EMPLOYEE_TERMINATED = "hr.employee.terminated"
    EMPLOYEE_ON_LEAVE = "hr.employee.on_leave"
    EMPLOYEE_RETURNED = "hr.employee.returned"
    EMPLOYEE_PROMOTED = "hr.employee.promoted"
    
    # Department events
    DEPARTMENT_CREATED = "hr.department.created"
    DEPARTMENT_UPDATED = "hr.department.updated"
    DEPARTMENT_DELETED = "hr.department.deleted"
    DEPARTMENT_RESTRUCTURED = "hr.department.restructured"
    
    # Candidate events
    CANDIDATE_CREATED = "hr.candidate.created"
    CANDIDATE_UPDATED = "hr.candidate.updated"
    CANDIDATE_INTERVIEWED = "hr.candidate.interviewed"
    CANDIDATE_HIRED = "hr.candidate.hired"
    CANDIDATE_REJECTED = "hr.candidate.rejected"
    CANDIDATE_WITHDRAWN = "hr.candidate.withdrawn"
    
    # Position events
    POSITION_CREATED = "hr.position.created"
    POSITION_UPDATED = "hr.position.updated"
    POSITION_CLOSED = "hr.position.closed"
    
    # Workflow events
    ONBOARDING_STARTED = "hr.onboarding.started"
    ONBOARDING_COMPLETED = "hr.onboarding.completed"
    PERFORMANCE_REVIEW_DUE = "hr.performance_review.due"
    PERFORMANCE_REVIEW_COMPLETED = "hr.performance_review.completed"
    
    # Time tracking events
    ATTENDANCE_MARKED = "hr.attendance.marked"
    LEAVE_REQUESTED = "hr.leave.requested"
    LEAVE_APPROVED = "hr.leave.approved"
    LEAVE_REJECTED = "hr.leave.rejected"
    
    # Payroll events
    SALARY_STRUCTURE_CREATED = "hr.salary_structure.created"
    SALARY_STRUCTURE_UPDATED = "hr.salary_structure.updated"
    SALARY_STRUCTURE_DELETED = "hr.salary_structure.deleted"
    SALARY_COMPONENT_CREATED = "hr.salary_component.created"
    SALARY_COMPONENT_UPDATED = "hr.salary_component.updated"
    SALARY_COMPONENT_DELETED = "hr.salary_component.deleted"
    
    PAYROLL_RUN_CREATED = "hr.payroll_run.created"
    PAYROLL_RUN_UPDATED = "hr.payroll_run.updated"
    PAYROLL_RUN_PROCESSED = "hr.payroll_run.processed"
    PAYROLL_RUN_DELETED = "hr.payroll_run.deleted"
    
    PAYSLIP_CREATED = "hr.payslip.created"
    PAYSLIP_UPDATED = "hr.payslip.updated"
    PAYSLIP_DELETED = "hr.payslip.deleted"
    
    # Attendance events
    ATTENDANCE_CREATED = "hr.attendance.created"
    ATTENDANCE_UPDATED = "hr.attendance.updated"
    ATTENDANCE_DELETED = "hr.attendance.deleted"
    ATTENDANCE_CHECK_IN = "hr.attendance.check_in"
    ATTENDANCE_CHECK_OUT = "hr.attendance.check_out"
    
    # Leave request events  
    LEAVE_REQUEST_CREATED = "hr.leave_request.created"
    LEAVE_REQUEST_UPDATED = "hr.leave_request.updated"
    LEAVE_REQUEST_APPROVED = "hr.leave_request.approved"
    LEAVE_REQUEST_REJECTED = "hr.leave_request.rejected"
    LEAVE_REQUEST_DELETED = "hr.leave_request.deleted"
    
    # Report events
    REPORT_LOG_CREATED = "hr.report_log.created"
    REPORT_LOG_UPDATED = "hr.report_log.updated"
    REPORT_LOG_DELETED = "hr.report_log.deleted"

# HR Permissions for API access control
HR_PERMISSIONS = {
    # Employee permissions
    "EMPLOYEE_CREATE": "hr.employee.create",
    "EMPLOYEE_READ": "hr.employee.read", 
    "EMPLOYEE_UPDATE": "hr.employee.update",
    "EMPLOYEE_DELETE": "hr.employee.delete",
    
    # Candidate permissions
    "CANDIDATE_CREATE": "hr.candidate.create",
    "CANDIDATE_READ": "hr.candidate.read",
    "CANDIDATE_UPDATE": "hr.candidate.update", 
    "CANDIDATE_DELETE": "hr.candidate.delete",
    
    # Salary Structure permissions
    "SALARY_STRUCTURE_CREATE": "hr.salary_structure.create",
    "SALARY_STRUCTURE_READ": "hr.salary_structure.read",
    "SALARY_STRUCTURE_UPDATE": "hr.salary_structure.update",
    "SALARY_STRUCTURE_DELETE": "hr.salary_structure.delete",
    
    # Salary Component permissions
    "SALARY_COMPONENT_CREATE": "hr.salary_component.create", 
    "SALARY_COMPONENT_READ": "hr.salary_component.read",
    "SALARY_COMPONENT_UPDATE": "hr.salary_component.update",
    "SALARY_COMPONENT_DELETE": "hr.salary_component.delete",
    
    # Payroll Run permissions
    "PAYROLL_RUN_CREATE": "hr.payroll_run.create",
    "PAYROLL_RUN_READ": "hr.payroll_run.read",
    "PAYROLL_RUN_UPDATE": "hr.payroll_run.update", 
    "PAYROLL_RUN_DELETE": "hr.payroll_run.delete",
    "PAYROLL_RUN_PROCESS": "hr.payroll_run.process",
    
    # Payslip permissions
    "PAYSLIP_CREATE": "hr.payslip.create",
    "PAYSLIP_READ": "hr.payslip.read",
    "PAYSLIP_UPDATE": "hr.payslip.update",
    "PAYSLIP_DELETE": "hr.payslip.delete",
    
    # Attendance permissions
    "ATTENDANCE_CREATE": "hr.attendance.create",
    "ATTENDANCE_READ": "hr.attendance.read",
    "ATTENDANCE_UPDATE": "hr.attendance.update",
    "ATTENDANCE_DELETE": "hr.attendance.delete",
    "ATTENDANCE_CHECK_IN": "hr.attendance.check_in",
    "ATTENDANCE_CHECK_OUT": "hr.attendance.check_out",
    
    # Leave Request permissions
    "LEAVE_REQUEST_CREATE": "hr.leave_request.create",
    "LEAVE_REQUEST_READ": "hr.leave_request.read", 
    "LEAVE_REQUEST_UPDATE": "hr.leave_request.update",
    "LEAVE_REQUEST_DELETE": "hr.leave_request.delete",
    "LEAVE_REQUEST_APPROVE": "hr.leave_request.approve",
    "LEAVE_REQUEST_REJECT": "hr.leave_request.reject",
    
    # Report Log permissions
    "REPORT_LOG_CREATE": "hr.report_log.create",
    "REPORT_LOG_READ": "hr.report_log.read",
    "REPORT_LOG_UPDATE": "hr.report_log.update", 
    "REPORT_LOG_DELETE": "hr.report_log.delete",
    
    # Report events
    "REPORT_LOG_CREATED": "hr.report_log.created",
    "REPORT_LOG_UPDATED": "hr.report_log.updated", 
    "REPORT_LOG_DELETED": "hr.report_log.deleted"
}

# Permission constants
HR_PERMISSIONS = {
    "DEPARTMENT_CREATE": "hr.create_department",
    "DEPARTMENT_UPDATE": "hr.update_department", 
    "DEPARTMENT_VIEW": "hr.view_department",
    "DEPARTMENT_DELETE": "hr.delete_department",
    
    "EMPLOYEE_CREATE": "hr.create_employee",
    "EMPLOYEE_UPDATE": "hr.update_employee",
    "EMPLOYEE_VIEW": "hr.view_employee", 
    "EMPLOYEE_DELETE": "hr.delete_employee",
    "EMPLOYEE_ACTIVATE": "hr.activate_employee",
    "EMPLOYEE_TERMINATE": "hr.terminate_employee",
    
    "CANDIDATE_CREATE": "hr.create_candidate",
    "CANDIDATE_UPDATE": "hr.update_candidate",
    "CANDIDATE_VIEW": "hr.view_candidate",
    "CANDIDATE_DELETE": "hr.delete_candidate",
    "CANDIDATE_INTERVIEW": "hr.interview_candidate",
    "CANDIDATE_HIRE": "hr.hire_candidate",
    
    "REPORTS_VIEW": "hr.view_reports",
    "REPORTS_GENERATE": "hr.generate_reports",
    "DATA_EXPORT": "hr.export_data",
    
    "ADMIN_SETTINGS": "hr.admin_settings",
    "MANAGE_INTEGRATIONS": "hr.manage_integrations"
}

# API Endpoint configurations
API_ENDPOINTS = {
    "employees": [
        "GET /hr/employees/",
        "POST /hr/employees/",
        "GET /hr/employees/{id}",
        "PUT /hr/employees/{id}",
        "DELETE /hr/employees/{id}",
        "POST /hr/employees/{id}/activate",
        "POST /hr/employees/{id}/terminate",
    ],
    "departments": [
        "GET /hr/departments/",
        "POST /hr/departments/",
        "GET /hr/departments/{id}",
        "PUT /hr/departments/{id}",
        "DELETE /hr/departments/{id}",
        "GET /hr/departments/{id}/employees",
    ],
    "candidates": [
        "GET /hr/candidates/",
        "POST /hr/candidates/",
        "GET /hr/candidates/{id}",
        "PUT /hr/candidates/{id}",
        "DELETE /hr/candidates/{id}",
        "POST /hr/candidates/{id}/interview",
        "POST /hr/candidates/{id}/hire",
    ],
    "reports": [
        "GET /hr/reports/dashboard/",
        "GET /hr/reports/headcount/",
        "GET /hr/reports/turnover/",
        "GET /hr/reports/recruitment/",
        "POST /hr/reports/export/",
    ]
}

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "employee_settings": {
        "probation_period_days": 90,
        "max_vacation_days": 25,
        "max_sick_days": 10,
        "automatic_onboarding": True,
        "performance_review_frequency": "annual"
    },
    "notifications": {
        "onboarding_email": True,
        "termination_email": True,
        "birthday_reminders": True,
        "anniversary_reminders": True,
        "leave_request_notifications": True
    },
    "integrations": {
        "crm_sync": True,
        "project_management_sync": True,
        "accounting_sync": True,
        "slack_integration": False,
        "teams_integration": False
    },
    "security": {
        "require_manager_approval": True,
        "audit_all_changes": True,
        "data_retention_days": 2555,  # 7 years
        "background_check_required": True
    },
    "recruitment": {
        "auto_create_candidate_from_application": True,
        "send_acknowledgment_email": True,
        "track_application_source": True,
        "candidate_rating_enabled": True
    }
}


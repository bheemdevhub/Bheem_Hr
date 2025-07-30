# HR API v1 routes package
from . import employees, departments, candidates, reports, lookups, address, contact, passport, bank_accounts, main_routes, hr_dashboard, hr_action_item
from . import job_requisitions, interviews, offers, onboarding
from . import salary_structure, salary_component, payroll_run, payslip, attendance, leave_request, report_log

__all__ = [
    "main_routes",
    "hr_dashboard",
    "hr_action_item",
    "employees", 
    "departments", 
    "candidates", 
    "reports", 
    "lookups",
    "address",
    "contact",
    "passport",
    "bank_accounts",
    "job_requisitions",
    "interviews", 
    "offers", 
    "onboarding",
    "salary_structure",
    "salary_component", 
    "payroll_run",
    "payslip",
    "attendance",
    "leave_request",
    "report_log"
]



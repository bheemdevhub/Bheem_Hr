
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI

from fastapi import FastAPI
from bheem_hr.api.v1.routes import (
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
    hr_dashboard,
    hr_action_item
)

app = FastAPI(title="HR Module Standalone")

# Register all routers for Swagger visibility
app.include_router(main_routes.router, prefix="/api/hr", tags=["Persons"])
app.include_router(hr_dashboard.router, prefix="/api/hr", tags=["HR Dashboard"])
app.include_router(hr_action_item.router, prefix="/api/hr/action-items", tags=["HR Action Items"])
app.include_router(employees.router, prefix="/api/hr/employees", tags=["Employees"])
app.include_router(departments.router, prefix="/api/hr/departments", tags=["Departments"])
app.include_router(candidates.router, prefix="/api/hr/candidates", tags=["Candidates"])
app.include_router(reports.router, prefix="/api/hr/reports", tags=["Reports"])
app.include_router(lookups.router, prefix="/api/hr/lookups", tags=["Lookups"])
app.include_router(address.router, prefix="/api/hr/addresses", tags=["Addresses"])
app.include_router(contact.router, prefix="/api/hr/contacts", tags=["Contacts"])
app.include_router(passport.router, prefix="/api/hr/passports", tags=["Passports"])
app.include_router(bank_accounts.router, prefix="/api/hr/bank-accounts", tags=["Bank Accounts"])
app.include_router(job_requisitions.router, prefix="/api/hr/job-requisitions", tags=["Job Requisitions"])
app.include_router(interviews.router, prefix="/api/hr/interviews", tags=["Interviews"])
app.include_router(offers.router, prefix="/api/hr/offers", tags=["Offers"])
app.include_router(onboarding.router, prefix="/api/hr/onboarding", tags=["Onboarding"])
app.include_router(salary_structure.router, prefix="/api/hr/salary-structures", tags=["Salary Structures"])
app.include_router(salary_component.router, prefix="/api/hr/salary-components", tags=["Salary Components"])
app.include_router(payroll_run.router, prefix="/api/hr/payroll-runs", tags=["Payroll Runs"])
app.include_router(payslip.router, prefix="/api/hr/payslips", tags=["Payslips"])
app.include_router(attendance.router, prefix="/api/hr/attendance", tags=["Attendance"])
app.include_router(leave_request.router, prefix="/api/hr/leave-requests", tags=["Leave Requests"])
app.include_router(report_log.router, prefix="/api/hr/report-logs", tags=["Report Logs"])

@app.get("/")
async def root():
    return {"message": "HR module is running independently"}


from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, time

class EmployeeSummaryItem(BaseModel):
    employee_code: str
    name: str

class CountedEmployees(BaseModel):
    count: int
    employees: List[EmployeeSummaryItem]

class HRDailySummaryResponse(BaseModel):
    present: CountedEmployees
    on_leave: CountedEmployees
    wfh: CountedEmployees
    absent: CountedEmployees
    new_joinees: CountedEmployees
    birthdays: List[str]
    birthdays_count: int
    work_anniversaries: List[str]
    work_anniversaries_count: int

class AttendanceTodayItem(BaseModel):
    employee_id: str
    employee_code: str
    status: str

class AttendanceTodayResponse(BaseModel):
    results: List[AttendanceTodayItem]

class PendingLeaveRequestItem(BaseModel):
    request_id: str
    employee_id: str
    employee_code: str
    name:str
    leave_type: str
    from_date: date
    to_date: date
    status: str

class PendingLeaveRequestsResponse(BaseModel):
    results: List[PendingLeaveRequestItem]

class HRActionTodayItem(BaseModel):
    action_id: str
    title: str
    due_date: date
    status: str

class HRActionTodayResponse(BaseModel):
    results: List[HRActionTodayItem]

class HRNotificationsResponse(BaseModel):
    upcoming_contracts: int
    birthdays: List[str]



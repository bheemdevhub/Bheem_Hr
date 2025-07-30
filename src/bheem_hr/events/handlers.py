"""HR Event Handlers"""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from bheem_core.core.database import get_db
from bheem_core.core.event_bus import Event

# Absolute import from the installable bheem_hr module
from bheem_hr.core.services.hr_service import HRService
# If department service is needed in future, import like this:
# from bheem_hr.core.services.department_service import DepartmentService

from bheem_hr.config import HREventTypes

logger = logging.getLogger(__name__)

class HREventHandlers:
    """HR Module Event Handlers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.hr_service = HRService(db)
        # self.department_service = DepartmentService(db)
        # self.department_service = DepartmentService(db)

    async def handle_employee_created(self, event: Event):
        """Handle employee creation - trigger onboarding workflow"""
        try:
            employee_id = event.data.get("employee_id")
            logger.info(f"Processing employee created event for ID: {employee_id}")
            
            # 1. Create onboarding checklist
            await self.hr_service.create_onboarding_checklist(employee_id)
            
            # 2. Setup IT resources
            await self.employee_service.trigger_it_setup(employee_id)
            
            # 3. Send welcome email
            await self.employee_service.send_welcome_email(employee_id)
            
            # 4. Create initial performance review schedule
            await self.employee_service.schedule_performance_review(employee_id)
            
            # 5. Notify manager
            await self.employee_service.notify_manager_of_new_hire(employee_id)
            
            logger.info(f"Employee created event processed successfully for ID: {employee_id}")
            
        except Exception as e:
            logger.error(f"Error handling employee created event: {str(e)}")
            raise

    async def handle_employee_terminated(self, event: Event):
        """Handle employee termination - cleanup workflow"""
        try:
            employee_id = event.data.get("employee_id")
            termination_date = event.data.get("termination_date")
            logger.info(f"Processing employee terminated event for ID: {employee_id}")
            
            # 1. Deactivate system access
            await self.employee_service.deactivate_system_access(employee_id)
            
            # 2. Final payroll processing
            await self.employee_service.process_final_payroll(employee_id, termination_date)
            
            # 3. Update benefits
            await self.employee_service.terminate_benefits(employee_id, termination_date)
            
            # 4. Generate exit documentation
            await self.employee_service.generate_exit_documents(employee_id)
            
            logger.info(f"Employee terminated event processed successfully for ID: {employee_id}")
            
        except Exception as e:
            logger.error(f"Error handling employee terminated event: {str(e)}")
            raise

    # ===================== SALARY STRUCTURE EVENTS =====================
    
    async def handle_salary_structure_created(self, event: Event):
        """Handle salary structure creation"""
        try:
            structure_id = event.data.get("structure_id")
            employee_id = event.data.get("employee_id")
            effective_date = event.data.get("effective_date")
            
            logger.info(f"Salary structure {structure_id} created for employee {employee_id}")
            
            # Send notification to employee
            await self.hr_service.send_notification(
                recipient_id=employee_id,
                title="New Salary Structure",
                message=f"Your new salary structure is effective from {effective_date}",
                type="salary_update"
            )
            
        except Exception as e:
            logger.error(f"Error handling salary structure created event: {str(e)}")
            raise

    async def handle_salary_structure_updated(self, event: Event):
        """Handle salary structure update"""
        try:
            structure_id = event.data.get("structure_id")
            employee_id = event.data.get("employee_id")
            
            logger.info(f"Salary structure {structure_id} updated for employee {employee_id}")
            
            # Audit log the change
            await self.hr_service.log_salary_change(structure_id, employee_id)
            
        except Exception as e:
            logger.error(f"Error handling salary structure updated event: {str(e)}")
            raise

    # ===================== PAYROLL RUN EVENTS =====================
    
    async def handle_payroll_run_created(self, event: Event):
        """Handle payroll run creation"""
        try:
            payroll_id = event.data.get("payroll_id")
            month = event.data.get("month")
            
            logger.info(f"Payroll run {payroll_id} created for {month}")
            
            # Send notification to payroll team
            await self.hr_service.send_notification(
                recipient_group="payroll_team",
                title="New Payroll Run Created",
                message=f"Payroll run for {month} has been created",
                type="payroll_alert"
            )
            
        except Exception as e:
            logger.error(f"Error handling payroll run created event: {str(e)}")
            raise

    async def handle_payroll_run_processed(self, event: Event):
        """Handle payroll processing completion"""
        try:
            payroll_id = event.data.get("payroll_id")
            employee_count = event.data.get("employee_count")
            
            logger.info(f"Payroll run {payroll_id} processed for {employee_count} employees")
            
            # Send completion notification
            await self.hr_service.send_notification(
                recipient_group="finance_team",
                title="Payroll Processing Complete",
                message=f"Payroll run {payroll_id} processed for {employee_count} employees",
                type="payroll_success"
            )
            
        except Exception as e:
            logger.error(f"Error handling payroll processed event: {str(e)}")
            raise

    # ===================== PAYSLIP EVENTS =====================
    
    async def handle_payslip_created(self, event: Event):
        """Handle payslip creation"""
        try:
            payslip_id = event.data.get("payslip_id")
            employee_id = event.data.get("employee_id")
            net_pay = event.data.get("net_pay")
            
            logger.info(f"Payslip {payslip_id} created for employee {employee_id}")
            
            # Send payslip notification to employee
            await self.hr_service.send_notification(
                recipient_id=employee_id,
                title="Payslip Generated",
                message=f"Your payslip has been generated. Net pay: ${net_pay}",
                type="payslip_ready"
            )
            
        except Exception as e:
            logger.error(f"Error handling payslip created event: {str(e)}")
            raise

    # ===================== ATTENDANCE EVENTS =====================
    
    async def handle_attendance_clock_in(self, event: Event):
        """Handle employee clock in"""
        try:
            employee_id = event.data.get("employee_id")
            check_in_time = event.data.get("check_in_time")
            
            logger.info(f"Employee {employee_id} clocked in at {check_in_time}")
            
            # Check if late and send notification
            from datetime import time, datetime
            standard_start_time = time(9, 0)  # 9:00 AM
            actual_time = datetime.fromisoformat(check_in_time).time()
            
            if actual_time > standard_start_time:
                await self.hr_service.send_notification(
                    recipient_id=employee_id,
                    title="Late Arrival",
                    message=f"You clocked in at {check_in_time}. Standard start time is 9:00 AM.",
                    type="attendance_warning"
                )
            
        except Exception as e:
            logger.error(f"Error handling clock in event: {str(e)}")
            raise

    async def handle_attendance_clock_out(self, event: Event):
        """Handle employee clock out"""
        try:
            employee_id = event.data.get("employee_id")
            check_out_time = event.data.get("check_out_time")
            
            logger.info(f"Employee {employee_id} clocked out at {check_out_time}")
            
        except Exception as e:
            logger.error(f"Error handling clock out event: {str(e)}")
            raise

    # ===================== LEAVE REQUEST EVENTS =====================
    
    async def handle_leave_request_created(self, event: Event):
        """Handle leave request creation"""
        try:
            leave_id = event.data.get("leave_id")
            employee_id = event.data.get("employee_id")
            leave_type = event.data.get("leave_type")
            start_date = event.data.get("start_date")
            end_date = event.data.get("end_date")
            
            logger.info(f"Leave request {leave_id} created by employee {employee_id}")
            
            # Send notification to manager
            await self.hr_service.send_notification(
                recipient_group="managers",
                title="New Leave Request",
                message=f"Employee {employee_id} requested {leave_type} from {start_date} to {end_date}",
                type="leave_approval_required"
            )
            
        except Exception as e:
            logger.error(f"Error handling leave request created event: {str(e)}")
            raise

    async def handle_leave_request_approved(self, event: Event):
        """Handle leave request approval"""
        try:
            leave_id = event.data.get("leave_id")
            employee_id = event.data.get("employee_id")
            approver_id = event.data.get("approver_id")
            
            logger.info(f"Leave request {leave_id} approved by {approver_id}")
            
            # Send approval notification to employee
            await self.hr_service.send_notification(
                recipient_id=employee_id,
                title="Leave Request Approved",
                message=f"Your leave request {leave_id} has been approved",
                type="leave_approved"
            )
            
        except Exception as e:
            logger.error(f"Error handling leave request approved event: {str(e)}")
            raise

    async def handle_leave_request_rejected(self, event: Event):
        """Handle leave request rejection"""
        try:
            leave_id = event.data.get("leave_id")
            employee_id = event.data.get("employee_id")
            rejector_id = event.data.get("rejector_id")
            reason = event.data.get("reason")
            
            logger.info(f"Leave request {leave_id} rejected by {rejector_id}")
            
            # Send rejection notification to employee
            await self.hr_service.send_notification(
                recipient_id=employee_id,
                title="Leave Request Rejected",
                message=f"Your leave request {leave_id} was rejected. Reason: {reason}",
                type="leave_rejected"
            )
            
        except Exception as e:
            logger.error(f"Error handling leave request rejected event: {str(e)}")
            raise
        """Handle employee termination - cleanup workflow"""
        try:
            employee_id = event.data.get("employee_id")
            logger.info(f"Processing employee termination event for ID: {employee_id}")
            
            # 1. Revoke system access
            await self.employee_service.revoke_system_access(employee_id)
            
            # 2. Transfer responsibilities
            await self.employee_service.initiate_responsibility_transfer(employee_id)
            
            # 3. Schedule exit interview
            await self.employee_service.schedule_exit_interview(employee_id)
            
            # 4. Handle equipment return
            await self.employee_service.initiate_equipment_return(employee_id)
            
            # 5. Update project assignments
            await self.employee_service.update_project_assignments(employee_id)
            
            # 6. Send farewell communications
            await self.employee_service.send_farewell_communications(employee_id)
            
            logger.info(f"Employee termination event processed successfully for ID: {employee_id}")
            
        except Exception as e:
            logger.error(f"Error handling employee termination event: {str(e)}")
            raise

    async def handle_candidate_hired(self, event: Event):
        """Handle candidate hiring - convert to employee"""
        try:
            candidate_id = event.data.get("candidate_id")
            position_id = event.data.get("position_id")
            logger.info(f"Processing candidate hired event for ID: {candidate_id}")
            
            # 1. Get candidate information
            candidate = await self.candidate_service.get_candidate(candidate_id)
            if not candidate:
                logger.warning(f"Candidate not found: {candidate_id}")
                return
            
            # 2. Create employee record from candidate
            employee_data = await self.candidate_service.convert_candidate_to_employee(
                candidate_id, position_id
            )
            
            # 3. Create employee record
            employee = await self.employee_service.create_employee(employee_data)
            
            # 4. Update candidate status
            await self.candidate_service.update_candidate_status(
                candidate_id, "hired", employee_id=employee.id
            )
            
            # 5. Trigger employee onboarding
            await self.employee_service.trigger_onboarding(employee.id)
            
            logger.info(f"Candidate hired event processed successfully. Employee ID: {employee.id}")
            
        except Exception as e:
            logger.error(f"Error handling candidate hired event: {str(e)}")
            raise

    async def handle_department_restructure(self, event: Event):
        """Handle department restructuring"""
        try:
            department_id = event.data.get("department_id")
            changes = event.data.get("changes", {})
            logger.info(f"Processing department restructure event for ID: {department_id}")
            
            # 1. Update employee assignments
            if changes.get("employee_transfers"):
                await self.department_service.process_employee_transfers(
                    changes["employee_transfers"]
                )
            
            # 2. Update reporting structure
            if changes.get("reporting_changes"):
                await self.department_service.update_reporting_structure(
                    changes["reporting_changes"]
                )
            
            # 3. Notify affected employees
            await self.department_service.notify_restructure_changes(department_id, changes)
            
            # 4. Update organizational chart
            await self.department_service.update_org_chart(department_id)
            
            logger.info(f"Department restructure event processed successfully for ID: {department_id}")
            
        except Exception as e:
            logger.error(f"Error handling department restructure event: {str(e)}")
            raise

    async def handle_performance_review_due(self, event: Event):
        """Handle performance review due notifications"""
        try:
            employee_id = event.data.get("employee_id")
            review_type = event.data.get("review_type", "annual")
            logger.info(f"Processing performance review due for employee ID: {employee_id}")
            
            # 1. Create performance review record
            review = await self.employee_service.create_performance_review(
                employee_id, review_type
            )
            
            # 2. Notify employee
            await self.employee_service.notify_employee_review_due(employee_id, review.id)
            
            # 3. Notify manager
            await self.employee_service.notify_manager_review_due(employee_id, review.id)
            
            # 4. Schedule review meeting
            await self.employee_service.schedule_review_meeting(employee_id, review.id)
            
            logger.info(f"Performance review due event processed for employee ID: {employee_id}")
            
        except Exception as e:
            logger.error(f"Error handling performance review due event: {str(e)}")
            raise

    async def handle_leave_request(self, event: Event):
        """Handle leave request submissions"""
        try:
            leave_request_id = event.data.get("leave_request_id")
            employee_id = event.data.get("employee_id")
            logger.info(f"Processing leave request ID: {leave_request_id}")
            
            # 1. Validate leave request
            validation_result = await self.employee_service.validate_leave_request(leave_request_id)
            
            if not validation_result["valid"]:
                await self.employee_service.reject_leave_request(
                    leave_request_id, validation_result["reason"]
                )
                return
            
            # 2. Check manager approval requirements
            if validation_result.get("requires_approval"):
                await self.employee_service.send_leave_approval_request(leave_request_id)
            else:
                # Auto-approve if within policy limits
                await self.employee_service.approve_leave_request(leave_request_id)
            
            # 3. Update team calendar if approved
            if validation_result.get("auto_approved"):
                await self.employee_service.update_team_calendar(leave_request_id)
            
            logger.info(f"Leave request processed for ID: {leave_request_id}")
            
        except Exception as e:
            logger.error(f"Error handling leave request event: {str(e)}")
            raise

    # ==================== SALARY STRUCTURE EVENTS ====================
    async def handle_salary_structure_created(self, event: Event):
        """Handle salary structure creation"""
        try:
            structure_id = event.data.get("structure_id")
            logger.info(f"Processing salary structure created event for ID: {structure_id}")
            
            # 1. Notify HR department
            await self.hr_service.notify_hr_department("salary_structure_created", structure_id)
            
            # 2. Update employee records
            await self.hr_service.update_employee_salary_info(structure_id)
            
            # 3. Trigger payroll recalculation if needed
            await self.hr_service.trigger_payroll_recalculation(structure_id)
            
            logger.info(f"Salary structure created event processed for ID: {structure_id}")
            
        except Exception as e:
            logger.error(f"Error handling salary structure created event: {str(e)}")
            raise

    async def handle_salary_structure_updated(self, event: Event):
        """Handle salary structure updates"""
        try:
            structure_id = event.data.get("structure_id")
            logger.info(f"Processing salary structure updated event for ID: {structure_id}")
            
            # 1. Notify affected employee
            await self.hr_service.notify_employee_salary_change(structure_id)
            
            # 2. Update future payroll calculations
            await self.hr_service.update_payroll_calculations(structure_id)
            
            # 3. Log audit trail
            await self.hr_service.log_salary_change_audit(structure_id)
            
            logger.info(f"Salary structure updated event processed for ID: {structure_id}")
            
        except Exception as e:
            logger.error(f"Error handling salary structure updated event: {str(e)}")
            raise

    async def handle_salary_structure_deleted(self, event: Event):
        """Handle salary structure deletion"""
        try:
            structure_id = event.data.get("structure_id")
            logger.info(f"Processing salary structure deleted event for ID: {structure_id}")
            
            # 1. Archive related payroll data
            await self.hr_service.archive_payroll_data(structure_id)
            
            # 2. Notify payroll department
            await self.hr_service.notify_payroll_department("structure_deleted", structure_id)
            
            logger.info(f"Salary structure deleted event processed for ID: {structure_id}")
            
        except Exception as e:
            logger.error(f"Error handling salary structure deleted event: {str(e)}")
            raise

    # ==================== PAYROLL RUN EVENTS ====================
    async def handle_payroll_run_created(self, event: Event):
        """Handle payroll run creation"""
        try:
            run_id = event.data.get("run_id")
            logger.info(f"Processing payroll run created event for ID: {run_id}")
            
            # 1. Notify payroll team
            await self.hr_service.notify_payroll_team("run_created", run_id)
            
            # 2. Prepare employee data for processing
            await self.hr_service.prepare_employee_payroll_data(run_id)
            
            # 3. Validate salary structures
            await self.hr_service.validate_salary_structures_for_payroll(run_id)
            
            logger.info(f"Payroll run created event processed for ID: {run_id}")
            
        except Exception as e:
            logger.error(f"Error handling payroll run created event: {str(e)}")
            raise

    async def handle_payroll_run_processed(self, event: Event):
        """Handle payroll run processing completion"""
        try:
            run_id = event.data.get("run_id")
            logger.info(f"Processing payroll run processed event for ID: {run_id}")
            
            # 1. Generate payslips for all employees
            await self.hr_service.generate_employee_payslips(run_id)
            
            # 2. Send payslips to employees
            await self.hr_service.distribute_payslips(run_id)
            
            # 3. Update accounting system
            await self.hr_service.update_accounting_with_payroll(run_id)
            
            # 4. Notify finance department
            await self.hr_service.notify_finance_payroll_complete(run_id)
            
            # 5. Generate payroll reports
            await self.hr_service.generate_payroll_reports(run_id)
            
            logger.info(f"Payroll run processed event processed for ID: {run_id}")
            
        except Exception as e:
            logger.error(f"Error handling payroll run processed event: {str(e)}")
            raise

    # ==================== PAYSLIP EVENTS ====================
    async def handle_payslip_created(self, event: Event):
        """Handle payslip creation"""
        try:
            payslip_id = event.data.get("payslip_id")
            logger.info(f"Processing payslip created event for ID: {payslip_id}")
            
            # 1. Generate PDF payslip
            await self.hr_service.generate_payslip_pdf(payslip_id)
            
            # 2. Send email notification to employee
            await self.hr_service.send_payslip_notification(payslip_id)
            
            # 3. Update employee payroll history
            await self.hr_service.update_employee_payroll_history(payslip_id)
            
            logger.info(f"Payslip created event processed for ID: {payslip_id}")
            
        except Exception as e:
            logger.error(f"Error handling payslip created event: {str(e)}")
            raise

    # ==================== ATTENDANCE EVENTS ====================
    async def handle_attendance_created(self, event: Event):
        """Handle attendance record creation"""
        try:
            attendance_id = event.data.get("attendance_id")
            logger.info(f"Processing attendance created event for ID: {attendance_id}")
            
            # 1. Calculate work hours
            await self.hr_service.calculate_daily_work_hours(attendance_id)
            
            # 2. Check for overtime
            await self.hr_service.check_overtime_eligibility(attendance_id)
            
            # 3. Update monthly attendance summary
            await self.hr_service.update_monthly_attendance_summary(attendance_id)
            
            logger.info(f"Attendance created event processed for ID: {attendance_id}")
            
        except Exception as e:
            logger.error(f"Error handling attendance created event: {str(e)}")
            raise

    async def handle_attendance_check_in(self, event: Event):
        """Handle employee check-in"""
        try:
            employee_id = event.data.get("employee_id")
            attendance_id = event.data.get("attendance_id")
            logger.info(f"Processing check-in event for employee ID: {employee_id}")
            
            # 1. Check if employee is late
            await self.hr_service.check_late_arrival(employee_id, attendance_id)
            
            # 2. Send welcome message
            await self.hr_service.send_daily_welcome_message(employee_id)
            
            # 3. Update real-time attendance dashboard
            await self.hr_service.update_attendance_dashboard(employee_id, "check_in")
            
            logger.info(f"Check-in event processed for employee ID: {employee_id}")
            
        except Exception as e:
            logger.error(f"Error handling check-in event: {str(e)}")
            raise

    async def handle_attendance_check_out(self, event: Event):
        """Handle employee check-out"""
        try:
            employee_id = event.data.get("employee_id")
            attendance_id = event.data.get("attendance_id")
            logger.info(f"Processing check-out event for employee ID: {employee_id}")
            
            # 1. Calculate total work hours for the day
            await self.hr_service.calculate_daily_work_hours(attendance_id)
            
            # 2. Check for early departure
            await self.hr_service.check_early_departure(employee_id, attendance_id)
            
            # 3. Update attendance status
            await self.hr_service.finalize_daily_attendance(attendance_id)
            
            # 4. Update dashboard
            await self.hr_service.update_attendance_dashboard(employee_id, "check_out")
            
            logger.info(f"Check-out event processed for employee ID: {employee_id}")
            
        except Exception as e:
            logger.error(f"Error handling check-out event: {str(e)}")
            raise

    # ==================== LEAVE REQUEST EVENTS ====================
    async def handle_leave_request_created(self, event: Event):
        """Handle leave request creation"""
        try:
            leave_id = event.data.get("leave_id")
            logger.info(f"Processing leave request created event for ID: {leave_id}")
            
            # 1. Validate leave balance
            validation_result = await self.hr_service.validate_leave_balance(leave_id)
            
            if not validation_result["valid"]:
                await self.hr_service.auto_reject_leave_request(leave_id, validation_result["reason"])
                return
            
            # 2. Notify manager for approval
            await self.hr_service.notify_manager_leave_approval(leave_id)
            
            # 3. Check team availability
            await self.hr_service.check_team_availability_impact(leave_id)
            
            # 4. Send confirmation to employee
            await self.hr_service.send_leave_request_confirmation(leave_id)
            
            logger.info(f"Leave request created event processed for ID: {leave_id}")
            
        except Exception as e:
            logger.error(f"Error handling leave request created event: {str(e)}")
            raise

    async def handle_leave_request_approved(self, event: Event):
        """Handle leave request approval"""
        try:
            leave_id = event.data.get("leave_id")
            employee_id = event.data.get("employee_id")
            approved_by = event.data.get("approved_by")
            logger.info(f"Processing leave request approved event for ID: {leave_id}")
            
            # 1. Update employee leave balance
            await self.hr_service.deduct_leave_balance(employee_id, leave_id)
            
            # 2. Update team calendar
            await self.hr_service.update_team_calendar_leave(leave_id, "approved")
            
            # 3. Notify employee
            await self.hr_service.notify_employee_leave_approved(employee_id, leave_id)
            
            # 4. Notify team members
            await self.hr_service.notify_team_member_leave(employee_id, leave_id)
            
            # 5. Schedule return-to-work reminder
            await self.hr_service.schedule_return_to_work_reminder(leave_id)
            
            logger.info(f"Leave request approved event processed for ID: {leave_id}")
            
        except Exception as e:
            logger.error(f"Error handling leave request approved event: {str(e)}")
            raise

    async def handle_leave_request_rejected(self, event: Event):
        """Handle leave request rejection"""
        try:
            leave_id = event.data.get("leave_id")
            employee_id = event.data.get("employee_id")
            rejected_by = event.data.get("rejected_by")
            reason = event.data.get("reason", "Not specified")
            logger.info(f"Processing leave request rejected event for ID: {leave_id}")
            
            # 1. Notify employee with reason
            await self.hr_service.notify_employee_leave_rejected(employee_id, leave_id, reason)
            
            # 2. Log rejection reason
            await self.hr_service.log_leave_rejection(leave_id, rejected_by, reason)
            
            # 3. Offer alternatives if applicable
            await self.hr_service.suggest_alternative_leave_dates(leave_id)
            
            logger.info(f"Leave request rejected event processed for ID: {leave_id}")
            
        except Exception as e:
            logger.error(f"Error handling leave request rejected event: {str(e)}")
            raise

    # ==================== REPORT LOG EVENTS ====================
    async def handle_report_log_created(self, event: Event):
        """Handle report log creation"""
        try:
            log_id = event.data.get("log_id")
            logger.info(f"Processing report log created event for ID: {log_id}")
            
            # 1. Archive previous reports if needed
            await self.hr_service.archive_old_reports(log_id)
            
            # 2. Notify stakeholders if critical report
            await self.hr_service.notify_report_stakeholders(log_id)
            
            # 3. Schedule report cleanup
            await self.hr_service.schedule_report_cleanup(log_id)
            
            logger.info(f"Report log created event processed for ID: {log_id}")
            
        except Exception as e:
            logger.error(f"Error handling report log created event: {str(e)}")
            raise



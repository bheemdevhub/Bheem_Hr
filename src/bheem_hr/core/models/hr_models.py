from sqlalchemy import Column, String, Date, Float, Boolean, ForeignKey, Numeric, Text, DateTime, Table, UniqueConstraint, cast, Enum
from sqlalchemy.orm import relationship, remote
from sqlalchemy.dialects.postgresql import ENUM as PGEnum, UUID
from bheem_core.shared.models import Person, AuditMixin, Base, BankAccount, Passport, JobRequisitionSkill, Contact, Attachment
from bheem_core.shared.models import (
    InterviewRoundEnum, RatingEnum, EmploymentTypeEnum, EmploymentStatusEnum,
    InterviewStatusEnum, CandidateStatusEnum, OfferStatusEnum, BackgroundCheckStatusEnum,
    LeaveTypeEnum, LeaveStatusEnum
)
from bheem_core.shared.models import Activity, ActivityType, ActivityStatus, Rating, RatingType, Tag, TagCategory
from bheem_core.shared.models import PayType, SalaryComponentType
import uuid
from bheem_core.shared.models import Base, TimestampMixin, SoftDeleteMixin
from sqlalchemy import Column, Date, Time, String, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import declared_attr
from sqlalchemy import JSON


# --------------------- Employee ---------------------
class Employee(Person):
    __tablename__ = "employees"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"), primary_key=True, default=uuid.uuid4)
    employee_code = Column(String(50), unique=True, nullable=False)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=True)
    employment_type = Column(PGEnum(EmploymentTypeEnum, name="employment_type_enum", create_type=False), nullable=False)
    employment_status = Column(PGEnum(EmploymentStatusEnum, name="employment_status_enum", create_type=False), default=EmploymentStatusEnum.ACTIVE, nullable=False)
    work_location = Column(String(200), nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=True)
    hourly_rate = Column(Numeric(8, 2), nullable=True)
    currency = Column(String(3), default="USD")
    pay_frequency = Column(String(20), nullable=True)
    national_id = Column(String(50), nullable=True)
    tax_id = Column(String(50), nullable=True)
    password = Column(String(255), nullable=False)
    is_superadmin = Column(Boolean, default=False)
    _department_id = Column("department_id", UUID(as_uuid=True), ForeignKey("public.lookups.id"), nullable=True)
    _position_id = Column("position_id", UUID(as_uuid=True), ForeignKey("public.lookups.id"), nullable=True)
    _role_id = Column("role_id", UUID(as_uuid=True), ForeignKey("public.lookups.id"), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'employee'
    }

    department = relationship(
        "Lookup",
        foreign_keys=[_department_id],
        primaryjoin="Employee._department_id == Lookup.id"
    )
    position_rel = relationship(
        "Lookup",
        foreign_keys=[_position_id],
        primaryjoin="Employee._position_id == Lookup.id"
    )
    role = relationship(
        "Lookup",
        foreign_keys=[_role_id],
        primaryjoin="Employee._role_id == Lookup.id"
    )
    manager = relationship(
        "Employee",
        remote_side="Employee.id",
        backref="subordinates",
        foreign_keys=[manager_id],
        primaryjoin=(cast(id, UUID) == remote(manager_id))
    )
    bank_accounts = relationship("BankAccount", back_populates="person", cascade="all, delete-orphan")
    passports = relationship("Passport", back_populates="person", cascade="all, delete-orphan")

    # Unified relationships using entity_type/entity_id pattern
    activities = relationship(
        "Activity",
        primaryjoin="and_(Employee.id == foreign(Activity.entity_id), Activity.entity_type == 'EMPLOYEE')",
        viewonly=True
    )
    ratings = relationship(
        "Rating",
        primaryjoin="and_(Employee.id == foreign(Rating.entity_id), Rating.entity_type == 'EMPLOYEE')",
        viewonly=True
    )
    tags = relationship(
        "Tag",
        primaryjoin="and_(Employee.id == foreign(Tag.entity_id), Tag.entity_type == 'EMPLOYEE')",
        viewonly=True
    )

    __mapper_args__ = {"polymorphic_identity": "employee"}

    def __repr__(self):
        return f"<Employee(id={self.id}, code={self.employee_code}, name={self.display_name})>"

    @property
    def performance_rating(self) -> float:
        """Get latest performance rating for this employee"""
        # This would be calculated in the service layer
        return 0.0

    def add_activity(self, activity_type: ActivityType, subject: str, description: str = None, 
                    assigned_to: str = None, scheduled_date: DateTime = None) -> Activity:
        """Helper method to add activities to this employee"""
        activity = Activity(
            entity_type="EMPLOYEE",
            entity_id=self.id,
            activity_type=activity_type,
            subject=subject,
            description=description,
            assigned_to=assigned_to or self.manager_id,
            scheduled_date=scheduled_date,
            company_id=self.company_id
        )
        return activity

    def add_performance_rating(self, rating_type: RatingType, rating_value: float, 
                             comments: str = None, rated_by: str = None) -> Rating:
        """Helper method to add performance ratings to this employee"""
        rating = Rating(
            entity_type="EMPLOYEE",
            entity_id=self.id,
            rating_type=rating_type,
            rating_value=rating_value,
            comments=comments,
            rated_by=rated_by or self.manager_id,
            company_id=self.company_id
        )
        return rating

    def add_tag(self, tag_value: str, tag_category: TagCategory = None, tag_color: str = None) -> Tag:
        """Helper method to add tags to this employee"""
        tag = Tag(
            entity_type="EMPLOYEE",
            entity_id=self.id,
            tag_category=tag_category,
            tag_value=tag_value,
            tag_color=tag_color,
            company_id=self.company_id
        )
        return tag

    @property
    def department_id(self):
        return self._department_id

    @department_id.setter
    def department_id(self, value):
        if value is not None and not isinstance(value, str):
            value = str(value)
        self._department_id = value

    @property
    def position_id(self):
        return self._position_id

    @position_id.setter
    def position_id(self, value):
        if value is not None and not isinstance(value, str):
            value = str(value)
        self._position_id = value

    @property
    def role_id(self):
        return self._role_id

    @role_id.setter
    def role_id(self, value):
        if value is not None and not isinstance(value, str):
            value = str(value)
        self._role_id = value


# --------------------- Job Requisition ---------------------
class JobRequisition(Base, AuditMixin):
    __tablename__ = "job_requisitions"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("public.lookups.id"), nullable=False)
    hiring_manager_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=False)
    job_type_id = Column(UUID(as_uuid=True), ForeignKey("public.lookups.id"), nullable=False)
    job_title = Column(String(255), nullable=False)
    number_of_openings = Column(Numeric, nullable=False, default=1)
    location = Column(String(255), nullable=False)
    salary_min = Column(Numeric, nullable=True)
    salary_max = Column(Numeric, nullable=True)
    requisition_date = Column(Date, nullable=False)
    job_description = Column(String, nullable=False)
    experience_required = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    hiring_manager = relationship("Employee")
    department = relationship(
        "Lookup",
        foreign_keys=[department_id],
        primaryjoin="JobRequisition.department_id == Lookup.id"
    )
    job_type = relationship(
        "Lookup",
        foreign_keys=[job_type_id],
        primaryjoin="JobRequisition.job_type_id == Lookup.id"
    )
    skills = relationship("JobRequisitionSkill", backref="job_requisition", cascade="all, delete-orphan")

    # Unified relationships using entity_type/entity_id pattern
    activities = relationship(
        "Activity",
        primaryjoin="and_(JobRequisition.id == foreign(Activity.entity_id), Activity.entity_type == 'JOB_REQUISITION')",
        viewonly=True
    )
    tags = relationship(
        "Tag",
        primaryjoin="and_(JobRequisition.id == foreign(Tag.entity_id), Tag.entity_type == 'JOB_REQUISITION')",
        viewonly=True
    )

    def __repr__(self):
        return f"<JobRequisition(id={self.id}, job_title={self.job_title})>"

    def add_recruitment_activity(self, activity_type: ActivityType, subject: str, 
                               description: str = None, assigned_to: str = None) -> Activity:
        """Helper method to add recruitment activities"""
        activity = Activity(
            entity_type="JOB_REQUISITION",
            entity_id=self.id,
            activity_type=activity_type,
            subject=subject,
            description=description,
            assigned_to=assigned_to or self.hiring_manager_id,
            company_id=self.company_id
        )
        return activity


# --------------------- Candidate ---------------------
class Candidate(Person, AuditMixin):
    __tablename__ = "candidates"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"), primary_key=True, default=uuid.uuid4)
    applied_position_id = Column(UUID(as_uuid=True), ForeignKey("hr.job_requisitions.id"))
    recruiter_assigned = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=True)
    application_date = Column(Date, nullable=False)
    notice_period = Column(String)
    interview_availability = Column(String)
    skills_matched = Column(Numeric)
    offer_letter_signed = Column(Boolean, default=False)
    id_proof_submitted = Column(Boolean, default=False)
    educational_documents = Column(Boolean, default=False)
    status = Column(PGEnum(CandidateStatusEnum, name="candidate_status_enum", create_type=False), default=CandidateStatusEnum.APPLIED, nullable=False)
    # Note: company_id is inherited from Person class    # Note: company_id is inherited from Person class
    
    recruiter = relationship("Employee", foreign_keys=[recruiter_assigned])
    applied_position = relationship("JobRequisition", backref="candidates")
    contacts = relationship("Contact", back_populates="person", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="candidate", cascade="all, delete-orphan")
    onboarding_checklist = relationship("OnboardingChecklist", back_populates="candidate", uselist=False)

    # Unified relationships using entity_type/entity_id pattern
    activities = relationship(
        "Activity",
        primaryjoin="and_(Candidate.id == foreign(Activity.entity_id), Activity.entity_type == 'CANDIDATE')",
        viewonly=True
    )
    ratings = relationship(
        "Rating",
        primaryjoin="and_(Candidate.id == foreign(Rating.entity_id), Rating.entity_type == 'CANDIDATE')",
        viewonly=True
    )
    tags = relationship(
        "Tag",
        primaryjoin="and_(Candidate.id == foreign(Tag.entity_id), Tag.entity_type == 'CANDIDATE')",
        viewonly=True
    )

    __mapper_args__ = {"polymorphic_identity": "candidate"}

    def __repr__(self):
        return f"<Candidate(id={self.id}, name={self.display_name}, status={self.status})>"

    def add_interview_activity(self, interview_type: str, scheduled_date: DateTime, 
                             interviewer_id: str = None) -> Activity:
        """Helper method to add interview activities"""
        activity = Activity(
            entity_type="CANDIDATE",
            entity_id=self.id,
            activity_type=ActivityType.MEETING,
            subject=f"{interview_type} Interview",
            description=f"Interview for {self.applied_position.job_title if self.applied_position else 'position'}",
            assigned_to=interviewer_id or self.recruiter_assigned,
            scheduled_date=scheduled_date,
            company_id=self.company_id
        )
        return activity

    def add_interview_rating(self, rating_value: float, comments: str = None, 
                           rated_by: str = None) -> Rating:
        """Helper method to add interview ratings"""
        rating = Rating(
            entity_type="CANDIDATE",
            entity_id=self.id,
            rating_type=RatingType.OVERALL,
            rating_value=rating_value,
            comments=comments,
            rated_by=rated_by,
            company_id=self.company_id
        )
        return rating


# --------------------- Interview ---------------------
class Interview(Base, AuditMixin):
    __tablename__ = "interviews"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("hr.candidates.id"), nullable=False)
    interview_date_time = Column(DateTime(timezone=True), nullable=False)
    interviewer_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=True)
    round_type = Column(PGEnum(InterviewRoundEnum, name="round_type_enum", create_type=False), nullable=False)
    feedback_comments = Column(Text, nullable=True)
    rating = Column(PGEnum(RatingEnum, name="interview_rating_enum", create_type=False), nullable=True)
    next_step = Column(String(255), nullable=True)
    status = Column(PGEnum(InterviewStatusEnum, name="interview_status_enum", create_type=False), default=InterviewStatusEnum.SCHEDULED, nullable=False)
    is_active = Column(Boolean, default=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    candidate = relationship("Candidate", back_populates="interviews")
    interviewer = relationship("Employee", backref="interviews_conducted", foreign_keys=[interviewer_id])


# --------------------- Offer ---------------------
class Offer(Base, AuditMixin):
    __tablename__ = "offers"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("hr.candidates.id"), nullable=False)
    offer_date = Column(Date, nullable=False)
    offered_ctc = Column(Float, nullable=False)
    joining_date = Column(Date, nullable=False)
    offer_status = Column(PGEnum(OfferStatusEnum, name="offer_status_enum", create_type=False), nullable=False)
    background_check_status = Column(PGEnum(BackgroundCheckStatusEnum, name="background_check_status_enum", create_type=False), nullable=False)
    documents_submitted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    candidate = relationship("Candidate", back_populates="offers")

    def __repr__(self):
        return f"<Offer id={self.id} candidate_id={self.candidate_id} status={self.offer_status}>"


# --------------------- Onboarding Checklist ---------------------
class OnboardingChecklist(Base, AuditMixin):
    __tablename__ = "onboarding_checklists"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("hr.candidates.id"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("hr.offers.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)
    
    offer_letter_signed = Column(Boolean, default=False)
    id_proof_submitted = Column(Boolean, default=False)
    educational_documents = Column(Boolean, default=False)
    background_verification = Column(Boolean, default=False)
    bank_account_details = Column(Boolean, default=False)
    work_email_created = Column(Boolean, default=False)
    system_allocation = Column(Boolean, default=False)
    software_access_setup = Column(Boolean, default=False)
    welcome_kit_given = Column(Boolean, default=False)
    assigned_buddy = Column(Boolean, default=False)
    first_day_orientation = Column(Boolean, default=False)
    department_introduction = Column(Boolean, default=False)
    hr_policy_acknowledgement = Column(Boolean, default=False)
    training_plan_shared = Column(Boolean, default=False)
    probation_period_set = Column(Boolean, default=False)
    employee_id_created = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, nullable=False)

    candidate = relationship("Candidate", back_populates="onboarding_checklist")
    offer = relationship("Offer", uselist=False)


class SalaryStructure(Base, AuditMixin):
    __tablename__ = "salary_structures"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=False)
    effective_date = Column(Date, nullable=False)
    pay_type = Column(Enum(PayType, name="pay_type_enum"), default=PayType.MONTHLY)
    is_active = Column(Boolean, default=True)

    components = relationship(
        "SalaryComponent",
        back_populates="structure",
        cascade="all, delete-orphan",
        lazy="selectin",  # <-- Important for async-safe eager loading
    )



class SalaryComponent(Base):
    __tablename__ = "salary_components"
    __table_args__ = {'schema': 'hr', "extend_existing": True}  # Changed from 'payroll' to 'hr'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    structure_id = Column(UUID(as_uuid=True), ForeignKey("hr.salary_structures.id"), nullable=False)
    name = Column(String, nullable=False)
    component_type = Column(Enum(SalaryComponentType, name="salary_component_type_enum"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    taxable = Column(Boolean, default=True)

    structure = relationship("SalaryStructure", back_populates="components")


class PayrollRun(Base, AuditMixin):
    __tablename__ = "payroll_runs"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    month = Column(String(7), nullable=False)  # format: YYYY-MM
    status = Column(String(20), default="Draft")  # Draft, Processed, Paid
    processed_by = Column(String(50), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)


class Payslip(Base, AuditMixin):
    __tablename__ = "payslips"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=False)
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("hr.payroll_runs.id"), nullable=False)
    total_earnings = Column(Numeric(12, 2), nullable=False)
    total_deductions = Column(Numeric(12, 2), nullable=False)
    net_pay = Column(Numeric(12, 2), nullable=False)
    attachment_id = Column(UUID(as_uuid=True), ForeignKey("public.attachments.id"), nullable=True)
    attachment = relationship("Attachment", foreign_keys=[attachment_id], lazy="joined")


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (


        UniqueConstraint('employee_id', 'date', name='uq_employee_date'),
        {'schema': 'hr', "extend_existing": True}  # Add schema here
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)
    status = Column(String(20), nullable=False, default="Present")

    created_at = Column(Date, server_default=func.now())
    updated_at = Column(Date, onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)




class LeaveRequest(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "leave_requests"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=False)
    leave_type = Column(Enum(LeaveTypeEnum, name="leave_type_enum"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(Enum(LeaveStatusEnum, name="leave_status_enum"), default=LeaveStatusEnum.PENDING, nullable=False)



class ReportLog(Base, AuditMixin):
    __tablename__ = "report_logs"
    __table_args__ = {'schema': 'hr', "extend_existing": True}  # Changed from 'report' to 'hr'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_name = Column(String(255), nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    generated_on = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    parameters = Column(JSON, nullable=True)
    attachment_id = Column(UUID(as_uuid=True), ForeignKey("public.attachments.id"), nullable=True)
    attachment = relationship("Attachment", foreign_keys=[attachment_id], lazy="joined")


class HRActionItem(Base, AuditMixin):
    __tablename__ = "hr_action_items"
    __table_args__ = {'schema': 'hr', "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, completed, cancelled
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("hr.employees.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 👇 This line disables the inherited updated_by column
    @declared_attr
    def updated_by(cls):
        return None  # disables inherited column mapping

    # Relationships
    assignee = relationship("Employee", foreign_keys=[assigned_to], backref="assigned_hr_actions")
    creator = relationship("User", foreign_keys=[created_by], backref="created_hr_actions")




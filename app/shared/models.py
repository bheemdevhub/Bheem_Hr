
from sqlalchemy import Column, String, Boolean, Text, DateTime, Date, ForeignKey, func, Table, Numeric, JSON, Enum, UniqueConstraint, Index, Integer, DECIMAL
from sqlalchemy.orm import relationship, object_session
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..core.database import Base
import enum
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAEnum


def generate_uuid():
    return str(uuid.uuid4())

class EntityTypes(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    LEAD = "LEAD"
    EMPLOYEE = "EMPLOYEE"
    VENDOR = "VENDOR"
    PROJECT = "PROJECT"
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"
    SKU = "SKU"
    ACTIVITY = "ACTIVITY"
    DOCUMENT = "DOCUMENT"
    TAG = "TAG"
    RATING = "RATING"
    # Add more as needed for your domain

class AuditMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(50), nullable=True)
    updated_by = Column(String(50), nullable=True)


class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    is_active = Column(Boolean, default=True)


class Address(BaseModel):
    __tablename__ = "addresses"
    __table_args__ = {'schema': 'public'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    address_type = Column(String(20), default="PRIMARY")
    line1 = Column(String(255), nullable=False)
    line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="USA")
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Address(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id}, city={self.city})>"


class Note(BaseModel):
    __tablename__ = "notes"
    __table_args__ = {'schema': 'public'}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="GENERAL")
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Note(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id}, title={self.title})>"


class Attachment(BaseModel):
    __tablename__ = "attachments"
    __table_args__ = {'schema': 'public'}  

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=True)
    file_size = Column(String(20), nullable=True)
    mime_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class Contact(BaseModel):
    __tablename__ = "contacts"
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"), nullable=False)
    email_primary = Column(String(100), nullable=True)
    email_secondary = Column(String(100), nullable=True)
    phone_primary = Column(String(20), nullable=True)
    phone_secondary = Column(String(20), nullable=True)
    phone_mobile = Column(String(20), nullable=True)
    phone_work = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)

    person = relationship("Person", back_populates="contacts")

    def __repr__(self):
        return f"<Contact(id={self.id}, person_id={self.person_id}, email_primary={self.email_primary})>"


class Gender(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class MaritalStatus(enum.Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    OTHER = "other"


class LeadStage(enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class LeadPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class ActivityType(enum.Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"


class Person(BaseModel):
    __tablename__ = "persons"
    __table_args__ = {'schema': 'public'}
    

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_type = Column(String(20), nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    preferred_name = Column(String(100), nullable=True)
    title = Column(String(20), nullable=True)
    suffix = Column(String(20), nullable=True)

    date_of_birth = Column(Date, nullable=True)
    gender = Column(PGEnum(Gender, name="gender_enum", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=True)
    marital_status = Column(PGEnum(MaritalStatus, name="marital_status_enum", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=True)
    nationality = Column(String(100), nullable=True)
    blood_group = Column(String(10), nullable=True)

    is_active = Column(Boolean, default=True)
    supabase_id = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'person',
        'polymorphic_on': person_type
    }

    addresses = relationship(
        "Address",
        primaryjoin="and_(Person.id == foreign(Address.entity_id), Address.entity_type == Person.person_type)",
        viewonly=True
    )
    notes = relationship(
        "Note",
        primaryjoin="and_(Person.id == foreign(Note.entity_id), Note.entity_type == Person.person_type)",
        viewonly=True
    )
    attachments = relationship(
        "Attachment",
        primaryjoin="and_(Person.id == foreign(Attachment.entity_id), Attachment.entity_type == Person.person_type)",
        viewonly=True
    )
    contacts = relationship("Contact", back_populates="person", cascade="all, delete-orphan")
    bank_accounts = relationship("BankAccount", back_populates="person", cascade="all, delete-orphan")
    passports = relationship("Passport", back_populates="person", cascade="all, delete-orphan")
    social_profiles = relationship("app.shared.models.SocialProfile", back_populates="person", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Person(id={self.id}, name={self.full_name}, type={self.person_type})>"

    @property
    def full_name(self) -> str:
        parts = []
        if self.title:
            parts.append(self.title)
        parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts)

    @property
    def display_name(self) -> str:
        return self.preferred_name or f"{self.first_name} {self.last_name}"

    @property
    def initials(self) -> str:
        initials = self.first_name[0] if self.first_name else ""
        if self.middle_name:
            initials += self.middle_name[0]
        if self.last_name:
            initials += self.last_name[0]
        return initials.upper()


class BankAccount(BaseModel):
    """Enhanced bank account model supporting both personal and company accounts"""
    __tablename__ = "bank_accounts"
    __table_args__ = {"schema": "public"}  # This is critical

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity relationship - can be linked to Person OR Company
    entity_type = Column(String(20), nullable=False, default="PERSON")  # PERSON, COMPANY
    person_id = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=True)

    
    # Account details
    account_name = Column(String(255), nullable=False)  # Enhanced for company accounts
    account_number = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=True)  # CHECKING, SAVINGS, CREDIT, BUSINESS
    
    # Bank details (enhanced)
    bank_name = Column(String(200), nullable=False)
    bank_branch = Column(String(255))
    routing_number = Column(String(50), nullable=True)
    swift_code = Column(String(20))
    iban = Column(String(50))
    
    # Currency and balances (for company accounts)
    currency = Column(String(3), default="USD")
    current_balance = Column(Numeric(15, 2), default=0)
    available_balance = Column(Numeric(15, 2))
    
    # Status flags
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # For company default account
    
    # Accounting integration (for company accounts)
    cash_account_id = Column(UUID(as_uuid=True))  # Reference to accounting.accounts
    
    # Relationships
    person = relationship("Person", back_populates="bank_accounts")
    
    def __repr__(self):
        return f"<BankAccount(id={self.id}, entity_type={self.entity_type}, bank_name={self.bank_name}, account_number={self.account_number})>"
    
    # =============================================
    # Unified Entity Relationship Helper Methods
    # =============================================
    
    def get_activities(self):
        """Get all activities for this bank account"""
        from app.shared.models import Activity
        session = object_session(self)
        return session.query(Activity).filter(
            Activity.entity_type == "BANK_ACCOUNT",
            Activity.entity_id == str(self.id),
            Activity.is_active == True
        ).all()
    
    def add_activity(self, activity_type, subject, description=None, assigned_to=None, **kwargs):
        """Add a new activity to this bank account"""
        from app.shared.models import Activity
        session = object_session(self)
        
        activity = Activity(
            entity_type="BANK_ACCOUNT",
            entity_id=str(self.id),
            activity_type=activity_type,
            subject=subject,
            description=description,
            assigned_to=assigned_to,
            company_id=self.company_id if self.entity_type == "COMPANY" else None,
            **kwargs
        )
        session.add(activity)
        return activity


class Passport(BaseModel):
    __tablename__ = "passports"
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"), nullable=False)
    passport_number = Column(String(50), nullable=False)
    expiry_date = Column(Date, nullable=True)
    country_of_issue = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False)

    person = relationship("Person", back_populates="passports")

    def __repr__(self):
        return f"<Passport(id={self.id}, person_id={self.person_id}, passport_number={self.passport_number})>"




class LookupType(enum.Enum):
    DEPARTMENT = "department"
    POSITION = "position"
    EMPLOYEE_STATUS = "employee_status"
    CANDIDATE_STATUS = "candidate_status"
    JOB_TYPE = "job_type"
    SKILL = "skill"           # Added for job requisition skills
    ROLE = "role"             # Added for roles
    PERMISSION = "permission" # Added for permissions
   


class Lookup(Base):
    """
    Lookup table for storing reference data like departments, positions, statuses, etc.

    Examples:
    - Department: type='department', code='ENG', name='Engineering'
    - Position: type='position', code='SE_SR', name='Senior Software Engineer' 
    - Status: type='employee_status', code='ACTIVE', name='Active'
    """
    __tablename__ = "lookups"
    __table_args__ = (
        Index('idx_lookup_type_active', 'type', 'is_active'),
        Index('idx_lookup_code_active', 'code', 'is_active'),
        {"schema": "public"}  
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(PGEnum(LookupType, name="lookup_type_enum", values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Lookup(id={self.id}, type={self.type}, code={self.code}, name={self.name})>"


role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("public.lookups.id"), primary_key=True),  
    Column("permission_id", UUID(as_uuid=True), ForeignKey("public.lookups.id"), primary_key=True) , 
   
)


class SocialProfile(Base):
    __tablename__ = 'social_profiles'
    __table_args__ = {'schema': 'public'}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey('public.persons.id'), nullable=False)
    
    linkedin_profile = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    profile_image_url = Column(String(255), nullable=True)

    person = relationship('Person', back_populates='social_profiles')


class OfferStatusEnum(str, enum.Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class BackgroundCheckStatusEnum(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"


class InterviewRoundEnum(str, enum.Enum):
    TECHNICAL = "Technical"
    HR = "HR"
    MANAGERIAL = "Managerial"
    FINAL = "Final"


class RatingEnum(str, enum.Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    POOR = "Poor"
    REJECTED = "Rejected"


class JobRequisitionSkill(Base):
    __tablename__ = "job_requisition_skills"
    __table_args__ = {'schema': 'hr'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_requisition_id = Column(UUID(as_uuid=True), ForeignKey("hr.job_requisitions.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("public.lookups.id"), nullable=False)  # Explicit public schema


    skill = relationship("Lookup", foreign_keys=[skill_id])

    def __repr__(self):
        return f"<JobRequisitionSkill(id={self.id}, job_requisition_id={self.job_requisition_id}, skill_id={self.skill_id})>"



class EmploymentTypeEnum(str, enum.Enum):
    FULL_TIME = "Full-Time"
    PART_TIME = "Part-Time"
    CONTRACT = "Contract"
    INTERN = "Intern"
    TEMPORARY = "Temporary"
    OTHER = "Other"


class EmploymentStatusEnum(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    TERMINATED = "Terminated"
    ON_LEAVE = "On Leave"
    RETIRED = "Retired"
    PROBATION = "Probation"
    SUSPENDED = "Suspended"


class InterviewStatusEnum(str, enum.Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"
    RESCHEDULED = "Rescheduled"


class CandidateStatusEnum(str, enum.Enum):
    APPLIED = "Applied"
    SCREENING = "Screening"
    INTERVIEW = "Interview"
    OFFERED = "Offered"
    HIRED = "Hired"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"




SCHEMA = "public"
SCHEMA = "public"

# -----------------------------
# Enums with str for API safety
# -----------------------------

class CompanyType(str, enum.Enum):
    HOLDING = "HOLDING"
    SUBSIDIARY = "SUBSIDIARY"
    DIVISION = "DIVISION"
    BRANCH = "BRANCH"


class ConsolidationMethod(str, enum.Enum):
    FULL = "FULL"
    EQUITY = "EQUITY"
    PROPORTIONAL = "PROPORTIONAL"
    NONE = "NONE"


class RateType(str, enum.Enum):
    SPOT = "SPOT"
    AVERAGE = "AVERAGE"
    BUDGET = "BUDGET"


# -----------------------------
# Company Model
# -----------------------------

class Company(BaseModel):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint('company_code', name='uq_company_code'),
        {'schema': 'public'}
        
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_code = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(200), nullable=False)
    legal_name = Column(String(300))
    company_type = Column(Enum(CompanyType, name="companytype", create_type=False), nullable=False)
    parent_company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"))
    
    functional_currency_id = Column(UUID(as_uuid=True), ForeignKey("public.currencies.id"))
    reporting_currency_id = Column(UUID(as_uuid=True), ForeignKey("public.currencies.id"))
    consolidation_method = Column(Enum(ConsolidationMethod, name="consolidationmethod", create_type=False), default=ConsolidationMethod.FULL)
    
    address = Column(Text)
    tax_id = Column(String(50))
    registration_number = Column(String(50))

    parent_company = relationship(
        "Company",
        remote_side=lambda: [Company.id],
        foreign_keys=[parent_company_id],
        backref="subsidiaries"
    )
    fiscal_years = relationship("FiscalYear", back_populates="company")



# -----------------------------
# Company Relationship
# -----------------------------

class CompanyRelationship(BaseModel):
    __tablename__ = "company_relationships"
    __table_args__ = {'schema': SCHEMA}


    parent_company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id", ondelete="RESTRICT"), nullable=False)
    subsidiary_company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id", ondelete="RESTRICT"), nullable=False)
    ownership_percentage = Column(Numeric(5, 2), nullable=False)
    control_percentage = Column(Numeric(5, 2))
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date)

    parent_company = relationship("Company", foreign_keys=[parent_company_id], backref="direct_subsidiaries")
    subsidiary_company = relationship("Company", foreign_keys=[subsidiary_company_id], backref="parent_links")


# -----------------------------
# Currency Model
# -----------------------------
class Currency(BaseModel):
    __tablename__ = "currencies"
    __table_args__ = (
        UniqueConstraint('currency_code', name='uq_currency_code'),
        Index('ix_currency_code', 'currency_code'),
        {'schema': SCHEMA}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    currency_code = Column(String(3), nullable=False)  # e.g., USD, INR
    currency_name = Column(String(100), nullable=False)
    symbol = Column(String(10))
    decimal_places = Column(Numeric(2), default=2)


# ----------------------
# ExchangeRate Model
# ----------------------
class ExchangeRate(BaseModel):
    __tablename__ = "exchange_rates"
    __table_args__ = {'schema': SCHEMA}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    from_currency_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.currencies.id", ondelete="RESTRICT"), nullable=False)
    to_currency_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.currencies.id", ondelete="RESTRICT"), nullable=False)

    rate_date = Column(Date, nullable=False)
    rate = Column(Numeric(15, 6), nullable=False)
    rate_type = Column(SQLAEnum(RateType, name="ratetype", create_type=False), default=RateType.SPOT, nullable=False)

    # Relationships
    from_currency = relationship("Currency", foreign_keys=[from_currency_id])
    to_currency = relationship("Currency", foreign_keys=[to_currency_id])
# -------------------------------
# ENUMS (str-based for safety)
# -------------------------------

class AccountCategory(str, enum.Enum):
    ASSETS = "ASSETS"
    LIABILITIES = "LIABILITIES"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSES = "EXPENSES"

class AccountType(str, enum.Enum):
    CURRENT_ASSETS = "CURRENT_ASSETS"
    FIXED_ASSETS = "FIXED_ASSETS"
    CURRENT_LIABILITIES = "CURRENT_LIABILITIES"
    LONG_TERM_LIABILITIES = "LONG_TERM_LIABILITIES"
    SHAREHOLDERS_EQUITY = "SHAREHOLDERS_EQUITY"
    OPERATING_REVENUE = "OPERATING_REVENUE"
    OTHER_REVENUE = "OTHER_REVENUE"
    COST_OF_GOODS_SOLD = "COST_OF_GOODS_SOLD"
    OPERATING_EXPENSES = "OPERATING_EXPENSES"
    OTHER_EXPENSES = "OTHER_EXPENSES"

class CenterType(str, enum.Enum):
    PROFIT = "PROFIT"
    COST = "COST"
    DEPARTMENT = "DEPARTMENT"
    PROJECT = "PROJECT"

class ProfitCenterType(str, enum.Enum):
    COMPANY = "COMPANY"
    DIVISION = "DIVISION"
    PRODUCT_LINE = "PRODUCT_LINE"
    GEOGRAPHY = "GEOGRAPHY"
    CUSTOMER_SEGMENT = "CUSTOMER_SEGMENT"

class SKUType(str, enum.Enum):
    GOODS = "GOODS"
    SERVICE = "SERVICE"
    MATERIAL = "MATERIAL"

class CostingMethod(str, enum.Enum):
    FIFO = "FIFO"
    LIFO = "LIFO"
    WEIGHTED_AVERAGE = "WEIGHTED_AVERAGE"
    STANDARD = "STANDARD"

class EntryStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


# -----------------------------
# Budget/Variance/Approval Enums (str-based for API safety)
# -----------------------------
class BudgetType(str, enum.Enum):
    OPERATING = "OPERATING"
    CAPITAL = "CAPITAL"
    PROJECT = "PROJECT"
    DEPARTMENTAL = "DEPARTMENTAL"
    MASTER = "MASTER"

class BudgetStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    LOCKED = "LOCKED"

class VersionType(str, enum.Enum):
    ORIGINAL = "ORIGINAL"
    REVISION = "REVISION"
    FORECAST = "FORECAST"
    REFORECAST = "REFORECAST"

class AllocationMethod(str, enum.Enum):
    EQUAL = "EQUAL"
    WEIGHTED = "WEIGHTED"
    CUSTOM = "CUSTOM"
    HISTORICAL = "HISTORICAL"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DELEGATED = "DELEGATED"

class VarianceType(str, enum.Enum):
    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"
    NEUTRAL = "NEUTRAL"

class SignificanceLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# -----------------------------
# Department Model
# -----------------------------

class Department(BaseModel):
    __tablename__ = "departments"
    __table_args__ = {'schema': SCHEMA}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)

class UserRole(str, enum.Enum):
    SUPERADMIN = "SuperAdmin"
    ADMIN = "Admin"
    ACCOUNTANT = "Accountant"
    HR = "HR"
    EMPLOYEE = "Employee"
    SALES_MANAGER = "SalesManager"
    SALES_REP = 'SalesRep'
    VIEWER = 'Viewer'
    PROJECT_MANAGER = 'ProjectManager'



# -----------------------------
# Product and Service Management Models
# -----------------------------

class ProductType(str, enum.Enum):
    PHYSICAL = "PHYSICAL"
    DIGITAL = "DIGITAL"
    SERVICE = "SERVICE"
    SUBSCRIPTION = "SUBSCRIPTION"


class ServiceType(str, enum.Enum):
    CONSULTING = "CONSULTING"
    MAINTENANCE = "MAINTENANCE"
    SUPPORT = "SUPPORT"
    TRAINING = "TRAINING"
    CUSTOM = "CUSTOM"


# class BillingType(str, enum.Enum):
#     HOURLY = "HOURLY"
#     FIXED = "FIXED"
#     RECURRING = "RECURRING"
#     USAGE_BASED = "USAGE_BASED"


class UnitOfMeasure(BaseModel):
    """Unit of measure for products and services"""
    __tablename__ = "units_of_measure"
    __table_args__ = (
        UniqueConstraint('code', name='uq_uom_code'),
        {'schema': 'public'}
    )

    code = Column(String(10), unique=True, nullable=False)  # kg, pcs, hrs, etc.
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # WEIGHT, VOLUME, TIME, COUNT, etc.
    is_active = Column(Boolean, default=True)


# class TaxCategory(Base):
#     __tablename__ = "tax_categories"
#     __table_args__ = (
#         UniqueConstraint('code', name='uq_tax_category_code'),
#         {'schema': 'public'}
#     )

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     code = Column(String(20), unique=True, nullable=False)
#     name = Column(String(100), nullable=False)
#     description = Column(Text)
#     default_tax_rate = Column(Numeric(5, 2), default=0)
#     is_active = Column(Boolean, default=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
#     created_by = Column(UUID(as_uuid=True))
#     updated_by = Column(UUID(as_uuid=True))




class TaxCategory(BaseModel):
    """Tax categories for products and services"""
    __tablename__ = "tax_categories"
    __table_args__ = (
        UniqueConstraint('code', name='uq_tax_category_code'),
        {'schema': 'public'}
    )

  
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    default_tax_rate = Column(Numeric(5, 2), default=0)
    is_active = Column(Boolean, default=True)


# class ProductCategory(BaseModel):
#     """Product category hierarchy"""
#     __tablename__ = "product_categories"
#     __table_args__ = (
#         UniqueConstraint('code', name='uq_product_category_code'),
#         {'schema': 'public'}
#     )

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     code = Column(String(20), unique=True, nullable=False)
#     name = Column(String(100), nullable=False)
#     description = Column(Text)

#     # Hierarchy
#     parent_id = Column(UUID(as_uuid=True), ForeignKey('public.product_categories.id'))
#     parent = relationship(
#         "ProductCategory",
#         remote_side="[ProductCategory.id]",
#         foreign_keys=[parent_id],
#         back_populates="children"
#     )
#     children = relationship("ProductCategory", back_populates="parent")

#     # Display
#     sort_order = Column(Integer, default=0)
#     is_active = Column(Boolean, default=True)

#     # Relationships
#     products = relationship("Product", back_populates="category")


# class Product(BaseModel):
#     """Shared Product model for SKU management across modules"""
#     __tablename__ = "products"
#     __table_args__ = (
#         UniqueConstraint('sku', name='uq_product_sku'),
#         Index('ix_product_sku', 'sku'),
#         Index('ix_product_name', 'name'),
#         {'schema': 'public'}
#     )

#     sku = Column(String(50), unique=True, nullable=False, index=True)
#     name = Column(String(255), nullable=False)
#     description = Column(Text)
#     short_description = Column(String(500))

#     category_id = Column(UUID(as_uuid=True), ForeignKey('public.product_categories.id'), nullable=True)
#     category = relationship("ProductCategory", back_populates="products")

#     product_type = Column(Enum(ProductType, name="product_type_enum", create_type=False), nullable=False)
#     is_service = Column(Boolean, default=False)
#     is_stockable = Column(Boolean, default=True)
#     is_purchasable = Column(Boolean, default=True)
#     is_sellable = Column(Boolean, default=True)

#     cost_price = Column(Numeric(15, 2))
#     list_price = Column(Numeric(15, 2))
#     currency_id = Column(UUID(as_uuid=True), ForeignKey('public.currencies.id'))
    # cost_price = Column(Numeric(15, 2))
    # list_price = Column(Numeric(15, 2))
    # currency_id = Column(UUID(as_uuid=True), ForeignKey('public.currencies.id'))

#     unit_of_measure_id = Column(UUID(as_uuid=True), ForeignKey('public.units_of_measure.id'))
#     unit_of_measure = relationship("UnitOfMeasure")

#     tax_category_id = Column(UUID(as_uuid=True), ForeignKey('public.tax_categories.id'))
#     tax_category = relationship("TaxCategory")
#     income_account_id = Column(UUID(as_uuid=True))
#     expense_account_id = Column(UUID(as_uuid=True))
#     cogs_account_id = Column(UUID(as_uuid=True))

#     track_quantity = Column(Boolean, default=True)
#     reorder_point = Column(Numeric(10, 3), default=0)
#     maximum_stock = Column(Numeric(10, 3))
#     costing_method = Column(Enum(CostingMethod, name="costing_method_enum", create_type=False), default=CostingMethod.FIFO)

#     weight = Column(Numeric(10, 3))
#     weight_unit = Column(String(10))
#     dimensions = Column(JSON)

#     digital_file_url = Column(String(500))
#     download_limit = Column(Integer)

#     is_active = Column(Boolean, default=True)
#     is_featured = Column(Boolean, default=False)
#     launch_date = Column(Date)
#     discontinue_date = Column(Date)

#     meta_title = Column(String(255))
#     meta_description = Column(Text)
#     tags = Column(JSON)

#     attributes = Column(JSON)
#     images = Column(JSON)
#     documents = Column(JSON)

#     company_id = Column(UUID(as_uuid=True), ForeignKey('public.companies.id'), nullable=False)

    # company_id = Column(UUID(as_uuid=True), ForeignKey('public.companies.id'), nullable=False)

# class Service(BaseModel):
#     """Service catalog for time-based and recurring services"""
#     __tablename__ = "services"
#     __table_args__ = (
#         UniqueConstraint('code', name='uq_service_code'),
#         Index('ix_service_code', 'code'),
#         {'schema': 'public'}
#     )

#     # Basic information
#     code = Column(String(50), unique=True, nullable=False)
#     name = Column(String(255), nullable=False)
#     description = Column(Text)
#     short_description = Column(String(500))
    
#     # Service type and billing
#     service_type = Column(Enum(ServiceType, name="service_type_enum", create_type=False), nullable=False)
#     billing_type = Column(Enum(BillingType, name="billing_type_enum", create_type=False), nullable=False)
    # Service type and billing
    # service_type = Column(Enum(ServiceType, name="service_type_enum", create_type=False), nullable=False)
    # billing_type = Column(Enum(BillingType, name="billing_type_enum", create_type=False), nullable=False)
    
#     # Pricing
#     hourly_rate = Column(Numeric(15, 2))
#     fixed_price = Column(Numeric(15, 2))
#     minimum_hours = Column(Numeric(8, 2))
#     maximum_hours = Column(Numeric(8, 2))
#     currency_id = Column(UUID(as_uuid=True), ForeignKey('public.currencies.id'))
    # Pricing
    # hourly_rate = Column(Numeric(15, 2))
    # fixed_price = Column(Numeric(15, 2))
    # minimum_hours = Column(Numeric(8, 2))
    # maximum_hours = Column(Numeric(8, 2))
    # currency_id = Column(UUID(as_uuid=True), ForeignKey('public.currencies.id'))
    
#     # Recurring service settings
#     recurring_period = Column(String(20))  # monthly, yearly, weekly, etc.
#     recurring_amount = Column(Numeric(15, 2))
#     setup_fee = Column(Numeric(15, 2))
    
#     # Units
#     unit_of_measure_id = Column(UUID(as_uuid=True), ForeignKey('public.units_of_measure.id'))
#     unit_of_measure = relationship("UnitOfMeasure")
    
#     # Tax and accounting
#     tax_category_id = Column(UUID(as_uuid=True), ForeignKey('public.tax_categories.id'))
#     tax_category = relationship("TaxCategory")
#     revenue_account_id = Column(UUID(as_uuid=True))  # Reference to accounting chart
    
#     # Service delivery
#     estimated_duration = Column(Numeric(8, 2))  # Hours
#     delivery_method = Column(String(50))  # ONSITE, REMOTE, HYBRID
#     skill_requirements = Column(JSON)  # Array of required skills
    
#     # Status and metadata
#     is_active = Column(Boolean, default=True)
#     is_featured = Column(Boolean, default=False)
    
#     # Service level agreements
#     sla_response_time = Column(Integer)  # Hours
#     sla_resolution_time = Column(Integer)  # Hours
#     availability_schedule = Column(JSON)  # Service availability schedule
    
#     # Flexible attributes
#     attributes = Column(JSON)  # Custom service attributes
    
#     # Images and media
#     images = Column(JSON)  # Array of image URLs
#     documents = Column(JSON)  # Array of document URLs
    
#     # Company relationship
#     company_id = Column(UUID(as_uuid=True), ForeignKey('public.companies.id'), nullable=False)
    # Company relationship
    #company_id = Column(UUID(as_uuid=True), ForeignKey('public.companies.id'), nullable=False)


# class ProductVariant(BaseModel):
#     """Product variants (different sizes, colors, etc.)"""
#     __tablename__ = "product_variants"
#     __table_args__ = (
#         UniqueConstraint('parent_product_id', 'variant_code', name='uq_product_variant'),
#         {'schema': 'public'}
#     )

#     parent_product_id = Column(UUID(as_uuid=True), ForeignKey('public.products.id', ondelete='CASCADE'), nullable=False)
#     variant_code = Column(String(50), nullable=False)
#     variant_name = Column(String(255), nullable=False)
    
#     # Variant-specific attributes
#     sku = Column(String(50), unique=True, nullable=False)
#     cost_price = Column(Numeric(15, 2))
#     list_price = Column(Numeric(15, 2))
    
#     # Variant attributes (size, color, etc.)
#     variant_attributes = Column(JSON)
    
#     # Inventory
#     track_quantity = Column(Boolean, default=True)
    
#     # Status
#     is_active = Column(Boolean, default=True)
    
#     # Relationships
#     parent_product = relationship("Product", foreign_keys=[parent_product_id])


class PriceList(BaseModel):
    """Price lists for different customer segments or periods"""
    __tablename__ = "price_lists"
    __table_args__ = (
        UniqueConstraint('code', name='uq_price_list_code'),
        {'schema': 'public'}
    )

    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Validity
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    
    # Customer segments
    customer_segments = Column(JSON)  # Array of customer types/segments
    
    # Currency
    currency_id = Column(UUID(as_uuid=True), ForeignKey('public.currencies.id'))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Company relationship
    company_id = Column(UUID(as_uuid=True), ForeignKey('public.companies.id'), nullable=False)
    
    # Relationships
    price_list_items = relationship("PriceListItem", back_populates="price_list", cascade="all, delete-orphan")


class PriceListItem(BaseModel):
    """Individual items in a price list"""
    __tablename__ = "price_list_items"
    __table_args__ = {'schema': 'public'}

    price_list_id = Column(UUID(as_uuid=True), ForeignKey('public.price_lists.id', ondelete='CASCADE'), nullable=False)
    #product_id = Column(UUID(as_uuid=True), ForeignKey('public.products.id'), nullable=True)
    #service_id = Column(UUID(as_uuid=True), ForeignKey('public.services.id'), nullable=True)
    
    # Pricing
    unit_price = Column(Numeric(15, 2), nullable=False)
    minimum_quantity = Column(Numeric(10, 3), default=1)
    
    # Discounts
    discount_percentage = Column(Numeric(5, 2), default=0)
    
    # Relationships
    price_list = relationship("PriceList", back_populates="price_list_items")
    # product = relationship("Product", foreign_keys=[product_id])
    # service = relationship("Service", foreign_keys=[service_id])


# -----------------------------
# Unified Activity/Event Management
# -----------------------------

class ActivityType(str, enum.Enum):
    CALL = "CALL"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    TASK = "TASK"
    NOTE = "NOTE"
    FOLLOW_UP = "FOLLOW_UP"
    APPOINTMENT = "APPOINTMENT"
    PROPOSAL = "PROPOSAL"
    DEMO = "DEMO"
    TRAINING = "TRAINING"


class ActivityStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    NO_SHOW = "NO_SHOW"


class Activity(BaseModel):
    """Unified activity/event tracking for all entities using entity_type/entity_id pattern"""
    __tablename__ = "activities"
    __table_args__ = (
        Index('ix_activity_entity', 'entity_type', 'entity_id'),
        Index('ix_activity_assigned_to', 'assigned_to'),
        Index('ix_activity_scheduled_date', 'scheduled_date'),
        {'schema': 'public'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Entity relationship using your established pattern
    entity_type = Column(String(50), nullable=False)  # e.g., "CUSTOMER", "LEAD", "EMPLOYEE", etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)  

    # Activity details
    activity_type = Column(SQLAEnum(ActivityType, name="activity_type_enum", create_type=False), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text)

    # Status and priority
    status = Column(SQLAEnum(ActivityStatus, name="activity_status_enum", create_type=False), default=ActivityStatus.PENDING)
    priority = Column(String(20), default="NORMAL")  # LOW, NORMAL, HIGH, URGENT

    # Scheduling
    scheduled_date = Column(DateTime)
    scheduled_end_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    actual_end_date = Column(DateTime)
    duration_minutes = Column(Integer)

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"))  # ✅ Changed from String to UUID
    created_by = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"))   # ✅ Changed from String to UUID

    # Location and method
    location = Column(String(255))
    meeting_method = Column(String(50))  # "IN_PERSON", "VIDEO_CALL", etc.
    meeting_url = Column(String(500))

    # Results and outcomes
    outcome = Column(Text)
    next_action = Column(Text)
    next_action_date = Column(Date)

    # Company context
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    # Relationships
    assigned_person = relationship("Person", foreign_keys=[assigned_to])
    creator = relationship("Person", foreign_keys=[created_by])

    def __repr__(self):
        return (
            f"<Activity(id={self.id}, type={self.activity_type}, "
            f"entity={self.entity_type}:{self.entity_id}, subject={self.subject})>"
        )

# -----------------------------
# Unified Financial Document Management
# -----------------------------

class DocumentType(str, enum.Enum):
    QUOTE = "QUOTE"
    SALES_ORDER = "SALES_ORDER"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    SALES_INVOICE = "SALES_INVOICE"
    PURCHASE_INVOICE = "PURCHASE_INVOICE"
    CREDIT_NOTE = "CREDIT_NOTE"
    DEBIT_NOTE = "DEBIT_NOTE"
    PAYMENT_VOUCHER = "PAYMENT_VOUCHER"
    RECEIPT_VOUCHER = "RECEIPT_VOUCHER"
    EXPENSE_CLAIM = "EXPENSE_CLAIM"
    JOURNAL_ENTRY = "JOURNAL_ENTRY"


class DocumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENT = "SENT"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PAID = "PAID"
    PARTIAL_PAID = "PARTIAL_PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    VOID = "VOID"

class FinancialDocument(BaseModel):
    """Unified financial document model for all transaction types"""
    __tablename__ = "financial_documents"
    __table_args__ = (
        UniqueConstraint('document_number', 'document_type', 'company_id', name='uq_document_number_per_type_company'),
        Index('ix_financial_doc_party', 'party_type', 'party_id'),
        Index('ix_financial_doc_number', 'document_number'),
        Index('ix_financial_doc_date', 'document_date'),
        {'schema': 'public'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document identification
    document_type = Column(SQLAEnum(DocumentType, name="documenttype", create_type=False), nullable=False)
    document_number = Column(String(50), nullable=False)
    reference_number = Column(String(50))

    # Party relationship (customer, vendor, employee, etc.)
    party_type = Column(String(20), nullable=False)  # Still a string discriminator
    party_id = Column(UUID(as_uuid=True), nullable=False)  #

    # Document hierarchy (quote -> order -> invoice)
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey('public.financial_documents.id'))

    # Status and dates
    status = Column(SQLAEnum(DocumentStatus, name="documentstatus", create_type=False), nullable=False)
    document_date = Column(Date, nullable=False)
    due_date = Column(Date)
    valid_until = Column(Date)

    # Financial totals
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    shipping_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)

    # Payment tracking
    paid_amount = Column(Numeric(15, 2), default=0)
    balance_due = Column(Numeric(15, 2))

    # Currency
    currency_id = Column(UUID(as_uuid=True), ForeignKey("public.currencies.id"))

    # Terms
    payment_terms = Column(Integer)
    notes = Column(Text)
    terms_and_conditions = Column(Text)

    # Workflow tracking
    sent_date = Column(DateTime)
    viewed_date = Column(DateTime)
    accepted_date = Column(DateTime)

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"))  # ✅ Updated

    # Company context
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    # Accounting integration
    accounting_journal_entry_id = Column(UUID(as_uuid=True))

    # Relationships
    parent_document = relationship(
        "FinancialDocument",
        remote_side=lambda: [FinancialDocument.id],
        back_populates="child_documents",
        foreign_keys=[parent_document_id]
    )
    child_documents = relationship("FinancialDocument", back_populates="parent_document")
    line_items = relationship("FinancialDocumentLineItem", back_populates="document", cascade="all, delete-orphan")
    assigned_person = relationship("Person", foreign_keys=[assigned_to])

    def __repr__(self):
        return (
            f"<FinancialDocument(id={self.id}, type={self.document_type}, "
            f"number={self.document_number}, party={self.party_type}:{self.party_id})>"
        )
from sqlalchemy import Column, String, Text, Date, Integer, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

class FinancialDocumentLineItem(BaseModel):
    """Line items for financial documents"""
    __tablename__ = "financial_document_line_items"
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 

    document_id = Column(UUID(as_uuid=True), ForeignKey('public.financial_documents.id', ondelete='CASCADE'), nullable=False)
    line_number = Column(Integer, nullable=False)
    
    # Product/Service reference
    item_type = Column(String(20), nullable=False)  # "PRODUCT", "SERVICE", "EXPENSE", "DISCOUNT"
    # Uncomment and retain UUID support if needed:
    # product_id = Column(UUID(as_uuid=True), ForeignKey('public.products.id', type_=UUID(as_uuid=True)), nullable=True)
    # service_id = Column(UUID(as_uuid=True), ForeignKey('public.services.id', type_=UUID(as_uuid=True)), nullable=True)
    
    # Item details
    item_code = Column(String(50))
    item_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Quantities and pricing
    quantity = Column(Numeric(10, 3), nullable=False, default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2), nullable=False)
    
    # Tax information
    tax_code = Column(String(20))
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    
    # Fulfillment tracking
    quantity_delivered = Column(Numeric(10, 3), default=0)
    quantity_invoiced = Column(Numeric(10, 3), default=0)
    expected_delivery_date = Column(Date)
    actual_delivery_date = Column(Date)
    
    # Accounting
    revenue_account_id = Column(UUID(as_uuid=True))  # UUID already
    expense_account_id = Column(UUID(as_uuid=True))  # UUID already
    
    # Flexible attributes
    attributes = Column(JSON)

    # Relationships
    document = relationship("FinancialDocument", back_populates="line_items")
    # product = relationship("Product", foreign_keys=[product_id])
    # service = relationship("Service", foreign_keys=[service_id])


# -----------------------------
# Unified Rating/Review System
# -----------------------------

class RatingType(str, enum.Enum):
    QUALITY = "QUALITY"
    DELIVERY = "DELIVERY"
    SERVICE = "SERVICE"
    COMMUNICATION = "COMMUNICATION"
    OVERALL = "OVERALL"
    PERFORMANCE = "PERFORMANCE"
    SATISFACTION = "SATISFACTION"


class Rating(BaseModel):
    """Unified rating system for vendors, customers, employees, etc."""
    __tablename__ = "ratings"
    __table_args__ = (
        Index('ix_rating_entity', 'entity_type', 'entity_id'),
        Index('ix_rating_type', 'rating_type'),
        {'schema': 'public'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  
    # Entity relationship
    entity_type = Column(String(50), nullable=False)  # e.g., "VENDOR", "CUSTOMER", etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)  #

    # Rating details
    rating_type = Column(SQLAEnum(RatingType, name="rating_type_enum", create_type=False), nullable=False)
    rating_value = Column(Numeric(3, 2), nullable=False)  # 0–5 scale
    max_rating = Column(Numeric(3, 2), default=5)

    # Context
    rated_by = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"))  
    rating_date = Column(Date, default=func.current_date())
    period_start = Column(Date)
    period_end = Column(Date)

    # Comments and feedback
    comments = Column(Text)
    improvement_suggestions = Column(Text)

    # Reference to transaction/document
    reference_document_type = Column(String(50))  # "SALES_ORDER", etc.
    reference_document_id = Column(UUID(as_uuid=True))

    # Company context
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    # Relationships
    rater = relationship("Person", foreign_keys=[rated_by])

    def __repr__(self):
        return f"<Rating(id={self.id}, entity={self.entity_type}:{self.entity_id}, type={self.rating_type}, value={self.rating_value})>"

# -----------------------------
# Unified Tag/Classification System
# -----------------------------

class TagCategory(str, enum.Enum):
    INDUSTRY = "INDUSTRY"
    PRIORITY = "PRIORITY"
    STATUS = "STATUS"
    SKILL = "SKILL"
    INTEREST = "INTEREST"
    PRODUCT_CATEGORY = "PRODUCT_CATEGORY"
    CUSTOMER_SEGMENT = "CUSTOMER_SEGMENT"
    CAMPAIGN = "CAMPAIGN"
    PROJECT = "PROJECT"
    DEPARTMENT = "DEPARTMENT"

class Tag(BaseModel):
    """Unified tagging system for all entities"""
    __tablename__ = "tags"
    __table_args__ = (
        Index('ix_tag_entity', 'entity_type', 'entity_id'),
        Index('ix_tag_category', 'tag_category'),
        {'schema': 'public'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    # Entity relationship
    entity_type = Column(String(50), nullable=False)  # e.g., "CUSTOMER", "PRODUCT", etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)  #

    # Tag details
    tag_category = Column(SQLAEnum(TagCategory, name="tag_category_enum", create_type=False))
    tag_value = Column(String(100), nullable=False)
    tag_color = Column(String(7))  # e.g., "#FF5733"

    # Metadata
    applied_by = Column(UUID(as_uuid=True), ForeignKey("public.persons.id"), nullable=False)
    applied_date = Column(Date, default=func.current_date())

    # Company context
    company_id = Column(UUID(as_uuid=True), ForeignKey("public.companies.id"), nullable=False)

    # Relationships
    applier = relationship("Person", foreign_keys=[applied_by])

    @property
    def entity(self):
        # Placeholder property for dynamic reference
        return None

    def __repr__(self):
        return f"<Tag(id={self.id}, entity={self.entity_type}:{self.entity_id}, category={self.tag_category}, value={self.tag_value})>"


class SoftDeleteMixin:
    """Reusable soft delete fields."""
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SoftDeleteMixin(id={self.id}, is_deleted={self.is_deleted}, deleted_at={self.deleted_at})>"



class SKUCategory(str, enum.Enum):
    PRODUCT = "product"
    SERVICE = "service"
    AGENT = "agent"
    HOSTING = "hosting"

class SKUSubcategory(str, enum.Enum):
    ERP_MODULE = "erp_module"
    CUSTOM_DEV = "custom_dev"
    AI_AGENT = "ai_agent"
    CLOUD_RESOURCE = "cloud_resource"
    COURSE = "course"
    CONSULTATION = "consultation"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    MAINTENANCE = "maintenance"
    SUPPORT = "support"

class SKUBillingType(str, enum.Enum):
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    USAGE = "usage"
    PROJECT = "project"

class SKUUnitType(str, enum.Enum):
    LICENSE = "license"
    HOUR = "hour"
    USER = "user"
    RESOURCE = "resource"
    PIECE = "piece"
    MONTH = "month"
    YEAR = "year"
    SESSION = "session"
    PROJECT = "project"

class SKUStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    DRAFT = "draft"



class SKU(BaseModel):
    __tablename__ = "sku"
    __table_args__ = (
        UniqueConstraint('sku_code', 'company_id', name='uq_sku_code_per_company'),
        Index('ix_sku_code', 'sku_code'),
        Index('ix_sku_category', 'category'),
        Index('ix_sku_billing_type', 'billing_type'),
        Index('ix_sku_status', 'status'),
        {'schema': 'public'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, name='sku_id')
    sku_code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    category = Column(SQLAEnum(SKUCategory, name="sku_category_enum", create_type=False), nullable=False)
    subcategory = Column(SQLAEnum(SKUSubcategory, name="sku_subcategory_enum", create_type=False), nullable=True)
    billing_type = Column(SQLAEnum(SKUBillingType, name="sku_billing_type_enum", create_type=False), nullable=False)
    base_price = Column(DECIMAL(19, 4), nullable=False)
    unit_type = Column(SQLAEnum(SKUUnitType, name="sku_unit_type_enum", create_type=False), nullable=False)

    taxable = Column(Boolean, default=True)
    tax_category_id = Column(UUID(as_uuid=True), ForeignKey('public.tax_categories.id'))
    status = Column(SQLAEnum(SKUStatus, name="sku_status_enum", create_type=False), default=SKUStatus.ACTIVE)
    sku_type = Column(SQLAEnum(SKUType, name="sku_type_enum"), nullable=False, default=SKUType.GOODS)  # ✅ NEW
    item_type = Column(String(50), nullable=False, default='sku')
    company_id = Column(UUID(as_uuid=True), ForeignKey('public.companies.id'), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'sku',
        'polymorphic_on': item_type,
        'with_polymorphic': '*'
    }

    def __init__(self, *args, **kwargs):
        if 'sku_type' not in kwargs:
            kwargs['sku_type'] = SKUType.GOODS  # default fallback
        super().__init__(*args, **kwargs)

    # Relationships
    tax_category = relationship("TaxCategory")
    company = relationship("Company")

    # Activity, Tag, and Rating retrieval
    def get_activities(self):
        session = object_session(self)
        return session.query(Activity).filter(
            Activity.entity_type == "SKU",
            Activity.entity_id == str(self.id),
            Activity.is_active == True
        ).all()

    def get_tags(self):
        session = object_session(self)
        return session.query(Tag).filter(
            Tag.entity_type == "SKU",
            Tag.entity_id == str(self.id),
            Tag.is_active == True
        ).all()

    def get_ratings(self):
        session = object_session(self)
        return session.query(Rating).filter(
            Rating.entity_type == "SKU",
            Rating.entity_id == str(self.id),
            Rating.is_active == True
        ).all()

    # Pricing display logic
    def calculate_price(self, quantity: int = 1) -> float:
        return float(self.base_price * quantity)

    def is_subscription_based(self) -> bool:
        return self.billing_type == SKUBillingType.SUBSCRIPTION

    def is_usage_based(self) -> bool:
        return self.billing_type == SKUBillingType.USAGE

    def get_display_price(self) -> str:
        if self.billing_type == SKUBillingType.SUBSCRIPTION:
            return f"${self.base_price:.2f}/{self.unit_type.value}"
        elif self.billing_type == SKUBillingType.USAGE:
            return f"${self.base_price:.4f} per {self.unit_type.value}"
        return f"${self.base_price:.2f}"

    def __repr__(self):
        return f"<SKU(id={self.id}, code={self.sku_code}, name={self.name}, category={self.category})>"



class PayType(enum.Enum):
    MONTHLY = "Monthly"
    HOURLY = "Hourly"
    WEEKLY = "Weekly"

class SalaryComponentType(enum.Enum):
    BASIC = "Basic"
    ALLOWANCE = "Allowance"
    DEDUCTION = "Deduction"
    BONUS = "Bonus"

class LeaveTypeEnum(str, enum.Enum):
    CASUAL = "Casual"
    SICK = "Sick"
    EARNED = "Earned"
    MATERNITY = "Maternity"
    UNPAID = "Unpaid"

class LeaveStatusEnum(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# class SoftDeleteMixin:
#     is_active = Column(Boolean, default=True)   

    
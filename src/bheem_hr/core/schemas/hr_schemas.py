# ==================== LEAVE REQUEST SCHEMAS ====================
from uuid import UUID
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from pydantic import computed_field

class LeaveRequestBase(BaseModel):
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: Optional[str] = None

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestRead(LeaveRequestBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
# ==================== ATTENDANCE SCHEMAS ====================
from uuid import UUID
from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel

class AttendanceBase(BaseModel):
    employee_id: UUID
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = "Present"

class AttendanceCreate(AttendanceBase):
    pass






from bheem_core.shared.schemas import AddressResponse, NoteResponse, ContactCreate, ContactResponse, AddressCreate, BankAccountCreate, BankAccountResponse, PassportCreate, PassportResponse, GenderSchema, MaritalStatusSchema
from bheem_core.shared.models import EmploymentTypeEnum, EmploymentStatusEnum, Gender, MaritalStatus, InterviewRoundEnum, RatingEnum, InterviewStatusEnum, OfferStatusEnum, BackgroundCheckStatusEnum, PayType, LeaveTypeEnum, LeaveStatusEnum, SalaryComponentType
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
from datetime import date, time

# -------------------------------
# Utility functions for enum conversion
# -------------------------------
def convert_db_enum_to_schema(enum_value, target_enum_class):
    """Convert database enum to schema enum with comprehensive handling"""
    if enum_value is None:
        return None
    
    # If it's already the target enum type, return as is
    if isinstance(enum_value, target_enum_class):
        return enum_value
    
    try:
        # If it's a database enum instance, extract the value
        if hasattr(enum_value, 'value'):
            return target_enum_class(enum_value.value)
        
        # If it's a string, convert to target enum
        if isinstance(enum_value, str):
            return target_enum_class(enum_value)
        
        # If it's an enum with a name attribute, try using the name
        if hasattr(enum_value, 'name'):
            return target_enum_class(enum_value.name)
            
    except (ValueError, KeyError) as e:
        # If conversion fails, log the error and return the original value
        import logging
        logging.warning(f"Failed to convert enum value {enum_value} to {target_enum_class.__name__}: {e}")
        return enum_value
    
    return enum_value

# -------------------------------
# Social Profile Schemas (moved to top to resolve forward references)
# -------------------------------
class SocialProfileCreate(BaseModel):
    linkedin_profile: Optional[str] = None
    website: Optional[str] = None
    profile_image_url: Optional[str] = None

class SocialProfileResponse(SocialProfileCreate):
    id: UUID
    class Config:
        from_attributes = True

# -------------------------------
# Lookup Schemas (Import from shared)
# -------------------------------
from bheem_core.shared.schemas import LookupCreate, LookupUpdate, LookupResponse, LookupTypeSchema

# You can also create HR-specific lookup functions
class HRLookupHelper:
    """Helper class for HR-specific lookup operations"""
    
    @staticmethod
    def create_department(code: str, name: str, description: str = None) -> LookupCreate:
        """Helper to create department lookup"""
        return LookupCreate(
            type=LookupTypeSchema.DEPARTMENT,
            code=code,
            name=name,
            description=description
        )
    
    @staticmethod
    def create_position(code: str, name: str, description: str = None) -> LookupCreate:
        """Helper to create position lookup"""
        return LookupCreate(
            type=LookupTypeSchema.POSITION,
            code=code,
            name=name,
            description=description
        )
    
    @staticmethod
    def create_employee_status(code: str, name: str, description: str = None) -> LookupCreate:
        """Helper to create employee status lookup"""
        return LookupCreate(
            type=LookupTypeSchema.EMPLOYEE_STATUS,
            code=code,
            name=name,
            description=description
        )

# -------------------------------
# Person Schemas
# -------------------------------
class PersonBase(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    title: Optional[str] = None
    suffix: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderSchema] = None
    marital_status: Optional[MaritalStatusSchema] = None
    nationality: Optional[str] = None
    blood_group: Optional[str] = None
    contacts: Optional[List[ContactCreate]] = None
    addresses: Optional[List[AddressCreate]] = None
    bank_accounts: Optional[List[BankAccountCreate]] = None
    passports: Optional[List[PassportCreate]] = None

    @field_validator('gender', mode='before')
    def normalize_gender(cls, v):
        if v is None:
            return v
        if isinstance(v, GenderSchema):
            return v
        if isinstance(v, str):
            # Normalize to uppercase and handle common variations
            normalized = v.upper()
            if normalized in ['M', 'MALE']:
                return GenderSchema.MALE
            elif normalized in ['F', 'FEMALE']:
                return GenderSchema.FEMALE
            elif normalized in ['OTHER', 'O']:
                return GenderSchema.OTHER
            elif normalized in ['PREFER_NOT_TO_SAY', 'PREFER NOT TO SAY', 'NOT_SAY']:
                return GenderSchema.PREFER_NOT_TO_SAY
            # Try direct match
            try:
                return GenderSchema(normalized)
            except ValueError:
                pass
        raise ValueError(f'Invalid gender: {v}. Valid values are: MALE, FEMALE, OTHER, PREFER_NOT_TO_SAY')

    @field_validator('marital_status', mode='before')
    def normalize_marital_status(cls, v):
        if v is None:
            return v
        if isinstance(v, MaritalStatusSchema):
            return v
        if isinstance(v, str):
            # Normalize to lowercase
            normalized = v.lower()
            try:
                return MaritalStatusSchema(normalized)
            except ValueError:
                pass
        raise ValueError(f'Invalid marital status: {v}. Valid values are: single, married, divorced, widowed, separated, other')

class PersonCreate(PersonBase):
    company_id: UUID  # Required for multi-tenancy
    social_profiles: Optional[List[SocialProfileCreate]] = None

class PersonResponse(PersonBase):
    id: UUID
    person_type: str
    is_active: bool
    blood_group: Optional[str] = None
    company_id: Optional[str] = None
    contacts: List[ContactResponse] = []
    addresses: List[AddressResponse] = []
    bank_accounts: List[BankAccountResponse] = []
    passports: List[PassportResponse] = []
    social_profiles: List[SocialProfileResponse] = []
    
    @field_validator('gender', mode='before')
    def convert_gender_enum(cls, v):
        return convert_db_enum_to_schema(v, GenderSchema)
    
    @field_validator('marital_status', mode='before')
    def convert_marital_status_enum(cls, v):
        return convert_db_enum_to_schema(v, MaritalStatusSchema)
    
    class Config:
        from_attributes = True

# -------------------------------
# Employee Schemas
# -------------------------------
class EmployeeBase(PersonBase):
    employee_code: Optional[str] = None
    hire_date: date
    termination_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    department_id: Optional[UUID] = None  # FK to Lookup
    position_id: Optional[UUID] = None    # FK to Lookup
    manager_id: Optional[UUID] = None
    role_id: Optional[UUID] = None  # <-- Add this line to allow setting role_id on create/update
    employment_type: EmploymentTypeEnum
    employment_status: Optional[EmploymentStatusEnum] = EmploymentStatusEnum.ACTIVE
    work_location: Optional[str] = None
    base_salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    currency: Optional[str] = "USD"
    pay_frequency: Optional[str] = None
    national_id: Optional[str] = None
    password: str
    is_active: bool = True
    is_superadmin: bool = False
    social_profiles: Optional[List[SocialProfileCreate]] = None

    @field_validator('employment_type', mode='before')
    def normalize_employment_type(cls, v):
        if v is None:
            return v
        if isinstance(v, EmploymentTypeEnum):
            return v
        if isinstance(v, str):
            try:
                return EmploymentTypeEnum[v] if v in EmploymentTypeEnum.__members__ else EmploymentTypeEnum(v)
            except Exception:
                raise ValueError('Invalid employment type')
        raise ValueError('Invalid employment type')

    @field_validator('employment_status', mode='before')
    def normalize_employment_status(cls, v):
        if v is None:
            return v
        if isinstance(v, EmploymentStatusEnum):
            return v
        if isinstance(v, str):
            try:
                return EmploymentStatusEnum[v] if v in EmploymentStatusEnum.__members__ else EmploymentStatusEnum(v)
            except Exception:
                raise ValueError('Invalid employment status')
        raise ValueError('Invalid employment status')

class EmployeeCreate(EmployeeBase):
    company_id: UUID  # Required for multi-tenancy
    bank_accounts: Optional[List[BankAccountCreate]] = None
    passports: Optional[List[PassportCreate]] = None

class EmployeeUpdate(BaseModel):
    # Person fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    preferred_name: Optional[str] = None
    title: Optional[str] = None
    suffix: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderSchema] = None
    marital_status: Optional[MaritalStatusSchema] = None
    nationality: Optional[str] = None
    blood_group: Optional[str] = None
    company_id: Optional[UUID] = None
    
    # Employee-specific fields
    employee_code: Optional[str] = None
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    role_id: Optional[UUID] = None  # <-- Add this line to allow updating role_id
    employment_type: Optional[EmploymentTypeEnum] = None
    employment_status: Optional[EmploymentStatusEnum] = None
    work_location: Optional[str] = None
    base_salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    currency: Optional[str] = None
    pay_frequency: Optional[str] = None
    national_id: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superadmin: Optional[bool] = None
    
    # Related objects
    bank_accounts: Optional[List[BankAccountCreate]] = None
    passports: Optional[List[PassportCreate]] = None
    contacts: Optional[List[ContactCreate]] = None
    addresses: Optional[List[AddressCreate]] = None

    @field_validator('gender', mode='before')
    def convert_gender_enum(cls, v):
        return convert_db_enum_to_schema(v, GenderSchema)
    
    @field_validator('marital_status', mode='before')
    def convert_marital_status_enum(cls, v):
        return convert_db_enum_to_schema(v, MaritalStatusSchema)
    
    @field_validator('employment_type', mode='before')
    def convert_employment_type_enum(cls, v):
        return convert_db_enum_to_schema(v, EmploymentTypeEnum)
    
    @field_validator('employment_status', mode='before')
    def convert_employment_status_enum(cls, v):
        return convert_db_enum_to_schema(v, EmploymentStatusEnum)

# class EmployeeResponseBase(PersonBase):
#     """Employee response model without sensitive fields like password"""
#     employee_code: Optional[str] = None
#     hire_date: date
#     termination_date: Optional[date] = None
#     probation_end_date: Optional[date] = None
#     department_id: Optional[str] = None  # FK to Lookup
#     position_id: Optional[str] = None    # FK to Lookup
#     manager_id: Optional[str] = None
#     employment_type: EmploymentTypeEnum
#     employment_status: Optional[EmploymentStatusEnum] = EmploymentStatusEnum.ACTIVE
#     work_location: Optional[str] = None
#     base_salary: Optional[Decimal] = None
#     hourly_rate: Optional[Decimal] = None
#     currency: Optional[str] = "USD"
#     pay_frequency: Optional[str] = None
#     national_id: Optional[str] = None
#     # password field is deliberately excluded from response
#     is_active: bool = True
#     is_superadmin: bool = False
#     social_profiles: Optional[List[SocialProfileCreate]] = None

#     @field_validator('employment_type', mode='before')
#     def normalize_employment_type(cls, v):
#         if v is None:
#             return v
#         if isinstance(v, EmploymentTypeEnum):
#             return v
#         if isinstance(v, str):
#             try:
#                 return EmploymentTypeEnum[v] if v in EmploymentTypeEnum.__members__ else EmploymentTypeEnum(v)
#             except Exception:
#                 raise ValueError('Invalid employment type')
#         raise ValueError('Invalid employment type')

#     @field_validator('employment_status', mode='before')
#     def normalize_employment_status(cls, v):
#         if v is None:
#             return v
#         if isinstance(v, EmploymentStatusEnum):
#             return v
#         if isinstance(v, str):
#             try:
#                 return EmploymentStatusEnum[v] if v in EmploymentStatusEnum.__members__ else EmploymentStatusEnum(v)
#             except Exception:
#                 raise ValueError('Invalid employment status')
#         raise ValueError('Invalid employment status')

class EmployeeResponse(EmployeeBase):
    id: UUID
    role_id: Optional[UUID] = None
    bank_accounts: List[BankAccountResponse] = []
    passports: List[PassportResponse] = []

    @field_validator('gender', mode='before')
    def convert_gender_enum(cls, v):
        return convert_db_enum_to_schema(v, GenderSchema)

    @field_validator('marital_status', mode='before')
    def convert_marital_status_enum(cls, v):
        return convert_db_enum_to_schema(v, MaritalStatusSchema)

    @field_validator('employment_type', mode='before')
    def convert_employment_type_enum(cls, v):
        return convert_db_enum_to_schema(v, EmploymentTypeEnum)

    @field_validator('employment_status', mode='before')
    def convert_employment_status_enum(cls, v):
        return convert_db_enum_to_schema(v, EmploymentStatusEnum)

    model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic v2 way

# -------------------------------
# Combined Response
# -------------------------------
class PersonEmployeeCombinedResponse(BaseModel):
    person: PersonResponse
    employee: Optional[EmployeeResponse]

# -------------------------------
# Employee Search Schemas
# -------------------------------
class EmployeeSearchParams(BaseModel):
    department_id: Optional[UUID] = None
    search_term: Optional[str] = None
    employment_type: Optional[EmploymentTypeEnum] = None
    status: Optional[EmploymentStatusEnum] = None
    page: int = 1
    page_size: int = 50

class EmployeeSearchResult(BaseModel):
    items: List[EmployeeResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

# -------------------------------
# Customer Schemas
# -------------------------------
class CustomerBase(BaseModel):
    customer_number: str
    status: Optional[str] = "ACTIVE"
    tier: Optional[str] = "STANDARD"

class CustomerCreate(CustomerBase):
    person_id: UUID

class CustomerUpdate(BaseModel):
    customer_number: Optional[str] = None
    status: Optional[str] = None
    tier: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: UUID
    person_id: UUID
    class Config:
        from_attributes = True

# -------------------------------
# Vendor Schemas
# -------------------------------
class VendorBase(BaseModel):
    vendor_number: str
    company_name: Optional[str] = None

class VendorCreate(VendorBase):
    person_id: UUID

class VendorUpdate(BaseModel):
    vendor_number: Optional[str] = None
    company_name: Optional[str] = None

class VendorResponse(VendorBase):
    id: UUID
    person_id: UUID
    class Config:
        from_attributes = True

# -------------------------------
# Job Requisition Schemas
# -------------------------------
class JobRequisitionCreate(BaseModel):
    job_title: str
    department_id: UUID
    hiring_manager_id: UUID
    company_id: UUID
    number_of_openings: int = 1
    job_type_id: UUID
    location: str
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    requisition_date: date
    job_description: str
    experience_required: Optional[str] = None
    is_active: Optional[bool] = True
    skills: Optional[List[UUID]] = None

class JobRequisitionUpdate(BaseModel):
    job_title: Optional[str] = None
    department_id: Optional[UUID] = None
    hiring_manager_id: Optional[UUID] = None
    number_of_openings: Optional[int] = None
    job_type_id: Optional[UUID] = None
    location: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    requisition_date: Optional[date] = None
    job_description: Optional[str] = None
    experience_required: Optional[str] = None
    is_active: Optional[bool] = None
    skills: Optional[List[UUID]] = None

class JobRequisitionResponse(BaseModel):
    id: UUID
    job_title: str
    department_id: UUID
    hiring_manager_id: UUID
    number_of_openings: int
    job_type_id: UUID
    company_id: UUID
    location: str
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    requisition_date: date
    job_description: str
    experience_required: Optional[str] = None
    is_active: bool
    # skills: Optional[List[str]] = None
    skills : List[UUID]
    class Config:
        from_attributes = True

# -------------------------------
# Candidate Schemas
# -------------------------------
class ResumeAttachmentCreate(BaseModel):
    file_url: str
    description: str
    filename: str
    original_filename: str
    file_path: str

    model_config = ConfigDict(from_attributes=True)

class CandidateCreate(BaseModel):

    person: PersonCreate
    applied_position_id: Optional[str] = None
    application_date: Optional[date] = None
    notice_period: Optional[str] = None
    interview_availability: Optional[str] = None
    skills_matched: Optional[float] = None
    recruiter_assigned: Optional[str] = None
    offer_letter_signed: Optional[bool] = False
    id_proof_submitted: Optional[bool] = False
    educational_documents: Optional[bool] = False
    status: Optional[str] = "APPLIED"
    resume: Optional[ResumeAttachmentCreate] = None
    contacts: Optional[List[ContactCreate]] = None
    addresses: Optional[List[AddressCreate]] = None
    bank_accounts: Optional[List[BankAccountCreate]] = None
    passports: Optional[List[PassportCreate]] = None
    social_profiles: Optional[List[SocialProfileCreate]] = None

    @classmethod
    def model_validate(cls, data):
        if 'person' not in data or data['person'] is None:
            person_fields = [
                'id', 'first_name', 'last_name', 'middle_name', 'preferred_name',
                'title', 'suffix', 'date_of_birth', 'gender', 'marital_status',
                'nationality', 'blood_group', 'contacts', 'addresses',
                'bank_accounts', 'passports', 'social_profiles'
            ]
            person_data = {k: data[k] for k in person_fields if k in data}
            if not person_data.get('first_name') or not person_data.get('last_name'):
                raise ValueError("'person' field is required with 'first_name' and 'last_name'.")
            data['person'] = person_data
        return super().model_validate(data)

class CandidateUpdate(BaseModel):
    person: Optional[PersonCreate] = None
    applied_position_id: Optional[str] = None
    application_date: Optional[date] = None
    notice_period: Optional[str] = None
    interview_availability: Optional[str] = None
    skills_matched: Optional[float] = None
    recruiter_assigned: Optional[str] = None
    offer_letter_signed: Optional[bool] = None
    id_proof_submitted: Optional[bool] = None
    educational_documents: Optional[bool] = None
    status: Optional[str] = None
    resume: Optional[ResumeAttachmentCreate] = None
    # ...existing code...
from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel

# SalaryComponentType, PayType, LeaveTypeEnum, LeaveStatusEnum should be imported from shared.models



class PayrollRunBase(BaseModel):
    month: str
    status: str = "Draft"
    processed_by: Optional[str] = None

class PayrollRunCreate(PayrollRunBase):
    pass

class PayrollRunRead(PayrollRunBase):
    id: UUID
    class Config:
        from_attributes = True

class PayslipBase(BaseModel):
    employee_id: UUID
    payroll_run_id: UUID
    total_earnings: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    attachment_id: Optional[UUID] = None

class PayslipCreate(PayslipBase):
    pass

class PayslipRead(PayslipBase):
    id: UUID
    class Config:
        from_attributes = True

class LeaveRequestBase(BaseModel):
    employee_id: UUID
    leave_type: str  # Use Enum if available
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: str = "PENDING"

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestRead(LeaveRequestBase):
    id: UUID
    class Config:
        from_attributes = True

class ReportLogBase(BaseModel):
    report_name: str
    generated_by: UUID
    generated_on: Optional[datetime] = None
    parameters: Optional[dict] = None
    attachment_id: Optional[UUID] = None

class ReportLogCreate(ReportLogBase):
    pass

class ReportLogRead(ReportLogBase):
    id: UUID
    class Config:
        from_attributes = True

class CandidateResponse(BaseModel):
    id: UUID
    person: PersonResponse
    applied_position_id: Optional[UUID] = None
    application_date: Optional[date] = None
    notice_period: Optional[str] = None
    interview_availability: Optional[str] = None
    skills_matched: Optional[float] = None
    recruiter_assigned: Optional[UUID] = None
    offer_letter_signed: Optional[bool] = False
    id_proof_submitted: Optional[bool] = False
    educational_documents: Optional[bool] = False
    status: Optional[str] = "APPLIED"
    resume: Optional[ResumeAttachmentCreate] = None
    # ...existing code...

    class Config:
        orm_mode = True
        from_attributes = True

# -------------------------------
# Interview Schemas
# -------------------------------
class InterviewBase(BaseModel):
    candidate_id: UUID
    interview_date_time: datetime
    interviewer_id: Optional[UUID] = None
    round_type: InterviewRoundEnum
    feedback_comments: Optional[str] = None
    rating: Optional[RatingEnum] = None
    next_step: Optional[str] = None
    status: InterviewStatusEnum = InterviewStatusEnum.SCHEDULED
    is_active: Optional[bool] = True

class InterviewCreate(InterviewBase):
    pass

class InterviewUpdate(BaseModel):
    interview_date_time: Optional[datetime] = None
    interviewer_id: Optional[str] = None
    round_type: Optional[InterviewRoundEnum] = None
    feedback_comments: Optional[str] = None
    rating: Optional[RatingEnum] = None
    next_step: Optional[str] = None
    status: Optional[InterviewStatusEnum] = None
    is_active: Optional[bool] = None

class InterviewResponse(InterviewBase):
    id: UUID
    class Config:
        from_attributes = True

# -------------------------------
# Offer Schemas
# -------------------------------
class OfferBase(BaseModel):
    candidate_id: UUID
    offer_date: date
    offered_ctc: float
    joining_date: date
    offer_status: OfferStatusEnum
    background_check_status: BackgroundCheckStatusEnum
    documents_submitted: Optional[bool] = False
    is_active: Optional[bool] = True

class OfferCreate(OfferBase):
    pass

class OfferUpdate(BaseModel):
    offer_date: Optional[date] = None
    offered_ctc: Optional[float] = None
    joining_date: Optional[date] = None
    offer_status: Optional[OfferStatusEnum] = None
    background_check_status: Optional[BackgroundCheckStatusEnum] = None
    documents_submitted: Optional[bool] = None
    is_active: Optional[bool] = None

class OfferResponse(OfferBase):
    id: UUID
    class Config:
        from_attributes = True

# -------------------------------
# OnboardingChecklist Schemas
# -------------------------------
class OnboardingChecklistBase(BaseModel):
    candidate_id: UUID
    offer_id: Optional[UUID] = None
    offer_letter_signed: Optional[bool] = False
    id_proof_submitted: Optional[bool] = False
    educational_documents: Optional[bool] = False
    background_verification: Optional[bool] = False
    bank_account_details: Optional[bool] = False
    work_email_created: Optional[bool] = False
    system_allocation: Optional[bool] = False
    software_access_setup: Optional[bool] = False
    welcome_kit_given: Optional[bool] = False
    assigned_buddy: Optional[bool] = False
    first_day_orientation: Optional[bool] = False
    department_introduction: Optional[bool] = False
    hr_policy_acknowledgement: Optional[bool] = False
    training_plan_shared: Optional[bool] = False
    probation_period_set: Optional[bool] = False
    employee_id_created: Optional[bool] = False
    is_active: Optional[bool] = True

class OnboardingChecklistCreate(OnboardingChecklistBase):
    pass

class OnboardingChecklistUpdate(BaseModel):
    offer_id: Optional[str] = None
    offer_letter_signed: Optional[bool] = None
    id_proof_submitted: Optional[bool] = None
    educational_documents: Optional[bool] = None
    background_verification: Optional[bool] = None
    bank_account_details: Optional[bool] = None
    work_email_created: Optional[bool] = None
    system_allocation: Optional[bool] = None
    software_access_setup: Optional[bool] = None
    welcome_kit_given: Optional[bool] = None
    assigned_buddy: Optional[bool] = None
    first_day_orientation: Optional[bool] = None
    department_introduction: Optional[bool] = None
    hr_policy_acknowledgement: Optional[bool] = None
    training_plan_shared: Optional[bool] = None
    probation_period_set: Optional[bool] = None
    employee_id_created: Optional[bool] = None
    is_active: Optional[bool] = None

class OnboardingChecklistResponse(OnboardingChecklistBase):
    id: UUID
    class Config:
        from_attributes = True



# ===================== PAYROLL RUN SCHEMAS =====================

class PayrollRunBase(BaseModel):
    month: str  # format: YYYY-MM
    status: str = "Draft"  # Draft, Processed, Paid
    processed_by: Optional[str] = None
    company_id: UUID

class PayrollRunCreate(PayrollRunBase):
    pass

class PayrollRunRead(PayrollRunBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ===================== PAYSLIP SCHEMAS =====================

class PayslipBase(BaseModel):
    employee_id: UUID
    payroll_run_id: UUID
    total_earnings: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    attachment_id: Optional[UUID] = None

class PayslipCreate(PayslipBase):
    pass

class PayslipRead(PayslipBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ===================== ATTENDANCE SCHEMAS =====================

class AttendanceBase(BaseModel):
    employee_id: UUID
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = "Present"

class AttendanceCreate(AttendanceBase):
    pass

# class AttendanceRead(AttendanceBase):
#     id: UUID
#     class Config:
#         from_attributes = True


class AttendanceBase(BaseModel):
    employee_id: UUID
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = "Present"

class AttendanceCreate(AttendanceBase):
    pass



class AttendanceRead(AttendanceBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    @computed_field
    @property
    def total_working_hours(self) -> Optional[str]:
        if self.check_in and self.check_out:
            total = datetime.combine(date.min, self.check_out) - datetime.combine(date.min, self.check_in)
            return str(total)
        return None
    class Config:
        from_attributes = True
        

class AttendancePaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    records: List[AttendanceRead]

# ===================== LEAVE REQUEST SCHEMAS =====================

class LeaveRequestBase(BaseModel):
    employee_id: UUID
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: LeaveStatusEnum = LeaveStatusEnum.PENDING

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestRead(LeaveRequestBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ===================== REPORT LOG SCHEMAS =====================

class ReportLogBase(BaseModel):
    report_name: str
    generated_by: UUID
    parameters: Optional[dict] = None
    attachment_id: Optional[UUID] = None

class ReportLogCreate(ReportLogBase):
    pass

class ReportLogRead(ReportLogBase):
    id: UUID
    generated_on: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
    amount: Decimal
    taxable: bool = True


class PayrollRunBase(BaseModel):
    month: str
    status: str = "Draft"
    processed_by: Optional[str] = None

class PayrollRunCreate(PayrollRunBase):
    pass

class PayrollRunRead(PayrollRunBase):
    id: UUID

    class Config:
        from_attributes = True

class PayslipBase(BaseModel):
    employee_id: UUID
    payroll_run_id: UUID
    total_earnings: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    pdf_url: Optional[str] = None

class PayslipCreate(PayslipBase):
    pass

class PayslipRead(PayslipBase):
    id: UUID

    class Config:
        from_attributes = True


class AttendanceBase(BaseModel):
    employee_id: UUID
    date: date
    check_in: time | None = None
    check_out: time | None = None
    status: str = "Present"



class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: Optional[str] = None




class LeaveRequestCreate(BaseModel):
    employee_id: UUID
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: str

class LeaveRequestUpdate(BaseModel):
    status: LeaveStatusEnum

# ==================== PAYROLL RUN SCHEMAS ====================
class PayrollRunBase(BaseModel):
    month: str  # format: YYYY-MM
    status: str = "Draft"  # Draft, Processed, Paid
    processed_by: Optional[str] = None

class PayrollRunCreate(PayrollRunBase):
    pass

class PayrollRunRead(PayrollRunBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==================== PAYSLIP SCHEMAS ====================
class PayslipBase(BaseModel):
    employee_id: UUID
    payroll_run_id: UUID
    total_earnings: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    attachment_id: Optional[UUID] = None

class PayslipCreate(PayslipBase):
    pass

class PayslipRead(PayslipBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==================== ATTENDANCE SCHEMAS ====================
class AttendanceBase(BaseModel):
    employee_id: UUID
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str = "Present"

class AttendanceCreate(AttendanceBase):
    pass

# ==================== LEAVE REQUEST SCHEMAS ====================
class LeaveRequestBase(BaseModel):
    employee_id: UUID
    leave_type: LeaveTypeEnum
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: LeaveStatusEnum = LeaveStatusEnum.PENDING

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestRead(LeaveRequestBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==================== REPORT LOG SCHEMAS ====================
class ReportLogBase(BaseModel):
    report_name: str
    generated_by: Optional[UUID] = None
    parameters: Optional[dict] = None
    attachment_id: Optional[UUID] = None

class ReportLogCreate(ReportLogBase):
    pass

class ReportLogRead(ReportLogBase):
    id: UUID
    generated_on: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Rebuild models to resolve forward references
PersonCreate.model_rebuild()
PersonResponse.model_rebuild()
EmployeeBase.model_rebuild()
EmployeeCreate.model_rebuild()
CandidateCreate.model_rebuild()
CandidateResponse.model_rebuild()
SocialProfileCreate.model_rebuild()
SocialProfileResponse.model_rebuild()



# Base schema for salary component without structure_id (for nested creation)
class SalaryComponentBase(BaseModel):
    name: str
    component_type: SalaryComponentType
    amount: float
    taxable: bool = True

# Schema for creating a salary component independently (requires structure_id)
class SalaryComponentCreate(SalaryComponentBase):
    structure_id: UUID

# Schema for creating components nested within salary structure (no structure_id needed)
class SalaryComponentNestedCreate(SalaryComponentBase):
    pass

class SalaryStructureCreate(BaseModel):
    employee_id: UUID
    effective_date: date
    pay_type: PayType
    is_active: bool = True
    components: list[SalaryComponentNestedCreate] = []

class SalaryComponentRead(BaseModel):
    id: UUID
    name: str
    component_type: str
    amount: float
    taxable: bool

    model_config = ConfigDict(from_attributes=True)

class SalaryStructureRead(BaseModel):
    id: UUID
    employee_id: UUID
    effective_date: date
    pay_type: PayType
    is_active: bool
    components: list[SalaryComponentRead]

    model_config = ConfigDict(from_attributes=True)



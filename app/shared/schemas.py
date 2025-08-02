from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from uuid import UUID

# --- Enums ---
class GenderSchema(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"
    
    @classmethod
    def normalize(cls, value):
        """Normalize gender values to uppercase"""
        if isinstance(value, str):
            normalized = value.upper()
            # Handle common variations
            if normalized in ['M', 'MALE']:
                return cls.MALE
            elif normalized in ['F', 'FEMALE']:
                return cls.FEMALE
            elif normalized in ['OTHER', 'O']:
                return cls.OTHER
            elif normalized in ['PREFER_NOT_TO_SAY', 'PREFER NOT TO SAY', 'NOT_SAY']:
                return cls.PREFER_NOT_TO_SAY
        return value

class MaritalStatusSchema(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    OTHER = "other"

class LookupTypeSchema(str, Enum):
    DEPARTMENT = "department"
    POSITION = "position"
    EMPLOYEE_STATUS = "employee_status"
    CANDIDATE_STATUS = "candidate_status"
    JOB_TYPE = "job_type"
    SKILL = "skill"
    ROLE = "role"
    PERMISSION = "permission"
    # Add more as needed

# --- Address Schemas ---
class AddressBase(BaseModel):
    address_type: str = Field(default="PRIMARY", max_length=20)
    line1: str = Field(..., min_length=1, max_length=255)
    line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="USA", max_length=100)
    is_active: Optional[bool] = True

class AddressCreate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: UUID
    entity_type: str
    entity_id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Note Schemas ---
class NoteBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    note_type: str = Field(default="GENERAL", max_length=50)

class NoteCreate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: UUID
    entity_type: str
    entity_id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Attachment Schemas ---
class AttachmentBase(BaseModel):
    original_filename: str = Field(..., max_length=255)
    description: Optional[str] = None

class AttachmentCreate(AttachmentBase):
    pass

class AttachmentResponse(AttachmentBase):
    id: UUID
    entity_type: str
    entity_id: UUID
    filename: str
    file_path: str
    file_size: Optional[str]
    mime_type: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Person Schemas ---
class PersonBase(BaseModel):
    """Base schema for all person types"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=20)
    suffix: Optional[str] = Field(None, max_length=20)

    date_of_birth: Optional[date] = None
    gender: Optional[GenderSchema] = None
    marital_status: Optional[MaritalStatusSchema] = None
    nationality: Optional[str] = Field(None, max_length=100)

    email_primary: Optional[EmailStr] = None
    email_secondary: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    phone_work: Optional[str] = Field(None, max_length=20)

    linkedin_profile: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    blood_group: Optional[str] = Field(None, max_length=10)
    
    @field_validator('gender', mode='before')
    @classmethod
    def validate_gender(cls, v):
        """Normalize gender values"""
        if v is None:
            return v
        return GenderSchema.normalize(v)

class PersonResponse(PersonBase):
    """Base response schema for person"""
    id: UUID
    person_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Computed fields
    full_name: str
    display_name: str
    initials: str

    # Related data
    addresses: List[AddressResponse] = []
    notes: List[NoteResponse] = []
    attachments: List[AttachmentResponse] = []

    class Config:
        from_attributes = True

# --- Contact Schemas ---
class ContactBase(BaseModel):
    email_primary: Optional[EmailStr] = None
    email_secondary: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    phone_mobile: Optional[str] = Field(None, max_length=20)
    phone_work: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = True
    # Emergency contact fields
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactResponse(ContactBase):
    id: UUID
    person_id: UUID
    is_active: bool
    class Config:
        from_attributes = True

# --- Bank Account Schemas ---
class BankAccountBase(BaseModel):
    account_name: str = Field(..., description="Account holder name or account description")
    account_number: str
    bank_name: str
    routing_number: Optional[str] = None
    account_type: Optional[str] = None
    is_primary: Optional[bool] = False

class BankAccountCreate(BankAccountBase):
    pass

class BankAccountResponse(BankAccountBase):
    id: UUID
    person_id: UUID
    entity_type: Optional[str] = "PERSON"
    currency: Optional[str] = "USD"
    current_balance: Optional[float] = 0.0
    is_active: Optional[bool] = True
    class Config:
        from_attributes = True

# --- Passport Schemas ---
class PassportBase(BaseModel):
    passport_number: str
    expiry_date: Optional[date] = None
    country_of_issue: Optional[str] = None
    is_primary: Optional[bool] = False

class PassportCreate(PassportBase):
    pass

class PassportResponse(PassportBase):
    id: UUID
    person_id: UUID
    class Config:
        from_attributes = True

# --- Lookup Schemas ---
# Lookup system provides centralized management for reference data like departments, positions, etc.
# 
# Usage Examples:
# - DEPARTMENT: Engineering, Sales, Marketing, HR
# - POSITION: Software Engineer, Manager, Director
# - EMPLOYEE_STATUS: Active, Inactive, Terminated
# - CANDIDATE_STATUS: Applied, Interviewed, Hired, Rejected
# - JOB_TYPE: Full-Time, Part-Time, Contract, Internship
# - SKILL: Python, Java, React, Project Management
# - ROLE: Admin, HR Manager, Employee, Manager
# - PERMISSION: create_employee, view_reports, manage_departments

class LookupBase(BaseModel):
    """Base schema for Lookup with common fields"""
    type: LookupTypeSchema = Field(..., description="Type of lookup (department, position, etc.)")
    code: str = Field(..., min_length=1, max_length=50, description="Unique code for the lookup")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=255, description="Optional description")
    is_active: Optional[bool] = Field(default=True, description="Whether the lookup is active")

class LookupCreate(LookupBase):
    """Schema for creating a new lookup"""
    pass

class LookupUpdate(BaseModel):
    """Schema for updating an existing lookup (partial updates allowed)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class LookupResponse(LookupBase):
    """Schema for lookup response with ID"""
    id: UUID
    
    class Config:
        from_attributes = True

# Example usage in API calls:
#
# Create Department:
# {
#   "type": "department",
#   "code": "ENG",
#   "name": "Engineering",
#   "description": "Software Development Department"
# }
#
# Create Position:
# {
#   "type": "position", 
#   "code": "SE_SR",
#   "name": "Senior Software Engineer",
#   "description": "Senior level software development role"
# }

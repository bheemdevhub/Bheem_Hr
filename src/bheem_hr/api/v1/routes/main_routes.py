# app/modules/hr/routes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, Body, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update, cast, String
from bheem_core.shared.models import Person, Contact, Address
from bheem_core.shared.schemas import (
    ContactCreate, ContactResponse, AddressCreate, AddressResponse,
    BankAccountCreate, BankAccountResponse, PassportCreate, PassportResponse
    # CustomerCreate, CustomerResponse, VendorCreate, VendorResponse - Not available yet
)
from bheem_core.shared.schemas import LookupCreate, LookupUpdate, LookupResponse, LookupTypeSchema
# Import authentication dependencies
from bheem_core.modules.auth.core.services.permissions_service import get_current_user, require_roles, require_api_permission

# Fix the service import path
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.modules.hr.core.schemas.hr_schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    EmployeeSearchParams, EmployeeSearchResult,
    PersonCreate, PersonResponse,
    LookupResponse,
    JobRequisitionCreate, JobRequisitionUpdate, JobRequisitionResponse,
    CandidateCreate, CandidateUpdate, CandidateResponse,
    InterviewCreate, InterviewUpdate, InterviewResponse,
    OfferCreate, OfferUpdate, OfferResponse,
    OnboardingChecklistCreate, OnboardingChecklistUpdate, OnboardingChecklistResponse
)
from bheem_core.core.database import get_db
from sqlalchemy.dialects.postgresql import UUID
import uuid

router = APIRouter()

# # -------------------------------
# # Employee Routes
# # -------------------------------

# @router.post("/employees", response_model=EmployeeResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("employee.create"))])
# async def create_employee(
#     emp_data: EmployeeCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """Create an employee (and person) in one step. All person and employee fields must be provided."""
#     service = HRService(db)
#     return await service.create_employee(emp_data)

# @router.post("/employees/batch", response_model=list[EmployeeResponse], dependencies=[Depends(lambda: require_api_permission("employee.create"))])
# async def create_employees_batch(
#     emp_list: list[EmployeeCreate],
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """Create multiple employees in a batch, each with a unique auto-generated employee code."""
#     service = HRService(db)
#     created = []
#     for emp_data in emp_list:
#         created.append(await service.create_employee(emp_data))
#     return created

# @router.get("/employees", response_model=EmployeeSearchResult, dependencies=[Depends(lambda: require_api_permission("employee.read"))])
# async def search_employees(
#     department_id: str = Query(None, description="Filter by department ID"),
#     search_term: str = Query(None, description="Search in name, email, or employee code"),
#     employment_type: str = Query(None, description="Filter by employment type"),
#     status: str = Query(None, description="Filter by employee status"),
#     page: int = Query(1, ge=1, description="Page number"),
#     page_size: int = Query(50, ge=1, le=500, description="Items per page"),
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """Search and filter employees with pagination"""
#     params = EmployeeSearchParams(
#         department_id=department_id,
#         search_term=search_term,
#         employment_type=employment_type,
#         status=status,
#         page=page,
#         page_size=page_size
#     )
#     service = HRService(db)
#     return await service.search_employees(params)

# @router.get("/employees/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(lambda: require_api_permission("employee.read"))])
# async def get_employee(
#     employee_id: str,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """Get employee by ID"""
#     service = HRService(db)
#     return await service.get_employee_by_id(employee_id)

# @router.put("/employees/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(lambda: require_api_permission("employee.update"))])
# async def update_employee(
#     employee_id: str,
#     emp_data: EmployeeUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """Update employee"""
#     service = HRService(db)
#     return await service.update_employee(employee_id, emp_data)

# @router.put("/employees/by-person/{person_id}", response_model=EmployeeResponse, dependencies=[Depends(lambda: require_api_permission("employee.update"))])
# async def update_employee_by_person_id(
#     person_id: str,
#     emp_data: EmployeeUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """Update employee by person_id"""
#     service = HRService(db)
#     return await service.update_employee_by_person_id(person_id, emp_data)

# @router.get("/employees/by-person/{person_id}", response_model=EmployeeResponse, dependencies=[Depends(lambda: require_api_permission("employee.read"))])
# async def get_employee_by_person_id(
#     person_id: str,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     """Get employee by person_id"""
#     service = HRService(db)
#     return await service.get_employee_by_id(person_id)

# -------------------------------
# Employee Actions
# -------------------------------

@router.post("/employees/{employee_id}/activate", dependencies=[Depends(lambda: require_api_permission("employee.activate"))])
async def activate_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Activate an employee"""
    service = HRService(db)
    emp_data = EmployeeUpdate(status="ACTIVE")
    return await service.update_employee(employee_id, emp_data)

@router.post("/employees/{employee_id}/terminate", dependencies=[Depends(lambda: require_api_permission("employee.terminate"))])
async def terminate_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Terminate an employee"""
    service = HRService(db)
    emp_data = EmployeeUpdate(status="TERMINATED")
    return await service.update_employee(employee_id, emp_data)

# -------------------------------
# Customer Routes (Disabled - schemas not available)
# -------------------------------

# @router.post("/customers", response_model=CustomerResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("customer.create"))])
# async def create_or_update_customer(
#     person_data: PersonCreate = Body(...),
#     customer_data: CustomerCreate = Body(...),
#     db: AsyncSession = Depends(get_db),
#     request: Request = None,
#     current_user=Depends(get_current_user)
# ):
#     """Create or update customer (upsert logic): create person if needed, then upsert customer."""
#     event_bus = None
#     if request and hasattr(request.app, 'state') and hasattr(request.app.state, 'erp_system'):
#         erp_system = request.app.state.erp_system
#         if hasattr(erp_system, 'event_bus'):
#             event_bus = erp_system.event_bus
#     service = HRService(db, event_bus=event_bus)
#     return await service.upsert_customer(person_data, customer_data)

# -------------------------------
# Vendor Routes (Disabled - schemas not available)
# -------------------------------

# @router.post("/vendors", response_model=VendorResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("vendor.create"))])
# async def create_or_update_vendor(
#     person_data: PersonCreate = Body(...),
#     vendor_data: VendorCreate = Body(...),
#     db: AsyncSession = Depends(get_db),
#     request: Request = None,
#     current_user=Depends(get_current_user)
# ):
#     """Create or update vendor (upsert logic): create person if needed, then upsert vendor."""
#     event_bus = None
#     if request and hasattr(request.app, 'state') and hasattr(request.app.state, 'erp_system'):
#         erp_system = request.app.state.erp_system
#         if hasattr(erp_system, 'event_bus'):
#             event_bus = erp_system.event_bus
#     service = HRService(db, event_bus=event_bus)
#     return await service.upsert_vendor(person_data, vendor_data)

@router.post("/persons", response_model=PersonResponse, dependencies=[Depends(lambda: require_api_permission("person.create"))])
async def create_person_endpoint(
    person_data: PersonCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Create a new person"""
    service = HRService(db)
    person = await service.create_person(person_data)
    return PersonResponse.model_validate(person)

# # -------------------------------
# # Employee Contacts and Addresses
# # -------------------------------

# @router.get("/employees/{employee_id}/contacts", response_model=List[ContactResponse], dependencies=[Depends(lambda: require_api_permission("contact.read"))])
# async def list_employee_contacts(employee_id: str, db: AsyncSession = Depends(get_db)):
#     """List all contacts for an employee"""
#     service = HRService(db)
#     return await service.list_contacts(employee_id)

# @router.post("/employees/{employee_id}/contacts", response_model=ContactResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("contact.create"))])
# async def create_employee_contact(employee_id: str, contact: ContactCreate, db: AsyncSession = Depends(get_db)):
#     """Create a new contact for an employee"""
#     service = HRService(db)
#     return await service.create_contact(employee_id, contact)

# @router.put("/employees/{employee_id}/contacts/{contact_id}", response_model=ContactResponse, dependencies=[Depends(lambda: require_api_permission("contact.update"))])
# async def update_employee_contact(employee_id: str, contact_id: str, contact: ContactCreate, db: AsyncSession = Depends(get_db)):
#     """Update an employee's contact"""
#     service = HRService(db)
#     return await service.update_contact(contact_id, contact)

# @router.delete("/employees/{employee_id}/contacts/{contact_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("contact.delete"))])
# async def delete_employee_contact(employee_id: str, contact_id: str, db: AsyncSession = Depends(get_db)):
#     """Delete an employee's contact"""
#     service = HRService(db)
#     await service.delete_contact(contact_id)
#     return None

# @router.get("/employees/{employee_id}/addresses", response_model=List[AddressResponse], dependencies=[Depends(lambda: require_api_permission("address.read"))])
# async def list_employee_addresses(employee_id: str, db: AsyncSession = Depends(get_db)):
#     """List all addresses for an employee"""
#     service = HRService(db)
#     return await service.list_addresses(employee_id)

# @router.post("/employees/{employee_id}/addresses", response_model=AddressResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("address.create"))])
# async def create_employee_address(employee_id: str, address: AddressCreate, db: AsyncSession = Depends(get_db)):
#     """Create a new address for an employee"""
#     service = HRService(db)
#     return await service.create_address(employee_id, address)

# @router.put("/employees/{employee_id}/addresses/{address_id}", response_model=AddressResponse, dependencies=[Depends(lambda: require_api_permission("address.update"))])
# async def update_employee_address(employee_id: str, address_id: str, address: AddressCreate, db: AsyncSession = Depends(get_db)):
#     """Update an employee's address"""
#     service = HRService(db)
#     return await service.update_address(address_id, address)

# @router.delete("/employees/{employee_id}/addresses/{address_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("address.delete"))])
# async def delete_employee_address(employee_id: str, address_id: str, db: AsyncSession = Depends(get_db)):
#     """Delete an employee's address"""
#     service = HRService(db)
#     await service.delete_address(address_id)
#     return None

# -------------------------------
# Bank Account Routes
# -------------------------------

@router.get("/persons/{person_id}/bank-accounts", response_model=List[BankAccountResponse], dependencies=[Depends(lambda: require_api_permission("bankaccount.read"))])
async def list_bank_accounts(person_id: str, db: AsyncSession = Depends(get_db)):
    """List all bank accounts for a person"""
    service = HRService(db)
    return await service.list_bank_accounts(person_id)

@router.post("/persons/{person_id}/bank-accounts", response_model=BankAccountResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("bankaccount.create"))])
async def create_bank_account(person_id: str, bank_data: BankAccountCreate, db: AsyncSession = Depends(get_db)):
    """Create a new bank account for a person"""
    service = HRService(db)
    return await service.create_bank_account(person_id, bank_data)

@router.put("/bank-accounts/{bank_account_id}", response_model=BankAccountResponse, dependencies=[Depends(lambda: require_api_permission("bankaccount.update"))])
async def update_bank_account(bank_account_id: str, bank_data: BankAccountCreate, db: AsyncSession = Depends(get_db)):
    """Update a bank account"""
    service = HRService(db)
    return await service.update_bank_account(bank_account_id, bank_data)

@router.delete("/bank-accounts/{bank_account_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("bankaccount.delete"))])
async def delete_bank_account(bank_account_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a bank account"""
    service = HRService(db)
    await service.delete_bank_account(bank_account_id)
    return None


@router.get("/persons/{person_id}", response_model=PersonResponse, dependencies=[Depends(lambda: require_api_permission("person.read"))])
async def get_person(person_id: str, db: AsyncSession = Depends(get_db)):
    """Get a person by ID"""
    service = HRService(db)
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Fetch contacts and addresses
    contacts = await service.list_contacts(person_id)
    addresses = await service.list_addresses(person_id, entity_type=person.person_type)
    
    # Convert person data to dict and handle UUID fields
    person_dict = person.__dict__.copy()
    person_dict.pop("_sa_instance_state", None)  # Remove SQLAlchemy state
    
    # Convert UUID fields to strings
    if person_dict.get("company_id"):
        person_dict["company_id"] = str(person_dict["company_id"])
    
    # Add related data
    person_dict["contacts"] = contacts
    person_dict["addresses"] = addresses
    
    person_data = PersonResponse.model_validate(person_dict)
    return person_data

@router.put("/persons/{person_id}", response_model=PersonResponse, dependencies=[Depends(lambda: require_api_permission("person.update"))])
async def update_person(person_id: str, person_data: PersonCreate, db: AsyncSession = Depends(get_db)):
    """Update a person by ID"""
    service = HRService(db)
    
    # Get the person using async query
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    # Update person fields using async-safe approach
    update_data = person_data.model_dump(
        exclude_unset=True, 
        exclude={"contacts", "addresses", "bank_accounts", "passports", "social_profiles"}
    )
    
    # Remove any fields that shouldn't be updated or don't exist in the Person model
    # Ensure we only update fields that actually exist in the Person table
    valid_person_fields = {
        'first_name', 'last_name', 'middle_name', 'preferred_name', 
        'title', 'suffix', 'date_of_birth', 'gender', 'marital_status', 
        'nationality', 'blood_group', 'company_id', 'person_type', 
        'is_active', 'supabase_id', 'position'
    }
    
    # Filter update_data to only include valid fields and exclude any None/list values
    filtered_update_data = {}
    for k, v in update_data.items():
        if k in valid_person_fields and v is not None and not isinstance(v, (list, dict)):
            filtered_update_data[k] = v
    
    if filtered_update_data:
        from sqlalchemy import update as sql_update
        await db.execute(
            sql_update(Person)
            .where(Person.id == person_id)
            .values(**filtered_update_data)
        )
        await db.commit()
        
        # Refresh person object
        result = await db.execute(select(Person).where(Person.id == person_id))
        person = result.scalar_one()
    
    # Update contacts if provided
    if person_data.contacts is not None:
        # Delete existing contacts
        await db.execute(Contact.__table__.delete().where(Contact.person_id == person_id))
        # Add new contacts
        for contact in person_data.contacts:
            contact_obj = Contact(person_id=person_id, **contact.model_dump())
            db.add(contact_obj)
        await db.commit()
    
    # Update addresses if provided
    if person_data.addresses is not None:
        # Delete existing addresses
        await db.execute(Address.__table__.delete().where(
            Address.entity_id == person_id, 
            Address.entity_type == person.person_type
        ))
        # Add new addresses
        for address in person_data.addresses:
            address_obj = Address(
                entity_type=person.person_type, 
                entity_id=person_id, 
                **address.model_dump(exclude={"entity_type", "entity_id"})
            )
            db.add(address_obj)
        await db.commit()
    
    # Fetch updated related data
    contacts = await service.list_contacts(person_id)
    addresses = await service.list_addresses(person_id, entity_type=person.person_type)
    
    # Convert person data to dict and handle UUID fields
    person_dict = person.__dict__.copy()
    person_dict.pop("_sa_instance_state", None)  # Remove SQLAlchemy state
    
    # Convert UUID fields to strings
    if person_dict.get("company_id"):
        person_dict["company_id"] = str(person_dict["company_id"])
    
    # Add related data
    person_dict["contacts"] = contacts
    person_dict["addresses"] = addresses
    
    return PersonResponse.model_validate(person_dict)

@router.delete("/persons/{person_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("person.delete"))])
async def delete_person(person_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a person by ID (and cascade all related records)"""
    # First check if person exists
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    try:
        # Import the required models
        from bheem_core.shared.models import BankAccount, Passport, SocialProfile
        from bheem_core.modules.hr.core.models.hr_models import Interview, Offer, OnboardingChecklist, Employee, JobRequisition
        from sqlalchemy import update as sql_update
        
        # Delete all related records first to avoid foreign key constraint violations
        # Start with HR-specific models that reference candidates/employees
        
        # Check if this person has an Employee record (regardless of person_type)
        employee_result = await db.execute(select(Employee).where(Employee.id == person_id))
        employee_record = employee_result.scalar_one_or_none()
        
        if employee_record:
            emp_uuid = uuid.UUID(person_id)
            await db.execute(
                sql_update(Employee)
                .where(Employee.manager_id == emp_uuid)
                .values(manager_id=None)
            )
            
            # Set hiring_manager_id to NULL for job reqs managed by this employee
            await db.execute(
                sql_update(JobRequisition)
                .where(JobRequisition.hiring_manager_id == person_id)
                .values(hiring_manager_id=None)
            )
            
            # Delete interviews where this employee was the interviewer
            await db.execute(Interview.__table__.delete().where(Interview.interviewer_id == person_id))
        
        # Delete onboarding checklists (references candidates)
        await db.execute(OnboardingChecklist.__table__.delete().where(OnboardingChecklist.candidate_id == person_id))
        
        # Delete offers (references candidates)
        await db.execute(Offer.__table__.delete().where(Offer.candidate_id == person_id))
        
        # Delete interviews (references candidates)
        await db.execute(Interview.__table__.delete().where(Interview.candidate_id == person_id))
        
        # Delete shared models that reference persons
        
        # Delete social profiles
        await db.execute(SocialProfile.__table__.delete().where(SocialProfile.person_id == person_id))
        
        # Delete bank accounts
        await db.execute(BankAccount.__table__.delete().where(BankAccount.person_id == person_id))
        
        # Delete passports
        await db.execute(Passport.__table__.delete().where(Passport.person_id == person_id))
        
        # Delete contacts
        await db.execute(Contact.__table__.delete().where(Contact.person_id == person_id))
        
        # Delete addresses
        await db.execute(Address.__table__.delete().where(
            Address.entity_id == person_id, 
            Address.entity_type == person.person_type
        ))
        
        # If this person has an Employee record, delete it before deleting the Person
        if employee_record:
            await db.execute(Employee.__table__.delete().where(Employee.id == person_id))
        
        # Delete the person using direct SQL to avoid relationship loading
        await db.execute(Person.__table__.delete().where(Person.id == person_id))
        
        await db.commit()
        return None
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting person: {str(e)}")

@router.delete("/employees/{employee_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("employee.delete"))])
async def delete_employee(employee_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an employee by ID (and cascade contacts/addresses/bank accounts/passports)"""
    # First check if employee exists
    result = await db.execute(select(Person).where(Person.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    try:
        # Import the required models
        from bheem_core.shared.models import BankAccount, Passport, SocialProfile
        from bheem_core.modules.hr.core.models.hr_models import Interview, Offer, OnboardingChecklist, Employee, JobRequisition
        from sqlalchemy import update as sql_update
        
        # Delete all related records first to avoid foreign key constraint violations
        # Start with HR-specific models that reference candidates/employees
        
        # Handle employee management relationships - set manager_id to NULL for subordinates
        emp_uuid = uuid.UUID(employee_id)
        await db.execute(
            sql_update(Employee)
            .where(Employee.manager_id == emp_uuid)
            .values(manager_id=None)
        )
        
        # Handle job requisitions - set hiring_manager_id to NULL for job reqs managed by this employee
        await db.execute(
            sql_update(JobRequisition)
            .where(JobRequisition.hiring_manager_id == employee_id)
            .values(hiring_manager_id=None)
        )
        
        # Delete onboarding checklists (references candidates)
        await db.execute(OnboardingChecklist.__table__.delete().where(OnboardingChecklist.candidate_id == employee_id))
        
        # Delete offers (references candidates)
        await db.execute(Offer.__table__.delete().where(Offer.candidate_id == employee_id))
        
        # Delete interviews (references candidates and employees as interviewers)
        await db.execute(Interview.__table__.delete().where(Interview.candidate_id == employee_id))
        await db.execute(Interview.__table__.delete().where(Interview.interviewer_id == employee_id))
        
        # Delete shared models that reference persons
        
        # Delete social profiles
        await db.execute(SocialProfile.__table__.delete().where(SocialProfile.person_id == employee_id))
        
        # Delete bank accounts
        await db.execute(BankAccount.__table__.delete().where(BankAccount.person_id == employee_id))
        
        # Delete passports
        await db.execute(Passport.__table__.delete().where(Passport.person_id == employee_id))
        
        # Delete contacts
        await db.execute(Contact.__table__.delete().where(Contact.person_id == employee_id))
        
        # Delete addresses
        await db.execute(Address.__table__.delete().where(
            Address.entity_id == employee_id, 
            Address.entity_type == employee.person_type
        ))
        
        # Delete the Employee record first, then the Person record
        await db.execute(Employee.__table__.delete().where(Employee.id == employee_id))
        await db.execute(Person.__table__.delete().where(Person.id == employee_id))
        
        await db.commit()
        return None
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting employee: {str(e)}")

@router.get("/persons/employees", response_model=List[PersonResponse], dependencies=[Depends(lambda: require_api_permission("employee.read"))])
async def list_person_employees(db: AsyncSession = Depends(get_db)):
    """List all employees from the persons table (person_type='employee')."""
    result = await db.execute(
        select(Person).where(Person.person_type == "employee", Person.is_active == True)
    )
    employees = result.scalars().all()
    
    # Convert employees to PersonResponse with proper UUID handling
    employee_responses = []
    for emp in employees:
        emp_dict = emp.__dict__.copy()
        emp_dict.pop("_sa_instance_state", None)  # Remove SQLAlchemy state
        
        # Convert UUID fields to strings
        if emp_dict.get("company_id"):
            emp_dict["company_id"] = str(emp_dict["company_id"])
        
        employee_responses.append(PersonResponse.model_validate(emp_dict))
    
    return employee_responses

# -------------------------------
# Lookup Routes
# -------------------------------
# from fastapi import status

# Simplified lookups endpoint without authentication
# @router.get("/lookups", response_model=List[LookupResponse], summary="Get all lookups")
# async def list_lookups(
#     type: Optional[str] = Query(None, description="Filter by lookup type"),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get all lookups with optional filtering by type"""
#     service = HRService(db, event_bus=None)
#     return await service.list_lookups(type)

# @router.get("/lookups/{lookup_id}", response_model=LookupResponse, summary="Get lookup by ID")
# async def get_lookup(
#     lookup_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get lookup by ID"""
#     service = HRService(db, event_bus=None)
#     return await service.get_lookup(lookup_id)

# @router.post("/lookups", response_model=LookupResponse, status_code=status.HTTP_201_CREATED, summary="Create new lookup")
# async def create_lookup(
#     data: LookupCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Create a new lookup"""
#     service = HRService(db, event_bus=None)
#     return await service.create_lookup(data)

# @router.put("/lookups/{lookup_id}", response_model=LookupResponse, summary="Update lookup")
# async def update_lookup(
#     lookup_id: str,
#     data: LookupUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Update lookup"""
#     service = HRService(db, event_bus=None)
#     return await service.update_lookup(lookup_id, data)

# @router.delete("/lookups/{lookup_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete lookup")
# async def delete_lookup(
#     lookup_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Delete lookup"""
#     service = HRService(db, event_bus=None)
#     await service.delete_lookup(lookup_id)
    # return None

# -------------------------------
# Job Requisition Routes
# -------------------------------

# @router.post("/job-requisitions", response_model=JobRequisitionResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("jobrequisition.create"))])
# async def create_job_requisition(
#     data: JobRequisitionCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.create_job_requisition(data)

# @router.get("/job-requisitions/{job_req_id}", response_model=JobRequisitionResponse, dependencies=[Depends(lambda: require_api_permission("jobrequisition.read"))])
# async def get_job_requisition(
#     job_req_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.get_job_requisition(job_req_id)

# @router.put("/job-requisitions/{job_req_id}", response_model=JobRequisitionResponse, dependencies=[Depends(lambda: require_api_permission("jobrequisition.update"))])
# async def update_job_requisition(
#     job_req_id: str,
#     data: JobRequisitionUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.update_job_requisition(job_req_id, data)

# @router.delete("/job-requisitions/{job_req_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("jobrequisition.delete"))])
# async def delete_job_requisition(
#     job_req_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     await service.delete_job_requisition(job_req_id)
#     return None

# @router.get("/job-requisitions", response_model=List[JobRequisitionResponse], dependencies=[Depends(lambda: require_api_permission("jobrequisition.read"))])
# async def list_job_requisitions(
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.list_job_requisitions()

# # -------------------------------
# # Candidate Routes
# # -------------------------------

# @router.post("/candidates", response_model=CandidateResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("candidate.create"))])
# async def create_candidate(
#     data: CandidateCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.create_candidate(data)

# @router.get("/candidates/{candidate_id}", response_model=CandidateResponse, dependencies=[Depends(lambda: require_api_permission("candidate.read"))])
# async def get_candidate(
#     candidate_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.get_candidate(candidate_id)

# @router.put("/candidates/{candidate_id}", response_model=CandidateResponse, dependencies=[Depends(lambda: require_api_permission("candidate.update"))])
# async def update_candidate(
#     candidate_id: str,
#     data: CandidateUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.update_candidate(candidate_id, data)

# @router.delete("/candidates/{candidate_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("candidate.delete"))])
# async def delete_candidate(
#     candidate_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     await service.delete_candidate(candidate_id)
#     return None

# @router.get("/candidates", response_model=List[CandidateResponse], dependencies=[Depends(lambda: require_api_permission("candidate.read"))])
# async def list_candidates(
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.list_candidates()

# -------------------------------
# Interview Routes
# -------------------------------

# @router.post("/interviews", response_model=InterviewResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("interview.create"))])
# async def create_interview(
#     data: InterviewCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     interview = await service.create_interview(data)
#     return InterviewResponse.model_validate(interview)

# @router.get("/interviews/{interview_id}", response_model=InterviewResponse, dependencies=[Depends(lambda: require_api_permission("interview.read"))])
# async def get_interview(
#     interview_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     interview = await service.get_interview(interview_id)
#     return InterviewResponse.model_validate(interview)

# @router.get("/interviews", response_model=List[InterviewResponse], dependencies=[Depends(lambda: require_api_permission("interview.read"))])
# async def list_interviews(
#     candidate_id: str = None,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     interviews = await service.list_interviews(candidate_id)
#     return [InterviewResponse.model_validate(i) for i in interviews]

# @router.put("/interviews/{interview_id}", response_model=InterviewResponse, dependencies=[Depends(lambda: require_api_permission("interview.update"))])
# async def update_interview(
#     interview_id: str,
#     data: InterviewUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     interview = await service.update_interview(interview_id, data)
#     return InterviewResponse.model_validate(interview)

# @router.delete("/interviews/{interview_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("interview.delete"))])
# async def delete_interview(
#     interview_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     await service.delete_interview(interview_id)
#     return None

# -------------------------------
# Offer CRUD Routes
# -------------------------------
# @router.post("/offers", response_model=OfferResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("offer.create"))])
# async def create_offer(
#     offer_data: OfferCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     offer = await service.create_offer(offer_data)
#     return offer

# @router.get("/offers/{offer_id}", response_model=OfferResponse, dependencies=[Depends(lambda: require_api_permission("offer.read"))])
# async def get_offer(
#     offer_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.get_offer(offer_id)

# @router.get("/offers", response_model=list[OfferResponse], dependencies=[Depends(lambda: require_api_permission("offer.read"))])
# async def list_offers(
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.list_offers(skip=skip, limit=limit)

# @router.put("/offers/{offer_id}", response_model=OfferResponse, dependencies=[Depends(lambda: require_api_permission("offer.update"))])
# async def update_offer(
#     offer_id: str,
#     offer_data: OfferUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.update_offer(offer_id, offer_data)

# @router.delete("/offers/{offer_id}", dependencies=[Depends(lambda: require_api_permission("offer.delete"))])
# async def delete_offer(
#     offer_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.delete_offer(offer_id)

# # -------------------------------
# # OnboardingChecklist CRUD Routes
# # -------------------------------
# @router.post("/onboarding-checklists", response_model=OnboardingChecklistResponse, status_code=201, dependencies=[Depends(lambda: require_api_permission("onboardingchecklist.create"))])
# async def create_onboarding_checklist(
#     checklist_data: OnboardingChecklistCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     checklist = await service.create_onboarding_checklist(checklist_data)
#     return checklist

# @router.get("/onboarding-checklists/{checklist_id}", response_model=OnboardingChecklistResponse, dependencies=[Depends(lambda: require_api_permission("onboardingchecklist.read"))])
# async def get_onboarding_checklist(
#     checklist_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.get_onboarding_checklist(checklist_id)

# @router.get("/onboarding-checklists", response_model=list[OnboardingChecklistResponse], dependencies=[Depends(lambda: require_api_permission("onboardingchecklist.read"))])
# async def list_onboarding_checklists(
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.list_onboarding_checklists(skip=skip, limit=limit)

# @router.put("/onboarding-checklists/{checklist_id}", response_model=OnboardingChecklistResponse, dependencies=[Depends(lambda: require_api_permission("onboardingchecklist.update"))])
# async def update_onboarding_checklist(
#     checklist_id: str,
#     checklist_data: OnboardingChecklistUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.update_onboarding_checklist(checklist_id, checklist_data)

# @router.delete("/onboarding-checklists/{checklist_id}", dependencies=[Depends(lambda: require_api_permission("onboardingchecklist.delete"))])
# async def delete_onboarding_checklist(
#     checklist_id: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     service = HRService(db)
#     return await service.delete_onboarding_checklist(checklist_id)

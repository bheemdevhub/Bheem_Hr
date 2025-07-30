# app/modules/hr/api/v1/routes/contact.py
"""Contact CRUD Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from starlette import status as http_status

from bheem_core.core.database import get_db
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.shared.schemas import ContactCreate, ContactResponse

# Mock dependencies for auth - replace with actual imports when available
def get_current_user():
    """Mock user authentication"""
    return {"user_id": "mock_user", "role": "admin"}

def require_api_permission(permission: str):
    """Mock permission check"""
    def permission_dependency():
        return True
    return permission_dependency

router = APIRouter()

# -------------------------------
# Contact CRUD Operations
# -------------------------------

@router.get("/employees/{employee_id}/contacts", response_model=List[ContactResponse], summary="List contacts for employee")
async def list_employee_contacts(
    employee_id: str = Path(..., description="ID of the employee"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all contacts for a specific employee"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contacts = await hr_service.list_contacts(employee_id)
        if is_active is not None:
            contacts = [c for c in contacts if c.is_active == is_active]
        return contacts
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving employee contacts: {str(e)}"
        )

@router.post("/employees/{employee_id}/contacts", response_model=ContactResponse, status_code=http_status.HTTP_201_CREATED, summary="Create new contact for employee")
async def create_employee_contact(
    contact_data: ContactCreate,
    employee_id: str = Path(..., description="ID of the employee"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new contact for an employee"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contact = await hr_service.create_contact(employee_id, contact_data)
        return contact
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating employee contact: {str(e)}"
        )

@router.get("/employees/{employee_id}/contacts/{contact_id}", response_model=ContactResponse, summary="Get specific employee contact")
async def get_employee_contact(
    employee_id: str = Path(..., description="Employee ID"),
    contact_id: str = Path(..., description="Contact ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific contact for an employee"""
    from sqlalchemy import select
    from bheem_core.shared.models import Contact
    
    try:
        result = await db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.person_id == employee_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contact not found for this employee"
            )
        
        return ContactResponse.model_validate(contact)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving employee contact: {str(e)}"
        )

@router.put("/employees/{employee_id}/contacts/{contact_id}", response_model=ContactResponse, summary="Update employee contact")
async def update_employee_contact(
    contact_data: ContactCreate,
    employee_id: str = Path(..., description="Employee ID"),
    contact_id: str = Path(..., description="Contact ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a specific contact for an employee"""
    from sqlalchemy import select
    from bheem_core.shared.models import Contact
    
    try:
        # Verify the contact belongs to this employee
        result = await db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.person_id == employee_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contact not found for this employee"
            )
        
        # Update the contact
        hr_service = HRService(db, event_bus=None)
        updated_contact = await hr_service.update_contact(contact_id, contact_data)
        return updated_contact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating employee contact: {str(e)}"
        )

@router.delete("/employees/{employee_id}/contacts/{contact_id}", status_code=http_status.HTTP_204_NO_CONTENT, summary="Delete employee contact")
async def delete_employee_contact(
    employee_id: str = Path(..., description="Employee ID"),
    contact_id: str = Path(..., description="Contact ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a specific contact for an employee"""
    from sqlalchemy import select
    from bheem_core.shared.models import Contact
    
    try:
        # Verify the contact belongs to this employee
        result = await db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.person_id == employee_id
            )
        )
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Contact not found for this employee"
            )
        
        # Delete the contact
        hr_service = HRService(db, event_bus=None)
        await hr_service.delete_contact(contact_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting employee contact: {str(e)}"
        )

@router.get("/employees/{employee_id}/contacts/primary", response_model=ContactResponse, summary="Get employee primary contact")
async def get_employee_primary_contact(
    employee_id: str = Path(..., description="Employee ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the primary contact for an employee"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contact = await hr_service.get_primary_contact(employee_id)
        return contact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving employee primary contact: {str(e)}"
        )

# Keep the original generic contact routes for other use cases
@router.get("/", response_model=List[ContactResponse], summary="List contacts for person")
async def list_contacts(
    person_id: str = Query(..., description="ID of the person (employee, candidate, etc.)"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all contacts for a specific person (generic endpoint)"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contacts = await hr_service.list_contacts(person_id)
        if is_active is not None:
            contacts = [c for c in contacts if c.is_active == is_active]
        return contacts
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contacts: {str(e)}"
        )

@router.post("/", response_model=ContactResponse, status_code=http_status.HTTP_201_CREATED, summary="Create new contact")
async def create_contact(
    contact_data: ContactCreate,
    person_id: str = Query(..., description="ID of the person"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new contact for a person (generic endpoint)"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contact = await hr_service.create_contact(person_id, contact_data)
        return contact
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating contact: {str(e)}"
        )

@router.get("/{contact_id}", response_model=ContactResponse, summary="Get contact by ID")
async def get_contact(
    contact_id: str = Path(..., description="Contact ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific contact by ID"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contact = await hr_service.get_contact_by_id(contact_id)
        return contact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contact: {str(e)}"
        )

@router.put("/{contact_id}", response_model=ContactResponse, summary="Update contact")
async def update_contact(
    contact_data: ContactCreate,
    contact_id: str = Path(..., description="Contact ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing contact"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contact = await hr_service.update_contact(contact_id, contact_data)
        return contact
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating contact: {str(e)}"
        )

@router.delete("/{contact_id}", status_code=http_status.HTTP_204_NO_CONTENT, summary="Delete contact")
async def delete_contact(
    contact_id: str = Path(..., description="Contact ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a contact (soft delete - set is_active to False)"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        await hr_service.delete_contact(contact_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting contact: {str(e)}"
        )

@router.get("/search", response_model=List[ContactResponse], summary="Search contacts")
async def search_contacts(
    email: Optional[str] = Query(None, description="Search by email"),
    phone: Optional[str] = Query(None, description="Search by phone number"),
    person_id: Optional[str] = Query(None, description="Filter by person ID"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Search contacts by email, phone, or person ID"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        contacts = await hr_service.search_contacts(
            email=email,
            phone=phone,
            person_id=person_id,
            is_active=is_active
        )
        return contacts
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching contacts: {str(e)}"
        )


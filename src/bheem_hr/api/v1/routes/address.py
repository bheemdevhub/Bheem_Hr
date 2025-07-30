# app/modules/hr/api/v1/routes/address.py
"""Address CRUD Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from starlette import status as http_status

from bheem_core.core.database import get_db
from bheem_core.modules.hr.core.services.hr_service import HRService
from bheem_core.shared.schemas import AddressCreate, AddressResponse
from bheem_core.shared.models import Address

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
# Address CRUD Operations
# -------------------------------

@router.get("/", response_model=List[AddressResponse], summary="List addresses for entity")
async def list_addresses(
    entity_id: str = Query(..., description="ID of the entity (person, employee, etc.)"),
    entity_type: str = Query(default="employee", description="Type of entity (employee, candidate, etc.)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all addresses for a specific entity"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        addresses = await hr_service.list_addresses(entity_id, entity_type)
        return addresses
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving addresses: {str(e)}"
        )

@router.get("/{address_id}", response_model=AddressResponse, summary="Get address by ID")
async def get_address(
    address_id: str = Path(..., description="Address ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific address by ID"""
    from sqlalchemy import select
    
    try:
        result = await db.execute(select(Address).where(Address.id == address_id))
        address = result.scalar_one_or_none()
        
        if not address:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Address not found"
            )
        
        return AddressResponse.model_validate(address)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving address: {str(e)}"
        )

@router.post("/", response_model=AddressResponse, status_code=http_status.HTTP_201_CREATED, summary="Create new address")
async def create_address(
    address_data: AddressCreate,
    entity_id: str = Query(..., description="ID of the entity"),
    entity_type: str = Query(default="employee", description="Type of entity"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new address for an entity"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        address = await hr_service.create_address(entity_id, address_data, entity_type)
        return address
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating address: {str(e)}"
        )

@router.put("/{address_id}", response_model=AddressResponse, summary="Update address")
async def update_address(
    address_id: str = Path(..., description="Address ID"),
    address_data: AddressCreate = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing address"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        address = await hr_service.update_address(address_id, address_data)
        return address
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating address: {str(e)}"
        )


@router.delete("/{address_id}", status_code=http_status.HTTP_204_NO_CONTENT, summary="Delete address")
async def delete_address(
    address_id: str = Path(..., description="Address ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an address (soft delete - set is_active to False)"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        await hr_service.delete_address(address_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting address: {str(e)}"
        )



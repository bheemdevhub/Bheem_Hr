# app/modules/hr/api/v1/routes/passport.py
"""Passport CRUD Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from starlette import status as http_status

from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.shared.schemas import PassportCreate, PassportResponse

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
# Passport CRUD Operations
# -------------------------------

@router.get("/", response_model=List[PassportResponse], summary="List passports for person", tags=["Passport Management"])
async def list_passports(
    person_id: str = Query(..., description="ID of the person (employee, candidate, etc.)"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all passports for a specific person"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        passports = await hr_service.list_passports(person_id)
        if is_active is not None:
            passports = [p for p in passports if p.is_active == is_active]
        return passports
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving passports: {str(e)}"
        )

@router.post("/", response_model=PassportResponse, status_code=http_status.HTTP_201_CREATED, summary="Create new passport", tags=["Passport Management"])
async def create_passport(
    passport_data: PassportCreate,
    person_id: str = Query(..., description="ID of the person"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new passport for a person"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        passport = await hr_service.create_passport(person_id, passport_data)
        return passport
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating passport: {str(e)}"
        )

@router.get("/search", response_model=List[PassportResponse], summary="Search passports", tags=["Passport Management"])
async def search_passports(
    passport_number: Optional[str] = Query(None, description="Search by passport number"),
    country: Optional[str] = Query(None, description="Search by issuing country"),
    person_id: Optional[str] = Query(None, description="Filter by person ID"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Search passports by passport number, country, or person ID"""
    from sqlalchemy import select, or_
    from app.shared.models import Passport
    
    try:
        query = select(Passport)
        filters = []
        
        if is_active is not None:
            filters.append(Passport.is_active == is_active)
        
        if person_id:
            filters.append(Passport.person_id == person_id)
        
        if passport_number:
            filters.append(Passport.passport_number.ilike(f"%{passport_number}%"))
        
        if country:
            filters.append(Passport.issuing_country.ilike(f"%{country}%"))
        
        if filters:
            query = query.where(*filters)
        
        result = await db.execute(query)
        passports = result.scalars().all()
        return [PassportResponse.model_validate(passport) for passport in passports]
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching passports: {str(e)}"
        )

@router.get("/{passport_id}", response_model=PassportResponse, summary="Get passport by ID", tags=["Passport Management"])
async def get_passport(
    passport_id: str = Path(..., description="Passport ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific passport by ID"""
    from sqlalchemy import select
    from app.shared.models import Passport
    
    try:
        result = await db.execute(select(Passport).where(Passport.id == passport_id))
        passport = result.scalar_one_or_none()
        
        if not passport:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Passport not found"
            )
        
        return PassportResponse.model_validate(passport)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving passport: {str(e)}"
        )

@router.put("/{passport_id}", response_model=PassportResponse, summary="Update passport", tags=["Passport Management"])
async def update_passport(
    passport_data: PassportCreate,
    passport_id: str = Path(..., description="Passport ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update an existing passport"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        passport = await hr_service.update_passport(passport_id, passport_data)
        return passport
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating passport: {str(e)}"
        )

@router.delete("/{passport_id}", status_code=http_status.HTTP_204_NO_CONTENT, summary="Delete passport", tags=["Passport Management"])
async def delete_passport(
    passport_id: str = Path(..., description="Passport ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a passport (soft delete - set is_active to False)"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        await hr_service.delete_passport(passport_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting passport: {str(e)}"
        )

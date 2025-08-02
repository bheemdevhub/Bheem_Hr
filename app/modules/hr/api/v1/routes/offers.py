# app/modules/hr/api/v1/routes/offers.py
"""HR Offers Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from functools import partial
from app.modules.auth.core.services.permissions_service import (
    get_current_user, require_roles, require_superadmin, require_api_permission
)
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from app.modules.hr.core.services.hr_service import HRService
from app.modules.auth.core.services.permissions_service import get_current_company_id

router = APIRouter()

@router.get("/", summary="Get all offers", tags=["Offers"])
async def list_offers(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate"),
    offer_status: Optional[str] = Query(None, description="Filter by offer status"),
    background_check_status: Optional[str] = Query(None, description="Filter by background check status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "offer:view")),
):
   
    hr_service = HRService(db, event_bus=None)
    
    try:
        result = await hr_service.list_offers(
            candidate_id=candidate_id,
            offer_status=offer_status,
            background_check_status=background_check_status,
            is_active=is_active
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving offers: {str(e)}"
        )

@router.get("/{offer_id}", summary="Get offer by ID", tags=["Offers"])
async def get_offer(
    offer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "offer:view")),
):
   
    hr_service = HRService(db, event_bus=None)
    
    try:
        return await hr_service.get_offer(offer_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving offer: {str(e)}"
        )

from app.modules.hr.core.schemas.hr_schemas import OfferCreate, OfferResponse, OfferUpdate

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create job offer", tags=["Offers"], response_model=OfferResponse)
async def create_offer(
    offer: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    company_id: str = Depends(get_current_company_id),
    permission=Depends(partial(require_api_permission, "offer:create")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        result = await hr_service.create_offer(offer, company_id=company_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating offer: {str(e)}"
        )

@router.put("/{offer_id}", summary="Update offer", tags=["Offers"])
async def update_offer(
    offer_id: str,
    offer: OfferUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "offer:update")),
):
    hr_service = HRService(db, event_bus=None)
    try:
        return await hr_service.update_offer(offer_id, offer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating offer: {str(e)}"
        )

@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Withdraw offer", tags=["Offers"])
async def delete_offer(
    offer_id: str,
    reason: Optional[str] = Query(None, description="Delete for Offers"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    permission=Depends(partial(require_api_permission, "offer:delete")),
):
   
    hr_service = HRService(db, event_bus=None)
    
    try:
        await hr_service.delete_offer(offer_id, reason)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting offer: {str(e)}"
        )

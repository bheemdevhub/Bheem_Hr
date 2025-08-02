# app/modules/hr/api/v1/routes/bank_accounts.py
"""Bank Account CRUD Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from starlette import status as http_status

from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.shared.schemas import BankAccountCreate, BankAccountResponse

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
# Bank Account CRUD Operations 
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

@router.get("/persons/{person_id}/bank-accounts/{bank_account_id}", response_model=BankAccountResponse, dependencies=[Depends(lambda: require_api_permission("bankaccount.read"))])
async def get_bank_account(person_id: str, bank_account_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific bank account for a person"""
    service = HRService(db)
    bank_account = await service.get_bank_account_by_id(bank_account_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    if bank_account.person_id != person_id:
        raise HTTPException(status_code=404, detail="Bank account not found for this person")
    return bank_account

@router.put("/persons/{person_id}/bank-accounts/{bank_account_id}", response_model=BankAccountResponse, dependencies=[Depends(lambda: require_api_permission("bankaccount.update"))])
async def update_person_bank_account(person_id: str, bank_account_id: str, bank_data: BankAccountCreate, db: AsyncSession = Depends(get_db)):
    """Update a specific bank account for a person"""
    service = HRService(db)
    # Verify bank account belongs to person
    existing = await service.get_bank_account_by_id(bank_account_id)
    if not existing or existing.person_id != person_id:
        raise HTTPException(status_code=404, detail="Bank account not found for this person")
    return await service.update_bank_account(bank_account_id, bank_data)

@router.delete("/persons/{person_id}/bank-accounts/{bank_account_id}", status_code=204, dependencies=[Depends(lambda: require_api_permission("bankaccount.delete"))])
async def delete_person_bank_account(person_id: str, bank_account_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a specific bank account for a person"""
    service = HRService(db)
    # Verify bank account belongs to person
    existing = await service.get_bank_account_by_id(bank_account_id)
    if not existing or existing.person_id != person_id:
        raise HTTPException(status_code=404, detail="Bank account not found for this person")
    await service.delete_bank_account(bank_account_id)
    return None

# Individual bank account operations (without person context)
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

@router.get("/persons/{person_id}/bank-accounts/primary", response_model=BankAccountResponse, dependencies=[Depends(lambda: require_api_permission("bankaccount.read"))])
async def get_primary_bank_account(person_id: str, db: AsyncSession = Depends(get_db)):
    """Get the primary bank account for a person"""
    service = HRService(db)
    bank_account = await service.get_primary_bank_account(person_id)
    if not bank_account:
        raise HTTPException(status_code=404, detail="No primary bank account found")
    return bank_account

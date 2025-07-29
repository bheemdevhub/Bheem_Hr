# app/modules/hr/api/v1/routes/lookups.py
"""HR Lookups Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.hr.core.services.hr_service import HRService
from app.shared.schemas import LookupResponse, LookupCreate, LookupUpdate, LookupTypeSchema

router = APIRouter()

@router.get("/", response_model=List[LookupResponse], summary="Get all lookups", tags=["Lookup Management"])
async def list_lookups(
    type: Optional[LookupTypeSchema] = Query(None, description="Filter by lookup type (department, position, skill, etc.)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in lookup name or code"),
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRService(db, event_bus=None)
    try:
        type_str = type.value if type else None
        result = await hr_service.list_lookups(type_str)
        if is_active is not None:
            result = [lookup for lookup in result if lookup.is_active == is_active]
        if search:
            search_lower = search.lower()
            result = [
                lookup for lookup in result 
                if search_lower in lookup.name.lower() or search_lower in lookup.code.lower()
            ]
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving lookups: {str(e)}"
        )

@router.get("/{lookup_id}", response_model=LookupResponse, summary="Get lookup by ID", tags=["Lookup Management"])
async def get_lookup(
    lookup_id: str,
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRService(db, event_bus=None)
    try:
        return await hr_service.get_lookup(lookup_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving lookup: {str(e)}"
        )

@router.post("/", response_model=LookupResponse, status_code=status.HTTP_201_CREATED, summary="Create new lookup", tags=["Lookup Management"])
async def create_lookup(
    lookup_data: LookupCreate,
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRService(db, event_bus=None)
    try:
        return await hr_service.create_lookup(lookup_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lookup: {str(e)}"
        )

@router.put("/{lookup_id}", response_model=LookupResponse, summary="Update lookup", tags=["Lookup Management"])
async def update_lookup(
    lookup_id: str,
    lookup_data: LookupUpdate,
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRService(db, event_bus=None)
    try:
        return await hr_service.update_lookup(lookup_id, lookup_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lookup: {str(e)}"
        )

@router.delete("/{lookup_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete lookup", tags=["Lookup Management"])
async def delete_lookup(
    lookup_id: str,
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRService(db, event_bus=None) 
    try:
        await hr_service.delete_lookup(lookup_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting lookup: {str(e)}"
        )

@router.get("/schema/updateable-fields", summary="Get updateable fields schema")
async def get_updateable_fields_schema():
    return {
        "updateable_fields": {
            "name": {
                "type": "string",
                "description": "Display name of the lookup",
                "required": False
            },
            "description": {
                "type": "string", 
                "description": "Description of the lookup",
                "required": False
            },
            "is_active": {
                "type": "boolean",
                "description": "Whether the lookup is active",
                "required": False
            }
        },
        "immutable_fields": {
            "type": {
                "description": "Lookup category - set during creation only",
                "valid_values": [t.value for t in LookupTypeSchema]
            },
            "code": {
                "description": "Unique identifier code - set during creation only"
            },
            "id": {
                "description": "Primary key - system generated"
            }
        },
        "notes": [
            "Only name, description, and is_active can be updated",
            "To change type or code, create a new lookup and deactivate the old one",
            "All update fields are optional - only provide fields you want to change"
        ]
    }

@router.get("/types", summary="Get all available lookup types", tags=["Lookup Types"])
async def get_lookup_types():
    """
    Get all available lookup types with descriptions and examples.
    
    This endpoint provides a comprehensive list of all supported lookup types
    in the system, along with their descriptions and example codes.
    """
    return {
        "lookup_types": [
            {
                "type": "department",
                "name": "Departments",
                "description": "Organizational departments and units",
                "examples": ["ENG (Engineering)", "HR (Human Resources)", "SALES (Sales)", "FINANCE (Finance)"],
                "usage": "Used in employee records and job requisitions"
            },
            {
                "type": "position", 
                "name": "Positions",
                "description": "Job positions and titles",
                "examples": ["SR_DEV (Senior Developer)", "PM (Product Manager)", "DESIGNER (UI/UX Designer)"],
                "usage": "Used in employee records and job requisitions"
            },
            {
                "type": "skill",
                "name": "Skills",
                "description": "Technical and soft skills",
                "examples": ["PYTHON (Python Programming)", "JAVASCRIPT (JavaScript)", "REACT (React.js)", "AWS (Amazon Web Services)"],
                "usage": "Used in job requisitions and candidate profiles"
            },
            {
                "type": "job_type",
                "name": "Job Types", 
                "description": "Types of employment",
                "examples": ["FULL_TIME (Full-time Employment)", "CONTRACT (Contract Work)", "INTERN (Internship)"],
                "usage": "Used in job requisitions"
            },
            {
                "type": "employee_status",
                "name": "Employee Status",
                "description": "Employee status values",
                "examples": ["ACTIVE (Active Employee)", "INACTIVE (Inactive)", "ON_LEAVE (On Leave)"],
                "usage": "Used in employee records"
            },
            {
                "type": "candidate_status",
                "name": "Candidate Status",
                "description": "Candidate pipeline status",
                "examples": ["APPLIED (Application Received)", "SCREENING (Under Screening)", "INTERVIEW (Interview Stage)"],
                "usage": "Used in candidate management"
            },
            {
                "type": "role",
                "name": "User Roles",
                "description": "System user roles",
                "examples": ["ADMIN (Administrator)", "MANAGER (Manager)", "EMPLOYEE (Employee)"],
                "usage": "Used in user management and permissions"
            },
            {
                "type": "permission",
                "name": "Permissions",
                "description": "System permissions",
                "examples": ["CREATE_USER (Create User)", "VIEW_REPORTS (View Reports)", "MANAGE_PAYROLL (Manage Payroll)"],
                "usage": "Used in role-based access control"
            }
        ],
        "total_types": 8,
        "notes": [
            "Each lookup type serves a specific purpose in the HR system",
            "Lookups provide consistent reference data across modules",
            "Use the /lookups endpoint with type parameter to filter by specific type"
        ]
    }

# @router.get("/stats", summary="Get lookup statistics", tags=["Lookup Statistics"])
# async def get_lookup_stats(
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Get statistics about lookups by type.
    
#     **Returns:** Statistics including total count and breakdown by type.
#     """
#     hr_service = HRService(db, event_bus=None)
    
#     try:
#         all_lookups = await hr_service.list_lookups()
        
#         # Group by type and count
#         stats_by_type = {}
#         active_count = 0
#         inactive_count = 0
        
#         for lookup in all_lookups:
#             lookup_type = lookup.type
#             if lookup_type not in stats_by_type:
#                 stats_by_type[lookup_type] = {
#                     "total": 0,
#                     "active": 0,
#                     "inactive": 0
#                 }
            
#             stats_by_type[lookup_type]["total"] += 1
            
#             if lookup.is_active:
#                 stats_by_type[lookup_type]["active"] += 1
#                 active_count += 1
#             else:
#                 stats_by_type[lookup_type]["inactive"] += 1
#                 inactive_count += 1
        
#         return {
#             "total_lookups": len(all_lookups),
#             "active_lookups": active_count,
#             "inactive_lookups": inactive_count,
#             "by_type": stats_by_type,
#             "available_types": list(stats_by_type.keys()),
#             "summary": [
#                 f"Total: {len(all_lookups)} lookups",
#                 f"Active: {active_count} lookups",
#                 f"Types: {len(stats_by_type)} different types"
#             ]
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error retrieving lookup statistics: {str(e)}"
#         )

@router.get("/stats", summary="Get lookup statistics", tags=["Lookup Statistics"])
async def get_lookup_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about lookups by type.
    
    **Returns:** Statistics including total count and breakdown by type.
    """
    hr_service = HRService(db, event_bus=None)
    
    try:
        all_lookups = await hr_service.list_lookups()
        
        # Group by type and count
        stats_by_type = {}
        active_count = 0
        inactive_count = 0
        
        for lookup in all_lookups:
            lookup_type = lookup.type
            if lookup_type not in stats_by_type:
                stats_by_type[lookup_type] = {
                    "total": 0,
                    "active": 0,
                    "inactive": 0
                }
            
            stats_by_type[lookup_type]["total"] += 1
            
            if lookup.is_active:
                stats_by_type[lookup_type]["active"] += 1
                active_count += 1
            else:
                stats_by_type[lookup_type]["inactive"] += 1
                inactive_count += 1
        
        return {
            "total_lookups": len(all_lookups),
            "active_lookups": active_count,
            "inactive_lookups": inactive_count,
            "by_type": stats_by_type,
            "available_types": list(stats_by_type.keys()),
            "summary": [
                f"Total: {len(all_lookups)} lookups",
                f"Active: {active_count} lookups",
                f"Types: {len(stats_by_type)} different types"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving lookup statistics: {str(e)}"
        )

# Utility endpoints for better API experience
@router.get("/health", summary="Check lookup service health", tags=["Service Health"])
async def check_lookup_service_health(
    db: AsyncSession = Depends(get_db)
):
    """Check if the lookup service is healthy and responsive"""
    try:
        hr_service = HRService(db, event_bus=None)
        # Simple test - try to get lookups count
        lookups = await hr_service.list_lookups()
        return {
            "status": "healthy",
            "service": "lookup_service",
            "total_lookups": len(lookups),
            "timestamp": "2025-07-02T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@router.post("/bulk", response_model=List[LookupResponse], status_code=status.HTTP_201_CREATED, summary="Create multiple lookups", tags=["Bulk Operations"])
async def create_bulk_lookups(
    lookups_data: List[LookupCreate],
    db: AsyncSession = Depends(get_db)
):
    """Create multiple lookups at once"""
    hr_service = HRService(db, event_bus=None)
    created_lookups = []
    errors = []
    
    for i, lookup_data in enumerate(lookups_data):
        try:
            lookup = await hr_service.create_lookup(lookup_data)
            created_lookups.append(lookup)
        except Exception as e:
            errors.append({
                "index": i,
                "data": lookup_data.model_dump(),
                "error": str(e)
            })
    
    if errors and not created_lookups:
        # All failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "All lookups failed to create", "errors": errors}
        )
    elif errors:
        # Partial success
        raise HTTPException(
            status_code=status.HTTP_207_MULTI_STATUS,
            detail={
                "message": f"Created {len(created_lookups)} of {len(lookups_data)} lookups",
                "created": created_lookups,
                "errors": errors
            }
        )
    
    return created_lookups

@router.patch("/{lookup_id}/toggle", response_model=LookupResponse, summary="Toggle lookup active status", tags=["Lookup Management"])
async def toggle_lookup_status(
    lookup_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Toggle the active status of a lookup (active -> inactive or inactive -> active)"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        # Get current lookup
        current_lookup = await hr_service.get_lookup(lookup_id)
        
        # Create update with toggled status
        from app.shared.schemas import LookupUpdate
        update_data = LookupUpdate(is_active=not current_lookup.is_active)
        
        # Update and return
        return await hr_service.update_lookup(lookup_id, update_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling lookup status: {str(e)}"
        )

@router.get("/by-type/{lookup_type}", response_model=List[LookupResponse], summary="Get lookups by type", tags=["Lookup Management"])
async def get_lookups_by_type(
    lookup_type: LookupTypeSchema,
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db)
):
    """Get all lookups of a specific type"""
    hr_service = HRService(db, event_bus=None)
    
    try:
        lookups = await hr_service.list_lookups(lookup_type.value)
        
        if is_active is not None:
            lookups = [lookup for lookup in lookups if lookup.is_active == is_active]
        
        return lookups
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving lookups by type: {str(e)}"
        )

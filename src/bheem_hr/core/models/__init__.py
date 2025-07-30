# app/modules/hr/core/models/__init__.py

from .hr_models import *

__all__ = [
    # Employee related
    "Employee",
    
    # Job Requisition related
    "JobRequisition",
    
    # Candidate related
    "Candidate",
    "CandidateEducation", 
    "CandidateExperience",
    "CandidateApplication",
    
    # Interview related
    "Interview",
    
    # Offer related
    "Offer",
    
    # Onboarding related
    "OnboardingChecklist",
    
    # Unified Models (imported from shared.models)
    "Activity",
    "ActivityType", 
    "ActivityStatus",
    "Rating",
    "RatingType",
    "Tag",
    "TagCategory",
]


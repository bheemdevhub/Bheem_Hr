# app/modules/hr/core/schemas/__init__.py

from .hr_schemas import *

__all__ = [
    # Social Profile schemas
    "SocialProfileCreate",
    "SocialProfileResponse",
    
    # Lookup schemas
    "LookupResponse",
    
    # Employee schemas
    "EmployeeCreate",
    "EmployeeUpdate", 
    "EmployeeResponse",
    "EmployeeListResponse",
    
    # Job Requisition schemas
    "JobRequisitionCreate",
    "JobRequisitionUpdate",
    "JobRequisitionResponse",
    "JobRequisitionListResponse",
    "JobRequisitionSkillCreate",
    "JobRequisitionSkillResponse",
    
    # Candidate schemas
    "CandidateCreate",
    "CandidateUpdate",
    "CandidateResponse",
    "CandidateListResponse",
    "CandidateSkillCreate",
    "CandidateSkillResponse",
    "CandidateEducationCreate",
    "CandidateEducationResponse",
    "CandidateExperienceCreate",
    "CandidateExperienceResponse",
    "CandidateApplicationCreate",
    "CandidateApplicationUpdate",
    "CandidateApplicationResponse",
    
    # Interview schemas
    "InterviewCreate",
    "InterviewUpdate",
    "InterviewResponse",
    "InterviewListResponse",
    "InterviewFeedbackCreate",
    "InterviewFeedbackUpdate",
    "InterviewFeedbackResponse",
    
    # Offer schemas
    "OfferCreate",
    "OfferUpdate",
    "OfferResponse",
    "OfferListResponse",
    "OfferApprovalCreate",
    "OfferApprovalResponse",
    "BackgroundCheckCreate",
    "BackgroundCheckUpdate",
    "BackgroundCheckResponse",
    
    # Onboarding schemas
    "OnboardingChecklistTemplateCreate",
    "OnboardingChecklistTemplateResponse",
    "OnboardingChecklistCreate",
    "OnboardingChecklistResponse",
    "OnboardingChecklistItemCreate",
    "OnboardingChecklistItemUpdate",
    "OnboardingChecklistItemResponse",
]


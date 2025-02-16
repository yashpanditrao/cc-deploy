from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional

class PersonalProfileBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str]
    bio: Optional[str]
    role: str
    linkedin_url: Optional[str]
    education: Optional[str]
    company_id: Optional[str]
    interests: Optional[List[str]]
    image_url: Optional[str]

class ProfileResponse(BaseModel):
    id: str
    name: str
    role: str
    education: Optional[str]
    bio: Optional[str]
    ai_bio: Optional[str]
    interests: Optional[List[str]]
    image_url: Optional[str]
    similarity_score: Optional[float]
    match_explanation: Optional[str]

class SearchQuery(BaseModel):
    query: str
    search_type: str  # 'profile', 'company', or 'cofounder'
    num_results: Optional[int] = 5
    profile_id: Optional[str] = None  # Required for cofounder search
    role_filter: Optional[str] = None  # 'founder' or 'investor'

    @validator('role_filter')
    def validate_role_filter(cls, v, values):
        if v is not None and values.get('search_type') == 'company':
            raise ValueError("role_filter cannot be used with company search")
        return v

    @validator('profile_id')
    def validate_profile_id(cls, v, values):
        if v is not None and values.get('search_type') == 'company':
            raise ValueError("profile_id cannot be used with company search")
        return v 
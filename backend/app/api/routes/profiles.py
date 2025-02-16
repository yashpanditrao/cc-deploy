from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.core.config import settings
from app.services.embeddings import update_single_profile_embeddings, update_single_profile_ai_bio
from supabase import create_client

router = APIRouter()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

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

@router.post("/")
async def create_profile(profile: PersonalProfileBase):
    try:
        # First create the profile without embeddings
        profile_dict = profile.dict()
        result = supabase.table("PersonalProfile").insert(profile_dict).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create profile")
            
        # Get the created profile's ID
        profile_id = result.data[0]['id']
        
        # Generate embeddings for the new profile
        embeddings = update_single_profile_embeddings(profile_id)
        
        # Generate AI bio
        ai_bio = update_single_profile_ai_bio(profile_id)
        
        return {
            "message": "Profile created successfully with embeddings and AI bio",
            "data": result.data[0],
            "embeddings": embeddings,
            "ai_bio": ai_bio
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{profile_id}/embeddings")
async def update_profile_embeddings(profile_id: str):
    """Update embeddings for a specific profile"""
    try:
        embeddings = update_single_profile_embeddings(profile_id)
        return {
            "message": "Profile embeddings updated successfully",
            "embeddings": embeddings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{profile_id}/ai-bio")
async def update_profile_ai_bio(profile_id: str):
    """Update AI bio and its embedding for a specific profile"""
    try:
        ai_bio = update_single_profile_ai_bio(profile_id)
        return {
            "message": "Profile AI bio updated successfully",
            "ai_bio": ai_bio
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
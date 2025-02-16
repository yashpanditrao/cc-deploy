from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from app.services.embeddings import get_embedding, update_single_company_embeddings
from supabase import create_client

router = APIRouter()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class CompanyProfileBase(BaseModel):
    name: str
    description: Optional[str]
    industry: Optional[str]
    website: Optional[str]
    founded_year: Optional[int]
    location: Optional[str]

@router.post("/")
async def create_company(company: CompanyProfileBase):
    try:
        # Store company data in Supabase
        company_dict = company.dict()
        
        # Generate embedding for company description if available
        if company.description:
            description_embedding = get_embedding(company.description)
            if description_embedding:
                company_dict['description_vector'] = description_embedding
        
        result = supabase.table("CompanyProfile").insert(company_dict).execute()
        return {"message": "Company created successfully", "data": result.data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{company_id}/embeddings")
async def update_company_embeddings(company_id: str):
    """Update embeddings for a specific company"""
    try:
        embeddings = update_single_company_embeddings(company_id)
        return {
            "message": "Company embeddings updated successfully",
            "data": embeddings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
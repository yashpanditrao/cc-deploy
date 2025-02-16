from fastapi import APIRouter, HTTPException
from app.api.models.company import CompanyProfileBase
from app.core.config import settings
from app.services.embeddings import get_embedding, update_single_company_embeddings
from supabase import create_client

router = APIRouter()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@router.post("")
async def create_company(company: CompanyProfileBase):
    try:
        # Store company data in Supabase
        company_dict = company.dict()
        result = supabase.table("companyprofile").insert(company_dict).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create company")
        
        # Get the created company's ID
        company_id = result.data[0]['id']
        
        # Generate embeddings for the new company
        embeddings = update_single_company_embeddings(company_id)
        
        return {
            "message": "Company created successfully with embeddings",
            "data": result.data[0],
            "embeddings": embeddings
        }
    
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
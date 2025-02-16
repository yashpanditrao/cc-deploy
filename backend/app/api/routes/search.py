from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.api.models.profile import SearchQuery
from app.core.config import settings
from app.services.embeddings import get_embedding
from app.utils.explanations import generate_match_explanation, generate_company_explanation
from supabase import create_client

router = APIRouter()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

class SearchQuery(BaseModel):
    query: str
    search_type: str  # 'profile', 'company', or 'cofounder'
    num_results: Optional[int] = 5
    profile_id: Optional[str] = None  # Required for cofounder search
    role_filter: Optional[str] = None  # 'founder' or 'investor'

@router.post("/")
async def search_profiles(query: SearchQuery):
    try:
        # Generate embedding for the search query
        query_embedding = get_embedding(query.query)
        if query_embedding is None:
            raise HTTPException(status_code=400, detail="Failed to generate query embedding")
        
        # Convert embedding to list if it's numpy array
        if hasattr(query_embedding, 'tolist'):
            query_embedding = query_embedding.tolist()
        
        print(f"Generated embedding type: {type(query_embedding)}")
        print(f"Generated embedding length: {len(query_embedding)}")
        
        # Perform vector similarity search based on search type
        if query.search_type == 'profile':
            try:
                # Prepare RPC parameters
                rpc_params = {
                    'query_embedding': query_embedding,
                    'match_count': query.num_results
                }
                
                # Add role filter if provided
                if query.role_filter:
                    rpc_params['role_filter'] = query.role_filter
                
                print(f"Calling RPC with params: {rpc_params}")
                
                # Use weighted similarity search for profiles with role filter
                rpc_response = supabase.rpc(
                    'match_profiles_weighted',
                    rpc_params
                ).execute()
                
                print(f"RPC Response: {rpc_response}")
                results = rpc_response.data
                
                if not results:
                    return {"results": []}
                
                # Format response with similarity explanations
                formatted_results = []
                for result in results[:3]:
                    formatted_result = {
                        'profile': {
                            'id': result['id'],
                            'name': result['name'],
                            'role': result['role'],
                            'education': result['education'],
                            'bio': result['bio'],
                            'ai_bio': result['ai_bio'],
                            'interests': result['interests'],
                            'image_url': result['image_url']
                        },
                        'similarity_score': result['combined_similarity'],
                        'match_explanation': generate_match_explanation(
                            query.query,
                            result
                        )
                    }
                    formatted_results.append(formatted_result)
                
                return {"results": formatted_results}
            except Exception as e:
                print(f"Error in profile search: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error in profile search: {str(e)}\nFull error: {repr(e)}"
                )
                
        elif query.search_type == 'company':
            try:
                # Prepare RPC parameters for company search
                rpc_params = {
                    'query_embedding': query_embedding,
                    'match_count': query.num_results
                }
                
                # Use company matching function
                rpc_response = supabase.rpc(
                    'match_companies_weighted',
                    rpc_params
                ).execute()
                
                results = rpc_response.data
                
                if not results:
                    return {"results": []}
                
                # Format company results
                formatted_results = []
                for result in results[:3]:
                    formatted_result = {
                        'company': {
                            'id': result['id'],
                            'name': result['name'],
                            'description': result['description'],
                            'industry': result['industry'],
                            'location': result['location'],
                            'website': result['website'],
                            'founded_year': result['founded_year'],
                            'image_url': result['image_url']
                        },
                        'similarity_score': result['combined_similarity'],
                        'match_explanation': generate_company_explanation(
                            query.query,
                            result
                        )
                    }
                    formatted_results.append(formatted_result)
                
                return {"results": formatted_results}
            except Exception as e:
                print(f"Error in company search: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error in company search: {str(e)}\nFull error: {repr(e)}"
                )
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
    
    except Exception as e:
        print(f"Error in search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in search: {str(e)}\nFull error: {repr(e)}"
        )

def generate_match_explanation(query: str, result: Dict) -> str:
    """Generate a human-readable explanation of why this profile matched"""
    explanation = f"This profile matches your search '{query}' based on "
    reasons = []
    
    if result['role']:
        reasons.append(f"their role as {result['role']}")
    if result['education']:
        reasons.append(f"their education background in {result['education']}")
    if result['bio']:
        reasons.append("their professional experience")
    if result.get('interests'):
        reasons.append(f"their interests in {', '.join(result['interests'][:3])}")
    
    if reasons:
        explanation += ", ".join(reasons[:-1])
        if len(reasons) > 1:
            explanation += f" and {reasons[-1]}"
        elif len(reasons) == 1:
            explanation += reasons[0]
    
    return explanation
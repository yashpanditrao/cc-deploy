from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from supabase import create_client
import uvicorn
import os
from dotenv import load_dotenv
from app.services.embeddings import update_single_profile_embeddings, update_single_profile_ai_bio, get_embedding

# Load environment variables
load_dotenv()
port = os.getenv("PORT")
# Initialize FastAPI app
app = FastAPI(title="Profile Matching API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://cc-deploy-pi.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

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

class CompanyProfileBase(BaseModel):
    name: str
    description: Optional[str]
    industry: Optional[str]
    website: Optional[str]
    founded_year: Optional[int]
    location: Optional[str]

class SearchQuery(BaseModel):
    query: str
    search_type: str  # 'profile', 'company', or 'cofounder'
    num_results: Optional[int] = 5
    profile_id: Optional[str] = None  # Required for cofounder search
    role_filter: Optional[str] = None  # 'founder' or 'investor'

@app.post("/profiles")
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

@app.post("/companies")
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

@app.post("/search")
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
                            'interests': result['interests']
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
                rpc_response = supabase.rpc(
                    'match_companies',
                    {
                        'query_embedding': query_embedding,
                        'match_count': query.num_results
                    }
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
                            'location': result['location']
                        },
                        'similarity_score': result['similarity'],
                        'match_explanation': f"This company matches your search based on its industry, description, and location."
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

def generate_cofounder_explanation(interests: List[str], role: str, interest_similarity: float) -> str:
    """Generate a human-readable explanation for co-founder matching"""
    explanation = f"This potential co-founder could be a great match! "
    
    # Add role-based explanation
    explanation += f"They are a {role}. "
    
    # Add interests-based explanation
    if interests:
        if interest_similarity > 0.8:
            explanation += f"You share many common interests, including {', '.join(interests[:3])}. "
        elif interest_similarity > 0.5:
            explanation += f"You have some interests in common, such as {', '.join(interests[:2])}. "
        else:
            explanation += f"They bring diverse interests including {', '.join(interests[:2])}. "
    
    # Add compatibility score explanation
    if interest_similarity > 0.8:
        explanation += "Your interests align very strongly!"
    elif interest_similarity > 0.6:
        explanation += "You have good interest alignment."
    else:
        explanation += "Your different interests could bring diverse perspectives."
    
    return explanation

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.put("/profiles/{profile_id}/embeddings")
async def update_profile_embeddings(profile_id: str):
    """Update embeddings for a specific profile"""
    try:
        embeddings = update_single_profile_embeddings(profile_id)
        return {
            "message": "Profile embeddings updated successfully",
            "data": embeddings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/profiles/{profile_id}/ai-bio")
async def update_profile_ai_bio(profile_id: str):
    """Update AI bio and its embedding for a specific profile"""
    try:
        return await update_single_profile_ai_bio(profile_id, supabase)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port_number = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port_number, reload=True)
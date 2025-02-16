import os
from dotenv import load_dotenv
import google.generativeai as genai
import numpy as np
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def normalize_embedding(embedding):
    """Normalize embedding vector using L2 normalization"""
    embedding_array = np.array(embedding)
    norm = np.linalg.norm(embedding_array)
    if norm == 0:
        return embedding_array.tolist()
    return (embedding_array / norm).tolist()

def get_embedding(text):
    """Get embedding for text using Gemini API"""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
            title="Embedding of text"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        return None

def generate_ai_bio(profile):
    """Generate AI bio from profile attributes"""
    prompt = f"""
    Create a comprehensive professional bio based on the following information:
    Name: {profile['name']}
    Role: {profile['role']}
    Current Bio: {profile['bio'] if profile['bio'] else 'Not provided'}
    Education: {profile['education'] if profile['education'] else 'Not provided'}
    Interests: {', '.join(profile['interests']) if profile['interests'] else 'Not provided'}
    LinkedIn: {profile.get('linkedin_url', 'Not provided')}
    
    Please write a concise but detailed professional biography that highlights their expertise, 
    background, and professional focus. The bio should be in third person and maintain a 
    professional tone.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating AI bio for {profile['name']}: {str(e)}")
        return None

def update_single_profile_embeddings(profile_id):
    """Update embeddings for a single profile"""
    try:
        response = supabase.table("personalprofile").select(
            "id, name, role, bio, interests, ai_bio, education, linkedin_url"
        ).eq("id", profile_id).execute()
        
        if not response.data:
            raise Exception(f"Profile with ID {profile_id} not found")
            
        profile = response.data[0]
        embeddings = {}
        
        # Generate role embedding
        if profile['role']:
            role_embedding = get_embedding(profile['role'])
            if role_embedding:
                embeddings['role_vector'] = normalize_embedding(role_embedding)
        
        # Generate bio embedding
        if profile['bio']:
            bio_embedding = get_embedding(profile['bio'])
            if bio_embedding:
                embeddings['bio_vector'] = normalize_embedding(bio_embedding)
        
        # Generate interests embedding
        if profile['interests']:
            interests_text = ' '.join(profile['interests'])
            interests_embedding = get_embedding(interests_text)
            if interests_embedding:
                embeddings['interests_vector'] = normalize_embedding(interests_embedding)
        
        # Generate education embedding
        if profile['education']:
            education_embedding = get_embedding(profile['education'])
            if education_embedding:
                embeddings['education_vector'] = normalize_embedding(education_embedding)
        
        # Update profile with new embeddings
        if embeddings:
            supabase.table("personalprofile").update(
                embeddings
            ).eq("id", profile_id).execute()
            
        return embeddings
            
    except Exception as e:
        print(f"Error updating embeddings for profile {profile_id}: {str(e)}")
        raise e

def update_single_profile_ai_bio(profile_id):
    """Update AI bio for a single profile"""
    try:
        response = supabase.table("personalprofile").select(
            "id, name, role, bio, interests, education, linkedin_url"
        ).eq("id", profile_id).execute()
        
        if not response.data:
            raise Exception(f"Profile with ID {profile_id} not found")
            
        profile = response.data[0]
        
        # Generate and update AI bio and its embedding
        ai_bio = generate_ai_bio(profile)
        if ai_bio:
            updates = {'ai_bio': ai_bio}
            ai_bio_embedding = get_embedding(ai_bio)
            if ai_bio_embedding:
                updates['ai_bio_vector'] = normalize_embedding(ai_bio_embedding)
            
            supabase.table("personalprofile").update(
                updates
            ).eq("id", profile_id).execute()
            
            return updates
        
        return None
            
    except Exception as e:
        print(f"Error updating AI bio for profile {profile_id}: {str(e)}")
        raise e

def update_profile_embeddings():
    """Fetch all profiles and update embeddings"""
    try:
        response = supabase.table("personalprofile").select(
            "id, name, role, bio, interests, ai_bio, education, linkedin_url"
        ).execute()
        
        profiles = response.data
        
        for profile in profiles:
            try:
                update_single_profile_embeddings(profile["id"])
                print(f"Updated embeddings for {profile['name']}")
            except Exception as e:
                print(f"Error updating profile {profile['id']}: {str(e)}")
                continue
        
        print("Completed profile embedding updates")
        
    except Exception as e:
        print(f"Error in update_profile_embeddings: {str(e)}")

def update_single_company_embeddings(company_id):
    """Update embeddings for a single company"""
    try:
        response = supabase.table("companyprofile").select(
            "id, name, description, industry, location"
        ).eq("id", company_id).execute()
        
        if not response.data:
            raise Exception(f"Company with ID {company_id} not found")
            
        company = response.data[0]
        embeddings = {}
        
        # Generate description embedding
        if company['description']:
            description_embedding = get_embedding(company['description'])
            if description_embedding:
                embeddings['description_vector'] = normalize_embedding(description_embedding)
        
        # Generate industry embedding
        if company['industry']:
            industry_embedding = get_embedding(company['industry'])
            if industry_embedding:
                embeddings['industry_vector'] = normalize_embedding(industry_embedding)
        
        # Generate location embedding
        if company['location']:
            location_embedding = get_embedding(company['location'])
            if location_embedding:
                embeddings['location_vector'] = normalize_embedding(location_embedding)
        
        # Update company with new embeddings
        if embeddings:
            supabase.table("companyprofile").update(
                embeddings
            ).eq("id", company_id).execute()
            
        return embeddings
            
    except Exception as e:
        print(f"Error updating embeddings for company {company_id}: {str(e)}")
        raise e

def update_company_embeddings():
    """Fetch all companies and update embeddings"""
    try:
        response = supabase.table("companyprofile").select(
            "id, name, description, industry, location"
        ).execute()
        
        companies = response.data
        print(f"Found {len(companies)} companies to update")
        
        for company in companies:
            try:
                embeddings = update_single_company_embeddings(company["id"])
                print(f"Updated embeddings for {company['name']}")
                print(f"Generated vectors: {list(embeddings.keys())}")
            except Exception as e:
                print(f"Error updating company {company['id']}: {str(e)}")
                continue
        
        print("Completed company embedding updates")
        
    except Exception as e:
        print(f"Error in update_company_embeddings: {str(e)}")
        raise e

if __name__ == "__main__":
    print("Starting embedding updates...")
    try:
        update_company_embeddings()
        print("Successfully updated company embeddings")
    except Exception as e:
        print(f"Error updating embeddings: {str(e)}")

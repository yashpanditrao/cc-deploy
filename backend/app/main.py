from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import profiles, companies, search
from supabase import create_client

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Initialize Supabase client
supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

# Include routers
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
app.include_router(companies.router, prefix="/companies", tags=["companies"])
app.include_router(search.router, prefix="/search", tags=["search"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 
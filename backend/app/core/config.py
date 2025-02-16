from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Profile Matching API"
    VERSION: str = "1.0.0"
    
    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://cc-deploy-pi.vercel.app",
        "https://*.onrender.com"
    ]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Server settings
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings() 
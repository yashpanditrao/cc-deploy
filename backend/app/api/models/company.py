from pydantic import BaseModel
from typing import Optional

class CompanyProfileBase(BaseModel):
    name: str
    description: Optional[str]
    industry: Optional[str]
    website: Optional[str]
    founded_year: Optional[int]
    location: Optional[str]
    image_url: Optional[str]

class CompanyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    industry: Optional[str]
    location: Optional[str]
    image_url: Optional[str]
    similarity_score: Optional[float]
    match_explanation: Optional[str] 
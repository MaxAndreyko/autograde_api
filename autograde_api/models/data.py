from typing import Dict, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Input data model for prediction"""

    data: Dict[str, str]


class PredictionResult(BaseModel):
    """Output data model for prediction result"""
    username: str
    task: str
    essay: str
    k1: int
    k2: int
    k3: int
    comments: Optional[str] = Field(default=None, description="Optional comment")
    
class EssaySubmission(BaseModel):
    id: int
    input_task: str
    input_essay: str
    score_content: int
    score_organization: int
    score_grammar: int
    comment: str
    submitted_at: str

class UserRegister(BaseModel):
    """User data model"""
    username: str
    password: str


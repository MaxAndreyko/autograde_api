from typing import Dict

from pydantic import BaseModel


class PredictionRequest(BaseModel):
    """Input data model for prediction"""

    data: Dict[str, str]


class PredictionResult(BaseModel):
    """Output data model for prediction result"""

    total: int
    k1_score: int
    k2_score: int
    k3_score: int
    comments: str


class UserRegister(BaseModel):
    """User data model"""

    username: str
    password: str
    prediction_request: str
    prediction_result: str

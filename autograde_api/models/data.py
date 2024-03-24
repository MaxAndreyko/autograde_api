from typing import AnyStr, Dict

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
    comments: AnyStr


class User(BaseModel):
    """User data model"""

    username: AnyStr
    email: AnyStr
    prediction_request: AnyStr
    prediction_result: AnyStr

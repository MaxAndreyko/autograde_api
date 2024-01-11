import yaml
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel

from utils import dict_to_df, form_send_request_body
from scorers.bert_rate import K1ScoreRegressor


with open("config.yaml") as cfg:
    cfg_dict = yaml.safe_load(cfg)

# Create instances of global classes
app = FastAPI() # FastAPI
k1_model = K1ScoreRegressor(**cfg_dict["bert_model"]) # K2-criterion (BERT) model

class PredictionRequest(BaseModel):
    """Input data model for prediction"""
    data: Dict

@app.post("/predict")
async def predict(request: PredictionRequest) -> Dict:
    """API POST predicting scores function

    Parameters
    ----------
    request : PredictionRequest
        Input raw data for prediction

    Returns
    -------
    dict
        Predicted scores dictionary
    """
    data = request.data
    df = dict_to_df(data)
    
    predictions = form_send_request_body(k1=k1_model.predict(df), k2=None, k3=None)
    
    return predictions
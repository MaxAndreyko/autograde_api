import yaml
from typing import Dict, AnyStr

from fastapi import FastAPI
from pydantic import BaseModel

from utils import dict_to_df, form_send_request_body
from scorers.bert_rate import K1ScoreRegressor
from load import s3_load_folder

# Read config yaml file
with open("config.yaml") as cfg:
    cfg_dict = yaml.safe_load(cfg)

# Load BERT model weights for K1-criterion prediction
s3_load_folder(cfg_dict["s3_data"]["bucket_name"], cfg_dict["s3_data"]["bert_model_path"], cfg_dict["s3_data"]["bert_model_path"])

# Create instances of global classes
app = FastAPI() # FastAPI
k1_model = K1ScoreRegressor(**cfg_dict["bert_model"]) # K1-criterion (BERT) model

class PredictionRequest(BaseModel):
    """Input data model for prediction"""
    data: Dict

@app.get('/', response_model=AnyStr)
def root():
    return 'Successfully connected!'

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
import yaml
from typing import Dict, AnyStr

from fastapi import FastAPI
from pydantic import BaseModel

from utils import dict_to_df
from scorers.k1_scorer import K1ScoreRegressor
from scorers.main_scorer import evaluate_text
from loggers.log_middleware import LogMiddleware
from transformers import pipeline
import nltk
nltk.download("punkt")

import logging

log = logging.getLogger(__name__)


# Read config yaml file
with open("config.yaml") as cfg:
    cfg_dict = yaml.safe_load(cfg)

with open(cfg_dict["k2_score"]["keywords_path"], encoding="utf-8") as f:
    KEYWORDS = f.read().split(",")

# Create instances of global classes
app = FastAPI(debug=True) # FastAPI
app.add_middleware(LogMiddleware)

k1_model = K1ScoreRegressor(**cfg_dict["bert_model"]) # K1-criterion (BERT) model
k3_model = pipeline(
    'text2text-generation',
    cfg_dict["flan_t5_model"]["model_dir"],
)

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
    
    predictions = evaluate_text(df, cfg_dict["k2_score"]["answer_col"], k1_model, k3_model, KEYWORDS)
    
    return predictions
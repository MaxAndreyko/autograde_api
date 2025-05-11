import redis as pyredis
import yaml
from celery import Celery
import json
from transformers import pipeline

from autograde_api.utils.formatter import dict_to_df
from autograde_api.scorers.k1_scorer import K1ScoreRegressor
from autograde_api.scorers.main_scorer import evaluate_text

# Read config yaml file
with open("config.yaml") as cfg:
    cfg_dict = yaml.safe_load(cfg)

with open(cfg_dict["k2_score"]["keywords_path"], encoding="utf-8") as f:
    KEYWORDS = f.read().split(",")

k1_model = K1ScoreRegressor(**cfg_dict["bert_model"])
k3_model = pipeline(
    "text2text-generation",
    cfg_dict["flan_t5_model"]["model_dir"],
)

celery = Celery(
    '"autograde_api.celery_worker"',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery.task
def predict_task(data: dict, cache_key: str):
    # Your actual prediction logic
    df = dict_to_df(data)
    predictions = evaluate_text(
        df, cfg_dict["k2_score"]["answer_col"], k1_model, k3_model, KEYWORDS
    )
    # Store result in Redis cache for 10 minutes (600 seconds)
    r = pyredis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.setex(cache_key, 600, json.dumps(predictions))
    return predictions





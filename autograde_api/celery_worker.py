import redis as pyredis
import yaml
from celery import Celery
import json
import torch
from transformers import BertTokenizer

from autograde_api.scorers.main_scorer import evaluate_text
from src.models.bert import MultiHeadBERT
from autograde_api.scorers.multi_scorer import MultiHeadRegressorInferer
from autograde_api.utils.creds_getter import get_redis_creds

# Read config yaml file
with open("config.yaml") as cfg:
    cfg_dict = yaml.safe_load(cfg)

BERT_CFG = cfg_dict["bert_model"]
redis_creds = get_redis_creds()
celery = Celery(
    "autograde_api.celery_worker",
    broker=f"redis://{redis_creds['redis_host']}:{redis_creds['redis_port']}/0",
    backend=f"redis://{redis_creds['redis_host']}:{redis_creds['redis_port']}/0"
)

bert = MultiHeadBERT(
    model_name=BERT_CFG["model_name"],
    freeze_bert=BERT_CFG["freeze_bert"],
    freeze_layers=BERT_CFG["freeze_layers"],
    dim_in=BERT_CFG["dim_in"],
    dim_out=BERT_CFG["dim_out"],
    p_dropout=BERT_CFG["p_dropout"],
    head_hidden_dim=BERT_CFG["head_hidden_dim"],
)

bert_tokenizer = BertTokenizer.from_pretrained(bert.model_name)

multi_scorer_inferer = MultiHeadRegressorInferer(
    bert,
    bert_tokenizer,
    max_target=2,
    min_target=0,
    scale_predictions=True,
    padding=BERT_CFG["padding"],
    truncation=BERT_CFG["truncation"],
    max_length=BERT_CFG["max_length"]
)
multi_scorer_inferer.load_weights(BERT_CFG["model_weights"])

multi_scorer = lambda x, y: multi_scorer_inferer.predict(x, y, post_process_func=torch.round)


@celery.task
def predict_task(data: dict, cache_key: str):
    predictions = evaluate_text(data["Text"], data["Question"], multi_scorer=multi_scorer)
    # Store result in Redis cache for 10 minutes (600 seconds)
    r = pyredis.Redis(host=redis_creds['redis_host'], port=redis_creds['redis_port'], db=0, decode_responses=True)
    r.setex(cache_key, 600, json.dumps(predictions))
    return predictions





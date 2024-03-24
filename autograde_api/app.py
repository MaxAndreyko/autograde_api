import logging
import sys
from typing import AnyStr, Dict

import aioredis
import nltk
import yaml
from fastapi import FastAPI, HTTPException, status
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from transformers import pipeline

from autograde_api.email.sender import send_email
from autograde_api.models.data import PredictionRequest, User
from autograde_api.scorers.k1_scorer import K1ScoreRegressor
from autograde_api.scorers.main_scorer import evaluate_text
from autograde_api.utils.creds_getter import get_redis_creds, get_smtp_credentials
from autograde_api.utils.formatter import (
    dict_to_df,
    format_prediction_request,
    format_prediction_result,
)
from loggers.log_middleware import LogMiddleware

log = logging.getLogger(__name__)

nltk.download("punkt")

# Read config yaml file
with open("config.yaml") as cfg:
    cfg_dict = yaml.safe_load(cfg)

with open(cfg_dict["k2_score"]["keywords_path"], encoding="utf-8") as f:
    KEYWORDS = f.read().split(",")

# Create instances of global classes
app = FastAPI(debug=True)  # FastAPI
app.add_middleware(LogMiddleware)

# K1-criterion (BERT) model
k1_model = K1ScoreRegressor(**cfg_dict["bert_model"])
k3_model = pipeline(
    "text2text-generation",
    cfg_dict["flan_t5_model"]["model_dir"],
)


# Redis global client
redis: aioredis.Redis = None


@app.on_event("startup")
async def startup():
    global redis
    redis_creds = get_redis_creds()
    if redis_creds is not None:
        redis = await aioredis.from_url(
            f"redis://{redis_creds['redis_host']}:{redis_creds['redis_port']}",
            encoding="utf8",
            decode_responses=True,
        )
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    else:
        log.error("Service stopped")
        sys.exit(1)


@app.delete("/cache/clear")
async def delete_cache_key(username: str):
    """Deletes cache from Redis by username (key)

    Args:
        username (str): Username as a key in Redis

    Raises:
        HTTPException: Cache deletion status
    """
    await redis.delete(username)
    raise HTTPException(status_code=status.HTTP_200_OK, detail=f"Кэш {username} очищен")


@app.post("/login")
async def login(user_data: User):
    """Loads new user to Redis

    Args:
        user_data (User): User data

    Raises:
        HTTPException: User adding status
    """
    user_data = user_data.model_dump()
    username = user_data.pop("username")
    await redis.hset(username, mapping=user_data)
    raise HTTPException(
        status_code=status.HTTP_200_OK,
        detail=f"Пользователь с ником {username} и почтой {user_data['email']} добавлен",
    )


@app.post("/send_email")
async def prediction_send_email(username: str):
    """Sends email with predictions results to user

    Args:
        username (str): Username to send mail to

    Raises:
        HTTPException: Success email send status
        HTTPException: No connection to SMTP server status
        HTTPException: User not found status
    """

    user_email = await redis.hget(username, "email")
    prediction_request = await redis.hget(username, "prediction_request")
    prediction_result = await redis.hget(username, "prediction_result")
    if user_email:
        smtp_creds = get_smtp_credentials()
        if smtp_creds is not None:
            await send_email(
                subject="Your Prediction Result",
                recipient=user_email,
                body=f"Привет, {username}, твой результат:<br><br>{prediction_result}.<br><br><br>Твоя работа:<br><br> {prediction_request}",
                **smtp_creds,
            )
            raise HTTPException(
                status_code=status.HTTP_200_OK, detail="Результат отправлен на почту"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Нет подключения к SMTP-серверу",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )


@app.get("/ping", response_model=AnyStr)
@cache(expire=60)
async def root():
    """Check service functionality"""
    raise HTTPException(status_code=status.HTTP_200_OK, detail="Сервис доступен")


@app.post("/predict/")
@cache(expire=600)
async def predict(username: str, prediction_request: PredictionRequest) -> Dict:
    """API POST predicting scores function

    Parameters
    ----------
    prediction_request : Dict
        Input raw data for prediction

    Returns
    -------
    dict
        Predicted scores dictionary
    """
    user_exists = await redis.exists(username)
    if user_exists == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    data = prediction_request.data
    await redis.hset(username, "prediction_request", format_prediction_request(data))
    df = dict_to_df(data)
    predictions = evaluate_text(
        df, cfg_dict["k2_score"]["answer_col"], k1_model, k3_model, KEYWORDS
    )
    await redis.hset(
        username, "prediction_result", format_prediction_result(predictions)
    )
    return predictions

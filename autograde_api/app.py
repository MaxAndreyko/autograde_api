import logging
import sys
from typing import AnyStr, Dict

import aioredis
import nltk

import json
from fastapi import FastAPI, HTTPException, status
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache


from autograde_api.email_sender.sender import send_email
from autograde_api.models.data import PredictionRequest, User

from autograde_api.utils.creds_getter import get_redis_creds, get_smtp_credentials
from loggers.log_middleware import LogMiddleware
from autograde_api.celery_worker import predict_task
from autograde_api.caching.utils import make_cache_key
from autograde_api.caching.queue import get_task_position

log = logging.getLogger(__name__)

nltk.download("punkt")

# Create instances of global classes
app = FastAPI(debug=True)  # FastAPI
app.add_middleware(LogMiddleware)

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
    await redis.hmset(username, mapping=user_data)
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

@app.post("/predict")
async def predict(username: str, prediction_request: PredictionRequest) -> Dict:
    user_exists = await redis.exists(username)
    if user_exists == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

    data = prediction_request.data
    cache_key = make_cache_key(username, data)

    # Check cache first
    cached = await redis.get(cache_key)
    if cached:
        response = json.loads(cached)
        response["status"] = "done"
        return response

    # Not cached: enqueue Celery task
    task = predict_task.delay(data, cache_key)
    return {"task_id": task.id, "status": "processing"}

@app.get("/predict/result/{task_id}")
async def get_prediction_result(task_id: str) -> Dict:
    task_result = predict_task.AsyncResult(task_id)
    if task_result.ready():
        result = task_result.get()
        result["status"] = "done"
        return result
    else:
        return {"status": "processing"}

@app.get("/predict/position/{task_id}")
async def get_task_position_endpoint(task_id: str):
    position = await get_task_position(task_id, redis)
    
    if position == -1:
        task_result = predict_task.AsyncResult(task_id)
        if task_result.ready():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Task already completed"
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found in queue"
        )

    return {
        "task_id": task_id,
        "position": position
    }
import logging
import sys
from typing import AnyStr, Dict, List

import aioredis
import nltk

import json
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from autograde_api.email_sender.sender import send_email
from autograde_api.models.data import PredictionRequest, UserRegister, PredictionResult, EssaySubmission
from autograde_api.database.utils import hash_password
from autograde_api.database.models import User
from autograde_api.utils.creds_getter import get_redis_creds, get_smtp_credentials
from loggers.log_middleware import LogMiddleware
from autograde_api.celery_worker import predict_task
from autograde_api.caching.utils import make_cache_key
from autograde_api.caching.queue import get_task_position
from autograde_api.database.connection import get_db
from autograde_api.database.query import add_user, save_essay_submission, get_user_id_by_username, get_last_n_essay_submissions

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

@app.post("/register")
async def register_user(user: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        # User exists: check password
        if existing_user.password_hash == hash_password(user.password):
            return {
                "status": "success",
                "detail": "User already exists and password matches.",
                }
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists and password does not match."
            )
    # User does not exist: create new user
    await add_user(user.username, user.password)
    return {
        "status": "success",
        "detail": "User registered successfully.",
    }


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

@app.post("/essay/submit")
async def submit_essay(prediction_result: PredictionResult):
    user_id = await get_user_id_by_username(prediction_result.username)
    try:
        result = await save_essay_submission(
            user_id=user_id,
            input_task=prediction_result.task,
            input_essay=prediction_result.essay,
            score_content=prediction_result.k1,
            score_organization=prediction_result.k2,
            score_grammar=prediction_result.k3,
            comment=prediction_result.comments,
        )
        return {"message": "Essay submission saved successfully.", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save essay submission: {e}")
    
@app.get("/submissions/last/{username}/{n}", response_model=List[EssaySubmission])
async def get_last_submissions(username: str, n: int):
    try:
        user_id = await get_user_id_by_username(username)
        raw_submissions = await get_last_n_essay_submissions(user_id, n)
        submissions = []
        for rsub in raw_submissions:
            sub = EssaySubmission(
                id = rsub.id,
                input_task = rsub.input_task,
                input_essay = rsub.input_essay,
                score_content = rsub.score_content,
                score_organization = rsub.score_organization,
                score_grammar = rsub.score_grammar,
                comment = rsub.comment if rsub.comment is not None else "",
                submitted_at = rsub.submitted_at.strftime("%d-%m-%Y %H:%M:%S")
            )
            submissions.append(sub)
        return submissions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {e}")

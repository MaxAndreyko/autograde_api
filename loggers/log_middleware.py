import sys
import traceback
from time import time

from asgi_correlation_id import correlation_id
from starlette.middleware.base import BaseHTTPMiddleware

from loggers.logger import logger


class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            start = time()
            response = await call_next(request)
            process_time = time() - start
            logger.info(
                "Incoming request",
                extra={
                    "process_time": process_time,
                    "req": {
                        "method": request.method,
                        "url": str(request.url),

                    },
                    "res": {"status_code": response.status_code, },
                },
            )
            return response
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(
                "Internal server error",
                extra={
                        "request_id": correlation_id.get(),
                    "req": {
                        "method": request.method,
                        "url": str(request.url),
                    },
                    "res": {"status_code": 500, "err": "".join(traceback.format_exception(
                        exc_type,
                        exc_value,
                        exc_traceback))},
                },
            )
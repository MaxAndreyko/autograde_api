import json
import logging
from logging import Formatter

from asgi_correlation_id import correlation_id


class JsonFormatter(Formatter):
    def __init__(self):
        super(JsonFormatter, self).__init__()

    def format(self, record):
        json_record = {}
        json_record["message"] = record.getMessage()
        json_record["request_id"] = correlation_id.get()
        json_record["level"] = str.replace(str.replace(record.levelname, "WARNING", "WARN"), "CRITICAL", "FATAL")
        if "req" in record.__dict__:
            json_record["req"] = record.__dict__["req"]

        if "res" in record.__dict__:
            json_record["res"] = record.__dict__["res"]

        if record.levelno == logging.ERROR and record.exc_info:
            json_record["err"] = self.formatException(record.exc_info)
        return json.dumps(json_record)


logger = logging.root
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)

logging.getLogger("uvicorn.access").disabled = True
logging.getLogger("uvicorn.asgi").disabled = True
logging.getLogger("uvicorn.error").disabled = True
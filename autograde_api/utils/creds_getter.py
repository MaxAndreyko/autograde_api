import logging
from os import environ
from typing import Dict

from dotenv import find_dotenv, load_dotenv

from autograde_api.utils.helpers import get_none_keys

load_dotenv(find_dotenv())


def get_smtp_credentials() -> Dict:
    """Gets SMTP credentials from environment variables

    Returns:
        Dict: Dictionary with SMTP credentials
    """
    logger = logging.getLogger(__name__)
    smtp_creds = {
        "smtp_server": environ.get("SMTP_SERVER"),
        "smtp_port": environ.get("SMTP_PORT"),
        "smtp_username": environ.get("SMTP_USERNAME"),
        "smtp_password": environ.get("SMTP_PASSWORD"),
    }
    if None in smtp_creds.values():
        none_keys = get_none_keys(smtp_creds)
        logger.error(f"SMTP credentials are not set: {none_keys}")
        return None
    else:
        return smtp_creds


def get_redis_creds() -> Dict:
    """Gets Redis credentials from environment variables

    Returns:
        Dict: Dictionary with Redis credentials
    """
    logger = logging.getLogger(__name__)
    reids_creds = {
        "redis_host": environ.get("REDIS_HOST"),
        "redis_port": environ.get("REDIS_PORT"),
    }
    if None in reids_creds.values():
        none_keys = get_none_keys(reids_creds)
        logger.error(f"Redis credentials are not set: {none_keys}")
        return None
    else:
        return reids_creds

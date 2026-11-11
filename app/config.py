from pydantic import AnyHttpUrl, BaseSettings
from fastapi.logger import logger as fast_api_logger
from typing import List
import secrets
import logging
import os

logger = logging.getLogger("gunicorn.error")
fast_api_logger.handlers = logger.handlers


def _env_flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings(BaseSettings):
    PROJECT_NAME: str = "Uptime-Kuma-API"
    # Shown in /openapi.json and /docs, so a deployment can be matched to a release tag.
    APP_VERSION: str = os.environ.get("APP_VERSION", "dev")
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Comma separated list of allowed CORS origins, "*" allows every origin.
    CORS_ALLOW_ORIGINS: str = os.environ.get("CORS_ALLOW_ORIGINS", "*")
    # Redirect every request that did not arrive over https (X-Forwarded-Proto aware).
    ENFORCE_HTTPS: bool = _env_flag("ENFORCE_HTTPS", True)

    ACCESS_TOKEN_EXPIRE: int = os.environ.get(
        "ACCESS_TOKEN_EXPIRATION", 60 * 24 * 8
    )  # 8 days
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))

    KUMA_SERVER: str = os.environ.get("KUMA_SERVER")
    KUMA_USERNAME: str = os.environ.get("KUMA_USERNAME")
    KUMA_PASSWORD: str = os.environ.get("KUMA_PASSWORD")
    # Seconds to wait for the Uptime Kuma connection and for each of its answers.
    KUMA_TIMEOUT: float = float(os.environ.get("KUMA_TIMEOUT", 10))

    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD")

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()

from pydantic import AnyHttpUrl, BaseSettings, validator
from fastapi.logger import logger as fast_api_logger
from typing import List
import secrets
import logging
import os

logger = logging.getLogger("gunicorn.error")
fast_api_logger.handlers = logger.handlers


class Settings(BaseSettings):
    PROJECT_NAME: str = "Uptime-Kuma-API"
    # Shown in /openapi.json and /docs, so a deployment can be matched to a release tag.
    APP_VERSION: str = "dev"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Comma separated list of allowed CORS origins, "*" allows every origin.
    CORS_ALLOW_ORIGINS: str = "*"
    # Redirect every request that did not arrive over https (X-Forwarded-Proto aware).
    ENFORCE_HTTPS: bool = True

    ACCESS_TOKEN_EXPIRE: int = os.environ.get(
        "ACCESS_TOKEN_EXPIRATION", 60 * 24 * 8
    )  # 8 days
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)

    KUMA_SERVER: str = os.environ.get("KUMA_SERVER")
    KUMA_USERNAME: str = os.environ.get("KUMA_USERNAME")
    KUMA_PASSWORD: str = os.environ.get("KUMA_PASSWORD")
    # Seconds to wait for the Uptime Kuma connection and for each of its answers.
    KUMA_TIMEOUT: float = 10

    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD")

    class Config:
        case_sensitive = True
        env_file = ".env"

    # BaseSettings takes an empty env value as is; treat it as unset.
    @validator("SECRET_KEY", pre=True)
    def _secret_key_not_empty(cls, value):
        if value is None or not str(value).strip():
            return secrets.token_urlsafe(32)
        return value

    @validator("APP_VERSION", pre=True)
    def _app_version_not_empty(cls, value):
        if value is None or not str(value).strip():
            return "dev"
        return value


settings = Settings()

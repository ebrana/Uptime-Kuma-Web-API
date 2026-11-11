# authentication.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from uptime_kuma_api import UptimeKumaApi, UptimeKumaException
from typing import Optional
import jwt
from pydantic import ValidationError

from utils.security import verify_password
from schemas.jwt import JWTData
from models.user import UserCreate, UserResponse
from config import settings, logger as logging
from utils import security

oauth2_token = OAuth2PasswordBearer(tokenUrl="/login/access-token/")


async def get_current_user(token: str = Depends(oauth2_token)):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = JWTData(**payload)

    except (jwt.exceptions.InvalidSignatureError, ValidationError) as e:
        logging.info(e)
        raise HTTPException(status_code=403, detail="invalid credentials")

    except jwt.exceptions.ExpiredSignatureError as e:
        logging.info(e)
        raise HTTPException(status_code=403, detail="Token expired !!")
    api = None
    try:
        api = UptimeKumaApi(settings.KUMA_SERVER, timeout=settings.KUMA_TIMEOUT)
        api.login_by_token(token_data.sub)
    except UptimeKumaException as e:
        logging.fatal(e)
        if api is not None:
            api.disconnect()
        raise HTTPException(400, {"error": str(e)})
    except Exception:
        if api is not None:
            api.disconnect()
        raise

    # One Socket.io connection per request: close it when the request is done,
    # otherwise every call leaves an open connection to Uptime Kuma behind.
    try:
        yield {"token": token_data.sub, "api": api}
    finally:
        api.disconnect()


def authenticate(user: UserCreate, password: str) -> Optional[UserResponse]:
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None
    return user

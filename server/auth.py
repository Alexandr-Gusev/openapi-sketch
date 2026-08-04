import time
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Response
from config import settings

USERS = {
    "admin": "12345",
}


def create_token(sub: str, ttl_s: int) -> str:
    return jwt.encode(
        {
            "sub": sub,
            "exp": int(time.time()) + ttl_s,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def get_sub_from_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        if not sub:
            return None
        return sub
    except (PyJWTError, ValueError, TypeError):
        return None


def authenticate_user(user: str, password: str) -> bool:
    return USERS.get(user) == password


def set_auth_cookies(response: Response, sub: str) -> None:
    response.set_cookie(
        key="accessToken",
        value=create_token(sub, settings.jwt_access_ttl_s),
        max_age=settings.jwt_access_ttl_s,
        httponly=True,
        samesite="lax",
        path=settings.api_prefix,
    )
    response.set_cookie(
        key="refreshToken",
        value=create_token(sub, settings.jwt_refresh_ttl_s),
        max_age=settings.jwt_refresh_ttl_s,
        httponly=True,
        samesite="lax",
        path=f"{settings.api_prefix}/refreshedSessions",
    )

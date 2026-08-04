from typing import Annotated, Optional

from fastapi import Depends, Security, status
from fastapi.security import APIKeyCookie

from auth import get_sub_from_token
from errors import ApiError

access_cookie = APIKeyCookie(
    name="accessToken",
    scheme_name="CookieAccessToken",
    auto_error=False,
)
refresh_cookie = APIKeyCookie(
    name="refreshToken",
    scheme_name="CookieRefreshToken",
    auto_error=False,
)


def _sub_from_token(token: Optional[str], missing_detail: str) -> str:
    if not token:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            missing_detail,
        )
    sub = get_sub_from_token(token)
    if not sub:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHORIZED",
            "Invalid token",
        )
    return sub


async def sub_from_access_cookie(
    access_token: Annotated[Optional[str], Security(access_cookie)] = None,
) -> str:
    return _sub_from_token(access_token, "Missing access token")


async def sub_from_refresh_cookie(
    refresh_token: Annotated[Optional[str], Security(refresh_cookie)] = None,
) -> str:
    return _sub_from_token(refresh_token, "Missing refresh token")


SubFromAccessCookie = Annotated[str, Depends(sub_from_access_cookie)]
SubFromRefreshCookie = Annotated[str, Depends(sub_from_refresh_cookie)]

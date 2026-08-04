from typing import List, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from generated.models import Detail, Error


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[Detail]] = None,
    ):
        self.status_code = status_code
        self.body = Error(code=code, message=message, details=details)


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.body.model_dump(exclude_none=True),
    )

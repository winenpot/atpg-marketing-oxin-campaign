"""One error shape for every new endpoint, so the frontend switches on codes.

Response body::

    {"error": {"code": "CODE_MISTYPED", "message": "..."}}

``code`` is stable and documented in ``docs/API_CONTRACT.md``; ``message``
is English developer text. User-facing (Persian) copy belongs to the
frontend, keyed by ``code``.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(examples=["CODE_MISTYPED"])
    message: str = Field(examples=["One character looks mistyped; check the code."])


class ErrorResponse(BaseModel):
    """The shape of every error body; see docs/API_CONTRACT.md#errors.

    ``responses={...}`` on a route should reference this model so /docs and
    the generated OpenAPI schema show the real envelope, not FastAPI's
    default ``{"detail": "..."}``.
    """

    error: ErrorDetail


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retry_after_seconds = retry_after_seconds


async def api_error_handler(_: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, ApiError):  # pragma: no cover - registered for ApiError
        raise error
    headers = (
        {"Retry-After": str(error.retry_after_seconds)}
        if error.retry_after_seconds is not None
        else None
    )
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
        headers=headers,
    )


async def unhandled_error_handler(_: Request, __: Exception) -> JSONResponse:
    """Last resort: same envelope, no internals. The exception is still logged."""
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "internal error"}},
    )

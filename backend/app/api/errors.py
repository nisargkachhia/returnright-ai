"""Consistent HTTP errors for domain failures."""

from fastapi import HTTPException

from app.services.errors import DomainError

_STATUS = {
    "not_found": 404,
    "validation_error": 400,
    "conflict": 409,
    "confirmation_required": 400,
}


def http_error(exc: DomainError) -> HTTPException:
    return HTTPException(
        status_code=_STATUS.get(exc.code, 400),
        detail={"error": exc.code, "code": exc.code, "detail": exc.message},
    )

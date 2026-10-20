"""Domain exceptions mapped to HTTP responses in app.main."""

from __future__ import annotations


class DomainError(Exception):
    status_code = 400
    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class SlotUnavailableError(ConflictError):
    code = "slot_unavailable"


class StaleVersionError(ConflictError):
    code = "stale_version"


class PolicyViolationError(DomainError):
    status_code = 422
    code = "policy_violation"


class ValidationError(DomainError):
    status_code = 422
    code = "validation_error"

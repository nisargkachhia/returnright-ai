"""Domain errors mapped to API/MCP responses."""


class DomainError(Exception):
    def __init__(self, message: str, *, code: str = "domain_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(DomainError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found")


class ValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class ConflictError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="conflict")


class ConfirmationRequiredError(DomainError):
    def __init__(self, message: str = "Explicit confirmation required") -> None:
        super().__init__(message, code="confirmation_required")

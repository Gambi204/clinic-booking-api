class DomainError(Exception):
    """Base class for predictable business-domain failures."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AppointmentValidationError(DomainError):
    """An appointment request violates a scheduling rule."""


class ResourceNotFoundError(DomainError):
    """A required domain resource does not exist."""


class AppointmentConflictError(DomainError):
    """An appointment operation conflicts with existing state."""
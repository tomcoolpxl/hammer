"""Custom exception hierarchy for HAMMER.

Provides structured exceptions with actionable context for users.
"""


class HammerError(Exception):
    """Base exception for all HAMMER errors."""
    pass


class HammerConfigError(HammerError):
    """Configuration or spec-related errors."""
    pass


class HammerValidationError(HammerConfigError):
    """Spec validation errors with field-level detail."""

    def __init__(self, message: str, field: str | None = None, suggestion: str | None = None):
        self.field = field
        self.suggestion = suggestion
        parts = [message]
        if field:
            parts.append(f"Field: {field}")
        if suggestion:
            parts.append(f"Suggestion: {suggestion}")
        super().__init__("\n".join(parts))


class HammerPathError(HammerConfigError):
    """Path traversal or invalid path errors."""
    pass


class HammerExecutionError(HammerError):
    """Runtime execution errors."""
    pass


class HammerTimeoutError(HammerExecutionError):
    """Timeout during execution with partial output."""

    def __init__(self, message: str, partial_output: str = ""):
        self.partial_output = partial_output
        super().__init__(message)


class HammerPrerequisiteError(HammerError):
    """Missing prerequisite tools or dependencies."""
    pass

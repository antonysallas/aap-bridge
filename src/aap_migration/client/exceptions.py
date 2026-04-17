"""Custom exceptions for AAP Bridge clients.

This module defines exception classes for handling various error conditions
that can occur during API interactions with AAP and Vault.
"""


class AAPMigrationError(Exception):
    """Base exception for all AAP migration tool errors."""

    pass


class APIError(AAPMigrationError):
    """Base class for API-related errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response: API response body
        """
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message with status code and response."""
        msg = self.message
        if self.status_code:
            msg = f"[{self.status_code}] {msg}"
        if self.response:
            msg = f"{msg}: {self.response}"
        return msg


class AuthenticationError(APIError):
    """Raised when authentication fails (401 Unauthorized)."""

    pass


class AuthorizationError(APIError):
    """Raised when authorization fails (403 Forbidden)."""

    pass


class NotFoundError(APIError):
    """Raised when a resource is not found (404 Not Found)."""

    pass


class ConflictError(APIError):
    """Raised when a resource conflict occurs (409 Conflict).

    This typically indicates the resource already exists and is used
    for idempotency checks.
    """

    pass


class ResourceInUseError(ConflictError):
    """Raised when a resource is being used by running jobs (409 Conflict).

    This error occurs when attempting to delete a resource (like a project or inventory)
    that has active or canceling jobs. The resource cannot be deleted until the jobs
    complete.

    Attributes:
        active_jobs: List of job dicts blocking the resource (from API response)
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict | None = None,
        active_jobs: list[dict] | None = None,
    ):
        """Initialize resource in use error.

        Args:
            message: Error message
            status_code: HTTP status code (typically 409)
            response: API response body
            active_jobs: List of jobs blocking deletion (e.g., [{"id": 123, "type": "project_update", "status": "canceling"}])
        """
        super().__init__(message, status_code, response)
        self.active_jobs = active_jobs or []


class PendingDeletionError(ConflictError):
    """Raised when a resource is already pending deletion (409 Conflict).

    This is an idempotent success case - the resource is already being deleted,
    so the desired end state will be achieved. This should be treated as a skip,
    not an error.
    """

    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded (429 Too Many Requests)."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict | None = None,
        retry_after: int | None = None,
    ):
        """Initialize rate limit error.

        Args:
            message: Error message
            status_code: HTTP status code
            response: API response body
            retry_after: Seconds to wait before retrying (from Retry-After header)
        """
        super().__init__(message, status_code, response)
        self.retry_after = retry_after


class ServerError(APIError):
    """Raised when server returns 5xx error."""

    pass


class NetworkError(AAPMigrationError):
    """Raised when network-related errors occur (timeouts, connection failures)."""

    pass


class ValidationError(AAPMigrationError):
    """Raised when data validation fails."""

    pass


class StateError(AAPMigrationError):
    """Raised when state management errors occur."""

    pass


class CheckpointError(StateError):
    """Raised when checkpoint operations fail."""

    pass


class VaultError(AAPMigrationError):
    """Base class for Vault-related errors."""

    pass


class VaultAuthenticationError(VaultError):
    """Raised when Vault authentication fails."""

    pass


class VaultPermissionError(VaultError):
    """Raised when Vault access is denied."""

    pass


class BulkOperationError(APIError):
    """Raised when bulk operations fail."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict | None = None,
        failed_items: list | None = None,
    ):
        """Initialize bulk operation error.

        Args:
            message: Error message
            status_code: HTTP status code
            response: API response body
            failed_items: List of items that failed
        """
        super().__init__(message, status_code, response)
        self.failed_items = failed_items or []


class ConfigurationError(AAPMigrationError):
    """Raised when configuration is invalid or missing."""

    pass


class MigrationError(AAPMigrationError):
    """Raised when migration operations fail."""

    pass


class TransformationError(MigrationError):
    """Raised when data transformation fails."""

    pass


class DependencyError(MigrationError):
    """Raised when resource dependencies cannot be resolved."""

    pass

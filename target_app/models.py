"""Pydantic schemas and models for the synthetic target application.

Defines API request/response contracts, authorization models, and audit records.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthDecision(str, Enum):
    """Authorization evaluation decision."""
    ALLOW = "ALLOW"
    DENY = "DENY"


class AuditOutcome(str, Enum):
    """Execution outcome of a requested operation."""
    SUCCESS = "SUCCESS"
    DENIED_UNAUTHENTICATED = "DENIED_UNAUTHENTICATED"
    DENIED_UNAUTHORIZED = "DENIED_UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"


class AuditAction(str, Enum):
    """Action category recorded by the audit logger."""
    RECORD_READ = "RECORD_READ"
    RECORD_UPDATE = "RECORD_UPDATE"
    HEALTH_CHECK = "HEALTH_CHECK"


class AuditEvent(BaseModel):
    """Structured audit record persisted to the audit log."""
    event_id: str = Field(description="Unique event UUID")
    timestamp: str = Field(description="ISO 8601 UTC timestamp")
    request_id: str = Field(description="Correlation/Request ID")
    principal_id: Optional[str] = Field(default=None, description="Authenticated principal ID")
    action: str = Field(description="Operation action name")
    resource_id: Optional[str] = Field(default=None, description="Target resource ID")
    resource_owner: Optional[str] = Field(default=None, description="Actual resource owner ID")
    auth_decision: AuthDecision = Field(description="Authorization decision (ALLOW or DENY)")
    outcome: AuditOutcome = Field(description="Execution outcome")
    error_detail: Optional[str] = Field(default=None, description="Sanitized diagnostic error description")

    model_config = ConfigDict(frozen=True)


class RecordResponse(BaseModel):
    """Public representation of a private tenant record."""
    record_id: str
    owner_id: str
    title: str
    content: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class RecordUpdateRequest(BaseModel):
    """Request payload for updating an existing record.

    Ownership (`owner_id`) cannot be modified through this endpoint.
    Extra fields are strictly forbidden.
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_non_empty(self) -> "RecordUpdateRequest":
        """Reject empty update requests where neither title nor content is supplied."""
        if self.title is None and self.content is None:
            raise ValueError("Empty update request: at least one field ('title' or 'content') must be provided.")
        return self


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str


class ErrorResponse(BaseModel):
    """Standardized error response preventing leakage of internal audit logs."""
    detail: str


"""Abstract persistence store interface.

Decouples the service and analytical layers from underlying storage technologies.
Allows swapping the file-based JSON store for a relational database (PostgreSQL)
without modifying any application or business logic.
"""

from abc import ABC, abstractmethod

from app.models.audit import Audit
from app.models.observation import ResponseObservation
from app.models.report import AuditReport
from app.models.response import RawLLMResponse


class AuditStore(ABC):
    """Abstract Base Class defining repository operations for audit data."""

    @abstractmethod
    def save_audit(self, audit: Audit) -> None:
        """Persist or update an Audit definition."""
        raise NotImplementedError

    @abstractmethod
    def get_audit(self, audit_id: str) -> Audit | None:
        """Retrieve an Audit definition by ID, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def list_audits(self) -> list[Audit]:
        """List all saved Audit definitions."""
        raise NotImplementedError

    @abstractmethod
    def save_raw_response(self, response: RawLLMResponse) -> None:
        """Persist an immutable raw provider response."""
        raise NotImplementedError

    @abstractmethod
    def get_raw_responses(self, audit_id: str) -> list[RawLLMResponse]:
        """Retrieve all raw responses collected for an audit."""
        raise NotImplementedError

    @abstractmethod
    def save_observations(
        self, audit_id: str, observations: list[ResponseObservation]
    ) -> None:
        """Persist normalized analytical observations for an audit."""
        raise NotImplementedError

    @abstractmethod
    def get_observations(self, audit_id: str) -> list[ResponseObservation]:
        """Retrieve normalized analytical observations for an audit."""
        raise NotImplementedError

    @abstractmethod
    def save_report(self, report: AuditReport) -> None:
        """Persist a generated audit report."""
        raise NotImplementedError

    @abstractmethod
    def get_report(self, audit_id: str) -> AuditReport | None:
        """Retrieve the latest report for an audit, or None if not yet generated."""
        raise NotImplementedError

"""Audit orchestrator service.

Central coordinator of the entire audit lifecycle:
1. Create and persist audit configurations
2. Execute concurrent queries across LLM providers
3. Save raw immutable responses
4. Run analytical pipeline (mentions, contexts, competitors, citations)
5. Save normalized observations
6. Compute metrics, detect gaps, rank observations, and compile report
7. Persist final report and update audit status
"""

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from app.core.exceptions import (
    AuditNotFoundError,
    ReportUnavailableError,
)
from app.models.audit import Audit, AuditStatus
from app.models.observation import ResponseObservation
from app.models.report import AuditReport, ClientSummary
from app.models.response import RawLLMResponse
from app.providers.base import LLMProvider
from app.services.analysis_service import AnalysisService
from app.services.query_service import QueryService
from app.services.report_service import ReportService
from app.storage.audit_store import AuditStore

logger = logging.getLogger(__name__)


class AuditService:
    """Master service orchestrating end-to-end brand visibility audits."""

    def __init__(
        self,
        store: AuditStore,
        query_service: QueryService,
        analysis_service: AnalysisService,
        report_service: ReportService,
    ) -> None:
        self.store = store
        self.query_service = query_service
        self.analysis_service = analysis_service
        self.report_service = report_service

    def create_audit(self, audit: Audit) -> Audit:
        """Validate and persist a newly defined audit."""
        audit.status = AuditStatus.CREATED
        audit.created_at = datetime.now(UTC)
        audit.updated_at = datetime.now(UTC)
        self.store.save_audit(audit)
        logger.info(f"Created audit '{audit.audit_id}' for brand '{audit.brand}'")
        return audit

    def get_audit(self, audit_id: str) -> Audit:
        """Retrieve audit definition or raise AuditNotFoundError."""
        audit = self.store.get_audit(audit_id)
        if not audit:
            raise AuditNotFoundError(f"Audit with ID '{audit_id}' not found.")
        return audit

    def list_audits(self) -> list[Audit]:
        """List all saved audits."""
        return self.store.list_audits()

    async def run_audit(
        self,
        audit_id: str,
        provider_instances: Sequence[LLMProvider] | None = None,
    ) -> tuple[AuditReport, list[RawLLMResponse], list[ResponseObservation]]:
        """Execute complete audit workflow end-to-end.

        Args:
            audit_id: Identifier of audit to execute.
            provider_instances: Optional injected LLM provider adapters for mock testing.

        Returns:
            Tuple of (AuditReport, list[RawLLMResponse], list[ResponseObservation]).
        """
        audit = self.get_audit(audit_id)
        run_id = f"run_{uuid.uuid4().hex[:8]}"

        audit.status = AuditStatus.RUNNING
        audit.updated_at = datetime.now(UTC)
        self.store.save_audit(audit)

        logger.info(
            f"Starting execution of audit '{audit_id}' (run_id: {run_id}) "
            f"with {len(audit.prompts)} prompts across {len(audit.providers)} providers."
        )

        try:
            # 1. Query LLM providers concurrently
            raw_responses = await self.query_service.execute_audit_queries(
                audit=audit,
                run_id=run_id,
                provider_instances=provider_instances,
            )

            # 2. Persist raw responses immediately
            for resp in raw_responses:
                self.store.save_raw_response(resp)

            # 3. Analyze raw responses into observations
            observations = self.analysis_service.analyze_all(raw_responses, audit)
            self.store.save_observations(audit_id, observations)

            # 4. Generate report and client summary
            report = self.report_service.generate_report(
                audit=audit,
                raw_responses=raw_responses,
                observations=observations,
            )
            self.store.save_report(report)

            # 5. Update audit lifecycle status
            successful = sum(1 for r in raw_responses if r.success)
            if successful == len(raw_responses):
                audit.status = AuditStatus.COMPLETED
            elif successful > 0:
                audit.status = AuditStatus.PARTIAL
            else:
                audit.status = AuditStatus.FAILED

            audit.updated_at = datetime.now(UTC)
            self.store.save_audit(audit)

            logger.info(
                f"Completed audit '{audit_id}': {successful}/{len(raw_responses)} "
                f"successful responses. Status: {audit.status.value}"
            )

            return report, raw_responses, observations

        except Exception as exc:
            audit.status = AuditStatus.FAILED
            audit.updated_at = datetime.now(UTC)
            self.store.save_audit(audit)
            logger.error(f"Audit run failed for '{audit_id}': {exc}", exc_info=True)
            raise exc

    def get_raw_responses(self, audit_id: str) -> list[RawLLMResponse]:
        """Fetch raw responses for an audit."""
        self.get_audit(audit_id)  # Validate audit exists
        return self.store.get_raw_responses(audit_id)

    def get_observations(self, audit_id: str) -> list[ResponseObservation]:
        """Fetch normalized observations for an audit."""
        self.get_audit(audit_id)
        return self.store.get_observations(audit_id)

    def get_report(self, audit_id: str) -> AuditReport:
        """Retrieve audit report or raise ReportUnavailableError."""
        self.get_audit(audit_id)
        report = self.store.get_report(audit_id)
        if not report:
            raise ReportUnavailableError(
                f"Report for audit '{audit_id}' has not been generated yet. Please run the audit first."
            )
        return report

    def get_summary(self, audit_id: str) -> ClientSummary:
        """Retrieve one-page client summary."""
        report = self.get_report(audit_id)
        return report.client_summary

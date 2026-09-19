"""JSON file-based persistence store.

Implements `AuditStore` interface using structured JSON files on the local filesystem:
  data/
  ├── audits/<audit_id>.json
  ├── raw/<audit_id>/<response_id>.json
  ├── processed/<audit_id>.json
  └── reports/<audit_id>.json

Thread-safe file creation, atomic writes, and graceful handling of missing files.
Ensures full audit inspectability without external database dependencies.
"""

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.exceptions import StorageError
from app.models.audit import Audit
from app.models.observation import ResponseObservation
from app.models.report import AuditReport
from app.models.response import RawLLMResponse
from app.storage.audit_store import AuditStore


class JSONAuditStore(AuditStore):
    """File-system JSON repository for audits, raw responses, observations, and reports."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._init_directories()

    def _init_directories(self) -> None:
        """Create storage directory tree if it does not already exist."""
        for path in (
            self.settings.audits_dir,
            self.settings.raw_dir,
            self.settings.processed_dir,
            self.settings.reports_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_json(file_path: Path, data: dict[str, Any] | list[Any]) -> None:
        """Atomically write JSON data to file with 2-space indentation."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Write to temporary file first then replace to avoid corruption
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            temp_path.replace(file_path)
        except Exception as exc:
            raise StorageError(
                f"Failed writing JSON to '{file_path}': {exc}",
                details={"file_path": str(file_path)},
            ) from exc

    @staticmethod
    def _read_json(file_path: Path) -> Any:
        """Read and parse JSON file."""
        if not file_path.exists():
            return None
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            raise StorageError(
                f"Failed reading JSON from '{file_path}': {exc}",
                details={"file_path": str(file_path)},
            ) from exc

    def save_audit(self, audit: Audit) -> None:
        """Save Audit definition to data/audits/<audit_id>.json."""
        target_path = self.settings.audits_dir / f"{audit.audit_id}.json"
        self._write_json(target_path, audit.model_dump())

    def get_audit(self, audit_id: str) -> Audit | None:
        """Read Audit definition from disk."""
        target_path = self.settings.audits_dir / f"{audit_id}.json"
        data = self._read_json(target_path)
        if data is None:
            return None
        return Audit.model_validate(data)

    def list_audits(self) -> list[Audit]:
        """List all saved Audit definitions sorted by created_at descending."""
        audits: list[Audit] = []
        for file_path in self.settings.audits_dir.glob("*.json"):
            data = self._read_json(file_path)
            if data:
                audits.append(Audit.model_validate(data))
        audits.sort(key=lambda a: a.created_at, reverse=True)
        return audits

    def save_raw_response(self, response: RawLLMResponse) -> None:
        """Save raw provider response to data/raw/<audit_id>/<response_id>.json."""
        target_path = (
            self.settings.raw_dir / response.audit_id / f"{response.response_id}.json"
        )
        self._write_json(target_path, response.model_dump())

    def get_raw_responses(self, audit_id: str) -> list[RawLLMResponse]:
        """Retrieve all raw responses collected under data/raw/<audit_id>/."""
        audit_raw_dir = self.settings.raw_dir / audit_id
        if not audit_raw_dir.exists():
            return []

        responses: list[RawLLMResponse] = []
        for file_path in audit_raw_dir.glob("*.json"):
            data = self._read_json(file_path)
            if data:
                responses.append(RawLLMResponse.model_validate(data))

        responses.sort(key=lambda r: r.timestamp)
        return responses

    def save_observations(
        self, audit_id: str, observations: list[ResponseObservation]
    ) -> None:
        """Save normalized observations list to data/processed/<audit_id>.json."""
        target_path = self.settings.processed_dir / f"{audit_id}.json"
        payload = [obs.model_dump() for obs in observations]
        self._write_json(target_path, payload)

    def get_observations(self, audit_id: str) -> list[ResponseObservation]:
        """Retrieve normalized observations list from data/processed/<audit_id>.json."""
        target_path = self.settings.processed_dir / f"{audit_id}.json"
        data = self._read_json(target_path)
        if not data or not isinstance(data, list):
            return []
        return [ResponseObservation.model_validate(item) for item in data]

    def save_report(self, report: AuditReport) -> None:
        """Save final AuditReport to data/reports/<audit_id>.json."""
        target_path = self.settings.reports_dir / f"{report.audit_id}.json"
        self._write_json(target_path, report.model_dump())

    def get_report(self, audit_id: str) -> AuditReport | None:
        """Retrieve AuditReport from data/reports/<audit_id>.json."""
        target_path = self.settings.reports_dir / f"{audit_id}.json"
        data = self._read_json(target_path)
        if data is None:
            return None
        return AuditReport.model_validate(data)

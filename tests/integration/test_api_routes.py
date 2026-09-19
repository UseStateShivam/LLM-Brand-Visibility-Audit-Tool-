"""Integration tests for FastAPI REST API endpoints using TestClient.

Verifies:
- GET /health
- POST /audits (creation)
- GET /audits/{audit_id}
- GET /prompts/templates
- POST /prompts/preview
- POST /audits/{audit_id}/run (with mocked providers)
- GET /audits/{audit_id}/responses
- GET /audits/{audit_id}/observations
- GET /audits/{audit_id}/report
- GET /audits/{audit_id}/report/summary
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_audit_store, get_provider_factory
from app.core.config import Settings
from app.main import app
from app.models.citation import CitationRecord
from app.providers.base import LLMProvider, ProviderResult
from app.providers.factory import ProviderFactory
from app.storage.json_store import JSONAuditStore


class MockProvider(LLMProvider):
    """Mock provider for API route integration testing."""

    def __init__(self, provider_name: str, response_text: str) -> None:
        super().__init__(provider_name=provider_name, model_name=f"{provider_name}-mock")
        self.text = response_text

    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> ProviderResult:
        return ProviderResult(
            response_text=self.text,
            latency_ms=35.0,
            citations=[
                CitationRecord(
                    url="https://acme.ai/product",
                    domain="acme.ai",
                    title="Acme AI Product",
                    is_brand_owned=True,
                )
            ],
        )


class MockProviderFactory(ProviderFactory):
    """Factory that always returns MockProvider instances."""

    def create(self, provider_name: str, model_name: str | None = None, **kwargs) -> LLMProvider:
        text = (
            "Here are top solutions:\n"
            "1. Acme AI: Highly recommended platform for support.\n"
            "2. Beta AI: Known competitor platform."
        )
        return MockProvider(provider_name, text)


@pytest.fixture
def client(tmp_path: Path):
    test_settings = Settings(data_dir=tmp_path / "data")
    test_store = JSONAuditStore(test_settings)
    mock_factory = MockProviderFactory(test_settings)

    app.dependency_overrides[get_audit_store] = lambda: test_store
    app.dependency_overrides[get_provider_factory] = lambda: mock_factory

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "LLM Brand Visibility" in data["app_name"]


def test_prompts_templates_and_preview(client: TestClient) -> None:
    # 1. Get templates
    templates_resp = client.get("/prompts/templates")
    assert templates_resp.status_code == 200
    templates = templates_resp.json()
    assert len(templates) > 0

    # 2. Preview template
    preview_payload = {
        "template": "What are the best tools for {category}?",
        "brand": "Acme AI",
        "category": "conversational support",
    }
    preview_resp = client.post("/prompts/preview", json=preview_payload)
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["rendered_prompt"] == "What are the best tools for conversational support?"
    assert preview_data["is_valid"] is True


def test_full_audit_api_lifecycle(client: TestClient) -> None:
    # 1. Create Audit
    create_payload = {
        "brand": "Acme AI",
        "aliases": ["Acme"],
        "brand_domain": "acme.ai",
        "competitors": ["Beta AI"],
        "industry": "Support AI",
        "topics": ["automation"],
        "prompts": [
            {
                "text": "What are the best tools for support automation?",
                "topic": "automation",
                "intent": "discovery",
            }
        ],
        "providers": [
            {"provider": "openai"},
            {"provider": "gemini"},
        ],
    }
    create_resp = client.post("/audits", json=create_payload)
    assert create_resp.status_code == 201
    audit_id = create_resp.json()["audit_id"]
    assert audit_id is not None

    # 2. Get Audit Status
    status_resp = client.get(f"/audits/{audit_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "CREATED"

    # 3. Run Audit
    run_resp = client.post(f"/audits/{audit_id}/run")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["successful_responses"] == 2
    assert run_data["failed_responses"] == 0

    # 4. Get Raw Responses
    raw_resp = client.get(f"/audits/{audit_id}/responses")
    assert raw_resp.status_code == 200
    assert raw_resp.json()["count"] == 2

    # 5. Get Observations
    obs_resp = client.get(f"/audits/{audit_id}/observations")
    assert obs_resp.status_code == 200
    assert obs_resp.json()["count"] == 2

    # 6. Get Full Report
    report_resp = client.get(f"/audits/{audit_id}/report")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["brand"] == "Acme AI"
    assert report_data["overall_metrics"]["mention_rate"] == 1.0

    # 7. Get Client Summary
    summary_resp = client.get(f"/audits/{audit_id}/report/summary")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["brand"] == "Acme AI"
    assert summary_data["visibility_score"] > 0
    assert len(summary_data["top_strengths"]) > 0

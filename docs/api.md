# REST API Reference

The LLM Brand Visibility Audit Tool exposes a RESTful API built on FastAPI.

Interactive Swagger documentation is available at:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

---

## 1. System Health

### `GET /health`
Returns system status, service name, and version.

**Response (200 OK):**
```json
{
  "status": "ok",
  "app_name": "LLM Brand Visibility Audit Tool",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2024-06-10T12:00:00Z"
}
```

---

## 2. Audits Lifecycle

### `POST /audits`
Create and configure an audit definition.

**Request Body:**
```json
{
  "brand": "Acme AI",
  "aliases": ["Acme", "AcmeAI"],
  "brand_domain": "acme.ai",
  "competitors": ["Beta AI", "Gamma AI"],
  "industry": "Customer Support Automation",
  "topics": ["automation", "pricing"],
  "prompts": [
    {
      "text": "What are the best tools for customer support automation?",
      "topic": "automation",
      "intent": "discovery"
    }
  ],
  "providers": [
    { "provider": "openai", "model": "gpt-4o-mini" },
    { "provider": "gemini", "model": "gemini-1.5-flash" }
  ]
}
```

**Response (201 Created):**
```json
{
  "audit_id": "8c64d8e2-3c0f-4c7b-af57-8ae5bf079101",
  "brand": "Acme AI",
  "status": "CREATED",
  "total_prompts": 1,
  "providers": ["openai", "gemini"],
  "created_at": "2024-06-10T12:00:00Z",
  "message": "Audit definition created successfully."
}
```

---

### `GET /audits/{audit_id}`
Retrieve the configuration, metadata, and status of an audit.

---

### `POST /audits/{audit_id}/run`
Execute the audit workflow across all configured providers.

**Response (200 OK):**
```json
{
  "audit_id": "8c64d8e2-3c0f-4c7b-af57-8ae5bf079101",
  "run_id": "rep_12ab34cd56ef",
  "status": "COMPLETED",
  "total_requests": 2,
  "successful_responses": 2,
  "failed_responses": 0,
  "started_at": "2024-06-10T12:00:01Z",
  "completed_at": "2024-06-10T12:00:03Z",
  "elapsed_seconds": 2.15,
  "message": "Audit executed. 2/2 requests succeeded. Report is ready."
}
```

---

### `GET /audits/{audit_id}/responses`
Retrieve immutable raw LLM responses.

---

### `GET /audits/{audit_id}/observations`
Retrieve normalized analytical observations (brand mentions, contexts, competitor presences, citations).

---

## 3. Reports and Summaries

### `GET /audits/{audit_id}/report`
Retrieve full, machine-readable `AuditReport` with complete data lineage.

---

### `GET /audits/{audit_id}/report/summary`
Retrieve concise, client-facing `ClientSummary`.

---

## 4. Prompts & Templates

### `GET /prompts/templates`
List default category prompt templates.

### `POST /prompts/preview`
Preview variable substitution and template validation.

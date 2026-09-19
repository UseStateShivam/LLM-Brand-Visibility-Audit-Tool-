# LLM Brand Visibility Audit Tool

> A production-oriented audit platform that measures how frequently and how accurately a brand appears in LLM-generated answers, extracts citation/source attribution and mention context, identifies visibility gaps, and converts raw model responses into ranked visibility reports and client-ready summaries.

## 1. Project Purpose

The **LLM Brand Visibility Audit Tool** is a backend-first application for AEO/GEO-style brand visibility analysis.

The system asks multiple LLM providers the same set of brand-relevant prompts, captures their raw answers, analyzes whether and where the target brand appears, extracts supporting/cited sources, and aggregates the observations into an auditable visibility report.

The project is intentionally designed around the workflow represented by the resume project description:

- Query LLMs such as GPT and Gemini with brand-relevant prompts.
- Measure brand mention/citation frequency.
- Preserve the surrounding mention context.
- Attribute influence/source information.
- Surface visibility gaps.
- Transform raw LLM responses into ranked visibility reports.
- Produce concise one-page client summaries.
- Expose the workflow through a FastAPI service.
- Keep outputs usable by both technical and non-technical stakeholders.

This README is the **master implementation specification**. An implementation agent should treat it as the source of truth for architecture, file responsibilities, data contracts, processing stages, testing, and operational expectations.

---

# 2. Exact Technology Stack

## Core language

- **Python 3.11+**

Python is the only primary application language.

## LLM providers

- **OpenAI API**
- **Google Gemini API**

The application must keep provider-specific code behind a common adapter interface so the auditing pipeline does not depend directly on one provider.

The initial model configuration should be environment-driven rather than hard-coded.

Example logical configuration:

- OpenAI provider
- Gemini provider
- model name
- temperature
- maximum output tokens
- request timeout
- retry count

Do not assume a specific model name is permanently available. Model identifiers belong in configuration/environment variables.

## Backend

- **FastAPI**
- **Uvicorn**
- **Pydantic / Pydantic Settings**

FastAPI owns the HTTP API and request validation.

## Data format

- **JSON**

JSON is the canonical interchange format for:

- audit configurations
- prompts
- raw model responses
- normalized observations
- source/citation records
- visibility metrics
- final reports

## HTTP

- `httpx`

Use an async HTTP client where provider SDKs are not sufficient or where direct API access is required.

## Data processing

- Standard Python collections/dataclasses where appropriate.
- No pandas dependency is required for the core MVP because the application is fundamentally an API/data-processing system rather than a notebook analytics project.

If tabular analytics are added later, pandas may be introduced without changing the core architecture.

## Testing

- `pytest`
- `pytest-asyncio`
- FastAPI test client

Provider APIs must be mocked in tests. Tests must not require real API keys.

## Code quality

- `ruff`
- `black`
- `mypy` (recommended)
- type hints throughout the codebase

## Environment / configuration

- `.env`
- `pydantic-settings`

Never commit API keys.

## Optional production packaging

- Docker
- Docker Compose

Docker should package the API consistently across development and deployment environments.

---

# 3. What the Application Does

At a high level:

```text
Brand + Competitors + Topics
            |
            v
     Audit Configuration
            |
            v
       Prompt Builder
            |
            v
  +-----------------------+
  |                       |
  v                       v
OpenAI Adapter       Gemini Adapter
  |                       |
  +-----------+-----------+
              |
              v
       Raw LLM Responses
              |
              v
       Response Analyzer
              |
       +------+------+
       |             |
       v             v
Brand Mention     Sources /
Detection         Citations
       |             |
       +------+------+
              |
              v
      Observation Records
              |
              v
       Metric Aggregator
              |
              v
      Visibility Scoring
              |
              v
       Gap Identification
              |
              v
       Ranked Audit Report
              |
       +------+------+
       |             |
       v             v
 JSON Report     Client Summary
```

The important design principle is:

> **Never destroy the raw LLM response.**

Every derived metric must be traceable back to the original provider response and prompt.

---

# 4. Core User Workflow

A user should be able to:

1. Define a brand.
2. Define alternative brand names / aliases.
3. Define competitors.
4. Define relevant topics/categories.
5. Provide a list of audit prompts.
6. Select LLM providers/models.
7. Run an audit.
8. View raw model responses.
9. See whether the brand was mentioned.
10. See where the brand was mentioned.
11. See surrounding mention context.
12. See sources/citations associated with the response where available.
13. Compare brand visibility across prompts and providers.
14. Identify prompts where competitors appeared but the target brand did not.
15. Identify source/citation patterns.
16. Generate a ranked visibility report.
17. Generate a concise client-facing summary.

---

# 5. MVP Scope

The first production-quality version MUST implement:

## A. Audit configuration

Inputs:

- brand name
- brand aliases
- competitors
- industry/category
- target topics
- prompts
- selected providers
- selected models
- audit metadata

## B. Multi-provider querying

The system must query:

- OpenAI
- Gemini

through a common provider abstraction.

## C. Raw response capture

For every request, store:

- provider
- model
- prompt
- response
- request timestamp
- latency
- request identifier if available
- success/failure
- error information
- audit ID

## D. Brand mention extraction

For each response:

- detect target brand mention
- detect aliases
- detect competitor mentions
- capture mention count
- capture context around each mention
- identify approximate position/order of appearance
- classify whether the target brand was recommended, merely mentioned, or absent

## E. Citation/source extraction

Where the provider response exposes sources/citations:

- capture source URL
- source title when available
- source domain
- citation position/reference
- relationship to the brand mention when determinable

If a provider/model does not expose citations in a structured way, the system must mark citation data as unavailable rather than fabricate it.

## F. Visibility metrics

At minimum:

- mention rate
- citation/source rate
- prompt coverage
- provider coverage
- competitor comparison
- recommendation rate
- average mention position where measurable
- source-domain frequency
- visibility gap count

## G. Gap analysis

Examples:

- target brand absent while competitor is present
- target brand absent across an entire topic
- target brand mentioned but not recommended
- target brand mentioned without supporting source attribution
- competitor receives stronger visibility on the same prompt
- target brand is repeatedly associated with the wrong topic/context

## H. Ranked report

The report must rank audit observations according to transparent, deterministic metrics.

The scoring formula must be documented in code and report metadata.

Do not create an unexplained black-box score.

## I. Client summary

Generate a compact summary containing:

- overall visibility snapshot
- strongest visibility areas
- largest gaps
- competitor observations
- source/citation patterns
- recommended areas for further investigation

The summary is a presentation layer over the measured data. It must not invent evidence.

---

# 6. Non-Goals for MVP

Do NOT expand the first implementation into:

- automated SEO crawling
- website scraping
- browser automation
- social-media monitoring
- Google search ranking tracking
- autonomous content generation
- automatic publishing
- paid advertising management
- CRM integration
- user authentication
- multi-tenant billing
- complex frontend dashboards
- vector databases
- agentic autonomous workflows

These can become future modules.

The MVP is specifically an **LLM brand visibility audit engine + API + report generator**.

---

# 7. Recommended Repository Structure

```text
llm-brand-visibility-audit/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
│
├── app/
│   ├── __init__.py
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── audits.py
│   │   │   ├── reports.py
│   │   │   └── prompts.py
│   │   │
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   ├── prompt.py
│   │   ├── response.py
│   │   ├── observation.py
│   │   ├── citation.py
│   │   ├── metrics.py
│   │   └── report.py
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   └── factory.py
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   ├── templates.py
│   │   └── validator.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── mention_detector.py
│   │   ├── context_extractor.py
│   │   ├── competitor_detector.py
│   │   ├── citation_extractor.py
│   │   ├── recommendation_classifier.py
│   │   └── source_analyzer.py
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── visibility_score.py
│   │   ├── gap_analyzer.py
│   │   └── ranking.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audit_service.py
│   │   ├── query_service.py
│   │   ├── analysis_service.py
│   │   ├── report_service.py
│   │   └── summary_service.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── audit_store.py
│   │   └── json_store.py
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py
│       └── responses.py
│
├── data/
│   ├── audits/
│   ├── raw/
│   ├── processed/
│   └── reports/
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_mention_detector.py
│   │   ├── test_context_extractor.py
│   │   ├── test_citation_extractor.py
│   │   ├── test_gap_analyzer.py
│   │   ├── test_visibility_score.py
│   │   └── test_prompt_builder.py
│   │
│   ├── integration/
│   │   ├── test_openai_provider.py
│   │   ├── test_gemini_provider.py
│   │   └── test_audit_pipeline.py
│   │
│   └── fixtures/
│       ├── openai_response.json
│       ├── gemini_response.json
│       └── sample_audit.json
│
├── scripts/
│   ├── run_audit.py
│   └── generate_report.py
│
└── docs/
    ├── architecture.md
    ├── scoring.md
    ├── api.md
    └── sample-report.md
```

---

# 8. File-by-File Responsibilities

## Root

### `README.md`

The master project specification.

It explains:

- purpose
- architecture
- setup
- stack
- data flow
- file responsibilities
- API
- metrics
- scoring
- testing
- deployment
- implementation rules

### `pyproject.toml`

Single source of truth for:

- Python version
- dependencies
- development dependencies
- Ruff
- Black
- pytest
- mypy configuration

### `.env.example`

Documents required environment variables without exposing secrets.

Expected categories:

```text
OPENAI_API_KEY=
GEMINI_API_KEY=

OPENAI_MODEL=
GEMINI_MODEL=

APP_ENV=
LOG_LEVEL=
DATA_DIR=
```

### `Dockerfile`

Builds the API application into a reproducible container.

### `docker-compose.yml`

Provides a convenient local deployment definition.

For MVP, the application can remain file/JSON backed and does not require a database container.

---

# 9. Application Entry Point

## `app/main.py`

Creates the FastAPI application.

Responsibilities:

- initialize FastAPI
- register routers
- configure middleware
- configure startup/shutdown behavior
- expose health endpoint

It must NOT contain:

- LLM business logic
- mention analysis
- scoring formulas
- large prompt strings
- provider-specific API calls

---

# 10. API Layer

## `app/api/routes/health.py`

Provides:

```text
GET /health
```

Returns application health/status.

---

## `app/api/routes/audits.py`

Owns audit lifecycle endpoints.

Recommended endpoints:

```text
POST /audits
GET  /audits/{audit_id}
POST /audits/{audit_id}/run
GET  /audits/{audit_id}/responses
GET  /audits/{audit_id}/observations
```

The route layer validates requests and calls services.

It should not perform analysis itself.

---

## `app/api/routes/reports.py`

Recommended endpoints:

```text
GET /audits/{audit_id}/report
GET /audits/{audit_id}/report/summary
```

---

## `app/api/routes/prompts.py`

Provides prompt configuration/validation functionality.

Potential endpoints:

```text
POST /prompts/validate
POST /prompts/preview
```

---

## `app/api/dependencies.py`

Dependency injection for:

- services
- configuration
- stores
- provider factory

---

# 11. Configuration

## `app/core/config.py`

Centralized settings using Pydantic Settings.

Responsibilities:

- environment loading
- API key configuration
- provider model configuration
- timeouts
- retry limits
- storage directories
- application environment

Never access `os.environ` throughout random application files.

---

## `app/core/logging.py`

Centralized structured logging configuration.

Logs should make it possible to answer:

- which audit ran?
- which provider was queried?
- which prompt failed?
- how long did the request take?
- how many requests succeeded?
- what stage failed?

Never log API keys or sensitive provider payloads by default.

---

## `app/core/exceptions.py`

Application-specific exception types.

Examples:

- provider error
- invalid audit
- unsupported provider
- analysis error
- report generation error

---

# 12. Domain Models

## `app/models/audit.py`

Defines the internal representation of an audit.

Conceptually:

```text
Audit
├── audit_id
├── brand
├── aliases
├── competitors
├── industry
├── topics
├── prompts
├── providers
├── models
├── created_at
└── status
```

---

## `app/models/prompt.py`

Represents an individual audit prompt.

Fields should capture:

- prompt ID
- text
- topic
- intent/category
- ordering
- metadata

---

## `app/models/response.py`

Represents a raw provider response.

Important fields:

- response ID
- audit ID
- prompt ID
- provider
- model
- raw text
- timestamp
- latency
- success
- error
- provider metadata

The raw response must remain immutable after collection.

---

## `app/models/observation.py`

Represents the normalized result of analyzing one response.

Conceptually:

```text
Observation
├── response_id
├── brand_mentioned
├── mention_count
├── mention_contexts
├── competitors_mentioned
├── recommendation_class
├── citations
└── analysis_metadata
```

---

## `app/models/citation.py`

Represents source information.

Fields may include:

- URL
- title
- domain
- citation identifier
- position
- related mention
- extraction confidence
- provider

---

## `app/models/metrics.py`

Defines calculated metrics.

Examples:

- mention rate
- citation rate
- recommendation rate
- coverage rate
- competitor presence rate
- average mention position
- gap rate

---

## `app/models/report.py`

Defines final report structure.

A report should contain:

```text
Report
├── audit metadata
├── executive summary
├── overall metrics
├── provider breakdown
├── topic breakdown
├── competitor observations
├── source analysis
├── visibility gaps
├── ranked observations
└── raw evidence references
```

---

# 13. Provider Architecture

The most important architectural requirement is **provider abstraction**.

The rest of the application must not know how OpenAI or Gemini APIs work internally.

## `app/providers/base.py`

Define a common provider contract.

Conceptually:

```text
LLMProvider
├── provider_name
├── model_name
└── generate(...)
```

The interface should normalize provider responses into the application's internal response model.

---

# 14. OpenAI Provider

## `app/providers/openai_provider.py`

Responsible only for:

- authentication
- OpenAI client initialization
- sending prompts
- handling provider errors
- extracting provider response text
- extracting structured citation information when available
- returning normalized provider output

Do not put visibility scoring here.

---

# 15. Gemini Provider

## `app/providers/gemini_provider.py`

Same responsibility as OpenAI provider, but for Gemini.

The rest of the system must be able to swap:

```text
OpenAI
```

with:

```text
Gemini
```

without changing analysis code.

---

# 16. Provider Factory

## `app/providers/factory.py`

Maps configuration/provider names to provider implementations.

Example logical mapping:

```text
"openai" -> OpenAIProvider
"gemini" -> GeminiProvider
```

Unknown providers must produce a controlled application error.

---

# 17. Prompt System

## `app/prompts/builder.py`

Builds audit prompts from structured configuration.

The builder should preserve the user's original prompt wording.

It may inject controlled variables such as:

- brand name
- category
- geography
- competitor names

But prompt construction must be deterministic and reproducible.

---

## `app/prompts/templates.py`

Stores reusable prompt templates.

Prompt categories can include:

### Discovery prompts

Questions asking the LLM to recommend products/services/brands.

### Comparison prompts

Questions explicitly comparing alternatives.

### Category prompts

Questions asking which brands are relevant in a category.

### Problem/solution prompts

Questions asking which companies solve a particular problem.

### Authority prompts

Questions asking for recognized companies, tools, providers, or experts.

The initial MVP should support arbitrary user-provided prompts even if templates are later expanded.

---

## `app/prompts/validator.py`

Validates:

- prompt is non-empty
- variables are valid
- duplicate prompts are detected
- provider compatibility is checked
- prompt configuration is serializable

---

# 18. Mention Detection

## `app/analysis/mention_detector.py`

Determines whether the target brand appears in an LLM response.

It must support:

- exact brand names
- aliases
- case-insensitive matching
- punctuation variations
- normalized whitespace

The detector should return:

- mentioned/not mentioned
- count
- character positions
- matched form

Avoid overly aggressive fuzzy matching in the initial version because false positives can corrupt visibility metrics.

If fuzzy matching is introduced, store the matching method and confidence.

---

# 19. Context Extraction

## `app/analysis/context_extractor.py`

For every brand mention, capture a bounded text window around the mention.

Example concept:

```text
... surrounding sentence(s) containing the brand ...
```

The context should answer:

> Why did the model mention this brand?

Store:

- raw context
- mention position
- sentence/paragraph where possible

Do not rewrite the original model output.

---

# 20. Competitor Detection

## `app/analysis/competitor_detector.py`

Runs the same normalized matching process for competitor brands.

Outputs:

- competitor name
- mention count
- contexts
- relative appearance order

This enables direct prompt-level comparisons without claiming an overall winner.

---

# 21. Recommendation Classification

## `app/analysis/recommendation_classifier.py`

Classifies the target brand's role in the answer.

Minimum classes:

```text
ABSENT
MENTIONED
RECOMMENDED
STRONGLY_RECOMMENDED
```

The classifier should be deterministic wherever possible.

If an LLM is later used as a secondary classifier, preserve:

- classifier model
- classifier prompt
- raw classifier result
- confidence

The MVP should avoid making the entire audit dependent on a second LLM call.

---

# 22. Citation Extraction

## `app/analysis/citation_extractor.py`

Normalizes source/citation information from provider responses.

Possible information:

- URL
- title
- domain
- citation marker
- source order
- relation to brand mention

Important rule:

> Missing citation data is not the same thing as zero citations.

Use explicit states such as:

```text
AVAILABLE
NONE_FOUND
NOT_SUPPORTED_BY_PROVIDER
EXTRACTION_FAILED
```

This prevents misleading reports.

---

# 23. Source Analysis

## `app/analysis/source_analyzer.py`

Aggregates source domains and source frequency.

Examples:

```text
example.com -> 7 citations
reddit.com -> 4 citations
officialbrand.com -> 3 citations
```

The system should be able to identify:

- domains repeatedly influencing answers
- whether target-brand-owned sources appear
- whether third-party sources dominate
- source distribution by topic
- source distribution by provider

This is descriptive analysis, not proof of causal influence.

The report should use careful wording such as:

> "Sources observed alongside the model's answer"

rather than claiming that a source definitely caused the model output.

---

# 24. Audit Service

## `app/services/audit_service.py`

Orchestrates the full audit.

Logical pipeline:

```text
validate audit
    ↓
build prompts
    ↓
select providers
    ↓
query providers
    ↓
store raw responses
    ↓
analyze responses
    ↓
calculate metrics
    ↓
identify gaps
    ↓
rank observations
    ↓
generate report
```

This is the central orchestration layer.

It should coordinate components rather than implement their internals.

---

# 25. Query Service

## `app/services/query_service.py`

Responsible for executing provider requests.

Responsibilities:

- concurrency control
- retries
- timeouts
- provider selection
- response normalization
- latency measurement
- failure handling

The query service must not calculate brand visibility.

---

# 26. Analysis Service

## `app/services/analysis_service.py`

Takes raw responses and converts them into normalized observations.

Pipeline:

```text
raw response
    ↓
brand detector
    ↓
context extractor
    ↓
competitor detector
    ↓
recommendation classifier
    ↓
citation extractor
    ↓
source analyzer
    ↓
observation
```

---

# 27. Report Service

## `app/services/report_service.py`

Combines observations and metrics into a structured report.

The report must contain evidence references back to:

- audit
- prompt
- provider
- response
- observation

This makes the report auditable.

---

# 28. Summary Service

## `app/services/summary_service.py`

Converts the detailed report into a one-page client-oriented summary.

The summary should prioritize:

1. What was measured.
2. What was observed.
3. Where visibility was strongest.
4. Where visibility gaps occurred.
5. What source patterns appeared.
6. What should be investigated next.

Avoid unsupported prescriptions such as:

> "Do X and your ranking will increase by Y%."

The system measures visibility; it does not prove future ranking outcomes.

---

# 29. Storage

## `app/storage/audit_store.py`

Defines the persistence interface.

The application should not directly manipulate JSON files throughout the codebase.

---

## `app/storage/json_store.py`

MVP persistence implementation.

Suggested layout:

```text
data/
├── audits/
│   └── <audit_id>.json
├── raw/
│   └── <audit_id>/
│       └── <response_id>.json
├── processed/
│   └── <audit_id>.json
└── reports/
    └── <audit_id>.json
```

This makes the entire audit inspectable without requiring a database.

A database can replace this store later.

---

# 30. Scoring System

The scoring system must be transparent.

Do not create a magical "AI visibility score" with arbitrary weights.

The MVP should calculate independent metrics first.

## Mention Rate

```text
mention_rate =
    prompts_where_brand_mentioned
    /
    total_successful_prompt_responses
```

## Recommendation Rate

```text
recommendation_rate =
    prompts_where_brand_was_recommended
    /
    total_successful_prompt_responses
```

## Citation Rate

Only calculate when citation data is supported/available:

```text
citation_rate =
    responses_with_target_brand_related_citations
    /
    responses_with_available_citation_data
```

## Topic Coverage

```text
topic_coverage =
    topics_with_at_least_one_brand_mention
    /
    total_topics_audited
```

## Competitor Gap

At the individual prompt level:

```text
competitor_gap =
    target_brand_absent
    AND competitor_present
```

This is more useful than hiding the observation inside a single score.

---

# 31. Ranking Logic

The ranking layer should prioritize observable gaps.

Recommended priority ordering for report generation:

1. Brand absent while a competitor appears.
2. Brand absent across repeated prompts in the same topic.
3. Brand mentioned but not recommended.
4. Brand recommended but without observable supporting sources.
5. Brand visibility concentrated in only one provider.
6. Source/citation concentration patterns.

This ordering is a report-organization mechanism, not a political/evaluative ranking of people or organizations.

Each ranked observation must contain evidence.

Example:

```text
Prompt:
"Best tools for X?"

Provider:
OpenAI

Target brand:
Absent

Competitor:
Competitor A

Evidence:
Raw response ID
```

---

# 32. Visibility Gap Definition

A visibility gap is an observable mismatch between the target brand and the expected visibility pattern.

Examples:

### Gap A — competitor presence

```text
Target brand: absent
Competitor: present
```

### Gap B — topic invisibility

```text
Topic: enterprise automation
Target brand mentions: 0 / 10
```

### Gap C — weak recommendation presence

```text
Brand mentioned: yes
Brand recommended: no
```

### Gap D — provider inconsistency

```text
OpenAI: brand appears
Gemini: brand absent
```

These are observations, not guarantees about search/market performance.

---

# 33. Raw Data Contract

Every provider response should preserve enough information to reproduce the analysis.

Conceptual structure:

```json
{
  "response_id": "...",
  "audit_id": "...",
  "prompt_id": "...",
  "provider": "openai",
  "model": "...",
  "prompt": "...",
  "response_text": "...",
  "timestamp": "...",
  "latency_ms": 1234,
  "success": true,
  "provider_metadata": {}
}
```

Provider metadata must not contain secrets.

---

# 34. Observation Contract

Conceptual structure:

```json
{
  "response_id": "...",
  "brand": "...",
  "brand_mentioned": true,
  "mention_count": 2,
  "mention_contexts": [],
  "competitors": [],
  "recommendation": "RECOMMENDED",
  "citations": [],
  "analysis_metadata": {
    "mention_detection_method": "normalized_exact_match"
  }
}
```

---

# 35. Report Contract

Conceptual structure:

```json
{
  "audit_id": "...",
  "brand": "...",
  "metrics": {
    "mention_rate": 0.0,
    "recommendation_rate": 0.0,
    "citation_rate": 0.0,
    "topic_coverage": 0.0
  },
  "provider_breakdown": [],
  "topic_breakdown": [],
  "competitor_observations": [],
  "source_analysis": [],
  "visibility_gaps": [],
  "ranked_observations": [],
  "summary": "...",
  "evidence": []
}
```

---

# 36. API Contract

## Create audit

```text
POST /audits
```

Request concept:

```json
{
  "brand": "Example Brand",
  "aliases": ["ExampleBrand"],
  "competitors": ["Competitor A", "Competitor B"],
  "industry": "software",
  "topics": ["topic one", "topic two"],
  "prompts": [
    {
      "text": "What are the best tools for ...?",
      "topic": "topic one"
    }
  ],
  "providers": [
    {
      "provider": "openai",
      "model": "configured-model"
    },
    {
      "provider": "gemini",
      "model": "configured-model"
    }
  ]
}
```

---

## Run audit

```text
POST /audits/{audit_id}/run
```

Starts the audit pipeline.

For the MVP, the API may execute synchronously.

A later production version can introduce:

```text
POST /audits/{audit_id}/run
GET  /audits/{audit_id}/status
```

with background workers.

---

## Retrieve report

```text
GET /audits/{audit_id}/report
```

Returns the complete structured report.

---

## Retrieve summary

```text
GET /audits/{audit_id}/report/summary
```

Returns the compact client summary.

---

# 37. Concurrency

Multiple prompts and providers should be queried concurrently where safe.

Example:

```text
Prompt 1 -> OpenAI
Prompt 1 -> Gemini
Prompt 2 -> OpenAI
Prompt 2 -> Gemini
...
```

Use bounded concurrency.

Do NOT create unlimited tasks.

The implementation must respect:

- provider rate limits
- request timeouts
- retry limits

The query layer should use an explicit concurrency limit from configuration.

---

# 38. Error Handling

One provider failing must not automatically destroy the entire audit.

Example:

```text
10 prompts
2 providers

OpenAI:
9 successful
1 failed

Gemini:
10 successful
```

The audit should still produce a report with:

```text
successful observations: 19
failed requests: 1
```

The failed response must be recorded with:

- provider
- prompt
- error category
- timestamp

---

# 39. Retry Strategy

Retry only transient failures.

Potential retryable cases:

- timeout
- temporary provider availability issue
- rate limiting when appropriate

Do not blindly retry:

- invalid API key
- invalid request
- malformed configuration
- unsupported model

Use bounded exponential backoff.

---

# 40. Idempotency

An audit run should have a unique identifier.

If a request is retried internally, it should not silently create duplicate logical observations.

Store:

```text
audit_id
prompt_id
provider
model
run_id
```

so every observation can be traced.

---

# 41. Testing Strategy

Testing is a major part of the project because the application claims to produce measurable reports.

## Unit tests

Test independently:

- brand matching
- alias matching
- competitor matching
- context extraction
- recommendation classification
- citation normalization
- metrics
- gap detection
- ranking logic
- prompt validation

---

# 42. Provider Tests

Never call real APIs in ordinary CI tests.

Use mocked provider responses.

Test:

- successful response
- timeout
- rate limit
- invalid request
- malformed response
- missing citation data

---

# 43. Integration Test

A complete mocked audit should verify:

```text
audit creation
    ↓
prompt generation
    ↓
provider querying
    ↓
raw response storage
    ↓
analysis
    ↓
metrics
    ↓
gap detection
    ↓
report
```

The final report should be deterministic for a fixed fixture set.

---

# 44. Golden Test Fixtures

The fixture directory should contain realistic but synthetic provider responses.

Example:

```text
tests/fixtures/openai_response.json
tests/fixtures/gemini_response.json
```

Include cases such as:

### Case 1

Brand clearly recommended.

### Case 2

Brand mentioned but not recommended.

### Case 3

Brand absent and competitor present.

### Case 4

Brand appears multiple times.

### Case 5

No citation information.

### Case 6

Brand alias appears instead of canonical brand name.

### Case 7

Potential false-positive substring.

The last case is especially important.

For example, if the brand is:

```text
Art
```

the system must not blindly treat:

```text
partial
```

as a brand mention.

---

# 45. Security Requirements

Never:

- commit `.env`
- log API keys
- expose provider credentials through API responses
- return secrets in error messages
- place API keys in prompts
- store credentials inside audit JSON

API keys must be loaded from environment/configuration.

---

# 46. Observability

Every audit should have a traceable identifier.

Logs should contain:

```text
audit_id
run_id
prompt_id
provider
model
stage
status
latency
```

This makes debugging individual audits possible.

---

# 47. Reproducibility

A report must record enough metadata to understand how it was generated.

Record:

- audit ID
- timestamp
- providers
- model identifiers
- prompts
- analysis version
- scoring version

Recommended:

```text
analysis_version = "1.0"
scoring_version = "1.0"
```

When scoring changes, reports from different versions remain distinguishable.

---

# 48. Important LLM Measurement Caveats

LLM responses are stochastic and provider behavior changes over time.

Therefore the application should never present one audit run as permanent truth.

A report should make clear:

> This report measures observed model responses for the selected prompts, providers, models, and run time.

For more reliable measurement, future versions can support:

- repeated runs
- multiple temperatures/configurations where appropriate
- scheduled audits
- trend analysis

---

# 49. Client Summary Design

The one-page summary should be readable without technical knowledge.

Recommended structure:

```text
LLM BRAND VISIBILITY AUDIT
──────────────────────────

Brand
Audit date
Providers tested
Prompts tested

VISIBILITY SNAPSHOT
Mention rate
Recommendation rate
Citation/source coverage
Topic coverage

TOP OBSERVATIONS
1. ...
2. ...
3. ...

VISIBILITY GAPS
1. ...
2. ...
3. ...

COMPETITOR OBSERVATIONS
...

SOURCE PATTERNS
...

WHAT THIS MEANS
Short factual interpretation based only on observed data.

NEXT INVESTIGATION AREAS
...
```

Avoid marketing claims that cannot be supported by the audit data.

---

# 50. Example End-to-End Audit

Suppose the user configures:

```text
Brand:
Acme AI

Competitors:
Beta AI
Gamma AI

Topic:
Customer support automation

Prompt:
"What are the best AI tools for automating customer support?"
```

The application sends the prompt to:

```text
OpenAI
Gemini
```

Suppose OpenAI returns an answer containing:

```text
Beta AI
Gamma AI
Acme AI
```

The analyzer records:

```text
Acme mentioned = true
Acme recommendation = true
Competitors = Beta AI, Gamma AI
```

Suppose Gemini returns:

```text
Beta AI
Gamma AI
```

The analyzer records:

```text
Acme mentioned = false
Competitor present = true
```

The gap analyzer identifies:

```text
Target absent while competitor present
```

The report then contains the exact evidence:

```text
Provider: Gemini
Prompt: ...
Target: Acme AI
Result: absent
Competitors: Beta AI, Gamma AI
```

The system does not invent a reason for the absence.

---

# 51. Source Attribution Model

"Influence source attribution" must be implemented carefully.

The tool can report:

- which sources were cited
- which domains appeared
- which sources appeared near relevant claims
- how frequently domains were observed

It must NOT automatically claim:

> "This website caused the LLM to mention the brand."

The technically defensible phrasing is:

> "This source/domain was observed among the sources associated with the model response."

This distinction is critical for a credible audit product.

---

# 52. Data Lineage

Every final metric should be traceable:

```text
Report metric
    ↓
Observation
    ↓
Raw response
    ↓
Prompt
    ↓
Provider + model
```

This is a core architectural requirement.

---

# 53. Design Principles

## Principle 1 — Raw evidence first

Never overwrite provider responses.

## Principle 2 — Provider abstraction

OpenAI/Gemini are interchangeable at the application layer.

## Principle 3 — Deterministic analysis

Where possible, metrics should be generated using deterministic code rather than another LLM.

## Principle 4 — Transparent scoring

Every score must have a documented formula.

## Principle 5 — Evidence-backed reports

Every major observation must point back to raw evidence.

## Principle 6 — Graceful degradation

One provider or prompt failure should not invalidate the entire audit.

## Principle 7 — No fabricated citations

Never infer a source that the provider did not expose.

## Principle 8 — Reproducibility

Record provider/model/prompt/analysis/scoring versions.

## Principle 9 — Separation of concerns

Routes → services → analysis → storage.

## Principle 10 — Production readability

The project should be understandable by another engineer without reverse-engineering the architecture.

---

# 54. Dependency Policy

Keep the dependency graph small.

Required categories:

```text
FastAPI
Uvicorn
Pydantic
Pydantic Settings
OpenAI SDK
Google Gemini SDK
HTTPX
Pytest
Pytest Asyncio
Ruff
Black
Mypy
```

Do not add libraries merely because they are popular.

Every dependency should have a clear responsibility.

---

# 55. Suggested Development Order

Build in this exact order.

## Phase 1 — Foundation

Create:

```text
pyproject.toml
.env.example
app/main.py
app/core/
```

Verify the FastAPI application starts.

---

## Phase 2 — Domain models

Implement:

```text
audit.py
prompt.py
response.py
observation.py
citation.py
metrics.py
report.py
```

Validate the schemas.

---

## Phase 3 — Provider abstraction

Implement:

```text
providers/base.py
providers/openai_provider.py
providers/gemini_provider.py
providers/factory.py
```

Test using mocks.

---

## Phase 4 — Prompt system

Implement:

```text
prompts/builder.py
prompts/templates.py
prompts/validator.py
```

---

## Phase 5 — Analysis engine

Implement:

```text
mention_detector.py
context_extractor.py
competitor_detector.py
recommendation_classifier.py
citation_extractor.py
source_analyzer.py
```

This is the analytical core of the project.

---

## Phase 6 — Metrics and gaps

Implement:

```text
scoring/metrics.py
scoring/visibility_score.py
scoring/gap_analyzer.py
scoring/ranking.py
```

All formulas must have tests.

---

## Phase 7 — Storage

Implement JSON persistence.

---

## Phase 8 — Services

Connect:

```text
audit_service
query_service
analysis_service
report_service
summary_service
```

---

## Phase 9 — API

Add:

```text
/audits
/reports
/prompts
/health
```

---

## Phase 10 — Testing

Complete unit and integration coverage.

---

## Phase 11 — Docker

Verify the complete application starts inside Docker.

---

# 56. Definition of Done

The project is complete when a fresh developer can:

1. Clone the repository.
2. Create a `.env`.
3. Install dependencies.
4. Start FastAPI.
5. Create an audit through the API.
6. Run an audit against OpenAI and Gemini.
7. See raw responses.
8. See brand mention results.
9. See competitor results.
10. See mention context.
11. See available citation/source information.
12. See calculated visibility metrics.
13. See visibility gaps.
14. Retrieve a structured report.
15. Retrieve a one-page client summary.
16. Run the full test suite without real API calls.
17. Run the application in Docker.

---

# 57. Resume-Claim Alignment

The implementation should directly substantiate the following project claims:

### Claim

> Built a tool querying LLMs (GPT, Gemini) with brand-relevant prompts.

### Implementation evidence

- `providers/openai_provider.py`
- `providers/gemini_provider.py`
- `prompts/builder.py`
- `services/query_service.py`

---

### Claim

> Extracting citation frequency and mention context.

### Implementation evidence

- `analysis/mention_detector.py`
- `analysis/context_extractor.py`
- `analysis/citation_extractor.py`
- `scoring/metrics.py`

---

### Claim

> Surfacing visibility gaps.

### Implementation evidence

- `scoring/gap_analyzer.py`
- `scoring/ranking.py`
- report output

---

### Claim

> Core workflow for AEO/GEO optimization platforms.

### Implementation evidence

The complete pipeline:

```text
prompt
→ LLM
→ raw response
→ brand detection
→ citation/source analysis
→ visibility metrics
→ gap analysis
→ ranked report
→ client summary
```

---

### Claim

> Transforming raw LLM responses into ranked visibility reports with influence source attribution.

### Implementation evidence

- raw response storage
- normalized observations
- source analyzer
- metrics
- gap analyzer
- ranking
- report service

---

### Claim

> Packaged into one-page client summaries for technical and non-technical audiences.

### Implementation evidence

- `summary_service.py`
- client summary schema
- report summary endpoint

---

# 58. What the Project Demonstrates Technically

If implemented according to this specification, the project demonstrates:

- Python backend engineering
- FastAPI API development
- third-party API integration
- OpenAI integration
- Gemini integration
- provider abstraction
- asynchronous/concurrent requests
- structured JSON data pipelines
- text/entity matching
- LLM response analysis
- source/citation normalization
- metric computation
- deterministic scoring
- data lineage
- error handling
- retries and timeouts
- testing with mocked external APIs
- Dockerized deployment
- technical documentation
- conversion of technical output into client-facing artifacts

This is the intended engineering value of the project.

---

# 59. Future Extensions

Only after the MVP is stable:

## Scheduled audits

Run the same audit daily/weekly/monthly.

## Historical trends

Track:

```text
mention rate over time
recommendation rate over time
provider differences over time
source-domain changes over time
```

## Database backend

Replace JSON storage with PostgreSQL while keeping the storage interface unchanged.

## Dashboard

Add a frontend displaying:

- visibility metrics
- provider comparison
- topic comparison
- competitor observations
- source analysis
- historical trends

## More LLM providers

Add new implementations behind the same provider interface.

## Prompt libraries

Create reusable prompt packs by industry.

## Automated report export

Add PDF/HTML report generation.

## Batch audits

Run many brands/topics in controlled batches.

---

# 60. Final Architecture

The finished system should conceptually look like:

```text
                         ┌──────────────────────┐
                         │      FastAPI API     │
                         └──────────┬───────────┘
                                    │
                                    v
                         ┌──────────────────────┐
                         │    Audit Service     │
                         └──────────┬───────────┘
                                    │
                      ┌─────────────┴─────────────┐
                      v                           v
             ┌────────────────┐          ┌────────────────┐
             │ Prompt Builder │          │ Audit Config   │
             └───────┬────────┘          └────────────────┘
                     │
                     v
             ┌────────────────┐
             │ Query Service  │
             └───────┬────────┘
                     │
          ┌──────────┴──────────┐
          v                     v
 ┌─────────────────┐   ┌─────────────────┐
 │ OpenAI Provider │   │ Gemini Provider │
 └────────┬────────┘   └────────┬────────┘
          │                     │
          └──────────┬──────────┘
                     v
             ┌────────────────┐
             │ Raw Responses  │
             └───────┬────────┘
                     v
             ┌────────────────┐
             │Analysis Service│
             └───────┬────────┘
                     │
       ┌─────────────┼───────────────┐
       v             v               v
 ┌──────────┐ ┌─────────────┐ ┌──────────────┐
 │ Mentions │ │ Competitors │ │ Citations    │
 └────┬─────┘ └──────┬──────┘ └──────┬───────┘
      └──────────────┼───────────────┘
                     v
             ┌────────────────┐
             │   Observations │
             └───────┬────────┘
                     v
             ┌────────────────┐
             │ Metrics/Scoring│
             └───────┬────────┘
                     v
             ┌────────────────┐
             │  Gap Analysis  │
             └───────┬────────┘
                     v
             ┌────────────────┐
             │ Report Service │
             └───────┬────────┘
                     │
              ┌──────┴──────┐
              v             v
       ┌────────────┐ ┌──────────────┐
       │ JSON Report│ │Client Summary│
       └────────────┘ └──────────────┘
```

---

# 61. Implementation Agent Rules

Any coding agent implementing this repository should follow these rules:

1. **Read this README completely before writing code.**
2. Do not collapse the architecture into one giant file.
3. Do not put provider API calls inside FastAPI routes.
4. Do not put scoring inside provider implementations.
5. Do not discard raw LLM responses.
6. Do not fabricate citations or source URLs.
7. Do not use an LLM for deterministic tasks unless explicitly justified.
8. Keep provider-specific logic isolated.
9. Use typed models for application contracts.
10. Validate all API inputs.
11. Handle partial provider failures gracefully.
12. Add tests for every analytical component.
13. Mock external LLM APIs in tests.
14. Never require real API credentials to run the test suite.
15. Keep secrets out of source control and logs.
16. Make metrics mathematically explicit.
17. Make report observations traceable to raw evidence.
18. Record provider/model/analysis/scoring versions.
19. Prefer readable production code over clever code.
20. Write meaningful comments explaining non-obvious decisions, not comments that merely restate code.
21. Keep functions focused on one responsibility.
22. Use async I/O for network-bound provider calls where appropriate.
23. Bound concurrency.
24. Implement bounded retries with backoff for transient failures.
25. Do not add dependencies without a concrete reason.
26. Do not silently change the stack defined in this README.
27. If a requirement is ambiguous, preserve the architecture and document the assumption.
28. Do not claim functionality that is not implemented and tested.
29. Ensure the complete project can be demonstrated from a clean environment.
30. The final implementation should make every major resume claim demonstrable from actual running code.

---

# 62. Master Success Criterion

The finished repository should allow a reviewer to perform one complete demonstration:

```text
Define brand
      ↓
Define competitors/topics/prompts
      ↓
Select OpenAI + Gemini
      ↓
Run audit
      ↓
Observe raw LLM responses
      ↓
See target-brand mentions
      ↓
See mention context
      ↓
See competitor mentions
      ↓
See available citations/sources
      ↓
Calculate visibility metrics
      ↓
Identify visibility gaps
      ↓
Rank evidence-backed observations
      ↓
Generate structured report
      ↓
Generate one-page client summary
```

If that workflow works reliably, is tested, and every result is traceable to the underlying LLM response, the project satisfies the intended scope of the **LLM Brand Visibility Audit Tool**.

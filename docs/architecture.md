# Architecture Overview — LLM Brand Visibility Audit Tool

## 1. System Design Philosophy

The **LLM Brand Visibility Audit Tool** is built on five core architectural principles:
1. **Raw Evidence Preservation**: Raw responses from LLM providers are stored immutably before any parsing occurs. Derived metrics and report statements link directly back to the exact response ID.
2. **Strict Provider Abstraction**: LLM vendor specifics (OpenAI Chat Completions, Google Gemini Grounding Metadata) are encapsulated behind the `LLMProvider` interface. The auditing engine remains decoupled from external vendor APIs.
3. **Deterministic Analysis**: Brand entity matching, competitor detection, context window extraction, and gap identification use explainable, deterministic algorithms rather than non-deterministic second-pass LLM calls.
4. **Resilience & Partial Failure Isolation**: Queries execute with bounded concurrency and exponential backoff retries for transient failures. A single failed provider request does not fail the entire audit.
5. **No Fabricated Citations**: Missing citation or web grounding metadata is explicitly flagged (`NOT_SUPPORTED_BY_PROVIDER` or `NONE_FOUND`), rather than inventing URLs or source domains.

---

## 2. End-to-End Data Pipeline

```text
       Client Request / CLI
                 │
                 ▼
        ┌─────────────────┐
        │   FastAPI App   │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  AuditService   │
        └────────┬────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
┌──────────────┐   ┌─────────────────┐
│PromptBuilder │   │  QueryService   │
└──────────────┘   └────────┬────────┘
                            │ (Bounded Concurrency & Retries)
                 ┌──────────┴──────────┐
                 ▼                     ▼
         ┌───────────────┐     ┌───────────────┐
         │OpenAIProvider │     │GeminiProvider │
         └───────┬───────┘     └───────┬───────┘
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   RawLLMResponse    │ (Persisted to data/raw/)
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   AnalysisService   │
                 └──────────┬──────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│MentionDetector │ │ContextExtractor│ │CitationExtract.│
└────────────────┘ └────────────────┘ └────────────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ ResponseObservation │ (Persisted to data/processed/)
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
         ┌───────────────┐     ┌───────────────┐
         │MetricsCalc.   │     │  GapAnalyzer  │
         └───────┬───────┘     └───────┬───────┘
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    ReportService    │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
         ┌───────────────┐     ┌───────────────┐
         │  AuditReport  │     │ ClientSummary │
         └───────────────┘     └───────────────┘
```

---

## 3. Directory Layout & Layer Responsibilities

- **`app/api/`**: HTTP transport layer, request validation, response serialization, dependency injection.
- **`app/core/`**: Centralized configuration (`config.py`), structured JSON logging (`logging.py`), and domain exceptions (`exceptions.py`).
- **`app/models/`**: Strongly-typed Pydantic domain models for audits, responses, observations, metrics, and reports.
- **`app/providers/`**: Pluggable vendor adapters (`OpenAIProvider`, `GeminiProvider`) and factory registry.
- **`app/prompts/`**: Prompt builder with parameter injection, validation rules, and templates.
- **`app/analysis/`**: Analytical engines for mention detection, context window extraction, competitor identification, recommendation stance, and citation extraction.
- **`app/scoring/`**: Mathematical metrics calculations, deterministic 0-100 scoring, visibility gap analysis, and observation ranking.
- **`app/services/`**: Workflow orchestration (`AuditService`, `QueryService`, `AnalysisService`, `ReportService`, `SummaryService`).
- **`app/storage/`**: Persistence abstraction (`AuditStore`) and thread-safe JSON file-backed implementation (`JSONAuditStore`).

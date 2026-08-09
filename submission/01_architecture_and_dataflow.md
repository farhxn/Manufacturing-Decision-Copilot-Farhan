# Architecture and Data-Flow Explanation
## Manufacturing Decision Copilot

---

## 1. System Overview

Manufacturing Decision Copilot is an evidence-backed procurement intelligence platform. It helps manufacturing procurement teams select the best supplier for a component by combining **deterministic scoring engines** (pure Python math, fully reproducible) with **LLM-generated narrative explanations** backed by retrieved document evidence.

The core architectural principle is a strict separation of concerns:

| Layer | Responsibility | Technology |
|---|---|---|
| Rule Engines | All mathematics: scoring, ranking, cost, risk | Pure Python — no I/O, no AI |
| AI Layer | Explanation and summarisation only — never calculations | PydanticAI → Gemini / GPT-4o |
| Retrieval Layer | Find evidence in uploaded documents | ChromaDB + BM25 + RRF |
| Data Layer | Source of truth for structured data | PostgreSQL (async SQLAlchemy) |
| Vector Store | Semantic document index | ChromaDB |
| Task Queue | Async document processing | Celery + Redis |
| Frontend | Decision intelligence dashboard | Next.js 15 App Router |

---

## 2. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Browser / Next.js 15                   │
│  Dashboard · Suppliers · Documents · Scenarios · Reports│
└──────────────────────┬──────────────────────────────────┘
                       │  REST /api/v1  (HTTPS)
                       ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend  (Python 3.12)            │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  API Routes  │  │   Services   │  │ Repositories │  │
│  │  (validate   │→ │  (business   │→ │  (DB I/O     │  │
│  │   + route)   │  │   workflow)  │  │   only)      │  │
│  └──────────────┘  └──────┬───────┘  └──────┬───────┘  │
│                           │                 │           │
│                    ┌──────▼──────┐          │           │
│                    │   Engines   │          │           │
│                    │ (pure math) │          │           │
│                    │ cost/risk/  │          │           │
│                    │ quality/    │          │           │
│                    │ delivery/   │          │           │
│                    │ capability/ │          │           │
│                    │ compliance/ │          │           │
│                    │ ranking/    │          │           │
│                    │ scenario/   │          │           │
│                    │ confidence  │          │           │
│                    └──────┬──────┘          │           │
│                           │                 │           │
│                    ┌──────▼──────┐          │           │
│                    │  AI Layer   │          │           │
│                    │ PydanticAI  │          │           │
│                    │ + retriever │          │           │
│                    └─────────────┘          │           │
└─────────────────────────────────────────────┼───────────┘
                                              │
          ┌───────────────┬──────────────┬───▼───────────┐
          │               │              │               │
     ┌────▼────┐   ┌──────▼──┐   ┌──────▼──┐   ┌───────▼──┐
     │PostgreSQL│   │ ChromaDB│   │  Redis  │   │ Celery   │
     │(relational│  │(vectors)│   │(cache + │   │(document │
     │ truth)  │   │         │   │ queue)  │   │ worker)  │
     └─────────┘   └─────────┘   └─────────┘   └──────────┘
```

---

## 3. Component Descriptions

### 3.1 Frontend — Next.js 15 App Router

**Technology stack:** Next.js 15, TypeScript (strict), Tailwind CSS v4, shadcn/ui, TanStack Query v5, Recharts, Framer Motion, Zustand v5.

**Key pages and their purpose:**

| Page | Purpose |
|---|---|
| `/dashboard` | Hero decision view: animated score gauge, recommendation card, citation popovers, scenario simulator, supplier landscape table |
| `/suppliers` | Full supplier list with search, filter, sort |
| `/suppliers/[id]` | Supplier detail with risk breakdown, evidence panel |
| `/documents` | Upload zone, processing timeline, extraction status |
| `/scenarios` | Full scenario simulator with sensitivity sliders |
| `/reports` | Executive report generation and PDF download |

The dashboard is the **primary demo surface**. Within 5 seconds a user can see: recommended supplier, composite score, confidence level, evidence count, and risk summary.

### 3.2 FastAPI Backend

**Technology:** FastAPI 0.141.1, Python 3.12+, Pydantic v2, async SQLAlchemy 2+, Alembic.

**Architectural contract (strictly enforced):**
- Routes: validate input + call service only. Zero business logic.
- Services: business workflows. Call engines and repositories.
- Repositories: database I/O only. No logic, no calculations.
- Engines: pure Python functions. No I/O, no AI calls, no side effects.
- AI: called through services only. Never directly from routes.

**API surface (prefix `/api/v1`):**

| Router | Key Endpoints |
|---|---|
| `/health` | GET /health |
| `/suppliers` | GET list, GET {id}, POST, PATCH, DELETE, POST /compare |
| `/documents` | POST /upload, GET, GET {id}, GET {id}/chunks, GET /jobs/{id} |
| `/recommendations` | GET list, GET {project_id}, POST /regenerate |
| `/scenarios` | GET, POST, GET {id}, POST {id}/simulate, DELETE {id} |
| `/evidence` | GET by recommendation_id |
| `/reports` | POST /generate, GET, GET {id}/download |
| `/dashboard` | GET?project_id=... |

### 3.3 Scoring Engines (Deterministic — No AI)

All engines live in `backend/app/engines/` and are pure, stateless functions.

**Cost Engine:**
```
landed_cost = (quoted_price × material_multiplier
             + shipping × shipping_multiplier
             + duty + insurance + taxes) × currency_rate

cost_score = (min_landed_cost / supplier_landed_cost) × 100
```

**Quality Engine:**
```
quality_score = defect_component × 0.40
              + inspection_pass_rate × 0.35
              + customer_rating_normalised × 0.25
```

**Delivery Engine:**
```
delivery_score = lead_time_component × 0.45
               + on_time_delivery_pct × 0.35
               + production_capacity_pct × 0.20

lead_time_component = (min_lead_time / supplier_lead_time) × 100
```

**Risk Engine:**
```
risk_score = 100 - (financial_risk  × 0.25
                  + country_risk    × 0.20
                  + supply_risk     × 0.20
                  + compliance_risk × 0.20
                  + capacity_risk   × 0.15)
  clamped to [0, 100]
```
*Note: DB stores safety scores (higher = safer). The mapper inverts them to risk magnitudes before calling this engine.*

**Compliance Engine:**
```
if any required_cert not in supplier_certs:
    compliance_score = 0.0   ← auto-disqualification
else:
    compliance_score = 100.0
```
Certificate matching supports prefix matching (e.g., `"ISO 9001"` matches `"ISO 9001:2015"`) while blocking overly broad family matches.

**Capability Engine:**
```
capability_score = match_score × 0.70
                 + capacity_pct × 0.30
                 + (10 if engineering_support else 0)

match_score = (required_capabilities_matched / total_required) × 100
```

**Ranking Engine (`score_suppliers`):**
```
final_score = cost_score       × 0.30
            + quality_score    × 0.20
            + delivery_score   × 0.15
            + risk_score       × 0.15
            + capability_score × 0.10
            + compliance_score × 0.10
  clamped to [0, 100]
```
Weights are configurable per project. All suppliers sorted descending; disqualified suppliers (unavailable or zero compliance) ranked last with zeroed scores.

**Confidence Engine (Deterministic — Never the LLM):**
```
confidence = extraction_quality × 0.30
           + evidence_coverage  × 0.20
           + retrieval_quality  × 0.20
           + rule_agreement     × 0.20
           + data_completeness  × 0.10
  → 0.0–1.0 → displayed as % with Low / Medium / High label
```

### 3.4 Scenario Engine

Wraps the Ranking Engine with a `ScenarioConfig`:

```python
ScenarioConfig:
  shipping_multiplier       float    # e.g. 1.4 for +40% shipping
  currency_rate             float    # spot rate override
  demand_multiplier         float    # scales required capacity
  lead_time_adjustment_days int      # global offset
  supplier_availability     dict     # disable specific suppliers
  certification_overrides   dict     # simulate cert loss
  material_cost_multiplier  float    # commodity price shock
  import_duty_rate          float|None  # override per-country duty
```

The engine runs the full ranking pipeline twice (baseline + scenario), compares rankings, detects winner changes, then asks the AI to explain what changed in plain English. The AI explanation is the **only AI call in this flow** — the delta calculation is pure Python.

### 3.5 AI Layer

**Provider:** PydanticAI agent framework. Default provider: Gemini 2.0 Flash (free tier). Fallbacks: GPT-4o, Groq Llama-3.3-70b, Ollama (offline).

**Five typed agents:**

| Agent | Output Schema | Use |
|---|---|---|
| RecommendationAgent | `RecommendationOutput` | Explains the top supplier choice with pros, cons, tradeoffs, risks, next actions |
| ScenarioExplainerAgent | `ScenarioExplanation` | Explains what changed after a scenario simulation |
| ExecutiveSummaryAgent | `ExecutiveSummary` | Board-ready summary for report generation |
| ComparisonAgent | `ComparisonOutput` | Head-to-head supplier comparison |
| ExtractionAgent | `SupplierExtraction` | Structured data extraction from uploaded PDF chunks |

All agents receive **pre-sanitised evidence chunks** from the retriever — never raw document text. Every output is validated against its Pydantic schema; schema violations trigger fallback to cached results.

### 3.6 Hybrid Retrieval (RAG Pipeline)

```
Query string
    │
    ├─► text-embedding-3-small / bge-small-en-v1.5
    │         ▼
    ├─► ChromaDB cosine similarity → top 20 chunks
    │         (filtered by project_id + optional supplier_id)
    │
    ├─► BM25Okapi keyword search on same candidates → top 20
    │
    ├─► Reciprocal Rank Fusion (k=60)
    │       score = Σ 1/(k + rank_in_list)
    │         ▼
    └─► Deduplicated, top-K (default 8) RankedChunks
```

**Self-RAG Loop Engineering:** `retrieve_with_loop()` runs up to 3 iterations. After each pass, coverage is checked (average RRF score). If coverage < 0.025 and < 3 chunks, an LLM grader assesses sufficiency and returns a refined query. The loop stops when evidence is sufficient, coverage threshold is met, or `MAX_LOOPS=3` is reached.

### 3.7 Prompt Injection Guardrails

All document text is treated as untrusted. Before any chunk is sent to the LLM, `sanitize_for_llm()` strips 7 injection pattern types:

1. `ignore previous instructions` variants
2. `you are now [different role]` variants
3. `new/revised instructions:` variants
4. `print/reveal/show your system prompt` variants
5. XML role injection tags (`<system>`, `<user>`, etc.)
6. `act as [role]` variants
7. DAN / jailbreak / unfiltered keywords

Maximum chunk size enforced at 4,000 characters (truncated with `[TRUNCATED]` marker).

Additionally, `filter_evidence_ids()` removes any evidence ID in the LLM output that was not in the retrieved set, preventing hallucinated document references.

### 3.8 Document Processing Pipeline

```
POST /documents/upload
    │
    ├─ MIME validation (python-magic, not extension)
    ├─ Size check (< 50 MB)
    ├─ SHA-256 checksum recorded
    ├─ Save to /uploads/{uuid}.ext
    ├─ Create document record → status: uploaded
    └─ Enqueue Celery task → return {document_id, job_id}

Celery Worker:
    1. Extract text       PyMuPDF (PDF) / python-docx / openpyxl
    2. OCR fallback       pytesseract (if no text layer)
    3. Semantic chunking  section-aware, max 800 tokens, 50-token overlap
    4. Batch embeddings   text-embedding-3-small or bge-small-en-v1.5
    5. Store in ChromaDB  with metadata: {document_id, project_id,
                          supplier_id, page_number, section_name,
                          document_type, extraction_confidence}
    6. PydanticAI extraction → SupplierExtraction → PostgreSQL
    7. Update job status → complete
    8. Invalidate Redis caches

Frontend: GET /jobs/{id} every 2 seconds → 0–100% progress bar
```

---

## 4. Primary Data Flow — End-to-End Hero Path

```
1.  Analyst uploads supplier PDF quotations via the document upload page.

2.  Backend validates MIME type + size, saves to /uploads/{uuid}.pdf,
    creates a document record, and enqueues a Celery processing job.

3.  Celery worker:
      a. Extracts text with PyMuPDF.
      b. Chunks text into 800-token semantic sections.
      c. Embeds each chunk with text-embedding-3-small.
      d. Stores chunks + embeddings in ChromaDB (document_chunks collection).
      e. Runs ExtractionAgent → stores structured fields in PostgreSQL.

4.  Frontend polls /jobs/{id} until complete; dashboard refreshes.

5.  Analyst clicks "Get Recommendation" on the dashboard.

6.  RecommendationService:
      a. Loads all Supplier records + SupplierRiskScores from PostgreSQL.
      b. Maps DB rows to SupplierInput dataclasses.
      c. Calls score_suppliers() → pure deterministic ranking.
      d. Runs retrieve_with_loop() to fetch evidence chunks from ChromaDB
         (hybrid BM25 + vector + RRF, up to 3 retrieval iterations).
      e. Calls sanitize_for_llm() on all chunks.
      f. Calls RecommendationAgent.run(evidence + scores).
      g. Filters hallucinated evidence_ids.
      h. Calls calculate_confidence() → deterministic confidence score.
      i. Stores Recommendation + RecommendationEvidence in PostgreSQL.
      j. Caches result in Redis (TTL 5 min).

7.  Dashboard renders:
      - Animated DonutGauge with composite score
      - Recommendation card with AI narrative, pros/cons/tradeoffs
      - CitationPopover on each data point → links to PDF page + chunk
      - SupplierLandscape table with all ranked suppliers
      - Confidence score badge (deterministic number, AI narrative text)

8.  Analyst runs "Shipping +40%" scenario:
      a. Frontend sends ScenarioConfig to POST /scenarios/{id}/simulate.
      b. ScenarioEngine recalculates all scores with shipping_multiplier=1.4.
      c. ScenarioExplainerAgent explains the ranking change in plain English.
      d. Frontend renders before/after comparison with score deltas.

9.  Analyst generates executive report:
      a. ExecutiveSummaryAgent produces board-ready narrative.
      b. @react-pdf/renderer renders PDF client-side.
      c. PDF includes: recommendation, evidence citations, risk summary,
         scenario sensitivity analysis, next steps, and AI disclaimer.
```

---

## 5. Database Schema Summary

### PostgreSQL (source of truth)

| Table group | Tables |
|---|---|
| Foundation | `organizations`, `users`, `projects` |
| Suppliers | `suppliers`, `supplier_capabilities`, `supplier_certifications`, `supplier_prices`, `supplier_risk_scores` |
| Documents | `documents`, `document_chunks`, `extracted_fields` |
| AI Outputs | `recommendations`, `recommendation_evidence`, `decision_traces` |
| Scenarios | `scenarios`, `scenario_results` |
| Reports & Audit | `reports`, `ai_requests`, `ai_responses`, `audit_logs` |

### ChromaDB

| Collection | Purpose | Key metadata fields |
|---|---|---|
| `document_chunks` | Semantic retrieval index | `document_id`, `project_id`, `supplier_id`, `page_number`, `section_name`, `document_type`, `extraction_confidence` |

### Redis

| Key pattern | Purpose | TTL |
|---|---|---|
| `job:{job_id}` | Document processing progress | 24 h |
| `recommendation:{project_id}` | Cached recommendation | 5 min |
| `dashboard:{project_id}` | Cached dashboard payload | 2 min |
| `supplier_scores:{project_id}` | Cached ranking | 5 min |

---

## 6. Deployment Topology

| Component | Platform | Notes |
|---|---|---|
| Frontend | Vercel | Next.js native deployment |
| Backend + Celery Worker | Railway | Same image, different process commands |
| PostgreSQL | Supabase / Railway | Managed Postgres 16+ |
| Redis | Upstash | Serverless Redis, free tier |
| ChromaDB | Railway volume | Persistent directory mount |
| File uploads | Railway volume | `/tmp/uploads` directory |

---

## 7. Security Boundaries

- All document content treated as untrusted (prompt injection stripping before any LLM call).
- UUID-based file storage (no user-controlled paths).
- MIME validation server-side (not extension-based).
- SHA-256 checksums recorded for challenge pack files.
- Pydantic schema validation on all LLM outputs; schema violation triggers deterministic fallback.
- Evidence IDs in LLM output filtered against the actual retrieved set (prevents hallucinated references reaching the database).
- API keys stored in `.env` only; never logged or returned in responses.

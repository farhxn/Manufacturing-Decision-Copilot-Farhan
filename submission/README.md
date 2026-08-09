# Hackathon Submission
## Manufacturing Decision Copilot
### Track: Manufacturing Procurement Intelligence

---

## What We Built

**Manufacturing Decision Copilot** is an evidence-backed procurement intelligence platform that helps manufacturing teams select the right supplier — and explain why — in seconds rather than hours.

It replaces manual spreadsheet comparison with a system that:
- Ingests supplier quotations, certificates, and audit documents via a PDF processing pipeline
- Scores every supplier across 6 dimensions using deterministic rule engines (pure Python, no AI in the math)
- Retrieves supporting evidence from documents using hybrid BM25 + vector + Reciprocal Rank Fusion retrieval
- Generates an AI narrative explanation backed by cited document chunks (never invented facts)
- Simulates "what-if" scenarios (shipping shocks, tariff changes, supplier removal) in under 2 milliseconds
- Produces a board-ready PDF executive report with a single click

The core design principle: **AI explains. Math decides. Humans approve.**

---

## Submission Checklist

Every item required by the submission brief is addressed in the documents below.

| # | Required Deliverable | Document | Status |
|---|---|---|---|
| 1 | Working end-to-end prototype for one primary track | [Setup instructions](#3-setup-and-run) + live demo | ✅ |
| 2 | Source code and reproducible setup instructions | [Setup instructions](#3-setup-and-run) + `02_data_source_manifest.md §5` | ✅ |
| 3 | Concise architecture and data-flow explanation | [`01_architecture_and_dataflow.md`](01_architecture_and_dataflow.md) | ✅ |
| 4 | Data/source manifest covering challenge pack and external inputs | [`02_data_source_manifest.md`](02_data_source_manifest.md) | ✅ |
| 5 | Baseline comparison and quantitative evaluation results | [`03_evaluation_results.md`](03_evaluation_results.md) | ✅ |
| 6 | Demonstration of success, ambiguous, and failure/fallback cases | [`04_case_demonstrations.md`](04_case_demonstrations.md) | ✅ |
| 7 | Intended-user statement, assumptions, limitations, human-approval points | [`05_users_assumptions_limitations.md`](05_users_assumptions_limitations.md) | ✅ |
| 8 | Short presentation explaining decision, evidence, and business value | [`06_presentation_script.md`](06_presentation_script.md) | ✅ |

---

## Submission Documents

### [01 — Architecture and Data-Flow](01_architecture_and_dataflow.md)
Full system architecture: component descriptions, the 9 deterministic scoring engines with their exact formulas, the hybrid RAG pipeline (ChromaDB + BM25 + RRF + Self-RAG loop), the Celery document processing pipeline, the 5 PydanticAI agents, prompt injection guardrails, database schema summary, and deployment topology.

### [02 — Data and Source Manifest](02_data_source_manifest.md)
Complete inventory of: 17 challenge pack documents with their purpose and extraction targets; all 10 supplier master records with landed cost, risk scores, and certification tables; the 3 scenario definitions; all external AI/embedding services used and what data is sent to them; ChromaDB chunk metadata schema; and step-by-step reproducible setup instructions.

### [03 — Baseline Comparison and Quantitative Evaluation Results](03_evaluation_results.md)
Live engine output for all three scenarios with actual scores from the running code. Includes: full 10-supplier baseline ranking table with all 6 dimension scores; Shipping Shock (+40%) scenario with score deltas; China Tariff (+50%) scenario with winner change; human-vs-system comparison table; performance benchmarks (501 unit tests, all passing; ranking engine ~2ms vs 50ms target); and complete test coverage summary by module.

### [04 — Case Demonstrations](04_case_demonstrations.md)
Three required demonstration cases:
- **Case 1 — Success:** FastTrack Manufacturing scores 93.37 with 87.6% High confidence. Single-pass evidence retrieval. All dimension scores populated from document data. Fully auditable, immediately actionable recommendation.
- **Case 2 — Ambiguous:** FastTrack vs Acme Precision — 1.48-point gap. AS9100D hidden disqualifier surfaces. Confidence drops to ~72% Medium. System names the conflict, quantifies tradeoffs, and triggers sensitivity banner rather than presenting false certainty.
- **Case 3 — Failure/Fallback:** PeakMetal Solutions — expired ISO 9001 cert detected, compliance_score = 0, supplier ranked #10. System explains the specific failure (cert name, issuer, expiry date), suggests a cert-override scenario path, and continues ranking all other suppliers normally. Redis fallback documented.

### [05 — Intended Users, Assumptions, Limitations, and Human-Approval Points](05_users_assumptions_limitations.md)
Four intended user profiles (Procurement Manager, Manufacturing Engineer, Operations Manager, Executive). Three assumption categories (data quality, scoring model, AI behaviour). Three limitation categories (data, AI, operational). Seven numbered Human-Approval Points (HAP-1 through HAP-7): supplier onboarding, compliance disqualification, low confidence, narrow margin, scenario winner change, report review before distribution, and final PO issuance. Explicit "What the System Will Not Do" list.

### [06 — Presentation Script and Slide Notes](06_presentation_script.md)
Full 7-minute presentation script with per-slide speaker notes, 4 live demo beats with exact UI actions and narration, business value framing, and 6 prepared Q&A answers (hallucination prevention, API fallback, FastTrack win rationale, confidence formula, scalability). Pre-demo 10-item checklist included.

---

## 3. Setup and Run

Full instructions are in [`02_data_source_manifest.md §5`](02_data_source_manifest.md). Quick reference:

```bash
# Prerequisites: Python 3.12+, Node.js 18+, PostgreSQL 16+, Redis 7+

# Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # add GEMINI_API_KEY and DATABASE_URL
alembic upgrade head

# Seed database (10 suppliers, 3 scenarios, 17 document records)
cd ..
python scripts/seed_db_production.py

# Generate sample PDFs
python scripts/generate_production_pdfs.py

# Start backend + worker (two terminals)
cd backend
uvicorn app.main:app --reload --port 8000
celery -A app.workers.celery_app worker --loglevel=info

# Frontend
cd frontend
npm install && npm run dev    # http://localhost:3000

# Verify
curl http://localhost:8000/api/v1/health
```

**Minimum required to run the demo:** `GEMINI_API_KEY` (free from [Google AI Studio](https://aistudio.google.com)) and a PostgreSQL connection string. The embedding model (`BAAI/bge-small-en-v1.5`) runs locally — no OpenAI key is needed for embeddings.

---

## 4. Repository Structure

```
SGTDP/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers (suppliers, documents,
│   │   │                    #   recommendations, scenarios, reports,
│   │   │                    #   evidence, dashboard, health)
│   │   ├── engines/         # 9 pure-Python deterministic engines
│   │   │   ├── cost.py      #   landed cost + cost score
│   │   │   ├── quality.py   #   defect rate, inspection, rating
│   │   │   ├── delivery.py  #   lead time, on-time %, capacity
│   │   │   ├── risk.py      #   5-factor weighted risk + breakdown
│   │   │   ├── compliance.py#   cert check + auto-disqualification
│   │   │   ├── capability.py#   capability match + engineering bonus
│   │   │   ├── confidence.py#   5-factor confidence score
│   │   │   ├── ranking.py   #   orchestrator: score_suppliers()
│   │   │   ├── scenario.py  #   ScenarioConfig → ScenarioResult
│   │   │   └── types.py     #   shared dataclasses
│   │   ├── ai/
│   │   │   ├── client.py    #   PydanticAI multi-provider LLM client
│   │   │   ├── embeddings.py#   pluggable embedding provider
│   │   │   ├── retriever.py #   hybrid retrieval + Self-RAG loop
│   │   │   ├── reranker.py  #   RankedChunk + RRF fusion
│   │   │   ├── guardrails.py#   injection stripping + output validation
│   │   │   ├── schemas.py   #   5 Pydantic output schemas
│   │   │   └── prompts/v1/  #   prompt templates per agent
│   │   ├── core/            #   config, logging, dependencies
│   │   ├── database/        #   PostgreSQL session, ChromaDB client
│   │   ├── models/          #   SQLAlchemy ORM models
│   │   ├── services/        #   business workflow layer
│   │   └── workers/         #   Celery document processing pipeline
│   ├── alembic/             #   database migrations
│   ├── tests/
│   │   ├── unit/            #   501 tests across all 9 engines + AI layer
│   │   ├── smoke_phase*.py  #   smoke tests per build phase
│   │   └── integration/     #   API integration tests
│   └── requirements.txt
├── frontend/
│   └── src/app/
│       ├── dashboard/       #   hero decision intelligence view
│       ├── suppliers/       #   supplier list + detail pages
│       ├── documents/       #   upload zone + PDF viewer
│       ├── scenarios/       #   full scenario simulator
│       └── reports/         #   executive report generation
├── scripts/
│   ├── seed_db_production.py    # seeds 10 suppliers + 3 scenarios
│   └── generate_production_pdfs.py
├── docs/                    # 22 specification documents
├── submission/              # ← this directory (all 7 deliverables)
└── .agents/rules/           # project constraints enforced by Kiro
```

---

## 5. Key Technical Facts

| Fact | Detail |
|---|---|
| Primary language | Python 3.12 (backend), TypeScript strict (frontend) |
| API framework | FastAPI 0.141.1 with Pydantic v2 |
| Frontend framework | Next.js 15 App Router |
| Default LLM provider | Google Gemini 2.0 Flash (free tier) |
| Fallback LLM providers | OpenAI GPT-4o · Groq Llama-3.3-70b · Ollama (offline) |
| Default embedding model | BAAI/bge-small-en-v1.5 (local, 384-dim, no API key) |
| Vector database | ChromaDB 0.5.23 (cosine similarity, HNSW) |
| Relational database | PostgreSQL 16+ via asyncpg + SQLAlchemy 2+ |
| Task queue | Celery 5 + Redis 7 |
| Retrieval strategy | Hybrid: ChromaDB cosine + BM25Okapi + RRF (k=60) |
| Self-RAG loop | Up to 3 iterations; LLM grader refines query if coverage < 0.025 |
| Scoring engines | 9 pure Python engines, zero I/O, zero AI |
| Unit tests | 501 tests, 0 failures (2.50 s runtime) |
| Ranking latency | ~2 ms for 10 suppliers (target was 50 ms) |
| Injection patterns blocked | 7 (ignore_previous, you_are_now, new_instructions, system_prompt_leak, role_injection, act_as, jailbreak_dan) |
| AI output schemas | 5 (RecommendationOutput, ScenarioExplanation, ExecutiveSummary, ComparisonOutput, SupplierExtraction) |
| Confidence engine | Deterministic 5-factor formula — LLM never produces a confidence number |

---

## 6. The One-Sentence Business Case

Manufacturing Decision Copilot turns a 3-hour manual procurement evaluation into a 30-second evidence-backed recommendation that every stakeholder can read, challenge, and approve with confidence.

# Manufacturing Decision Copilot

> **AI explains. Math decides. Humans approve.**

An evidence-backed procurement intelligence platform that turns 10 supplier quotations, certificates, and audit documents into a clear, auditable, confidence-scored recommendation — in under 30 seconds.

---

## Live Application

| | |
|---|---|
| **Dashboard** | https://manufacturing-decision-copilot-farhan.vercel.app/dashboard |
| **Suppliers** | https://manufacturing-decision-copilot-farhan.vercel.app/suppliers |
| **Scenarios** | https://manufacturing-decision-copilot-farhan.vercel.app/scenarios |
| **Documents** | https://manufacturing-decision-copilot-farhan.vercel.app/documents |
| **Reports** | https://manufacturing-decision-copilot-farhan.vercel.app/reports |

The live app is pre-seeded with 10 suppliers across 7 countries, 17 challenge-pack documents, and 3 pre-configured scenarios. The recommendation, scenario engine, evidence citations, and confidence score are all live and interactive.

---

## What the Dashboard Shows

When you open the live dashboard you see:

**Recommendation Card** — Animated composite score gauge (0–100), winner name, confidence badge (High/Medium/Low), AI-generated narrative with pros, cons, tradeoffs, and risks. Every data point is a clickable citation — tap any number to see the exact PDF page and paragraph it came from.

**Score Breakdown** — Six-dimension bar chart: cost · quality · delivery · risk · capability · compliance. Each bar shows the raw score and its weighted contribution to the final ranking.

**Supplier Landscape Table** — All 10 suppliers ranked, with compliance flags highlighted. Suppliers with missing or expired certifications show compliance = 0 in red. AlphaForge (zero certs) and PeakMetal (expired ISO cert) are visible at the bottom with the exact reason surfaced.

**Scenario Simulator** — Drag the shipping-cost slider to +40% and watch rankings recalculate in real time. FastTrack Manufacturing (Mexico) is the only supplier whose score *increases* because its $4 truck freight is nearly immune to maritime shipping shocks. The AI explains the change in plain English below the chart.

**Confidence Breakdown** — Deterministic 5-factor confidence score (extraction quality, evidence coverage, retrieval quality, rule agreement, data completeness). The LLM never produces this number.

---

## Key Numbers at a Glance

| Metric | Value |
|---|---|
| Suppliers evaluated | 10 across 7 countries |
| Challenge pack documents | 17 (quotations, certificates, audit report, tech spec) |
| Composite score — winner (FastTrack Manufacturing) | **93.37 / 100** |
| Composite score — runner-up (Acme Precision Mfg) | **91.89 / 100** |
| Confidence — winner | **87.6% — High** |
| Ranking engine latency | **~2 ms** (target was 50 ms) |
| Unit tests | **501 passing, 0 failures** |
| Injection patterns blocked | **7** |
| Scoring engines | **9** (all pure Python, zero AI) |
| PydanticAI output schemas | **5** (all Pydantic v2 validated) |
| Suppliers auto-disqualified by compliance | **2** (AlphaForge: zero certs · PeakMetal: expired cert) |

---

## Baseline Ranking — Live Engine Output

Scores produced by running `score_suppliers()` on the seeded dataset. Reproducible with `python scripts/seed_db_production.py && pytest tests/unit/`.

| Rank | Supplier | Country | Score | Landed Cost | Compliance |
|---|---|---|---|---|---|
| **1** | **FastTrack Manufacturing** | Mexico | **93.37** | $112.00 | ✅ ISO+RoHS+IATF |
| 2 | Acme Precision Mfg | Germany | 91.89 | $121.75 | ✅ ISO+AS9100D+RoHS |
| 3 | NovaCast Engineering | Poland | 90.61 | $117.95 | ✅ ISO+AS9100D |
| 4 | VoltEdge Components | South Korea | 87.60 | $132.48 | ✅ ISO+IATF |
| 5 | TechForge Industries | Taiwan | 84.74 | $139.54 | ✅ ISO+RoHS |
| 6 | Reliable Parts Co | India | 83.32 | $133.07 | ✅ ISO+IATF |
| 7 | AlphaForge Ltd | Canada | 79.77 | $107.30 | ❌ Zero certs → compliance = 0 |
| 8 | SteelPath Industries | Brazil | 79.52 | $121.28 | ✅ ISO only |
| 9 | Global Fabrication Ltd | China | 77.02 | $146.25 | ✅ ISO only (highest landed cost) |
| 10 | PeakMetal Solutions | Vietnam | 70.02 | $108.10 | ❌ Expired ISO → compliance = 0 |

> AlphaForge has the cheapest landed cost ($107.30) but zero certifications → compliance_score = 0 → ranked #7.
> PeakMetal has the second-cheapest landed cost ($108.10) but an expired ISO cert → ranked last.
> Global Fabrication has the cheapest unit price ($89) but 25% US duty pushes landed cost to the highest in the field ($146.25).

---

## Scenario Engine — Shipping Shock +40%

When international shipping costs rise 40% (Red Sea–style disruption) and lead times extend 7 days:

| Supplier | Score Change | Why |
|---|---|---|
| FastTrack Manufacturing | **+0.15** (only supplier to go up) | $4 truck freight — 40% of $4 is $1.60 extra |
| Acme Precision Mfg | −0.82 | $22 air freight — 40% of $22 is $8.80 extra |
| PeakMetal Solutions | −2.04 (largest drop) | High base shipping $30 + worst delivery metrics |

The near-shore thesis is proven in real time: Mexico (FastTrack) and Poland (NovaCast) gain structural advantage under freight stress. [Test this live on the Scenarios page →](https://manufacturing-decision-copilot-farhan.vercel.app/scenarios)

---

## Three Demonstration Cases

### Case 1 — Success (FastTrack Manufacturing)
Clear #1 winner at 93.37 with 87.6% High confidence. Evidence retrieval completes in a single loop. All 4 evidence chunks trace to exact PDF pages. Recommendation is fully auditable and immediately actionable.

### Case 2 — Ambiguous (FastTrack vs Acme — 1.48-point gap)
FastTrack wins mathematically but Acme holds AS9100D aerospace certification that FastTrack lacks. The system detects this, drops confidence to ~72% Medium, surfaces the hidden disqualifier in the recommendation's `risks` and `assumptions` fields, and shows a one-click test: adding AS9100D as a required cert inverts the winner.

### Case 3 — Failure/Fallback (PeakMetal Solutions — expired cert)
PeakMetal's ISO 9001 expired December 2024. The system automatically detects `is_valid=False`, scores compliance = 0, ranks it last, shows the specific cert name/issuer/expiry in the UI, and suggests a cert-override scenario showing it would rise to ~#3 if recertified. Redis fallback delivers the deterministic ranking if the LLM is unavailable.

---

## Architecture

```
Browser / Next.js 15  (Vercel)
    │  REST /api/v1
    ▼
FastAPI 0.141  (Railway)
    ├── Routes         validate + call service (zero business logic)
    ├── Services       business workflow orchestration
    ├── Repositories   DB I/O only
    ├── Engines ──────────────────────────── pure Python, no AI, no I/O
    │   cost · quality · delivery · risk
    │   compliance · capability · ranking
    │   scenario · confidence
    ├── AI Layer  ────────────────────────── explanation only, never scores
    │   PydanticAI → Gemini 2.0 Flash / GPT-4o / Groq / Ollama
    │   Hybrid retrieval: ChromaDB cosine + BM25 + RRF + Self-RAG loop
    │   Guardrails: 7 injection patterns stripped; Pydantic v2 schema enforcement
    └── Workers        Celery + Redis
                       PDF → chunks → embeddings → ChromaDB → extraction → PostgreSQL

Databases
  PostgreSQL 16   source of truth
  ChromaDB 0.5    vector index (HNSW cosine, 384-dim bge-small-en-v1.5)
  Redis 7         job queue + recommendation cache (TTL 5 min)
```

---

## Scoring Formula

```
final_score = cost_score       × 0.30   ← deterministic engine, no AI
            + quality_score    × 0.20
            + delivery_score   × 0.15
            + risk_score       × 0.15
            + capability_score × 0.10
            + compliance_score × 0.10   ← 0 if any required cert missing/expired

risk_score  = 100 − (financial×0.25 + country×0.20 + supply×0.20
                   + compliance×0.20 + capacity×0.15)

confidence  = extraction_quality×0.30 + evidence_coverage×0.20
            + retrieval_quality×0.20  + rule_agreement×0.20
            + data_completeness×0.10   ← LLM never produces this number
```

All weights are configurable per project. The LLM never reads, modifies, or influences any score.

---

## Submission Documents

The complete submission package is in the `submission/` directory:

| Document | Content |
|---|---|
| [`SUBMISSION_REPORT.pdf`](submission/SUBMISSION_REPORT.pdf) | **Full PDF report — all sections, live engine data, formulas, cases, architecture** |
| [`01_architecture_and_dataflow.md`](submission/01_architecture_and_dataflow.md) | System architecture, 9 engine formulas, RAG pipeline, guardrails, DB schema |
| [`02_data_source_manifest.md`](submission/02_data_source_manifest.md) | 17 documents, 10 supplier records, 3 scenarios, external services, setup guide |
| [`03_evaluation_results.md`](submission/03_evaluation_results.md) | Live engine output — all 3 scenarios, 501 test results, benchmarks |
| [`04_case_demonstrations.md`](submission/04_case_demonstrations.md) | Success · Ambiguous · Failure/Fallback cases with full score walkthroughs |
| [`05_users_assumptions_limitations.md`](submission/05_users_assumptions_limitations.md) | 4 user types, 7 Human-Approval Points, limitations, system boundaries |
| [`06_presentation_script.md`](submission/06_presentation_script.md) | 7-minute script, 4 demo beats, 6 Q&A answers, pre-demo checklist |

---

## Setup and Run

```bash
# Prerequisites: Python 3.12+, Node.js 18+, PostgreSQL 16+, Redis 7+

# Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # set GEMINI_API_KEY + DATABASE_URL
alembic upgrade head

# Seed (10 suppliers, 3 scenarios, 17 document records)
cd ..
python scripts/seed_db_production.py
python scripts/generate_production_pdfs.py

# Start
cd backend
uvicorn app.main:app --reload --port 8000
# separate terminal:
celery -A app.workers.celery_app worker --loglevel=info

# Frontend
cd frontend && npm install && npm run dev
# Open http://localhost:3000/dashboard

# Verify
curl http://localhost:8000/api/v1/health
pytest tests/unit/ -q    # → 501 passed in 2.50s
```

**Minimum required:** `GEMINI_API_KEY` (free — [Google AI Studio](https://aistudio.google.com)) and a PostgreSQL connection string. The default embedding model (`BAAI/bge-small-en-v1.5`) runs fully locally — no OpenAI key needed.

---

## Repository Structure

```
SGTDP/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI routers
│   │   ├── engines/         # 9 pure-Python deterministic engines
│   │   ├── ai/              # PydanticAI agents, retriever, guardrails
│   │   ├── core/            # config, logging, dependencies
│   │   ├── database/        # PostgreSQL session, ChromaDB client
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── services/        # business workflow layer
│   │   └── workers/         # Celery document processing pipeline
│   ├── alembic/             # database migrations
│   ├── tests/
│   │   ├── unit/            # 501 tests across all engines + AI layer
│   │   ├── smoke_phase*.py  # smoke tests per build phase
│   │   └── integration/     # API integration tests
│   └── requirements.txt
├── frontend/
│   └── src/app/
│       ├── dashboard/       # hero decision intelligence view
│       ├── suppliers/       # supplier list + detail pages
│       ├── documents/       # upload zone + PDF viewer
│       ├── scenarios/       # full scenario simulator
│       └── reports/         # executive report generation
├── scripts/
│   ├── seed_db_production.py         # seeds 10 suppliers + 3 scenarios
│   ├── generate_production_pdfs.py   # generates challenge pack PDFs
│   └── generate_submission_report.py # generates submission/SUBMISSION_REPORT.pdf
├── docs/                    # 22 specification documents (gitignored)
├── sample-data/             # challenge pack PDFs (gitignored)
├── submission/              # hackathon submission documents
└── .agents/                 # Kiro agent rules (gitignored)
```

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| API | FastAPI | 0.141.1 |
| Runtime | Python | 3.12+ |
| Frontend | Next.js App Router | 15+ |
| UI | shadcn/ui + Tailwind CSS | v4 |
| LLM (default) | Gemini 2.0 Flash | google-genai 0.1 |
| LLM (fallback) | GPT-4o · Groq · Ollama | — |
| Embeddings | BAAI/bge-small-en-v1.5 | local, 384-dim |
| AI Orchestration | PydanticAI | 0.0.14+ |
| Vector DB | ChromaDB | 0.5.23 |
| Relational DB | PostgreSQL | 16+ |
| Task Queue | Celery + Redis | 5.4 / 5.2 |
| ORM + Migrations | SQLAlchemy async + Alembic | 2.0 / 1.14 |
| PDF Parsing | PyMuPDF | 1.24.14 |
| Keyword Search | rank-bm25 BM25Okapi | 0.2.2 |
| Testing | pytest | 8.3.4 |

---

*The PDF report at [`submission/SUBMISSION_REPORT.pdf`](submission/SUBMISSION_REPORT.pdf) contains every section above plus live-generated score tables, architecture diagrams, and full formula documentation in a single printable document.*

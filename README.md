<div align="center">

# 🏭 Manufacturing Decision Copilot
### *Autonomous Procurement Intelligence & Evidence-Backed Decision Engine*

[![Production Status](https://img.shields.io/badge/Status-Live_Production-4F7868?style=for-the-badge&logo=vercel&logoColor=white)](https://manufacturing-decision-copilot-farhan.vercel.app/dashboard)
[![Python Version](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 15](https://img.shields.io/badge/Frontend-Next.js_15-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![PydanticAI](https://img.shields.io/badge/AI_Engine-PydanticAI-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://ai.pydantic.dev/)
[![Tests](https://img.shields.io/badge/Unit_Tests-501_Passing-success?style=for-the-badge&logo=pytest&logoColor=white)](#-key-numbers-at-a-glance)

---

### 💡 **The Core Thesis**
> **🤖 AI Explains. &nbsp; 🧮 Math Decides. &nbsp; 👤 Humans Approve.**

*Turns 10 supplier quotations, certificates, and audit documents into a clear, auditable, confidence-scored recommendation in **under 30 seconds**.*

[🚀 Open Live App](https://manufacturing-decision-copilot-farhan.vercel.app/dashboard) &nbsp;•&nbsp; [📄 Executive PDF Report](submission/SUBMISSION_REPORT.pdf) &nbsp;•&nbsp; [⚡ Live Scenarios](https://manufacturing-decision-copilot-farhan.vercel.app/scenarios) &nbsp;•&nbsp; [📚 Submission Docs](submission/README.md)

</div>

---

## ⚡ The 5-Second Hook: Why Spreadsheets are Dead

| Legacy Procurement (Spreadsheets) | Manufacturing Decision Copilot 🚀 |
|---|---|
| ⏳ **3–4 hours** spent reading PDF quotes manually | ⚡ **< 30 seconds** end-to-end processing & ranking |
| ❌ Expired ISO certs missed until production halts | 🛡️ **Auto-disqualification (Score = 0)** on invalid certs |
| 🎲 Subjective guesswork & unverified numbers | 🧮 **9 Pure-Python deterministic rule engines** |
| 🌀 Scenario simulation takes a full afternoon | 🏎️ **< 2 ms real-time scenario recalculation** |
| 🕵️ Unverified AI claims & hallucinations | 📌 **100% cited evidence** — tap any number to see the PDF line |

---

## 🌐 Interactive Live Application

The live deployment is pre-seeded with **10 suppliers across 7 countries**, **17 challenge-pack documents**, and **3 real-time scenarios**:

<div align="center">

| Destination | Live URL | What You Can Do |
|---|---|---|
| 🎯 **Dashboard** | [`/dashboard`](https://manufacturing-decision-copilot-farhan.vercel.app/dashboard) | View winner recommendation, composite score gauge, score breakdown, & cited evidence |
| 🏢 **Suppliers** | [`/suppliers`](https://manufacturing-decision-copilot-farhan.vercel.app/suppliers) | Explore all 10 suppliers, compliance statuses, unit prices, and landed costs |
| ⚡ **Scenarios** | [`/scenarios`](https://manufacturing-decision-copilot-farhan.vercel.app/scenarios) | Drag shipping sliders (+40% freight shock) & watch rankings update in < 2 ms |
| 📁 **Documents** | [`/documents`](https://manufacturing-decision-copilot-farhan.vercel.app/documents) | Inspect ingested quotation PDFs, ISO certificates, audit reports, & chunk extractions |
| 📊 **Reports** | [`/reports`](https://manufacturing-decision-copilot-farhan.vercel.app/reports) | Generate and download board-ready PDF executive decision reports |

</div>

---

## 📊 Live Baseline Supplier Leaderboard

Running `score_suppliers()` on the challenge pack dataset produces this deterministic ranking:

| Rank | Supplier | Origin | Final Score | Landed Cost | Compliance Status | Key Highlights |
|:---:|---|:---:|:---:|:---:|:---:|---|
| 🥇 | **FastTrack Manufacturing** | 🇲🇽 Mexico | **93.37** | **$112.00** | ✅ ISO + RoHS + IATF | **Clear Winner.** Near-shore $4 freight, 10-day lead time |
| 🥈 | **Acme Precision Mfg** | 🇩🇪 Germany | **91.89** | $121.75 | ✅ ISO + AS9100D + RoHS | Runner-up. Has AS9100D aerospace cert |
| 🥉 | **NovaCast Engineering** | 🇵🇱 Poland | **90.61** | $117.95 | ✅ ISO + AS9100D | Solid near-shore European alternative |
| 4 | **VoltEdge Components** | 🇰🇷 S. Korea | **87.60** | $132.48 | ✅ ISO + IATF | Strong quality, higher logistics cost |
| 5 | **TechForge Industries** | 🇹🇼 Taiwan | **84.74** | $139.54 | ✅ ISO + RoHS | Excellent precision, longer lead time |
| 6 | **Reliable Parts Co** | 🇮🇳 India | **83.32** | $133.07 | ✅ ISO + IATF | Competitive unit cost, higher country risk |
| 7 | **AlphaForge Ltd** | 🇨🇦 Canada | **79.77** | $107.30 | ❌ **Zero Certifications** | **Cheapest cost ($107.30), but compliance = 0** |
| 8 | **SteelPath Industries** | 🇧🇷 Brazil | **79.52** | $121.28 | ✅ ISO 9001 only | 35-day lead time lowers delivery score |
| 9 | **Global Fabrication Ltd** | 🇨🇳 China | **77.02** | $146.25 | ✅ ISO 9001 only | $89 unit cost ruined by 25% tariff + $35 freight |
| 10 | **PeakMetal Solutions** | 🇻🇳 Vietnam | **70.02** | $108.10 | ❌ **Expired Cert** | **ISO expired Dec 2024 → Auto-disqualified (#10)** |

> [!NOTE]
> **Why Math Beats Guesswork:**
> - **AlphaForge** offers the cheapest landed cost ($107.30) but has **0 certifications** → `compliance_score = 0` → drops to **#7**.
> - **Global Fabrication** has the cheapest raw quote ($89.00), but 25% tariff pushes landed cost to **$146.25** (highest in field).
> - **PeakMetal** has an **expired ISO 9001 cert** → system detects `is_valid=False` → ranked last at **#10**.

---

## 🧪 3 Benchmark Case Demonstrations

> [!TIP]
> ### 🟢 Case 1 — Clear Success (FastTrack Manufacturing)
> - **Score:** **93.37 / 100** &nbsp;•&nbsp; **Confidence:** **87.6% (High)**
> - **Result:** FastTrack wins on composite balance ($112 landed cost, 10-day lead time, near-shore Mexico truck freight).
> - **Evidence:** 100% single-pass RAG retrieval, all claims cited directly to PDF page numbers.

> [!IMPORTANT]
> ### 🟡 Case 2 — Ambiguous Tradeoff (FastTrack vs Acme — 1.48 point gap)
> - **The Conflict:** FastTrack wins overall, but **Acme Precision** holds **AS9100D aerospace certification** that FastTrack lacks.
> - **System Response:** Confidence drops to **72% (Medium)**. The copilot surfaces a sensitivity alert: *If AS9100D is flagged as mandatory, Acme immediately flips to #1.*

> [!CAUTION]
> ### 🔴 Case 3 — Compliance Failure & Fallback (PeakMetal Solutions)
> - **The Trigger:** PeakMetal's ISO 9001 certificate expired in December 2024.
> - **System Guardrail:** Parser detects `is_valid=False` → `compliance_score = 0` → supplier auto-disqualified.
> - **Resilience:** If LLM is unreachable, Redis fallback serves the exact deterministic table without interruption.

---

## 📈 Real-Time Scenario Simulator: +40% Shipping Shock

When maritime freight costs spike +40% (Red Sea / Panama Canal disruption):

```
FastTrack (Mexico)   [+0.15]  ████████████████████ (Gains relative advantage: $4 truck freight)
Acme (Germany)       [-0.82]  ██████████████░░░░░░ (Loses ground: $22 air freight)
PeakMetal (Vietnam)  [-2.04]  ████████░░░░░░░░░░░░ (Hardest hit: $30 sea freight)
```

[👉 Drag sliders live on the Scenarios page →](https://manufacturing-decision-copilot-farhan.vercel.app/scenarios)

---

## 🏗️ Architecture & Pure-Python Engine Guardrails

```
🌐 Next.js 15 App Router (Vercel)
        │
        ▼ REST API (/api/v1)
⚡ FastAPI 0.141 (Railway)
  ├── 🧮 9 Deterministic Rule Engines ─── PURE PYTHON (Zero AI, Zero I/O)
  │    ├── cost.py        landed cost = unit + shipping + duty
  │    ├── quality.py     defect rate + inspection pass rate
  │    ├── delivery.py    lead time + on-time %
  │    ├── risk.py        5-factor weighted risk formula
  │    ├── compliance.py  cert check (missing/expired = 0)
  │    └── ranking.py     score_suppliers() (~2ms runtime)
  │
  ├── 🤖 AI Layer (PydanticAI) ───────────── EXPLANATION & CITATION ONLY
  │    ├── Gemini 2.0 Flash / GPT-4o / Groq / Ollama
  │    ├── Hybrid RAG: ChromaDB + BM25Okapi + Reciprocal Rank Fusion
  │    └── Security: 7 prompt injection patterns stripped
  │
  └── ⚙️ Async Pipeline ────────────────── Celery + Upstash Redis 7
       └── PDF Ingestion → Chunking → Local Embeddings → ChromaDB + Postgres
```

<details>
<summary><b>📐 Click to Expand Deterministic Scoring Formulas</b></summary>

```python
# Composite Supplier Ranking Formula
final_score = (
    cost_score       * 0.30  # Landed cost vs field min/max
  + quality_score    * 0.20  # Defect rate + inspection pass rate
  + delivery_score   * 0.15  # Lead time + OTD percentage
  + risk_score       * 0.15  # 100 - (financial*0.25 + country*0.20 + supply*0.20 + compliance*0.20 + capacity*0.15)
  + capability_score * 0.10  # Process capability match + engineering bonus
  + compliance_score * 0.10  # Hard stop: 0 if required cert is missing or expired!
)

# 5-Factor Deterministic Confidence Score (LLM NEVER touches this)
confidence = (
    extraction_quality * 0.30
  + evidence_coverage  * 0.20
  + retrieval_quality  * 0.20
  + rule_agreement     * 0.20
  + data_completeness  * 0.10
)
```
</details>

---

## 🎯 Key Numbers at a Glance

| Metric | Value | Benchmark / Target | Status |
|---|:---:|:---:|:---:|
| **Suppliers Evaluated** | **10** | 7 Countries | ✅ Seeded & Interactive |
| **Challenge Pack Documents** | **17** | Quotations, Certs, Audits | ✅ Ingested & Vectorized |
| **Ranking Engine Latency** | **~2 ms** | < 50 ms target | 🚀 **25× Faster** |
| **Unit Test Suite** | **501 Passing** | 0 Failures | ✅ 100% Green (2.50s) |
| **Prompt Injections Blocked** | **7 Patterns** | Zero leaks | 🛡️ Sanitized & Enforced |
| **Confidence Score (Winner)** | **87.6% (High)** | Deterministic formula | 🎯 Evidence-grounded |

---

## 📚 Submission Package Index

All hackathon deliverables are available in the [`submission/`](submission/README.md) folder and in the printable PDF report:

| Document | Content Summary |
|---|---|
| 📕 [`SUBMISSION_REPORT.pdf`](submission/SUBMISSION_REPORT.pdf) | **Complete Submission PDF Report** (live score tables, formulas, case studies, diagrams) |
| 📑 [`01_architecture_and_dataflow.md`](submission/01_architecture_and_dataflow.md) | Component architecture, 9 scoring engines, hybrid RAG pipeline, guardrails, DB schema |
| 📑 [`02_data_source_manifest.md`](submission/02_data_source_manifest.md) | 17 documents manifest, 10 supplier records, 3 scenario configs, setup guide |
| 📑 [`03_evaluation_results.md`](submission/03_evaluation_results.md) | Quantitative engine benchmarks, human vs. system timing, test suite breakdown |
| 📑 [`04_case_demonstrations.md`](submission/04_case_demonstrations.md) | Success · Ambiguous · Failure/Fallback case walkthroughs |
| 📑 [`05_users_assumptions_limitations.md`](submission/05_users_assumptions_limitations.md) | 4 user personas, 7 Human-Approval Points (HAPs), system boundaries |
| 📑 [`06_presentation_script.md`](submission/06_presentation_script.md) | 7-minute pitch script, slide notes, 4 live demo beats, prepared Q&A |

---

## 💻 60-Second Developer Quickstart

```bash
# 1. Clone & Set Up Environment
git clone https://github.com/farhxn/Manufacturing-Decision-Copilot-Farhan.git
cd Manufacturing-Decision-Copilot-Farhan

# 2. Setup Backend & Seed Database
cd backend
python -m venv venv && venv\Scripts\activate  # On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                          # Set GEMINI_API_KEY + DATABASE_URL
alembic upgrade head

# 3. Seed Production Data & Generate PDFs
cd ..
python scripts/seed_db_production.py
python scripts/generate_production_pdfs.py

# 4. Run Backend & Celery Worker
cd backend
uvicorn app.main:app --reload --port 8000
# Separate terminal: celery -A app.workers.celery_app worker --loglevel=info

# 5. Run Frontend Dashboard
cd frontend && npm install && npm run dev     # Open http://localhost:3000/dashboard

# 6. Run Full Test Suite (501 Tests)
pytest tests/unit/ -q                         # → 501 passed in 2.50s
```

---

<div align="center">

### 🏆 *Manufacturing Decision Copilot*
*Built with ❤️ for the Manufacturing Procurement Intelligence Hackathon*

[🌐 Open Live Dashboard](https://manufacturing-decision-copilot-farhan.vercel.app/dashboard)

</div>

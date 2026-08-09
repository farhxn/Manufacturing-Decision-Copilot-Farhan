# Data and Source Manifest
## Manufacturing Decision Copilot

---

## 1. Challenge Pack — Primary Input Data

All primary analysis is performed against the **Manufacturing Challenge Pack** — a frozen, versioned set of procurement documents that simulate a real motor housing component sourcing exercise. No live internet scraping is performed at any point during evaluation.

### 1.1 Challenge Pack Documents (17 files)

| # | Filename | Type | Supplier | Purpose in System |
|---|---|---|---|---|
| 1 | `Acme_Precision_Quotation_Q4_2026.pdf` | Quotation | Acme Precision Mfg (Germany) | Price, lead time, MOQ, Incoterms extraction |
| 2 | `GlobalFab_Commercial_Quotation_2026.pdf` | Quotation | Global Fabrication Ltd (China) | Price, duty exposure, lead time extraction |
| 3 | `TechForge_Quotation_MotorHousing_2026.pdf` | Quotation | TechForge Industries (Taiwan) | Price, quality data extraction |
| 4 | `ReliableParts_Quotation_Oct2026.pdf` | Quotation | Reliable Parts Co (India) | Price, IATF 16949 certification extraction |
| 5 | `FastTrack_Commercial_Quotation_2026.pdf` | Quotation | FastTrack Manufacturing (Mexico) | USMCA duty-free status, truck freight extraction |
| 6 | `VoltEdge_Commercial_Quotation_2026.pdf` | Quotation | VoltEdge Components (South Korea) | Price, engineering support, IATF data |
| 7 | `NovaCast_Engineering_Quotation_2026.pdf` | Quotation | NovaCast Engineering (Poland) | EU near-shore, AS9100D dual-cert extraction |
| 8 | `SteelPath_Quotation_2026.pdf` | Quotation | SteelPath Industries (Brazil) | High-MOQ edge case, BB- credit signal |
| 9 | `PeakMetal_Quotation_2026.pdf` | Quotation | PeakMetal Solutions (Vietnam) | Expired ISO cert edge case |
| 10 | `AlphaForge_Quotation_2026.pdf` | Quotation | AlphaForge Ltd (Canada) | Zero-cert edge case, CUSMA DDP pricing |
| 11 | `Acme_ISO9001_AS9100D_Certificate_2026.pdf` | Certificate | Acme Precision Mfg | Compliance verification — AS9100D + ISO 9001 |
| 12 | `TechForge_RoHS_Certificate_2026.pdf` | Certificate | TechForge Industries | RoHS compliance verification |
| 13 | `FastTrack_RoHS_Certificate_2026.pdf` | Certificate | FastTrack Manufacturing | RoHS compliance verification |
| 14 | `VoltEdge_ISO9001_Certificate_2026.pdf` | Certificate | VoltEdge Components | ISO 9001 compliance verification |
| 15 | `MotorHousing_Technical_Specification_v3.pdf` | Technical Spec | N/A (buyer document) | Required capabilities and tolerances definition |
| 16 | `Purchase_Requirements_FY2027.pdf` | Requirements | N/A (buyer document) | Procurement constraints, MOQ limits, timeline |
| 17 | `NovaCast_Supplier_Audit_Report_2026.pdf` | Audit Report | NovaCast Engineering | Third-party audit evidence for risk scoring |

**Total challenge pack size:** 17 documents  
**Formats supported:** PDF (primary), DOCX, XLSX  
**File integrity:** SHA-256 checksums recorded at ingestion; stored in `documents.checksum` column

### 1.2 Challenge Pack Data Fields Extracted Per Supplier

The `ExtractionAgent` (PydanticAI) reads chunked document text and attempts to populate the following structured fields:

| Field | Source Document Type | Engine That Consumes It |
|---|---|---|
| `quoted_price` | Quotation | Cost Engine |
| `currency` | Quotation | Cost Engine (currency_rate conversion) |
| `shipping_cost` | Quotation | Cost Engine |
| `incoterms` | Quotation | Cost Engine (determines duty responsibility) |
| `lead_time_days` | Quotation | Delivery Engine |
| `certifications[]` | Quotation + Certificate | Compliance Engine |
| `capabilities[]` | Quotation + Technical Spec | Capability Engine |
| `defect_rate` | Quotation | Quality Engine |
| `on_time_delivery_pct` | Quotation / Audit Report | Quality Engine |
| `production_capacity_pct` | Quotation | Delivery + Capability Engines |
| Financial risk signal | Audit Report | Risk Engine (compliance_risk factor) |
| Country of origin | Quotation | Risk Engine (country_risk factor) |
| `confidence_note` | Any | Confidence Engine (data_completeness input) |

---

## 2. Seeded Supplier Dataset

The 10 suppliers are seeded into PostgreSQL via `scripts/seed_db_production.py`. Each supplier record populates five sub-tables. This dataset is the ground truth that the scoring engines operate on.

### 2.1 Supplier Master Records

| Supplier | Country | Unit Price (USD) | Shipping (USD) | Duty Rate | Landed Cost | Lead Time | MOQ |
|---|---|---|---|---|---|---|---|
| Acme Precision Mfg | Germany | 95.00 | 22.00 | 5% | 121.75 | 14 days | 100 |
| Global Fabrication Ltd | China | 89.00 | 35.00 | 25% | 146.25 | 28 days | 500 |
| TechForge Industries | Taiwan | 118.00 | 18.00 | 3% | 139.54 | 21 days | 250 |
| Reliable Parts Co | India | 101.00 | 25.00 | 7% | 133.07 | 18 days | 200 |
| FastTrack Manufacturing | Mexico | 108.00 | 4.00 | 0% | 112.00 | 10 days | 150 |
| VoltEdge Components | South Korea | 112.00 | 16.00 | 4% | 132.48 | 16 days | 200 |
| NovaCast Engineering | Poland | 99.00 | 14.00 | 5% | 117.95 | 12 days | 100 |
| SteelPath Industries | Brazil | 88.00 | 28.00 | 6% | 121.28 | 35 days | 2000 |
| PeakMetal Solutions | Vietnam | 71.00 | 30.00 | 10% | 108.10 | 30 days | 300 |
| AlphaForge Ltd | Canada | 107.30 | 0.00 | 0% | 107.30 | 8 days | 50 |

### 2.2 Supplier Risk Scores (Safety Scores, 0–100, higher = safer)

These are stored in `supplier_risk_scores`. The risk engine inverts them to magnitudes before computing.

| Supplier | Financial | Country | Supply | Compliance | Capacity | Risk Level |
|---|---|---|---|---|---|---|
| Acme Precision Mfg | 95 | 92 | 94 | 96 | 95 | Low |
| Global Fabrication Ltd | 70 | 55 | 62 | 68 | 72 | High |
| TechForge Industries | 86 | 78 | 82 | 88 | 84 | Low |
| Reliable Parts Co | 74 | 70 | 76 | 80 | 78 | Moderate |
| FastTrack Manufacturing | 84 | 82 | 88 | 90 | 86 | Low |
| VoltEdge Components | 88 | 80 | 85 | 92 | 87 | Low |
| NovaCast Engineering | 82 | 85 | 80 | 94 | 83 | Low |
| SteelPath Industries | 52 | 58 | 55 | 62 | 66 | Elevated |
| PeakMetal Solutions | 55 | 60 | 45 | 40 | 58 | High |
| AlphaForge Ltd | 62 | 91 | 65 | 35 | 68 | Moderate |

### 2.3 Certifications Per Supplier

| Supplier | Certifications Held | `is_valid` | Notes |
|---|---|---|---|
| Acme Precision Mfg | ISO 9001:2015, AS9100D, RoHS | All True | Full aerospace package |
| Global Fabrication Ltd | ISO 9001:2015 | True | Missing AS9100D, RoHS |
| TechForge Industries | ISO 9001:2015, RoHS | All True | Dual-cert |
| Reliable Parts Co | ISO 9001:2015, IATF 16949 | All True | Automotive quality bonus |
| FastTrack Manufacturing | ISO 9001:2015, RoHS, IATF 16949 | All True | Triple-cert near-shore |
| VoltEdge Components | ISO 9001:2015, IATF 16949 | All True | Automotive grade |
| NovaCast Engineering | ISO 9001:2015, AS9100D | All True | EU near-shore aerospace |
| SteelPath Industries | ISO 9001:2015 | True | Missing AS9100D, RoHS |
| PeakMetal Solutions | ISO 9001:2015 | **False** (expired 2024-12-31) | EDGE CASE: expired cert → compliance_score = 0 |
| AlphaForge Ltd | (none) | N/A | EDGE CASE: zero certs → compliance_score = 0 |

### 2.4 Scenario Definitions (Stored in PostgreSQL)

| Scenario ID | Name | Key Config Change | Expected Winner Change |
|---|---|---|---|
| `baseline` | Baseline — Default Weights | No changes; default weights | Acme Precision Mfg (#1) |
| `shipping_shock` | Shipping Shock — Freight +40% | `shipping_multiplier=1.4`, `lead_time_adjustment_days=7` | FastTrack Manufacturing displaces Acme (#1→#2) |
| `china_tariff` | China Tariff Escalation — +50% Duty | `import_duty_rate` for China-origin = 0.75, GlobalFab disabled | Acme retains #1; EU/Mexico dominate top 3 |

---

## 3. External Data Sources

### 3.1 AI / LLM Providers

| Service | Usage | Data Sent | Data Retained by Provider |
|---|---|---|---|
| Google Gemini 2.0 Flash (default) | LLM reasoning and narrative generation | Sanitised document chunks + scoring context | Per Google AI Studio terms |
| OpenAI GPT-4o (optional fallback) | Same as above | Same | Per OpenAI API terms |
| Groq Llama-3.3-70b (optional fallback) | Same as above | Same | Per Groq terms |
| Ollama (offline mode) | Same as above, fully local | Never leaves device | N/A |

**Important:** Only **sanitised, injection-stripped** chunks are sent to any LLM. Raw document text is never transmitted directly. The LLM never receives raw file bytes, filenames, or PII beyond what appears in the document content itself.

### 3.2 Embedding Models

| Model | Provider | Usage | Data Sent |
|---|---|---|---|
| `BAAI/bge-small-en-v1.5` | Hugging Face (downloaded locally, default) | Document chunk and query embedding | Runs fully locally; no external calls |
| `text-embedding-3-small` | OpenAI API | Alternative embedding provider | Sanitised chunk text |
| Gemini Embedding | Google AI | Alternative embedding provider | Sanitised chunk text |

**Default configuration uses `BAAI/bge-small-en-v1.5` locally** — no external embedding API calls required during the demo.

### 3.3 No Live External Data

The following data sources are explicitly **not used**:

| Source | Reason Not Used |
|---|---|
| Live supplier websites | Prohibited — off-limits per system guardrails |
| Live commodity/exchange rate feeds | Not used; rates are provided in document data or scenario config |
| Company credit databases (D&B, Fitch) | Not queried live; risk scores are sourced from seeded data representing challenge pack signals |
| Customs tariff APIs | Not queried live; duty rates are extracted from documents or set in scenario config |
| Government sanctions lists | Not queried live; compliance risk is encoded in the seeded risk scores |

---

## 4. Vector Store Contents

### ChromaDB `document_chunks` Collection

All document content ingested during the demo session is stored in ChromaDB with the following metadata per chunk:

| Metadata Field | Type | Source |
|---|---|---|
| `chunk_id` | UUID | Generated at ingestion |
| `document_id` | UUID | PostgreSQL `documents.id` |
| `project_id` | UUID | Demo project UUID |
| `supplier_id` | UUID or null | Linked supplier, or null for buyer docs |
| `page_number` | int | Extracted by PyMuPDF |
| `section_name` | str | Semantic section header (e.g., "DELIVERY TERMS") |
| `document_type` | str | quotation / certificate / specification / audit_report |
| `extraction_confidence` | float | 0.0–1.0 |

**Chunk parameters:**
- Max chunk size: 800 tokens
- Overlap: 50 tokens
- Splitting strategy: semantic section boundaries (not fixed-size windows)
- Embedding model: `BAAI/bge-small-en-v1.5` (384-dimensional vectors)
- Similarity metric: cosine

---

## 5. Reproducible Setup Instructions

### 5.1 Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12+ | Required |
| Node.js | 18+ | For frontend |
| PostgreSQL | 16+ | Local or Supabase |
| Redis | 7+ | Local or Upstash free tier |
| Git | Any | |

### 5.2 Quick Start (Local)

```bash
# 1. Clone and enter repo
git clone <repo-url>
cd SGTDP

# 2. Backend setup
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 3. Environment configuration
cp .env.example .env
# Edit .env — set GEMINI_API_KEY (free from Google AI Studio)
# Set DATABASE_URL to your PostgreSQL connection string

# 4. Database migrations
alembic upgrade head

# 5. Seed the database (10 suppliers + 3 scenarios)
cd ..
python scripts/seed_db_production.py

# 6. Generate sample PDFs (if not already present)
python scripts/generate_production_pdfs.py

# 7. Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# 8. Start Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# 9. Frontend setup (separate terminal)
cd ../frontend
npm install
npm run dev         # starts on http://localhost:3000

# 10. Open dashboard
# Navigate to http://localhost:3000/dashboard
```

### 5.3 Environment Variables Required

| Variable | Description | Where to Get |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (free tier) | https://aistudio.google.com |
| `DATABASE_URL` | PostgreSQL connection string | Local Postgres or Supabase |
| `REDIS_URL` | Redis connection string | Local Redis or Upstash |
| `OPENAI_API_KEY` | Optional — only if using OpenAI provider | https://platform.openai.com |

### 5.4 Verifying the Setup

```bash
# Confirm backend is healthy
curl http://localhost:8000/api/v1/health

# Confirm 10 suppliers are loaded
curl http://localhost:8000/api/v1/suppliers

# Confirm 3 scenarios are loaded
curl http://localhost:8000/api/v1/scenarios

# Run unit tests (all P0 engines)
cd backend
pytest tests/unit/ -v
```

---

## 6. Data Lineage Summary

```
Challenge Pack PDFs (17 files)
        │
        ▼  [PyMuPDF extraction + semantic chunking]
Document Chunks (ChromaDB)
        │
        ├──► [bge-small-en-v1.5 embedding → cosine similarity]
        │
        └──► [ExtractionAgent → structured fields → PostgreSQL]
                │
                ▼
        Supplier Records (PostgreSQL)
                │
                ▼  [score_suppliers() — pure Python]
        Ranked Scoring Results
                │
                ├──► [retrieve_with_loop() → top-K evidence chunks]
                │
                └──► [RecommendationAgent → narrative explanation]
                │
                ▼
        Recommendation (PostgreSQL + Redis cache)
                │
                ▼
        Dashboard / Report (Frontend)
```

Every step in this lineage is logged in `ai_requests`, `ai_responses`, and `audit_logs` tables, providing a complete traceable chain from raw document bytes to final recommendation.

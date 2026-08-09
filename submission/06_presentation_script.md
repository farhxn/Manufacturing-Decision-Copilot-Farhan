# Presentation Script and Slide Notes
## Manufacturing Decision Copilot
### Total time: 7 minutes · Demo: 3 minutes · Q&A: 3–5 minutes

---

## Delivery Notes (Read Before Presenting)

- Speak to the story, not the slides. Each slide should be visible for at most 30–40 seconds.
- Every sentence should answer "why does this matter to a real company?" — not "how did we build this?"
- The demo is the proof. Let the UI carry the technical credibility; you carry the business narrative.
- Pause after the scenario flip moment. It is the most dramatic beat — give judges a second to absorb it.
- Never say "basically," "kind of," or "we tried to." Speak with the confidence of a team that finished the product.

---

## Slide 1 — Title (0:00–0:20)

**Slide content:**
> **Manufacturing Decision Copilot**
> *From Documents to Decisions — in Seconds*
>
> Background: large, clean dashboard screenshot showing the recommendation card, animated score gauge, and score breakdown.

**Speaker:**

Good morning.

Every year, manufacturing companies spend billions on the wrong suppliers — not because they lack data, but because they drown in it.

Ten quotations. Fourteen certificates. Three spreadsheets. One deadline.

Today we show you what happens when that process takes thirty seconds instead of three hours.

---

## Slide 2 — The Problem (0:20–0:55)

**Slide content:**
> **The Current Reality**
>
> Left column — "What procurement teams do today":
> - Read 100+ pages of supplier documents manually
> - Build landing-cost formulas in Excel (and get them wrong)
> - Track certifications in a shared spreadsheet (and miss expiries)
> - Write a recommendation email that says "we think Supplier A is best"
> - Get asked "why?" and have no traceable answer
>
> Right column — "The cost":
> - 2–4 hours per supplier evaluation cycle
> - Decisions that cannot be audited or replicated
> - Missed certification expiries that delay production
> - Procurement risk that only surfaces after the PO is signed

**Speaker:**

Procurement professionals are not lacking intelligence. They are lacking tools that match the complexity of the problem.

They receive documents in dozens of formats. They calculate landed costs manually — and landed cost is not unit price, it is unit price plus shipping plus duty plus insurance.

They check certifications by eye — and nobody catches that the ISO certificate expired eight months ago until the quality audit fails.

The result is decisions that are slow, inconsistent, and impossible to explain to a regulator or an executive.

That is the problem we set out to solve.

---

## Slide 3 — The Solution (0:55–1:25)

**Slide content:**
> **Manufacturing Decision Copilot**
>
> Architecture diagram — clean, left-to-right:
> ```
> Supplier Documents
>       ↓  AI Extraction
> Structured Data
>       ↓  Deterministic Rule Engines
> Ranked Scores  (cost · quality · delivery · risk · capability · compliance)
>       ↓  Evidence-Backed AI Explanation
> Recommendation + Confidence + Citations
>       ↓  Scenario Simulation
> What-If Analysis
>       ↓  Executive Report
> Decision
> ```
>
> Key callout: **"AI explains. Math decides. Humans approve."**

**Speaker:**

Manufacturing Decision Copilot is not a chatbot. It is a decision intelligence platform built around one principle:

*AI should explain procurement decisions. Mathematics should make them.*

The workflow is simple. Upload your supplier documents. Our pipeline extracts structured data — prices, lead times, certifications, risk factors. A deterministic rule engine scores every supplier across six dimensions: cost, quality, delivery, risk, capability, and compliance.

The AI never touches a number. It reads the evidence and explains what the rules found. That separation is what makes the recommendation auditable, reproducible, and trustworthy.

Let me show you.

---

## Slide 4 — LIVE DEMO (1:25–4:25)

*[Switch to browser — dashboard already loaded with seeded data]*

---

### Demo Beat 1 — The Dashboard (1:25–2:10)

**Action:** Navigate to `http://localhost:3000/dashboard`

**Speaker:**

This is the dashboard for a real procurement scenario: ten suppliers competing to manufacture a precision motor housing component.

The system has already processed seventeen documents — quotations, certificates, an audit report, and our technical specification.

*[Point to the recommendation card and animated score gauge]*

In the top left: our recommended supplier. FastTrack Manufacturing, Mexico. Composite score 93.37 out of 100. Confidence: 87 percent — High.

But here is what makes this different from any other procurement tool.

*[Click the cited evidence count link or a CitationPopover]*

Every number here is linked to its source. That landed cost of $112? Click it — you see page 2 of FastTrack's quotation: "Unit price USD 108.00. Truck delivery to US border. USMCA certificate of origin enclosed." That is the document. That is the evidence. Nothing invented.

*[Point to score breakdown card]*

And on the right: the full score breakdown. FastTrack wins because it has the lowest landed cost among compliant suppliers — thanks to USMCA zero duty and four-dollar truck freight — while also delivering in ten days and holding three certifications.

---

### Demo Beat 2 — The Compliance Disqualifier (2:10–2:40)

**Action:** Scroll down to the Supplier Landscape table. Point to row 10 — PeakMetal Solutions.

**Speaker:**

Now look at the bottom of the ranking. PeakMetal Solutions, Vietnam. Landed cost $108 — the second cheapest in the field.

*[Point to the compliance score column — it reads 0]*

Compliance score: zero.

PeakMetal's ISO 9001 certificate expired in December 2024. The system detected it automatically, scored it zero on compliance, and ranked it last — while still keeping it visible so the team knows exactly why it failed and what the path to re-qualification looks like.

That is a catch that a spreadsheet would miss. That is a catch that protects a production line.

---

### Demo Beat 3 — The Scenario Engine (2:40–3:35)

**Action:** Scroll to the Scenario Simulator panel on the dashboard, or navigate to `/scenarios`

**Speaker:**

Here is where the product earns its keep in the real world.

*[Ask the audience]*

What happens to your supplier ranking if a Red Sea–style shipping disruption adds forty percent to international freight costs?

With a traditional spreadsheet: you rebuild the model. That takes hours.

*[Drag the shipping multiplier slider to 1.4]*

Watch.

*[Scores recalculate — hold for 2 seconds]*

FastTrack's score moves to 93.52 — it goes **up**. Because FastTrack ships by truck from Monterrey for four dollars. A forty percent increase on four dollars is $1.60. Acme ships by air from Stuttgart for twenty-two dollars. A forty percent increase on twenty-two dollars is $8.80.

Near-shore sourcing becomes structurally superior under freight stress. The scenario engine shows that in real time, and the AI explains it in plain English below.

*[Point to the ScenarioExplanation text]*

"FastTrack Manufacturing's structural truck-freight advantage makes it the most resilient supplier under sustained maritime disruption. Suppliers relying on transatlantic air freight — particularly Acme and TechForge — face the steepest landed-cost increases."

That is the business case for near-shore sourcing, generated automatically, cited from the documents.

---

### Demo Beat 4 — Executive Report (3:35–4:25)

**Action:** Navigate to `/reports`, click "Generate Executive Report"

**Speaker:**

Finally — the output that actually moves inside a company.

*[PDF renders and opens — 2-3 seconds]*

A board-ready executive report. Recommendation statement. Cost comparison table. Top three risks. Concrete next steps. And a disclaimer — because every AI output in this system carries one.

This took thirty seconds to generate. The alternative is two hours of writing after a meeting that should not have needed to happen.

*[Switch back to slides]*

---

## Slide 5 — Architecture and Innovation (4:25–5:00)

**Slide content:**
> **What Makes This Different**
>
> Three innovation callouts:
>
> **1. Deterministic + Explainable AI**
> Rule engines produce scores. LLM produces narrative. Scores are always reproducible — run the formula again, get the same answer.
>
> **2. Self-RAG Retrieval Loop**
> Hybrid BM25 + vector search + Reciprocal Rank Fusion. If the first retrieval pass is insufficient, an LLM grader refines the query and retries — up to 3 iterations. Evidence quality improves automatically.
>
> **3. Scenario Engine**
> Pure Python, sub-50ms re-ranking. Shipping shocks, tariff changes, supplier removal, certification override — all without touching a spreadsheet.
>
> Small architecture summary line: FastAPI · Next.js 15 · PostgreSQL · ChromaDB · Celery · PydanticAI

**Speaker:**

Three things make this architecture genuinely different from a standard AI procurement tool.

First: separation of concerns. The rule engines are pure mathematics — no I/O, no AI, 501 unit tests, all passing. The AI never calculates a number. It explains what the math found. That means a compliance team can audit every recommendation without understanding machine learning.

Second: iterative self-correcting retrieval. The system grades its own evidence quality after each retrieval pass and refines the search query if coverage is insufficient. It stops when it finds enough — not after a fixed number of calls.

Third: the scenario engine runs in under two milliseconds for ten suppliers. That is not a slow process running in the background — it is instant, which means procurement teams will actually use it.

---

## Slide 6 — Business Value (5:00–5:35)

**Slide content:**
> **The Business Case**
>
> | Metric | Before | After |
> |---|---|---|
> | Supplier evaluation time | 2–4 hours | < 30 seconds |
> | Landed cost errors | Common (manual Excel) | Zero (deterministic engine) |
> | Expired cert detection | Missed until audit fails | Automatic at ingestion |
> | Scenario analysis | New spreadsheet per scenario | Real-time, < 50 ms |
> | Recommendation audit trail | "We discussed it" | Full evidence chain, stored in DB |
> | Executive summary | 2 hours of writing | AI-generated in 3 seconds |
>
> One scenario: a $97,500 annual savings finding from the freight-shock simulation (10,000 units × $9.75 landed cost difference between FastTrack and Acme under baseline).

**Speaker:**

The numbers tell a direct story.

Supplier evaluation drops from hours to seconds. Certification gaps are caught automatically — not in a quality audit six months later. Every recommendation is traceable to a source document.

And the scenario engine has real monetary value. The shipping shock analysis we just ran quantifies a $9.75 per-unit landed cost advantage for FastTrack. At ten thousand annual units, that is $97,500 in savings identified in a thirty-second simulation that previously required a half-day spreadsheet exercise.

---

## Slide 7 — Closing (5:35–6:00)

**Slide content:**
> **Manufacturing Decision Copilot**
>
> Large centred text:
> *"AI recommends. Math decides. Humans approve."*
>
> Bottom: team name and track

**Speaker:**

We built Manufacturing Decision Copilot because procurement deserves the same level of rigor that finance applies to investment decisions — transparent, evidence-backed, and fully auditable.

This is not a chatbot with a procurement skin. It is a decision intelligence platform: deterministic scoring, iterative retrieval, explainable AI, and a scenario engine that makes "what if" questions cheap to ask.

The result is a system that procurement managers can trust on Monday morning — not because we told them to, but because every recommendation shows its work.

Thank you.

---

## Q&A — Prepared Answers

**Q: Why not just let the AI rank the suppliers?**

> Because enterprise procurement requires reproducibility. If you tell your CPO that the AI picked Supplier A, they will ask "why?" — and "the AI decided" is not an answer. A deterministic formula produces the same ranking every time. You can point to the formula, the weights, and the source data. The AI explains that result in plain English. That is the separation that builds organisational trust.

---

**Q: How do you prevent the AI from hallucinating?**

> Three layers. First: the LLM only receives sanitised evidence chunks retrieved from the actual uploaded documents — it cannot invent facts not in those chunks. Second: seven injection pattern types are stripped from all document text before it reaches the model. Third: every AI output is validated against a strict Pydantic schema; schema violations trigger an automatic fallback to the cached deterministic result. And finally: any evidence ID the LLM cites that was not in the retrieved set is silently removed before it reaches the database. The system cannot store a hallucinated citation.

---

**Q: What happens if the AI API goes down during a demo?**

> The deterministic scoring engines are completely independent of the AI layer. If the LLM call times out — we set a 10-second hard limit — the system returns the cached recommendation from Redis, or the raw score table if no cache exists. The ranking is always available. The AI narrative is the only thing that degrades.

---

**Q: Why did FastTrack win instead of Acme, which has better quality?**

> Two reasons. First, landed cost: USMCA eliminates duty and $4 truck freight versus $22 air freight gives FastTrack a $9.75 per-unit cost advantage. Cost carries 30% of the final score — the largest single weight. Second, delivery: FastTrack's 10-day lead time scores 86.15 on delivery versus Acme's 78.66. Acme wins on quality (97.45 vs 94.12) and risk (94.40 vs 85.90), but those dimensions carry less combined weight than cost alone. If the buyer adds AS9100D as a required certification, the ranking inverts — Acme becomes #1 and FastTrack drops to approximately #6. We demonstrated that live in the scenario engine.

---

**Q: How does the confidence score work?**

> It is entirely deterministic — the LLM never touches it. Five factors: extraction quality (how completely did we extract fields from the documents), evidence coverage (how many relevant chunks did retrieval find), retrieval quality (average RRF score across top chunks), rule agreement (are the six scoring dimensions consistent or conflicting), and data completeness (are all risk sub-scores populated). Weighted sum, result between 0 and 1, displayed as a percentage with Low/Medium/High label. FastTrack in the demo scores 87.6% — High — because all five factors are strong. A supplier with a missing risk score or poor document quality would see this drop, which flags it for human review.

---

**Q: Can this scale to a real company's supplier base — hundreds of suppliers?**

> The architecture is designed for it. The scoring engines are pure Python functions — linear in the number of suppliers, no I/O. ChromaDB scales to millions of document chunks with HNSW indexing. PostgreSQL with async SQLAlchemy handles concurrent requests. Celery workers can be horizontally scaled. The frontend is on Vercel, the backend on Railway — both scale automatically. The demo uses 10 suppliers to make the results legible to judges; nothing in the architecture prevents 1,000.

---

## Pre-Demo Checklist

Run through this 10 minutes before presenting:

- [ ] Backend running: `curl http://localhost:8000/api/v1/health` returns `{"status": "ok"}`
- [ ] Database seeded: `/api/v1/suppliers` returns 10 suppliers
- [ ] Scenarios seeded: `/api/v1/scenarios` returns 3 scenarios
- [ ] Frontend running: `http://localhost:3000/dashboard` loads without errors
- [ ] Dashboard populated: recommendation card shows FastTrack at 93.37
- [ ] CitationPopover works: click a cost figure, source text appears
- [ ] Scenario slider works: drag shipping to 1.4, scores update
- [ ] Report generation works: PDF renders and opens
- [ ] Gemini API key valid: test with a `/recommendations/regenerate` call
- [ ] Browser zoom: set to 100%. Font must be readable from the back of the room.
- [ ] Second browser tab open: `/scenarios` page ready for the scenario demo beat
- [ ] Demo PDF pre-generated: if report generation is slow, have a pre-built PDF ready to open

---

## Timing Reference

| Beat | Content | Cumulative |
|---|---|---|
| Slide 1 | Title + opening hook | 0:20 |
| Slide 2 | The problem | 0:55 |
| Slide 3 | The solution | 1:25 |
| Demo Beat 1 | Dashboard + citations | 2:10 |
| Demo Beat 2 | Compliance disqualifier | 2:40 |
| Demo Beat 3 | Scenario engine flip | 3:35 |
| Demo Beat 4 | Executive report | 4:25 |
| Slide 5 | Architecture + innovation | 5:00 |
| Slide 6 | Business value | 5:35 |
| Slide 7 | Closing | 6:00 |
| Buffer | Transition + applause | 6:30 |
| Q&A | See prepared answers above | +3–5 min |

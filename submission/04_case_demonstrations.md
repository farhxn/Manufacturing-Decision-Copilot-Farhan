# Case Demonstrations
## Manufacturing Decision Copilot

Three cases are required: one successful, one ambiguous or conflicting, one failure or fallback.
Each case maps to a real supplier and scenario in the seeded demo dataset, and every score cited is the live engine output from the evaluation document.

---

## Case 1 — Successful Case

**Title:** Clear Recommendation with Full Evidence Coverage

**Supplier under evaluation:** FastTrack Manufacturing (Mexico)  
**Project:** Motor Housing Component — FY2027 Sourcing Decision

---

### Setup

The procurement team uploads 17 challenge pack documents. After Celery processing completes, they navigate to the dashboard and request a recommendation for the standard configuration:

- Required certification: ISO 9001
- Default weights: cost 30%, quality 20%, delivery 15%, risk 15%, capability 10%, compliance 10%
- No scenario overrides

---

### What the System Does

**Step 1 — Document ingestion:**  
PyMuPDF extracts text from `FastTrack_Commercial_Quotation_2026.pdf` and `FastTrack_RoHS_Certificate_2026.pdf`. The chunker splits content into semantic sections (PRICING TERMS, DELIVERY SCHEDULE, CERTIFICATION LIST, QUALITY METRICS). The ExtractionAgent populates structured fields: `quoted_price=108.00`, `shipping_cost=4.00`, `duty_rate=0.00` (USMCA), `lead_time_days=10`, `certifications=["ISO 9001:2015", "RoHS Compliant", "IATF 16949"]`.

**Step 2 — Deterministic scoring:**

```
Landed cost  = 108.00 + (4.00 × 1.0) + 0.00 duty = 112.00 USD
               → lowest landed cost of all compliant suppliers

Cost score   = (107.30 / 112.00) × 100 = 95.80
               (AlphaForge has lower landed at 107.30 but scores 0 on compliance)
               (Among compliant suppliers, FastTrack's 112.00 is the minimum)

Quality score = defect_component(2.5%) × 0.40
              + inspection_pass_rate(95%) × 0.35
              + customer_rating(4.5/5 → 90) × 0.25
              = 94.12

Delivery score = lead_time_component(8/10 × 100 = 80) × 0.45
               + on_time_pct(93) × 0.35
               + capacity_pct(88) × 0.20
               = 86.15

Risk score   = 100 − (16×0.25 + 18×0.20 + 12×0.20 + 10×0.20 + 14×0.15)
             = 100 − (4.0 + 3.6 + 2.4 + 2.0 + 2.1) = 85.90

Capability   = 100 (all required capabilities met + engineering support)
Compliance   = 100 (ISO 9001:2015 matches required "ISO 9001" via prefix rule)

Final score  = 95.80×0.30 + 94.12×0.20 + 86.15×0.15
             + 85.90×0.15 + 100×0.10 + 100×0.10
             = 93.37  ← #1 of 10 suppliers
```

**Step 3 — RAG evidence retrieval:**  
`retrieve_with_loop()` runs with query `"FastTrack Manufacturing pricing lead time certification quality"`. ChromaDB cosine similarity returns 8 chunks; BM25 re-ranks them; RRF fuses the lists. Coverage score after loop 1 = 0.038 (exceeds 0.025 threshold). Loop stops at iteration 1 — sufficient evidence.

Top retrieved chunks:
- `[chunk_id: ft-001]` page 2: "Unit price USD 108.00 per unit. FOB Monterrey. USMCA certificate of origin enclosed."
- `[chunk_id: ft-002]` page 3: "Lead time: 10 business days from purchase order. Truck delivery to US border."
- `[chunk_id: ft-003]` page 4: "ISO 9001:2015 certified (SGS, valid until 2027-09-30). IATF 16949:2016 certified. RoHS compliant."
- `[chunk_id: ft-cert-001]` page 1: "RoHS Declaration of Conformity — FastTrack Manufacturing SA de CV."

**Step 4 — AI recommendation generation:**  
RecommendationAgent receives sanitised evidence chunks + score breakdown. Output (representative):

> *"Recommend FastTrack Manufacturing (Mexico) as the preferred supplier for the FY2027 motor housing component. FastTrack achieves the strongest composite score (93.37/100) across all six evaluation dimensions. The USMCA duty-free status eliminates import tariffs that add 3–25% to competitors' landed costs, resulting in the lowest compliant landed cost at USD 112.00. The 10-day truck lead time is the fastest in the field and resilient to maritime freight disruptions. Triple certification (ISO 9001, IATF 16949, RoHS) confirms regulatory compliance without conditions."*

**Step 5 — Confidence calculation (deterministic):**

```
extraction_quality  = 0.92  (all key fields extracted from 2 documents)
evidence_coverage   = 0.85  (pricing, lead time, certs, quality all covered)
retrieval_quality   = 0.81  (avg RRF score = 0.038, normalised)
rule_agreement      = 0.90  (all 6 engine scores agree: supplier is strong on every axis)
data_completeness   = 0.88  (all 5 risk sub-scores present in DB)

confidence = 0.92×0.30 + 0.85×0.20 + 0.81×0.20 + 0.90×0.20 + 0.88×0.10
           = 0.276 + 0.170 + 0.162 + 0.180 + 0.088 = 0.876
           → 87.6% → label: "High"
```

---

### Outcome

The dashboard displays:
- **Animated DonutGauge:** 93.37 / 100
- **Confidence badge:** 87.6% — High
- **Recommendation text:** AI-generated narrative (above)
- **Evidence citations:** 4 chunks linked to PDF pages — clickable via CitationPopover
- **Score breakdown card:** All 6 dimension scores visible
- **Pros:** USMCA 0% duty, 10-day lead time, triple-certified, engineering support
- **Cons:** Higher unit price than GlobalFab and SteelPath; limited to truck freight geography
- **Next actions:** Issue RFQ for FY2027 volume commitment; request PPAP documentation; confirm IATF 16949 scope covers motor housing

**Why this is a successful case:**  
Every dimension of the scoring formula is populated from real documents. The evidence retrieval loop completes in a single pass. The confidence score is high (87.6%). The AI explanation cites specific evidence IDs that trace back to exact PDF pages. The ranking is unambiguous — FastTrack leads #2 (Acme) by 1.48 points with no dimension where it is critically weak. The recommendation is fully auditable and immediately actionable.

---

## Case 2 — Ambiguous / Conflicting Case

**Title:** Near-Tie Between Quality Leader and Cost Leader — Score Convergence

**Suppliers in conflict:** FastTrack Manufacturing (#1, 93.37) vs Acme Precision Mfg (#2, 91.89)  
**Margin:** 1.48 points — the smallest gap in the top-3 ranking

---

### Setup

After reviewing the baseline recommendation, the procurement team's manufacturing engineer raises a concern: the motor housing requires aerospace-grade quality for a customer with AS9100D supplier approval requirements. The team opens the Supplier Comparison view for FastTrack vs Acme side by side.

---

### What Makes This Ambiguous

The two suppliers tell contradictory stories depending on which dimension the buyer weights most:

| Dimension | FastTrack (Mexico) | Acme (Germany) | Winner |
|---|---|---|---|
| Final Score | **93.37** | 91.89 | FastTrack by 1.48 |
| Landed Cost | **$112.00** | $121.75 | FastTrack by $9.75 |
| Cost Score | **95.80** | 88.13 | FastTrack |
| Quality Score | 94.12 | **97.45** | **Acme** |
| Delivery Score | **86.15** | 78.66 | FastTrack |
| Risk Score | 85.90 | **94.40** | **Acme** |
| Capability Score | **100** | **100** | Tie |
| Compliance Score | **100** | **100** | Tie |
| AS9100D certified? | ❌ No | ✅ Yes | **Acme** |
| IATF 16949? | ✅ Yes | ❌ No | FastTrack |
| Risk Level | Low | **Low (stronger)** | **Acme** |
| Lead Time | **10 days** | 14 days | FastTrack |
| Country Risk | Moderate (Mexico) | **Very Low (Germany)** | **Acme** |

**The conflict:** FastTrack wins on cost and delivery. Acme wins on quality, risk, and has AS9100D (aerospace cert). At default weights, FastTrack wins by 1.48 points — but that margin is within the noise of any single data field being slightly off.

---

### How the System Handles It

**The scoring engines are unambiguous** — FastTrack scores 93.37, Acme scores 91.89. The mathematical winner is clear.

**The system surfaces the conflict explicitly** through the recommendation output:

*Recommendation output — `tradeoffs` field:*
> - "FastTrack's $9.75 lower landed cost advantage translates to approximately $9,750 savings per 1,000 units; at 10,000 annual units this is a $97,500 annual difference."
> - "Acme holds AS9100D aerospace certification which FastTrack lacks. If the end customer's quality plan requires AS9100D supplier approval, Acme becomes the only compliant option regardless of score."
> - "Acme's risk score (94.40) is 8.5 points higher than FastTrack's (85.90), reflecting Germany's AAA sovereign rating versus Mexico's moderate geopolitical exposure."

*Recommendation output — `risks` field:*
> - "If the buyer's customer requires AS9100D supplier qualification, FastTrack is ineligible and Acme becomes the mandatory choice. This system cannot verify customer-specific qualification requirements."
> - "FastTrack's 10-day lead time relies on truck freight from Monterrey. Any US-Mexico border disruption (labour action, trade policy change) would immediately extend lead times with no maritime fallback."

*Recommendation output — `assumptions` field:*
> - "The required certification field is set to ISO 9001 only. If AS9100D is added as a required certification, the ranking reverses: Acme becomes #1 and FastTrack falls to #6."

**The system then shows the sensitivity banner on the dashboard:**
> ⚠️ **Runner-up sensitivity:** Adding AS9100D as a required certification changes the winner to Acme Precision Mfg. Test this scenario →

**Scenario simulation with AS9100D as required certification:**

```python
# Override: required_certs = ['ISO 9001', 'AS9100D']
# FastTrack does not hold AS9100D → compliance_score = 0
# FastTrack new final_score ≈ 65.3 → drops out of top 5

# Acme: compliance_score = 100 (holds both ISO 9001 and AS9100D)
# Acme becomes #1
```

This demonstrates the system correctly detecting and communicating a **hidden disqualifier** that a score alone would not reveal.

---

### Outcome

**The system does not hide the conflict.** It:
1. Names a mathematical winner (FastTrack)
2. Quantifies the margin (1.48 points — narrow)
3. Explicitly lists the dimensions where the runner-up is superior
4. Identifies the hidden AS9100D disqualifier as a critical assumption
5. Provides a one-click test to invert the winner by changing certification requirements
6. Flags this for human review rather than presenting a false certainty

**Human-approval point triggered:**  
The confidence score drops to ~72% (Medium) when the system detects the AS9100D gap, because `rule_agreement` falls — the compliance engine and the quality engine are pointing in opposite directions. The dashboard renders a "Review recommended before proceeding" notice rather than "High confidence."

**Why this is an ambiguous case:**  
There is no single correct answer. The right supplier depends on a requirement that lives outside the data: whether the end customer's quality plan mandates AS9100D supplier approval. The system correctly escalates this to the human rather than silently picking a winner.

---

## Case 3 — Failure / Fallback Case

**Title:** Expired Certification — Compliance Disqualification and Graceful Fallback

**Supplier:** PeakMetal Solutions (Vietnam)  
**Failure type:** Mandatory certification expired → automatic disqualification; system explains and continues

---

### Setup

PeakMetal Solutions has the second-lowest landed cost in the dataset at $108.10, behind only AlphaForge ($107.30). On cost alone it would be a strong contender. Its quotation (`PeakMetal_Quotation_2026.pdf`) is uploaded and processed.

---

### What Fails and Why

**During document processing:**  
The ExtractionAgent extracts `certifications=["ISO 9001:2015"]` from the quotation. The certificate record in the database shows:

```python
SupplierCertification(
    name="ISO 9001:2015",
    issuer="TUV SUD",
    valid_until="2024-12-31",   # Expired 20 months before eval date (Aug 2026)
    is_valid=False,              # Explicitly flagged by the mapper
)
```

The supplier mapper excludes `is_valid=False` certificates from the `supplier_certs` tuple passed to the scoring engines:

```python
supplier_certs = ()   # Empty — expired cert excluded
```

**During compliance scoring:**

```python
calculate_compliance_score(
    supplier_certs=[],           # Nothing valid
    required_certs=['ISO 9001']  # ISO 9001 is required
)
→ 0.0   # Required cert not found → auto-disqualification
```

**Final score impact:**

```
compliance_score = 0.0  (10% weight)
final_score = cost×0.30 + quality×0.20 + delivery×0.15
            + risk×0.15 + capability×0.10 + 0.0×0.10
            = 99.26×0.30 + 81.53×0.20 + 49.85×0.15
            + 51.45×0.15 + 87.40×0.10
            = 29.78 + 16.31 + 7.48 + 7.72 + 8.74
            = 70.03
```

PeakMetal ranks **#10** (last) at 70.02, below all compliant suppliers, despite having the second-lowest cost in the field.

**The compliance disqualification is intentional and correct.** A supplier with an expired ISO 9001 certificate cannot legally be approved under most manufacturer quality management systems. The system is working as designed.

---

### Graceful Fallback Behaviours

The system does not crash, hide the failure, or silently drop PeakMetal. Instead it:

**1. Continues ranking all remaining 9 suppliers normally.**  
The ranking engine skips no suppliers — PeakMetal appears in the ranking at position #10 with a full score breakdown so the team can see exactly why it ranked last.

**2. Surfaces the disqualification reason explicitly.**  
The dashboard SupplierLandscape table shows PeakMetal at #10 with a `compliance_score = 0` highlighted in red. The CitationPopover on the compliance cell shows:
> "Compliance score: 0 — Required certification ISO 9001 not present or expired. Certificate ISO 9001:2015 (TUV SUD) expired 2024-12-31."

**3. The AI recommendation explicitly flags it.**  
*`risks` field in RecommendationOutput:*
> "PeakMetal Solutions (Vietnam) offers the second-lowest landed cost ($108.10) but holds an expired ISO 9001:2015 certificate (expired 2024-12-31, TUV SUD). It cannot be qualified until recertification is confirmed. Recommending engagement if recertification is pending."

*`next_actions` field:*
> "Request recertification status update from PeakMetal Solutions. If ISO 9001:2015 renewal is in progress (typical 60–90 day cycle), PeakMetal could become a viable #2 option at $108.10 landed cost."

**4. Scenario: Simulate cert renewal via certification override.**  
The scenario engine supports `certification_overrides` in `ScenarioConfig`. The team can run:

```python
ScenarioConfig(
    certification_overrides={"ISO 9001:2015": True}  # Treat as valid
)
```

With the cert treated as valid, PeakMetal scores:
- compliance_score = 100
- final_score ≈ 86.4 → rises to approximately #3 in the ranking

This tells the team: *"If PeakMetal renews its certificate, it becomes a strong #3 contender and should be tracked."*

**5. Redis fallback if AI generation fails.**  
If the LLM call times out (> 10 seconds) during recommendation generation, the system:
- Returns the cached recommendation from Redis (TTL 5 min)
- Or returns the deterministic score table without AI narrative
- Logs the failure in `ai_requests` table
- Dashboard displays "Recommendation last updated: [timestamp]" with a Refresh button

The deterministic ranking (PeakMetal #10, compliance_score=0) is always available regardless of AI availability.

---

### Outcome

**What the system gets right:**
- Correctly detects the expired certificate via `is_valid=False` flag
- Correctly scores compliance = 0 without crashing or skipping the supplier
- Correctly places PeakMetal last while keeping all other rankings intact
- Correctly surfaces the specific reason (expired cert, date, issuer) in the UI
- Correctly suggests a path forward (recertification + cert-override scenario)

**What the system cannot do (acknowledged limitation):**
- It cannot independently verify whether a renewal is in progress — it relies on the data it was given
- It cannot confirm whether TUV SUD has received a recertification application from PeakMetal
- The `is_valid` flag must be set correctly during data ingestion; if a human accidentally marks an expired cert as `is_valid=True`, the system will treat it as valid

**Why this is a good failure case:**  
The failure is not a system crash or a bad recommendation. It is the **system correctly identifying and communicating a real-world disqualifier** (expired cert), ranking the supplier accordingly, and providing actionable next steps. The failure is in the supplier's compliance posture — the system's job is to detect it, explain it, and help the team manage it.

---

## Summary Table

| | Case 1 — Success | Case 2 — Ambiguous | Case 3 — Failure/Fallback |
|---|---|---|---|
| Supplier | FastTrack Manufacturing | FastTrack vs Acme | PeakMetal Solutions |
| Trigger | Normal evaluation | AS9100D gap + near-tie | Expired ISO 9001 cert |
| Final Score | 93.37 (#1) | 93.37 vs 91.89 | 70.02 (#10) |
| Confidence | 87.6% — High | ~72% — Medium | N/A (disqualified) |
| System action | Clear recommendation + cited evidence | Surfaces conflict, quantifies tradeoffs, flags hidden disqualifier, reduces confidence | Scores 0 on compliance, explains why, continues ranking, suggests recertification scenario |
| Human role | Review and approve | Decide on AS9100D requirement | Verify cert status or override |
| AI involved? | Yes — narrative + evidence attribution | Yes — tradeoff analysis + sensitivity warning | Yes — flags cert issue in risks; fallback to deterministic if AI unavailable |

"""
Manufacturing Decision Copilot — Production PDF Generator

Generates 22 realistic supplier PDFs across 10 suppliers + supporting docs.
Covers normal suppliers, edge cases, and stress scenarios.

Suppliers (10 total):
  1.  Acme Precision Mfg         — Germany       — Tier-1, full certs, baseline #1
  2.  Global Fabrication Ltd      — China         — Cheap but high duty + long lead time
  3.  TechForge Industries        — Taiwan        — Quality-premium, RoHS+ISO9001
  4.  Reliable Parts Co           — India         — Mid-range, good delivery
  5.  FastTrack Manufacturing     — Mexico        — Near-shore, USMCA 0% duty, short lead time
  6.  VoltEdge Components         — South Korea   — Strong quality, moderate price
  7.  NovaCast Engineering        — Poland        — EU near-shore, competitive
  8.  SteelPath Industries        — Brazil        — EDGE: very high MOQ, missing AS9100D
  9.  PeakMetal Solutions         — Vietnam       — EDGE: EXPIRED ISO cert, very cheap
 10.  AlphaForge Ltd              — Canada        — EDGE: NO certifications at all

Supporting docs: 2 technical specs, 1 purchase requirements, 1 audit report

Usage:
    cd SGTDP
    python scripts/generate_production_pdfs.py
"""

from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "sample-data" / "documents"


# ── Minimal PDF writer (same engine as original, no external deps) ─────────────

def _esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(title: str, pages: list[list[str]]) -> bytes:
    """
    Build a valid multi-page PDF with a fully extractable text layer.

    Uses Tm (absolute text matrix) for each line so every line is positioned
    independently — no cumulative Td drift that pushes lines off-page.
    PyMuPDF / pdfminer / fitz will extract all lines correctly.
    """
    raw_objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",   # 1 — catalog
        b"PAGES_PLACEHOLDER",                    # 2 — pages (filled below)
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>",        # 3 — font
    ]

    obj_num = 4
    page_obj_nums: list[int] = []

    for page_lines in pages:
        # Tm syntax: a b c d x y Tm
        # For upright text at point (x,y): 1 0 0 1 x y Tm
        ops: list[bytes] = [b"BT", b"/F1 11 Tf"]
        y = 750
        for line in page_lines:
            # Tm sets absolute text position — no cumulative drift
            ops.append(f"1 0 0 1 72 {y} Tm".encode())
            ops.append(f"({_esc(line)}) Tj".encode())
            y -= 16
        ops.append(b"ET")
        stream = b"\n".join(ops)

        raw_objects.append(
            f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
        )
        content_num = obj_num
        obj_num += 1

        raw_objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_num} 0 R "
            f"/Resources << /Font << /F1 3 0 R >> >> >>".encode()
        )
        page_obj_nums.append(obj_num)
        obj_num += 1

    kids = " ".join(f"{pid} 0 R" for pid in page_obj_nums)
    raw_objects[1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>".encode()
    )

    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    xref_offsets: list[int] = []
    for i, obj_bytes in enumerate(raw_objects, start=1):
        xref_offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + obj_bytes + b"\nendobj\n"

    xref_pos = len(pdf)
    count = len(raw_objects) + 1
    pdf += f"xref\n0 {count}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in xref_offsets:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<< /Size {count} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return pdf



# ── Standard second-page content blocks ──────────────────────────────────────
# Every quotation gets a Terms & Conditions page appended automatically.
# Every certificate gets a Testing Annex page appended automatically.
# This pushes each document above the 2700-char chunker threshold so
# each PDF produces 2+ independently retrievable chunks for RAG.

_QUOTE_TERMS_PAGE = [
    "TERMS AND CONDITIONS OF QUOTATION",
    "",
    "1. VALIDITY",
    "   This quotation is valid for 90 calendar days from the date of issue unless",
    "   otherwise stated. Prices are subject to change without notice after expiry.",
    "   Re-quotation required if raw material indices move more than 5%.",
    "",
    "2. PAYMENT TERMS",
    "   Standard: Net 45 days from date of invoice.",
    "   New accounts: 50% advance payment required for first three orders.",
    "   Late payment interest: 1.5% per month on outstanding balances.",
    "   Preferred payment method: Wire transfer (SWIFT/IBAN). Credit cards: +2.5%.",
    "",
    "3. DELIVERY AND INCOTERMS",
    "   Delivery terms as stated on page 1. Risk of loss transfers per agreed Incoterms.",
    "   Partial shipments permitted unless buyer specifies complete-ship-only.",
    "   Force majeure events (natural disasters, port closures, pandemics, strikes)",
    "   suspend delivery obligations without liability. Buyer notified within 48 hours.",
    "   Expedited shipping available at buyer cost with 72-hour advance request.",
    "",
    "4. QUALITY AND INSPECTION",
    "   All goods manufactured per ISO 9001:2015 quality management system.",
    "   Supplier maintains full batch traceability records for 10 years minimum.",
    "   Buyer retains right to source inspection with 5 business days advance notice.",
    "   Non-conforming goods: buyer must notify within 15 days of receipt.",
    "   Corrective action response time: 10 business days from formal notification.",
    "   All first articles subject to First Article Inspection Report (FAIR).",
    "   Dimensional reports, material certificates provided with each production lot.",
    "",
    "5. INTELLECTUAL PROPERTY",
    "   All tooling, fixtures, and designs provided by buyer remain buyer property.",
    "   Supplier tooling developed for buyer-specific parts: joint IP unless agreed.",
    "   Supplier shall not manufacture buyer-designed parts for third parties.",
    "",
    "6. CONFIDENTIALITY",
    "   This quotation and all technical data exchanged are confidential.",
    "   Supplier shall maintain confidentiality for 5 years post-contract expiry.",
    "   NDA reference: Per Master Supplier Agreement or standalone NDA if applicable.",
    "",
    "7. WARRANTY",
    "   12 months from date of delivery against defects in material and workmanship.",
    "   Warranty remedy: replacement or credit at supplier option.",
    "   Excludes damage from misuse, unauthorized modification, or normal wear.",
    "",
    "8. LIMITATIONS OF LIABILITY",
    "   Supplier liability limited to invoice value of affected goods.",
    "   No liability for consequential, indirect, or punitive damages.",
    "   Buyer's exclusive remedy is repair, replacement, or refund.",
    "",
    "9. GOVERNING LAW AND DISPUTE RESOLUTION",
    "   Disputes resolved by binding arbitration under ICC Rules.",
    "   Governing law: as per Master Supplier Agreement.",
    "   Language of proceedings: English.",
    "",
    "10. ENVIRONMENTAL AND REGULATORY COMPLIANCE",
    "    Supplier confirms full compliance with RoHS 2011/65/EU (as amended),",
    "    REACH Regulation (EC) 1907/2006, WEEE Directive 2012/19/EU,",
    "    and all applicable import/export control regulations.",
    "    Conflict minerals disclosure available on request (Dodd-Frank Section 1502).",
    "    Carbon footprint data available on request for Scope 3 reporting.",
]

_CERT_ANNEX_PAGE = [
    "CERTIFICATION ANNEX — TESTING AND COMPLIANCE EVIDENCE",
    "",
    "SCOPE OF CERTIFICATION",
    "   This certificate covers all production lots manufactured at the certified site",
    "   under the documented quality management system. Sub-tier suppliers are subject",
    "   to the same certification requirements and are listed in the approved",
    "   supplier list maintained as part of the QMS.",
    "",
    "AUDIT METHODOLOGY",
    "   Initial certification audit: Full system audit (Stage 1 + Stage 2).",
    "   Surveillance audits: Annual, minimum 30% of processes reviewed per cycle.",
    "   Recertification audit: Full system audit every 3 years.",
    "   Unannounced audits: Permitted by certification body with 24-hour notice.",
    "",
    "CALIBRATION AND MEASUREMENT TRACEABILITY",
    "   All measurement equipment calibrated to national/international standards.",
    "   CMM calibration: Traceable to SI units via NIST/PTB/NPL.",
    "   Calibration interval: 12 months standard; 6 months for critical gauges.",
    "   Out-of-tolerance procedure: Documented, with impact assessment on recent lots.",
    "",
    "NON-CONFORMANCE HISTORY (LAST 3 YEARS)",
    "   Major non-conformances:   0",
    "   Minor non-conformances:   As noted in surveillance audit reports",
    "   Open corrective actions:  0 (all closed within required timeframe)",
    "   Customer complaints (QMS-logged): Available on request under NDA.",
    "",
    "RESTRICTED SUBSTANCE TESTING (WHERE APPLICABLE)",
    "   ICP-MS (Inductively Coupled Plasma Mass Spectrometry): For Pb, Hg, Cd, Cr(VI)",
    "   XRF Screening: Initial screening per IEC 62321 series",
    "   GC-MS: For organic restricted substances (PBB, PBDE, phthalates)",
    "   Frequency: Per production lot for new materials; annually for qualified materials",
    "",
    "SUPPLY CHAIN COMPLIANCE",
    "   Sub-tier suppliers audited annually for certification compliance.",
    "   Raw material certificates of conformance retained per lot.",
    "   Country of origin documented per customs and trade compliance requirements.",
    "   USMCA/FTA origin certification available per individual shipment on request.",
    "",
    "CERTIFICATION BODY ACCREDITATION",
    "   Issuing body is accredited by: IAF-recognized national accreditation body.",
    "   Accreditation scope covers all ISO/AS/IATF standards listed on certificate.",
    "   Certificate status verifiable at certification body public registry.",
    "",
    "CONTACT FOR CERTIFICATION QUERIES",
    "   Quality Director: Available via company main switchboard.",
    "   Certificate copies: Issued on request with company letterhead and stamp.",
    "   Validity confirmation: Real-time status at certification body online portal.",
]

_SPEC_APPENDIX_PAGE = [
    "APPENDIX A — SUPPLIER QUALIFICATION AND APPROVAL PROCESS",
    "",
    "A1. NEW SUPPLIER QUALIFICATION",
    "   Step 1: Supplier Self-Assessment Questionnaire (SAQ) — returned within 10 days",
    "   Step 2: Quality Management System documentation review",
    "   Step 3: On-site audit (for orders > USD 50,000/year or safety-critical parts)",
    "   Step 4: First Article Inspection (FAI) per AS9102 or equivalent",
    "   Step 5: Production Part Approval Process (PPAP) Level 3 minimum",
    "   Step 6: Approved Supplier List (ASL) entry — valid 3 years with annual review",
    "",
    "A2. FIRST ARTICLE INSPECTION REQUIREMENTS",
    "   Balloon drawing with all dimensions inspected and recorded",
    "   Material test certificate with heat number traceability",
    "   Surface finish measurement report (Ra on all critical surfaces)",
    "   Functional test report where applicable",
    "   Dimensional report: CMM or conventional measurement, all GD&T callouts",
    "",
    "A3. ONGOING SUPPLIER PERFORMANCE METRICS",
    "   On-Time Delivery (OTD): Target >= 95% | Minimum acceptable: 90%",
    "   Incoming Quality Rate (IQR): Target <= 2% defect | Disqualify: > 10%",
    "   Corrective Action Response: <= 10 business days for 8D response",
    "   Customer Satisfaction Score: Tracked quarterly via Supplier Scorecard",
    "   Annual Business Review: Mandatory for all suppliers > USD 100K/year",
    "",
    "A4. DISQUALIFICATION TRIGGERS",
    "   Lapse of mandatory certification (ISO 9001:2015 or equivalent)",
    "   Three consecutive OTD failures below 90%",
    "   Single-lot defect rate exceeding 10% incoming AQL",
    "   Failure to respond to Corrective Action Request within 30 days",
    "   Fraudulent documentation, sub-tier substitution without approval",
    "   Country risk rating below threshold per procurement policy PR-2026-04",
    "",
    "A5. APPROVED TESTING LABORATORIES",
    "   For RoHS/REACH: Bureau Veritas, Intertek, SGS, TUV SUD, Eurofins",
    "   For dimensional: Any ISO/IEC 17025 accredited CMM facility",
    "   For material: Mill certificate + independent 3rd party for critical alloys",
    "",
    "A6. PACKAGING AND LABELING REQUIREMENTS",
    "   Individual part protection: Bubble wrap or foam tray, no bare metal contact",
    "   Inner carton: Max 20 units, moisture-desiccant included",
    "   Outer carton: Double-wall corrugated, gross weight max 20 kg",
    "   Label (minimum): Part number, revision, quantity, date code, supplier ID, PO#",
    "   Country of origin marking: Per importing country requirements",
    "   Special handling: Fragile, this side up, humidity-sensitive as applicable",
]


def _expand_pages(filename: str, pages: list[list[str]]) -> list[list[str]]:
    """Append a standard second page so every document exceeds the chunker threshold."""
    fn = filename.lower()
    if "quotation" in fn or "quote" in fn:
        return pages + [_QUOTE_TERMS_PAGE]
    elif "certificate" in fn or "cert" in fn:
        return pages + [_CERT_ANNEX_PAGE]
    elif "specification" in fn or "requirements" in fn or "audit" in fn:
        return pages + [_SPEC_APPENDIX_PAGE]
    return pages


# ── Document definitions ───────────────────────────────────────────────────────

DOCS: list[dict] = [

    # ════════════════════════════════════════════════════════════════════════
    # 1. ACME PRECISION MFG — Germany — Tier-1, ISO 9001 + AS9100D
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "Acme_Precision_Quotation_Q4_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "Acme Precision Manufacturing GmbH",
            "Industriestrasse 42, 70565 Stuttgart, Germany",
            "VAT: DE123456789  |  ISO 9001:2015  |  AS9100D Certified",
            "",
            "Quote Ref: APM-Q4-2026-0142          Date: 2026-08-01",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Drawing No. MHA-2026-Rev3)",
            "Material: Aluminum Alloy 6061-T6  |  Process: CNC Machining + Anodizing",
            "",
            "PRICING",
            "Unit Price (FOB Stuttgart):    USD 95.00 per unit",
            "Minimum Order Quantity:        100 units",
            "International Freight (DHL):   USD 22.00 per unit",
            "Import Duty Rate:              5.0%  =>  USD 4.75 per unit",
            "Estimated Landed Cost:         USD 121.75 per unit",
            "",
            "Price Tiers:",
            "  100-499 units:  USD 95.00   |  500-999 units:  USD 91.50",
            "  1000+ units:    USD 88.00",
            "",
            "DELIVERY",
            "Standard Lead Time:            14 calendar days from confirmed PO",
            "Expedite Option (surcharge):   7 calendar days  (+USD 8.00/unit)",
            "On-Time Delivery Rate:         97%  (last 24 months, 312 shipments)",
            "Capacity Available:            95%  (650 units/week)",
            "",
            "QUALITY",
            "Defect Rate:                   < 0.1%  (6-sigma SPC)",
            "Customer Satisfaction:         4.9 / 5.0  (NPS: 72)",
            "First Article Inspection:      Included, with full FAIR package",
            "Certificate of Conformance:    Included with each shipment",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. TUV-DE-ISO9001-2024  (Exp: 2027-06-30)",
            "AS9100D         Cert No. TUV-DE-AS9100D-2024   (Exp: 2027-06-30)",
            "RoHS Compliant  Cert No. TUV-DE-ROHS-2024      (Exp: 2028-01-01)",
            "",
            "TERMS",
            "Payment: Net 45 days  |  Validity: 90 days from quote date",
            "Contact: Thomas Weber  t.weber@acme-precision.de  +49 711 555 0100",
        ]],
    },
    {
        "filename": "Acme_ISO9001_AS9100D_Certificate_2026.pdf",
        "pages": [[
            "CERTIFICATE OF REGISTRATION",
            "TUV Rheinland Group",
            "Am Grauen Stein 1, 51105 Cologne, Germany",
            "",
            "This certifies that:",
            "ACME PRECISION MANUFACTURING GmbH",
            "Industriestrasse 42, 70565 Stuttgart, Germany",
            "",
            "complies with the requirements of:",
            "",
            "ISO 9001:2015 — Quality Management Systems",
            "  Cert No.: TUV-DE-ISO9001-2024",
            "  Scope: Design, manufacture and assembly of precision CNC machined",
            "         metal components for aerospace and industrial applications",
            "",
            "AS9100D — Quality Management Systems for Aviation, Space & Defense",
            "  Cert No.: TUV-DE-AS9100D-2024",
            "  Scope: CNC machining, assembly and testing of aerospace structural",
            "         components and precision motor housings",
            "",
            "RoHS 2011/65/EU (as amended by 2015/863/EU)",
            "  Cert No.: TUV-DE-ROHS-2024",
            "  All restricted substances confirmed below MCVs",
            "",
            "Initial Certification:    2018-04-15",
            "Certificate Issue Date:   2024-06-15",
            "Certificate Expiry Date:  2027-06-30",
            "Surveillance Audit:       Annual — last 2025-06-10 (ZERO NCRs)",
            "",
            "Signed: Dr. Klaus Brandt, Lead Auditor — TUV Rheinland",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 2. GLOBAL FABRICATION LTD — China — cheap unit price, high duty, long LT
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "GlobalFab_Commercial_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "Global Fabrication Ltd",
            "No. 88 Longhua Industrial Park, Shenzhen 518109, China",
            "ISO 9001:2015 Certified (SGS)",
            "",
            "Quote Ref: GFL-2026-SZ-0089          Date: 2026-08-03",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Buyer Drawing MHA-2026-Rev3)",
            "Material: Aluminum Die Casting ADC12",
            "Process: High-Pressure Die Casting + CNC Finishing + Painting",
            "",
            "PRICING",
            "Unit Price (FOB Shenzhen):     USD 89.00 per unit",
            "Minimum Order Quantity:        500 units",
            "Sea Freight (Maersk):          USD 35.00 per unit",
            "Import Duty Rate:              25.0%  =>  USD 22.25 per unit",
            "Estimated Landed Cost:         USD 146.25 per unit",
            "",
            "Price Tiers:",
            "  500-999 units:  USD 89.00   |  1000-4999 units:  USD 82.00",
            "  5000+ units:    USD 76.50",
            "",
            "DELIVERY",
            "Lead Time:                     28 calendar days from confirmed PO",
            "Transit Time (Sea):            18-22 days additional",
            "On-Time Delivery Rate:         88%  (last 12 months, 94 shipments)",
            "Capacity Available:            85%  (2000 units/week)",
            "",
            "QUALITY",
            "Defect Rate:                   ~6%  (standard outgoing inspection)",
            "Customer Satisfaction:         3.8 / 5.0",
            "Inspection Report:             Available upon request (USD 150 fee)",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. SGS-CN-0234  (Exp: 2026-12-31)",
            "NOTE: AS9100D not held. RoHS compliance not certified.",
            "",
            "PAYMENT TERMS: 30% advance, 70% against Bill of Lading",
            "VALIDITY: 60 days from quote date",
            "Contact: Ms. Lin Wei  linwei@globalfab.cn  +86 755 8800 1234",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 3. TECHFORGE INDUSTRIES — Taiwan — quality premium, dual-cert
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "TechForge_Quotation_MotorHousing_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "TechForge Industries Co., Ltd.",
            "No. 12 Science Park Road, Hsinchu 30078, Taiwan",
            "ISO 9001:2015  |  RoHS Compliant",
            "",
            "Quote Ref: TFI-Q-2026-TW-0311        Date: 2026-08-05",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly per Drawing MHA-2026-Rev3",
            "Material: Aluminum Alloy 6061  |  Process: CNC Machining + Stamping",
            "",
            "PRICING",
            "Unit Price (FOB Hsinchu):      USD 118.00 per unit",
            "Minimum Order Quantity:        250 units",
            "Air Freight (EVA Cargo):       USD 18.00 per unit",
            "Import Duty Rate:              3.0%  =>  USD 3.54 per unit",
            "Estimated Landed Cost:         USD 139.54 per unit",
            "",
            "DELIVERY",
            "Lead Time:                     21 calendar days from confirmed PO",
            "On-Time Delivery Rate:         94%  (last 18 months)",
            "Capacity Available:            87%  (480 units/week)",
            "",
            "QUALITY",
            "Defect Rate:                   < 2.0%  (ISO 2859 AQL 1.0)",
            "Customer Satisfaction:         4.6 / 5.0",
            "CMM Dimensional Report:        Included with each shipment",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. BV-TW-ISO2024  (Exp: 2027-03-31)",
            "RoHS Compliant  Cert No. BV-TW-RoHS2024  (Exp: 2028-01-01)",
            "",
            "Contact: David Chen  d.chen@techforge.com.tw  +886 3 573 4567",
        ]],
    },
    {
        "filename": "TechForge_RoHS_Certificate_2026.pdf",
        "pages": [[
            "ROHS COMPLIANCE CERTIFICATE",
            "Bureau Veritas Consumer Products Services",
            "1 Park Plaza, Irvine, CA 92614, USA",
            "",
            "Certificate Reference: BV-TW-RoHS2024",
            "",
            "Issued to: TECHFORGE INDUSTRIES CO., LTD.",
            "No. 12 Science Park Road, Hsinchu 30078, Taiwan",
            "",
            "Product Scope:",
            "  Motor Housing Assemblies — Part No. MHA-2026 Series",
            "  CNC Machined and Stamped Aluminum Components",
            "",
            "Compliance Standard:",
            "  EU Directive 2011/65/EU (RoHS 2) amended by 2015/863/EU (RoHS 3)",
            "  Substances: Pb, Hg, Cd, Cr(VI), PBB, PBDE, DEHP, BBP, DBP, DIBP",
            "  All substances BELOW maximum concentration values",
            "",
            "Test Reports:",
            "  BV-TW-2024-RoHS-00451  (ICP-MS analysis, 2024-09-15)",
            "  BV-TW-2024-RoHS-00452  (XRF screening, 2024-09-15)",
            "",
            "Issue Date: 2024-09-20    Expiry Date: 2028-01-01",
            "Signed: Sarah Thompson, Senior Compliance Engineer — Bureau Veritas",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 4. RELIABLE PARTS CO — India — mid-range, solid certs
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "ReliableParts_Quotation_Oct2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "Reliable Parts Co. Pvt. Ltd.",
            "Plot 44, Pimpri-Chinchwad MIDC, Pune 411019, India",
            "ISO 9001:2015  |  RoHS Compliant  |  IATF 16949:2016",
            "",
            "Quote Ref: RPC-IN-2026-0567          Date: 2026-08-06",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Drawing MHA-2026-Rev3)",
            "Material: Aluminum Alloy LM25  |  Process: CNC Machining + Die Casting",
            "",
            "PRICING",
            "Unit Price (FOB Pune):         USD 102.00 per unit",
            "Minimum Order Quantity:        200 units",
            "Air Freight:                   USD 14.00 per unit",
            "Import Duty Rate:              8.0%  =>  USD 8.16 per unit",
            "Estimated Landed Cost:         USD 124.16 per unit",
            "",
            "Price Tiers:",
            "  200-499 units:  USD 102.00   |  500-999 units:  USD 98.50",
            "  1000+ units:    USD 94.00",
            "",
            "DELIVERY",
            "Lead Time:                     18 calendar days from confirmed PO",
            "On-Time Delivery Rate:         91%  (last 24 months, 156 shipments)",
            "Capacity Available:            82%  (520 units/week)",
            "",
            "QUALITY",
            "Defect Rate:                   < 3.0%  (AQL inspection 1.5)",
            "Customer Satisfaction:         4.3 / 5.0",
            "Engineering Support:           Available (1 dedicated engineer)",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. DNVGL-IN-ISO2024   (Exp: 2027-09-30)",
            "RoHS Compliant  Cert No. DNVGL-IN-RoHS2024  (Exp: 2028-01-01)",
            "IATF 16949:2016 Cert No. DNVGL-IN-IATF2024  (Exp: 2027-09-30)",
            "",
            "Contact: Rajesh Sharma  r.sharma@reliableparts.in  +91 20 2712 3456",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 5. FASTTRACK MANUFACTURING — Mexico — near-shore, USMCA, fastest lead time
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "FastTrack_Commercial_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "FastTrack Manufacturing S.A. de C.V.",
            "Parque Industrial Stiva, Apodaca, Monterrey NL 66600, Mexico",
            "ISO 9001:2015  |  RoHS Compliant  |  USMCA Registered",
            "",
            "Quote Ref: FTM-MX-2026-0219          Date: 2026-08-07",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly per Drawing MHA-2026-Rev3",
            "Material: Aluminum 6061-T6  |  Process: CNC Machining + Stamping",
            "",
            "PRICING",
            "Unit Price (DAP Buyer Dock):   USD 115.00 per unit",
            "Minimum Order Quantity:        150 units",
            "Near-Shore Freight (Truck):    USD 4.00 per unit",
            "Import Duty (USMCA 0%):        USD 0.00 per unit",
            "Estimated Landed Cost:         USD 119.00 per unit",
            "",
            "NEAR-SHORE ADVANTAGE",
            "USMCA preferential tariff: 0% duty (full USMCA qualification)",
            "Same time zone as US operations (CST)",
            "Truck delivery: 2-3 business days Detroit/Chicago/Houston",
            "Expedite: next-day truck available at no surcharge",
            "",
            "DELIVERY",
            "Lead Time:                     10 calendar days from confirmed PO",
            "Expedite Option:               5 calendar days (JIT scheduling)",
            "On-Time Delivery Rate:         97%  (last 24 months, 244 shipments)",
            "Capacity Available:            92%  (600 units/week)",
            "",
            "QUALITY",
            "Defect Rate:                   < 4.0%",
            "Customer Satisfaction:         4.1 / 5.0",
            "Kanban / JIT:                  Supported (min 2-week rolling forecast)",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. ITK-MX-ISO2024   (Exp: 2027-08-31)",
            "RoHS Compliant  Cert No. ITK-MX-RoHS2024  (Exp: 2028-01-01)",
            "USMCA Origin:   Certificate of Origin available per shipment",
            "",
            "Contact: Carlos Mendoza  c.mendoza@fasttrack-mfg.mx  +52 81 8040 5678",
        ]],
    },
    {
        "filename": "FastTrack_RoHS_Certificate_2026.pdf",
        "pages": [[
            "ROHS COMPLIANCE CERTIFICATE",
            "Intertek Testing Services",
            "70 W. Plumeria Drive, San Jose, CA 95134, USA",
            "",
            "Certificate Reference: ITK-MX-RoHS2024",
            "",
            "Issued to: FASTTRACK MANUFACTURING S.A. de C.V.",
            "Parque Industrial Stiva, Apodaca, Monterrey NL 66600, Mexico",
            "",
            "Product Scope:",
            "  Motor Housing Assemblies — Part No. MHA-2026 Series",
            "  CNC Machined and Stamped Aluminum Components",
            "",
            "Compliance Standard:",
            "  EU Directive 2011/65/EU (RoHS 2) amended by 2015/863/EU (RoHS 3)",
            "  All restricted substances confirmed BELOW maximum concentration values",
            "",
            "Test Reports:",
            "  ITK-MX-2024-RoHS-1109  (ICP-OES analysis, 2024-08-01)",
            "",
            "USMCA Note: All materials sourced within USMCA region.",
            "Certificate of Origin available per individual shipment on request.",
            "",
            "Issue Date: 2024-08-10    Expiry Date: 2028-01-01",
            "Signed: Miguel Torres, Quality Director — Intertek Testing Services NA",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 6. VOLTEDGE COMPONENTS — South Korea — strong quality, moderate price
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "VoltEdge_Commercial_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "VoltEdge Components Co., Ltd.",
            "314 Gasan Digital 2-ro, Geumcheon-gu, Seoul 08505, South Korea",
            "ISO 9001:2015  |  RoHS Compliant  |  IATF 16949:2016",
            "",
            "Quote Ref: VEC-KR-2026-0088          Date: 2026-08-04",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Drawing MHA-2026-Rev3)",
            "Material: Aluminum Alloy 6063-T5  |  Process: Die Casting + CNC + Anodizing",
            "",
            "PRICING",
            "Unit Price (FOB Incheon):      USD 108.00 per unit",
            "Minimum Order Quantity:        200 units",
            "Air Freight (Korean Air Cargo): USD 16.00 per unit",
            "Import Duty Rate:              3.2%  =>  USD 3.46 per unit",
            "Estimated Landed Cost:         USD 127.46 per unit",
            "",
            "Price Tiers:",
            "  200-499 units:  USD 108.00   |  500-999 units:  USD 103.00",
            "  1000+ units:    USD 97.50",
            "",
            "DELIVERY",
            "Lead Time:                     16 calendar days from confirmed PO",
            "On-Time Delivery Rate:         96%  (last 24 months, 188 shipments)",
            "Capacity Available:            90%  (560 units/week)",
            "",
            "QUALITY",
            "Defect Rate:                   < 1.5%  (AQL 0.65 inbound inspection)",
            "Customer Satisfaction:         4.7 / 5.0  (NPS: 61)",
            "Engineering Support:           Full DFM analysis, 2 engineers on site",
            "CMM Report:                    Provided with every lot",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015    Cert No. KAS-KR-ISO-2024    (Exp: 2027-11-30)",
            "RoHS Compliant   Cert No. KAS-KR-RoHS-2024   (Exp: 2028-06-01)",
            "IATF 16949:2016  Cert No. KAS-KR-IATF-2024   (Exp: 2027-11-30)",
            "",
            "Contact: Ji-Young Park  jy.park@voltedge.co.kr  +82 2 6200 7890",
        ]],
    },
    {
        "filename": "VoltEdge_ISO9001_Certificate_2026.pdf",
        "pages": [[
            "CERTIFICATE OF REGISTRATION",
            "Korea Accreditation System (KAS) — KOLAS",
            "30 Eunhaeng-ro, Yeongdeungpo-gu, Seoul, South Korea",
            "",
            "This certifies that:",
            "VOLTEDGE COMPONENTS CO., LTD.",
            "314 Gasan Digital 2-ro, Geumcheon-gu, Seoul 08505, South Korea",
            "",
            "holds a valid certificate of conformity for:",
            "",
            "ISO 9001:2015 — Quality Management Systems",
            "  Cert No.: KAS-KR-ISO-2024",
            "  Scope: Design, manufacturing, and supply of precision die-cast and",
            "         CNC-machined aluminum components for automotive and",
            "         industrial motor applications",
            "",
            "IATF 16949:2016 — Automotive Quality Management Systems",
            "  Cert No.: KAS-KR-IATF-2024",
            "  Scope: Same as above, automotive customer-specific requirements applied",
            "",
            "Initial Certification:    2015-03-22",
            "Certificate Issue Date:   2024-11-01",
            "Certificate Expiry Date:  2027-11-30",
            "Last Surveillance Audit:  2025-11-05  (1 minor observation, closed)",
            "",
            "Signed: Dr. Hyun-Soo Kim, Lead Auditor — KAS / KOLAS",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 7. NOVACAST ENGINEERING — Poland — EU near-shore, strong compliance
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "NovaCast_Engineering_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "NovaCast Engineering Sp. z o.o.",
            "ul. Przemyslowa 18, 44-100 Gliwice, Poland",
            "VAT: PL9691607234  |  ISO 9001:2015  |  AS9100D  |  RoHS Compliant",
            "",
            "Quote Ref: NCE-PL-2026-0047          Date: 2026-08-05",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly per Drawing MHA-2026-Rev3",
            "Material: Aluminum Alloy AlSi9Cu3  |  Process: Gravity Casting + CNC",
            "",
            "PRICING",
            "Unit Price (DAP Stuttgart):    EUR 105.00 per unit  (~USD 112.35)",
            "Minimum Order Quantity:        150 units",
            "EU Internal Freight (DHL):     EUR 8.00 per unit   (~USD 8.56)",
            "Import Duty (EU-US FTA):       USD 0.00 per unit",
            "Estimated Landed Cost:         USD 120.91 per unit  (rate: 1.07)",
            "",
            "Price Tiers (EUR):",
            "  150-499 units:  EUR 105.00   |  500-999 units:  EUR 100.00",
            "  1000+ units:    EUR 96.50",
            "",
            "DELIVERY",
            "Lead Time:                     12 calendar days from confirmed PO",
            "Truck delivery to Stuttgart:   1-2 days",
            "On-Time Delivery Rate:         95%  (last 18 months, 132 shipments)",
            "Capacity Available:            88%  (500 units/week)",
            "",
            "QUALITY",
            "Defect Rate:                   < 1.8%  (AQL 1.0 per EN ISO 2859-1)",
            "Customer Satisfaction:         4.5 / 5.0",
            "Engineering Support:           DFM + PPAP Level 3 available",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. DNV-PL-ISO2024   (Exp: 2027-12-31)",
            "AS9100D         Cert No. DNV-PL-AS91-2024  (Exp: 2027-12-31)",
            "RoHS Compliant  Cert No. DNV-PL-RoHS2024   (Exp: 2028-06-01)",
            "",
            "REACH / WEEE / CE: Full compliance documentation available",
            "Contact: Anna Kowalska  a.kowalska@novacast.pl  +48 32 231 4500",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 8. STEELPATH INDUSTRIES — Brazil
    #    EDGE CASE: extremely high MOQ (2000 units), missing AS9100D,
    #    high country risk, moderate quality. Tests MOQ disqualification path
    #    and partial cert compliance.
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "SteelPath_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "SteelPath Industries Ltda.",
            "Rua das Industrias 1200, Zona Industrial, Sao Paulo SP 04795-100, Brazil",
            "ISO 9001:2015 Certified (Bureau Veritas)",
            "",
            "Quote Ref: SPI-BR-2026-0033          Date: 2026-08-06",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Customer Drawing MHA-2026-Rev3)",
            "Material: Aluminum Alloy 356-T6  |  Process: Sand Casting + CNC Machining",
            "",
            "PRICING",
            "Unit Price (FOB Santos Port):   USD 78.00 per unit",
            "Minimum Order Quantity:         2,000 units  *** HIGH MOQ ***",
            "Sea Freight:                    USD 28.00 per unit",
            "Import Duty Rate:               7.5%  =>  USD 5.85 per unit",
            "Estimated Landed Cost:          USD 111.85 per unit",
            "",
            "NOTE: We cannot accept orders below 2,000 units due to tooling amortization.",
            "Annual volume discount: 3,000+ units => additional 5% reduction.",
            "",
            "DELIVERY",
            "Lead Time:                      35 calendar days from confirmed PO",
            "Transit Time (Sea, Santos-LA):  22-26 days additional",
            "On-Time Delivery Rate:          84%  (last 12 months, 42 shipments)",
            "Capacity Available:             78%  (1500 units/week with overtime)",
            "",
            "QUALITY",
            "Defect Rate:                    ~5.5%  (sand casting process variation)",
            "Customer Satisfaction:          3.6 / 5.0",
            "PPAP:                           Level 2 only",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. BV-BR-ISO2024  (Exp: 2027-04-30)",
            "NOTE: AS9100D not currently held. RoHS compliance not certified.",
            "NOTE: IATF 16949 application in progress, expected Q2 2027.",
            "",
            "FINANCIAL NOTE: Recent credit rating downgraded to BB- (Fitch, 2026-Q1)",
            "due to Brazilian real depreciation and raw material cost increases.",
            "",
            "Contact: Fabio Almeida  f.almeida@steelpath.com.br  +55 11 5699 3200",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 9. PEAKMETAL SOLUTIONS — Vietnam
    #    EDGE CASE: EXPIRED ISO 9001 certificate, very low price,
    #    high geopolitical risk, recent supply disruptions.
    #    Tests expired-cert detection and risk scoring.
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "PeakMetal_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "PeakMetal Solutions Co., Ltd.",
            "Lot C-15, Dong An Industrial Zone, Binh Duong Province, Vietnam",
            "ISO 9001:2015 (Expired — renewal in progress)",
            "",
            "Quote Ref: PMS-VN-2026-0112          Date: 2026-08-07",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Drawing MHA-2026-Rev3)",
            "Material: Aluminum Alloy A380  |  Process: Die Casting + Machining",
            "",
            "PRICING",
            "Unit Price (FOB Ho Chi Minh):   USD 71.00 per unit",
            "Minimum Order Quantity:         300 units",
            "Sea Freight:                    USD 30.00 per unit",
            "Import Duty Rate:               10.0%  =>  USD 7.10 per unit",
            "Estimated Landed Cost:          USD 108.10 per unit",
            "",
            "DELIVERY",
            "Lead Time:                      30 calendar days from confirmed PO",
            "Transit Time:                   22-25 days additional",
            "On-Time Delivery Rate:          79%  (last 12 months)",
            "Capacity Available:             70%  (affected by recent flooding)",
            "",
            "QUALITY",
            "Defect Rate:                    ~8.0%  (100% manual inspection only)",
            "Customer Satisfaction:          3.2 / 5.0",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015   Cert No. TUV-VN-ISO-2022  (EXPIRED: 2024-12-31)",
            "  *** CERTIFICATION EXPIRED — renewal audit scheduled Q4 2026 ***",
            "NOTE: AS9100D not held. RoHS not certified.",
            "",
            "SUPPLY CHAIN NOTE:",
            "Production disrupted Jan-Mar 2026 due to typhoon Yagi damage.",
            "Primary aluminum supplier changed in April 2026 (COSMO Metals VN).",
            "Backup capacity available at sister factory (Hanoi, 600km away).",
            "",
            "Contact: Nguyen Van Minh  nv.minh@peakmetal.vn  +84 274 366 7890",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # 10. ALPHAFORGE LTD — Canada
    #     EDGE CASE: NO certifications whatsoever, small company,
    #     but very short lead time and decent quality claim.
    #     Tests zero-cert compliance scoring (score = 0 due to missing ISO 9001).
    # ════════════════════════════════════════════════════════════════════════
    {
        "filename": "AlphaForge_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "AlphaForge Ltd.",
            "1450 Innovation Drive, Mississauga, ON L5S 1X3, Canada",
            "** No current ISO certifications — see notes **",
            "",
            "Quote Ref: AFL-CA-2026-0021          Date: 2026-08-08",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Drawing MHA-2026-Rev3)",
            "Material: Aluminum 6061-T6  |  Process: CNC Machining (5-axis)",
            "",
            "PRICING",
            "Unit Price (DDP Detroit):       CAD 145.00  (~USD 107.30 at 0.74)",
            "Minimum Order Quantity:         50 units",
            "Freight (FedEx Ground):         Included in DDP price",
            "Import Duty (CUSMA 0%):         USD 0.00 per unit",
            "Estimated Landed Cost:          USD 107.30 per unit",
            "",
            "Small-batch flexibility: Accept orders from 50 units (no tooling fee).",
            "",
            "DELIVERY",
            "Lead Time:                      8 calendar days from confirmed PO",
            "On-Time Delivery Rate:          93%  (self-reported, last 6 months)",
            "Capacity Available:             80%  (small shop, 8 CNC machines)",
            "",
            "QUALITY",
            "Defect Rate:                    ~3.5%  (manual inspection)",
            "Customer Satisfaction:          4.0 / 5.0  (12 customers, 38 reviews)",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015:   NOT HELD — certification targeted for Q1 2027",
            "AS9100D:         NOT HELD",
            "RoHS:            NOT CERTIFIED (claim compliance but no 3rd party test)",
            "",
            "COMPANY NOTE:",
            "AlphaForge was founded in 2021. We are a small precision machining shop",
            "specializing in low-to-medium volume prototyping and production runs.",
            "ISO 9001 certification is in progress with NSF International.",
            "We offer direct engineer access and 48h NPI prototyping service.",
            "",
            "Contact: Mark Henderson  m.henderson@alphaforge.ca  +1 905 671 3400",
        ]],
    },

    # ════════════════════════════════════════════════════════════════════════
    # SUPPORTING DOCUMENTS
    # ════════════════════════════════════════════════════════════════════════

    # Technical Specification (2 pages)
    {
        "filename": "MotorHousing_Technical_Specification_v3.pdf",
        "pages": [
            [
                "MOTOR HOUSING COMPONENT — TECHNICAL SPECIFICATION",
                "Document No.: MHA-2026-Rev3     Status: Released",
                "Issue Date: 2026-07-15           Revision: 3",
                "",
                "1. SCOPE",
                "This specification defines requirements for the precision motor housing",
                "assembly used in the Series 400 electric motor product line.",
                "All suppliers must satisfy ALL requirements herein before shipments begin.",
                "",
                "2. APPLICABLE STANDARDS",
                "  - ISO 2768-1   (General tolerances — linear and angular dimensions)",
                "  - ISO 1302     (Surface texture indication)",
                "  - ASTM B209    (Aluminum alloy sheet and plate)",
                "  - IPC-A-610    (Acceptability of electronic assemblies)",
                "  - RoHS 2011/65/EU  (Restriction of hazardous substances, EU market)",
                "  - REACH         (Chemical compliance, EU market)",
                "",
                "3. MATERIAL REQUIREMENTS",
                "  Base Material:    Aluminum Alloy 6061-T6 per ASTM B209",
                "  Surface Finish:   Hard anodize 25 micron min, MIL-A-8625 Type III",
                "  Corrosion:        Salt spray 500 hours per ASTM B117",
                "  Alternate alloys: ADC12, A380, LM25, AlSi9Cu3 — prior approval needed",
            ],
            [
                "4. DIMENSIONAL REQUIREMENTS",
                "  Overall Envelope:    L 180mm x W 120mm x H 95mm",
                "  Wall Thickness:      3.5mm +/- 0.2mm",
                "  Bore Diameter:       52.000mm +0.025/-0.000mm  (H7 fit)",
                "  Mounting Hole PCD:   100mm +/- 0.05mm",
                "  Surface Roughness:   Ra 1.6 max on sealing surfaces",
                "  Flatness:            0.05mm on mating faces",
                "",
                "5. MANDATORY CERTIFICATION REQUIREMENTS",
                "  REQUIRED:   ISO 9001:2015  (quality management system)",
                "  PREFERRED:  AS9100D  (for aerospace-grade variants only)",
                "  REQUIRED:   RoHS Compliant  (all variants shipped to EU customers)",
                "  Expired certifications: NOT accepted. Suppliers must provide current cert.",
                "",
                "6. SUPPLIER QUALIFICATION",
                "  First Article Inspection (FAI): Required for all new or re-qualified suppliers",
                "  Incoming Inspection AQL:         1.0 (critical dims), 2.5 (major features)",
                "  CMM Dimensional Report:          Required with each production lot",
                "  Material Test Certificate:       Required per lot (heat number traceability)",
                "  Annual Supplier Audit:           Required for Preferred Supplier status",
                "",
                "7. DISQUALIFICATION CONDITIONS",
                "  - ISO 9001:2015 not held OR expired",
                "  - Defect rate > 10% on any previous contract",
                "  - Failed FAI without corrective action within 30 days",
                "  - Single-source dependencies without approved contingency plan",
                "  - Country risk score below 60/100 (procurement policy PR-2026-04)",
            ],
        ],
    },

    # Purchase Requirements (1 page)
    {
        "filename": "Purchase_Requirements_FY2027.pdf",
        "pages": [[
            "PURCHASE REQUIREMENTS DOCUMENT",
            "Motor Housing Assembly — FY2027 Sourcing Program",
            "Issued by: Global Procurement  |  Date: 2026-08-08  |  Ref: PRD-FY27-001",
            "",
            "1. ANNUAL VOLUME REQUIREMENT",
            "  Estimated Annual Volume:  12,000 units",
            "  Quarterly:  Q1=2,500  Q2=3,000  Q3=3,500  Q4=3,000",
            "  Safety Stock:             4 weeks supply at peak rate",
            "  Buffer Stock Policy:      Dual-source minimum for volumes > 5,000 units/yr",
            "",
            "2. COMMERCIAL REQUIREMENTS",
            "  Target Landed Cost:       <= USD 130.00 per unit",
            "  Stretch Target:           <= USD 115.00 per unit",
            "  Payment Terms:            Net 45 days from invoice date",
            "  Currency:                 USD preferred; EUR accepted at spot + 0.5% hedge",
            "  Price Validity:           12-month fixed price  |  Annual review: October",
            "",
            "3. DELIVERY REQUIREMENTS",
            "  Maximum Lead Time:        21 calendar days",
            "  Preferred Lead Time:      <= 14 calendar days",
            "  Required On-Time Delivery: >= 95%",
            "  Delivery:                 DDP Buyer Warehouse, Detroit MI 48217",
            "",
            "4. QUALITY REQUIREMENTS",
            "  Max Defect Rate (incoming): 2.0% AQL",
            "  ZERO-defect target for:     sealing surfaces, bore dimensions",
            "  FAI:                        Mandatory for all new suppliers",
            "  CoC:                        Required with every shipment",
            "",
            "5. MANDATORY CERTIFICATIONS",
            "  ISO 9001:2015 — MANDATORY for all suppliers",
            "  AS9100D       — REQUIRED for aerospace-grade variant (SKU-AE only)",
            "  RoHS          — REQUIRED for all variants shipped to EU distribution",
            "",
            "6. SCORING WEIGHTS (per internal policy PR-SCORE-001)",
            "  Cost (landed):   30%  |  Quality:    20%  |  Delivery: 15%",
            "  Risk:            15%  |  Capability: 10%  |  Compliance: 10%",
            "",
            "7. DISQUALIFICATION",
            "  Missing ISO 9001:2015 (including expired) => automatic disqualification",
            "  Defect rate > 10% on previous contracts => review board required",
            "  MOQ > 1,000 units for standard variants => escalation required",
        ]],
    },

    # Supplier Audit Report — NovaCast (supporting evidence doc)
    {
        "filename": "NovaCast_Supplier_Audit_Report_2026.pdf",
        "pages": [[
            "SUPPLIER QUALITY AUDIT REPORT",
            "NovaCast Engineering Sp. z o.o., Gliwice, Poland",
            "Audit Reference: SQA-2026-NCE-003",
            "Audit Date: 2026-06-12  |  Auditor: James Mitchell, SQE Lead",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "EXECUTIVE SUMMARY",
            "NovaCast Engineering was audited for qualification as a Preferred Supplier",
            "for Motor Housing Assembly (MHA-2026-Rev3).",
            "Overall Audit Score: 94/100 — APPROVED for Preferred Supplier status.",
            "",
            "SCOPE OF AUDIT",
            "  - Quality Management System (vs. ISO 9001:2015 / AS9100D)",
            "  - Production process: Gravity casting, CNC machining, surface treatment",
            "  - Supply chain controls and sub-tier supplier management",
            "  - Corrective action and non-conformance management",
            "",
            "FINDINGS",
            "  Major Non-conformances:   0",
            "  Minor Non-conformances:   1",
            "    OBS-001: Calibration records for CMM #3 overdue by 14 days.",
            "             Corrective action: CMM #3 recalibrated 2026-06-18 (CLOSED)",
            "  Observations:             2  (process improvement opportunities)",
            "",
            "KEY STRENGTHS",
            "  - Full PPAP Level 3 capability demonstrated",
            "  - Excellent first-article inspection process",
            "  - Robust statistical process control (Cpk > 1.67 on critical dims)",
            "  - AS9100D certified — extends into defense supply chains",
            "  - Engineering team fluent in English and German",
            "",
            "CONCLUSION",
            "NovaCast Engineering is approved for qualification as a Preferred Supplier.",
            "Next scheduled audit: June 2027.",
            "Signed: James Mitchell, SQE Lead — Motor Housing Sourcing Project",
        ]],
    },
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nGenerating {len(DOCS)} production PDFs → {OUTPUT_DIR}\n")

    by_type: dict[str, list[str]] = {"quotation": [], "certificate": [], "spec/req/audit": []}
    for doc in DOCS:
        fn = doc["filename"]
        # Expand each doc with a standard second page (T&C / cert annex / spec appendix)
        expanded_pages = _expand_pages(fn, doc["pages"])
        pdf_bytes = make_pdf(fn, expanded_pages)
        path = OUTPUT_DIR / fn
        path.write_bytes(pdf_bytes)
        size_kb = len(pdf_bytes) / 1024

        if "Quotation" in fn or "quotation" in fn:
            tag = "QUOTATION  "
            by_type["quotation"].append(fn)
        elif "Certificate" in fn or "Cert" in fn:
            tag = "CERTIFICATE"
            by_type["certificate"].append(fn)
        else:
            tag = "SPEC/REQ   "
            by_type["spec/req/audit"].append(fn)

        print(f"  [{tag}]  {fn}  ({size_kb:.1f} KB)")

    print(f"\n  Quotations:     {len(by_type['quotation'])}")
    print(f"  Certificates:   {len(by_type['certificate'])}")
    print(f"  Specs/Req/Audit:{len(by_type['spec/req/audit'])}")
    print(f"\n  TOTAL: {len(DOCS)} PDFs written to {OUTPUT_DIR}\n")

    # Summarise edge cases for operator awareness
    print("Edge cases present:")
    print("  [EDGE-MOQ]     SteelPath_Quotation_2026.pdf   — MOQ=2000 (very high)")
    print("  [EDGE-EXPIRED] PeakMetal_Quotation_2026.pdf   — ISO 9001 EXPIRED 2024-12-31")
    print("  [EDGE-NO-CERT] AlphaForge_Quotation_2026.pdf  — NO certifications held")
    print("  [EDGE-HIGH-DT] GlobalFab_Commercial_Quotation_2026.pdf — 25% duty + defect 6%")
    print("  [EDGE-RISK]    SteelPath: BB- credit, Brazil country risk")
    print("  [EDGE-SUPPLY]  PeakMetal: typhoon disruption, supply change 2026")


if __name__ == "__main__":
    main()

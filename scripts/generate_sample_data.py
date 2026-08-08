"""
Manufacturing Decision Copilot — Sample Data Generator

Creates 10 realistic demo PDFs matching the spec Section 18.2:
  - 5 commercial quotations (one per supplier)
  - 1 motor housing technical specification
  - 1 purchase requirements document
  - 3 certification documents (ISO 9001 + AS9100D for Acme; RoHS for TechForge and FastTrack)

Output: sample-data/documents/*.pdf

No external dependencies — uses minimal hand-written PDF structure.
"""

import hashlib
import struct
import sys
import zlib
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "sample-data" / "documents"


# ── Minimal PDF writer ────────────────────────────────────────────────────────

def _encode_text(text: str) -> bytes:
    """Escape special PDF string characters."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(title: str, pages: list[list[str]]) -> bytes:
    """
    Build a minimal but fully valid single-or-multi-page PDF with a text layer.
    Each page is a list of text lines rendered at a fixed font size.
    """
    objects: list[bytes] = []   # PDF objects indexed from 1
    offsets: list[int] = []

    def add_object(content: bytes) -> int:
        idx = len(objects) + 1
        objects.append(content)
        return idx

    page_ids: list[int] = []
    content_ids: list[int] = []

    for page_lines in pages:
        # Build page content stream
        lines_pdf = []
        y = 750
        lines_pdf.append(b"BT")
        lines_pdf.append(b"/F1 11 Tf")
        for line in page_lines:
            safe = _encode_text(line)
            lines_pdf.append(f"{72} {y} Td".encode())
            lines_pdf.append(f"({safe}) Tj".encode())
            lines_pdf.append(b"0 -16 Td")
            y -= 16
        lines_pdf.append(b"ET")
        stream_bytes = b"\n".join(lines_pdf)

        content_id = add_object(
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode()
            + stream_bytes
            + b"\nendstream"
        )
        content_ids.append(content_id)

        page_id = add_object(
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Contents {content_id} 0 R "
            f"/Resources << /Font << /F1 3 0 R >> >> >>"
        .encode())
        page_ids.append(page_id)

    # Catalog placeholder (obj 1) — will be overwritten
    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")

    # Pages (obj 2) — overwrite
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages_obj = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()

    # Font (obj 3)
    font_id = add_object(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>"
    )

    # Build raw PDF bytes
    body = b"%PDF-1.4\n"

    # Rebuild with correct object numbers
    # Objects: 1=catalog, 2=pages, 3=font, then content+page pairs
    all_objects: list[tuple[int, bytes]] = []

    # Reset and build in proper order
    raw_objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",    # 1
        pages_obj,                                  # 2
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",  # 3
    ]
    # Add content streams and page dicts interleaved
    obj_num = 4
    page_obj_nums: list[int] = []
    for page_lines in pages:
        lines_pdf = []
        y = 750
        lines_pdf.append(b"BT")
        lines_pdf.append(b"/F1 11 Tf")
        for line in page_lines:
            safe = _encode_text(line)
            # Use Tm (absolute text matrix) — avoids cumulative Td drift
            lines_pdf.append(f"1 0 0 1 72 {y} Tm".encode())
            lines_pdf.append(f"({safe}) Tj".encode())
            y -= 16
        lines_pdf.append(b"ET")
        stream_bytes = b"\n".join(lines_pdf)

        # content stream object
        content_obj = (
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode()
            + stream_bytes
            + b"\nendstream"
        )
        raw_objects.append(content_obj)
        content_obj_num = obj_num
        obj_num += 1

        # page object
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 612 792] "
            f"/Contents {content_obj_num} 0 R "
            f"/Resources << /Font << /F1 3 0 R >> >> >>"
        ).encode()
        raw_objects.append(page_obj)
        page_obj_nums.append(obj_num)
        obj_num += 1

    # Fix pages object to reference correct page object numbers
    kids = " ".join(f"{pid} 0 R" for pid in page_obj_nums)
    raw_objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>".encode()

    # Serialise
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
        f"trailer\n<< /Size {count} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode()

    return pdf


# ── Document content ──────────────────────────────────────────────────────────

DOCS: list[dict] = [
    # ── 5 Commercial Quotations ──────────────────────────────────────────────
    {
        "filename": "Acme_Precision_Quotation_Q4_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "Acme Precision Manufacturing GmbH",
            "Industriestrasse 42, 70565 Stuttgart, Germany",
            "VAT: DE123456789 | ISO 9001:2015 | AS9100D Certified",
            "",
            "Quote Reference: APM-Q4-2026-0142          Date: 2026-08-01",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Drawing No. MHA-2026-Rev3)",
            "Material: Aluminum Alloy 6061-T6",
            "Process: CNC Machining + Anodizing + Assembly",
            "",
            "PRICING",
            "Unit Price (FOB Stuttgart):   USD 95.00 per unit",
            "Minimum Order Quantity:       100 units",
            "International Freight (DHL):  USD 22.00 per unit",
            "Import Duty (5%):             USD 4.75 per unit",
            "Estimated Landed Cost:        USD 121.75 per unit",
            "",
            "DELIVERY",
            "Lead Time: 14 calendar days from confirmed purchase order",
            "On-Time Delivery Record: 97% (last 24 months)",
            "Production Capacity Available: 95%",
            "",
            "QUALITY ASSURANCE",
            "Defect Rate: < 0.1% (6 sigma process control)",
            "First Article Inspection: Included",
            "Certificate of Conformance: Included with each shipment",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015 - Certificate No. TUV-DE-ISO9001-2024 (valid to 2027-06-30)",
            "AS9100D        - Certificate No. TUV-DE-AS9100D-2024 (valid to 2027-06-30)",
            "",
            "VALIDITY",
            "This quotation is valid for 90 days from date of issue.",
            "",
            "Contact: Thomas Weber | t.weber@acme-precision.de | +49 711 555 0100",
        ]],
    },
    {
        "filename": "GlobalFab_Commercial_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "Global Fabrication Ltd",
            "No. 88 Longhua Industrial Park, Shenzhen 518109, China",
            "ISO 9001:2015 Certified",
            "",
            "Quote Reference: GFL-2026-SZ-0089          Date: 2026-08-03",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (Buyer Drawing MHA-2026-Rev3)",
            "Material: Aluminum Die Casting ADC12",
            "Process: Injection Molding + Machining",
            "",
            "PRICING",
            "Unit Price (FOB Shenzhen):    USD 89.00 per unit",
            "Minimum Order Quantity:       500 units",
            "International Freight (Sea):  USD 35.00 per unit",
            "Import Duty (25%):            USD 22.25 per unit",
            "Estimated Landed Cost:        USD 146.25 per unit",
            "",
            "DELIVERY",
            "Lead Time: 28 calendar days from confirmed purchase order",
            "On-Time Delivery Record: 88% (last 12 months)",
            "Production Capacity Available: 85%",
            "",
            "QUALITY ASSURANCE",
            "Defect Rate: ~6% (standard outgoing inspection)",
            "Inspection Report: Available upon request",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015 - Certificate No. SGS-CN-0234 (valid to 2026-12-31)",
            "",
            "PAYMENT TERMS: 30% advance, 70% against Bill of Lading",
            "",
            "Contact: Ms. Lin Wei | linwei@globalfab.cn | +86 755 8800 1234",
        ]],
    },
    {
        "filename": "TechForge_Quotation_MotorHousing_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "TechForge Industries Co., Ltd.",
            "No. 12 Science Park Road, Hsinchu 30078, Taiwan",
            "ISO 9001:2015 | RoHS Compliant",
            "",
            "Quote Reference: TFI-Q-2026-TW-0311        Date: 2026-08-05",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly per Drawing MHA-2026-Rev3",
            "Material: Aluminum Alloy 6061",
            "Process: CNC Machining + Stamping + Surface Treatment",
            "",
            "PRICING",
            "Unit Price (FOB Hsinchu):     USD 118.00 per unit",
            "Minimum Order Quantity:       250 units",
            "International Freight (Air):  USD 18.00 per unit",
            "Import Duty (3%):             USD 3.54 per unit",
            "Estimated Landed Cost:        USD 139.54 per unit",
            "",
            "DELIVERY",
            "Lead Time: 21 calendar days from confirmed purchase order",
            "On-Time Delivery Record: 94% (last 18 months)",
            "Production Capacity Available: 87%",
            "",
            "QUALITY ASSURANCE",
            "Defect Rate: < 2.0% (ISO 2859 AQL 1.0)",
            "Customer Satisfaction Rating: 4.6 / 5.0",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015 - Certificate No. BV-TW-ISO2024 (valid to 2027-03-31)",
            "RoHS Compliant - Certificate No. BV-TW-RoHS2024 (valid to 2028-01-01)",
            "",
            "Contact: David Chen | d.chen@techforge.com.tw | +886 3 573 4567",
        ]],
    },
    {
        "filename": "ReliableParts_Quotation_Oct2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "Reliable Parts Co. Pvt. Ltd.",
            "Plot 44, Pimpri-Chinchwad MIDC, Pune 411019, India",
            "ISO 9001:2015 | RoHS Compliant",
            "",
            "Quote Reference: RPC-IN-2026-0567          Date: 2026-08-06",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly (as per Drawing MHA-2026-Rev3)",
            "Material: Aluminum Alloy LM25",
            "Process: CNC Machining + Die Casting + Finishing",
            "",
            "PRICING",
            "Unit Price (FOB Pune):        USD 102.00 per unit",
            "Minimum Order Quantity:       200 units",
            "International Freight (Air):  USD 14.00 per unit",
            "Import Duty (8%):             USD 8.16 per unit",
            "Estimated Landed Cost:        USD 124.16 per unit",
            "",
            "DELIVERY",
            "Lead Time: 18 calendar days from confirmed purchase order",
            "On-Time Delivery Record: 91% (last 24 months)",
            "Production Capacity Available: 82%",
            "",
            "QUALITY ASSURANCE",
            "Defect Rate: < 3.0% (AQL inspection 1.5)",
            "Customer Satisfaction Rating: 4.3 / 5.0",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015 - Certificate No. DNVGL-IN-ISO2024 (valid to 2027-09-30)",
            "RoHS Compliant - Certificate No. DNVGL-IN-RoHS2024 (valid to 2028-01-01)",
            "",
            "Contact: Rajesh Sharma | r.sharma@reliableparts.in | +91 20 2712 3456",
        ]],
    },
    {
        "filename": "FastTrack_Commercial_Quotation_2026.pdf",
        "pages": [[
            "COMMERCIAL QUOTATION",
            "FastTrack Manufacturing S.A. de C.V.",
            "Parque Industrial Stiva, Apodaca, Monterrey NL 66600, Mexico",
            "ISO 9001:2015 | RoHS Compliant",
            "",
            "Quote Reference: FTM-MX-2026-0219          Date: 2026-08-07",
            "Buyer: Motor Housing Component Sourcing Project",
            "",
            "ITEM DESCRIPTION",
            "Part: Motor Housing Assembly per Drawing MHA-2026-Rev3",
            "Material: Aluminum 6061-T6",
            "Process: CNC Machining + Stamping",
            "",
            "PRICING",
            "Unit Price (DAP Buyer Dock):  USD 115.00 per unit",
            "Minimum Order Quantity:       150 units",
            "Freight (Near-Shore Truck):   USD 4.00 per unit",
            "Import Duty (USMCA 0%):       USD 0.00 per unit",
            "Estimated Landed Cost:        USD 119.00 per unit",
            "",
            "DELIVERY",
            "Lead Time: 10 calendar days from confirmed purchase order",
            "On-Time Delivery Record: 97% (last 24 months)",
            "Production Capacity Available: 92%",
            "",
            "QUALITY ASSURANCE",
            "Defect Rate: < 4.0%",
            "Customer Satisfaction Rating: 4.1 / 5.0",
            "",
            "CERTIFICATIONS",
            "ISO 9001:2015 - Certificate No. ITK-MX-ISO2024 (valid to 2027-08-31)",
            "RoHS Compliant - Certificate No. ITK-MX-RoHS2024 (valid to 2028-01-01)",
            "",
            "NEAR-SHORE ADVANTAGE: USMCA preferential tariff rate 0%",
            "Same time zone as US operations. Truck delivery in 2-3 days.",
            "",
            "Contact: Carlos Mendoza | c.mendoza@fasttrack-mfg.mx | +52 81 8040 5678",
        ]],
    },
    # ── Technical Specification ───────────────────────────────────────────────
    {
        "filename": "MotorHousing_Technical_Specification_v3.pdf",
        "pages": [
            [
                "MOTOR HOUSING COMPONENT — TECHNICAL SPECIFICATION",
                "Document No.: MHA-2026-Rev3      Status: Released",
                "Issue Date: 2026-07-15            Revision: 3",
                "",
                "1. SCOPE",
                "This specification defines requirements for the precision motor housing",
                "assembly used in the Series 400 electric motor product line.",
                "",
                "2. APPLICABLE STANDARDS",
                "  - ISO 2768-1 (General tolerances - Linear and angular dimensions)",
                "  - ISO 1302 (Surface texture indication)",
                "  - ASTM B209 (Aluminum alloy sheet and plate)",
                "  - IPC-A-610 (Acceptability of electronic assemblies)",
                "  - RoHS Directive 2011/65/EU (Restriction of hazardous substances)",
                "",
                "3. MATERIAL REQUIREMENTS",
                "  Base Material: Aluminum Alloy 6061-T6 per ASTM B209",
                "  Surface Finish: Hard anodize 25 micron min, per MIL-A-8625 Type III",
                "  Corrosion Protection: Salt spray resistance 500 hours per ASTM B117",
            ],
            [
                "4. DIMENSIONAL REQUIREMENTS",
                "  Overall Envelope:   L 180mm x W 120mm x H 95mm",
                "  Wall Thickness:     3.5mm +/- 0.2mm",
                "  Bore Diameter:      52.000mm +0.025/-0.000 mm (H7 fit)",
                "  Mounting Hole PCD:  100mm +/- 0.05mm",
                "  Surface Roughness:  Ra 1.6 max on sealing surfaces",
                "  Flatness:           0.05mm on mating faces",
                "",
                "5. CERTIFICATION REQUIREMENTS",
                "  Suppliers MUST hold the following certifications:",
                "  MANDATORY: ISO 9001:2015 (quality management system)",
                "  PREFERRED:  AS9100D (aerospace quality - for flight-critical variants)",
                "  REQUIRED:   RoHS Compliant (all variants shipped to EU customers)",
                "",
                "6. INSPECTION & TEST",
                "  First Article Inspection (FAI): Required for new suppliers",
                "  Incoming Inspection AQL:        1.0 (critical), 2.5 (major)",
                "  Dimensional Report:             CMM report with each lot",
                "  Material Test Certificate:      Required per lot",
                "",
                "7. PACKAGING",
                "  Individual bubble wrap + foam tray. Max 20 units per carton.",
                "  Carton marking: Part No., Rev, Qty, Date Code, Supplier ID.",
            ],
        ],
    },
    # ── Purchase Requirements ─────────────────────────────────────────────────
    {
        "filename": "Purchase_Requirements_FY2027.pdf",
        "pages": [[
            "PURCHASE REQUIREMENTS DOCUMENT",
            "Motor Housing Assembly — FY2027 Sourcing Program",
            "Issued by: Procurement Department",
            "Date: 2026-08-08          Reference: PRD-FY27-001",
            "",
            "1. ANNUAL VOLUME REQUIREMENT",
            "  Estimated Annual Volume:  12,000 units",
            "  Quarterly Breakdowns:     Q1: 2,500  Q2: 3,000  Q3: 3,500  Q4: 3,000",
            "  Safety Stock Target:      4 weeks supply",
            "",
            "2. COMMERCIAL REQUIREMENTS",
            "  Target Landed Cost:       <= USD 130.00 per unit",
            "  Payment Terms:            Net 45 days from invoice",
            "  Currency:                 USD (preferred) or EUR",
            "  Price Validity:           12 months fixed price contract",
            "  Annual Price Review:      October each year",
            "",
            "3. DELIVERY REQUIREMENTS",
            "  Maximum Lead Time:        21 calendar days",
            "  Required On-Time Delivery: >= 95%",
            "  Delivery Location:        DDP Buyer Warehouse, Detroit MI",
            "  Packaging:                Per drawing MHA-2026-Rev3 packaging spec",
            "",
            "4. QUALITY REQUIREMENTS",
            "  Maximum Acceptable Defect Rate:  2.0% incoming AQL",
            "  First Article Inspection:        Mandatory for all new suppliers",
            "  Certificate of Conformance:      Required with each shipment",
            "",
            "5. MANDATORY CERTIFICATIONS",
            "  ISO 9001:2015     — MANDATORY for all suppliers",
            "  AS9100D           — REQUIRED for aerospace-grade variant",
            "  RoHS Compliant    — REQUIRED for EU export variants",
            "",
            "6. SUPPLIER EVALUATION CRITERIA (WEIGHTING)",
            "  Cost (landed):     30%",
            "  Quality:           20%",
            "  Delivery:          15%",
            "  Risk:              15%",
            "  Capability:        10%",
            "  Compliance:        10%",
            "",
            "7. DISQUALIFICATION CONDITIONS",
            "  - Missing mandatory ISO 9001:2015 certification",
            "  - Defect rate > 10% on previous contracts",
            "  - Failed FAI without corrective action",
        ]],
    },
    # ── Certificates ──────────────────────────────────────────────────────────
    {
        "filename": "Acme_ISO9001_AS9100D_Certificate_2026.pdf",
        "pages": [[
            "CERTIFICATE OF REGISTRATION",
            "",
            "TUV Rheinland Group",
            "Am Grauen Stein 1, 51105 Cologne, Germany",
            "",
            "This certifies that",
            "",
            "ACME PRECISION MANUFACTURING GmbH",
            "Industriestrasse 42, 70565 Stuttgart, Germany",
            "",
            "has been assessed and found to comply with the requirements of:",
            "",
            "  ISO 9001:2015 — Quality Management Systems",
            "  Certificate Number: TUV-DE-ISO9001-2024",
            "  Scope: Design, manufacture and assembly of precision machined",
            "         metal components for aerospace and industrial applications",
            "",
            "  AS9100D — Quality Management Systems for Aviation, Space",
            "            and Defense Organizations",
            "  Certificate Number: TUV-DE-AS9100D-2024",
            "  Scope: CNC machining, assembly and testing of aerospace",
            "         structural components and motor housings",
            "",
            "Initial Certification Date:  2018-04-15",
            "Certificate Issue Date:      2024-06-15",
            "Certificate Expiry Date:     2027-06-30",
            "",
            "Surveillance Audits:         Annual (last audit: 2025-06-10 — No NCRs)",
            "",
            "Signed: Dr. Klaus Brandt, Lead Auditor",
            "TUV Rheinland — Zertifizierungsstelle",
        ]],
    },
    {
        "filename": "TechForge_RoHS_Certificate_2026.pdf",
        "pages": [[
            "ROHS COMPLIANCE CERTIFICATE",
            "",
            "Bureau Veritas Consumer Products Services",
            "1 Park Plaza, Irvine, CA 92614, USA",
            "",
            "CERTIFICATE OF COMPLIANCE",
            "Certificate Reference: BV-TW-RoHS2024",
            "",
            "This certificate is issued to:",
            "",
            "TECHFORGE INDUSTRIES CO., LTD.",
            "No. 12 Science Park Road, Hsinchu 30078, Taiwan",
            "",
            "Product Scope:",
            "  Motor Housing Assemblies — Part No. MHA-2026 Series",
            "  CNC Machined Aluminum Components",
            "  Stamped Metal Sub-Assemblies",
            "",
            "Compliance Standard:",
            "  EU Directive 2011/65/EU (RoHS 2) as amended by 2015/863/EU (RoHS 3)",
            "  Restricted Substances: Pb, Hg, Cd, Cr(VI), PBB, PBDE, DEHP, BBP, DBP, DIBP",
            "  All substances confirmed BELOW maximum concentration values",
            "",
            "Test Report References:",
            "  BV-TW-2024-RoHS-00451 (ICP-MS analysis, 2024-09-15)",
            "  BV-TW-2024-RoHS-00452 (XRF screening, 2024-09-15)",
            "",
            "Certificate Issue Date:   2024-09-20",
            "Certificate Expiry Date:  2028-01-01",
            "",
            "Signed: Sarah Thompson, Senior Compliance Engineer",
            "Bureau Veritas Consumer Products Services",
        ]],
    },
    {
        "filename": "FastTrack_RoHS_Certificate_2026.pdf",
        "pages": [[
            "ROHS COMPLIANCE CERTIFICATE",
            "",
            "Intertek Testing Services",
            "70 W. Plumeria Drive, San Jose, CA 95134, USA",
            "",
            "CERTIFICATE OF COMPLIANCE",
            "Certificate Reference: ITK-MX-RoHS2024",
            "",
            "This certificate is issued to:",
            "",
            "FASTTRACK MANUFACTURING S.A. de C.V.",
            "Parque Industrial Stiva, Apodaca, Monterrey NL 66600, Mexico",
            "",
            "Product Scope:",
            "  Motor Housing Assemblies — Part No. MHA-2026 Series",
            "  CNC Machined and Stamped Aluminum Components",
            "",
            "Compliance Standard:",
            "  EU Directive 2011/65/EU (RoHS 2) as amended by 2015/863/EU (RoHS 3)",
            "  Restricted Substances: Pb, Hg, Cd, Cr(VI), PBB, PBDE, DEHP, BBP, DBP, DIBP",
            "  All substances confirmed BELOW maximum concentration values",
            "",
            "Test Report References:",
            "  ITK-MX-2024-RoHS-1109 (ICP-OES analysis, 2024-08-01)",
            "",
            "Certificate Issue Date:   2024-08-10",
            "Certificate Expiry Date:  2028-01-01",
            "",
            "USMCA Trade Compliance Note:",
            "  All materials sourced within USMCA region or with tariff rate 0%.",
            "  USMCA Certificate of Origin available on request.",
            "",
            "Signed: Miguel Torres, Quality Director",
            "Intertek Testing Services NA Inc.",
        ]],
    },
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {len(DOCS)} sample PDFs → {OUTPUT_DIR}\n")
    for doc in DOCS:
        path = OUTPUT_DIR / doc["filename"]
        pdf_bytes = make_pdf(doc["filename"], doc["pages"])
        path.write_bytes(pdf_bytes)
        size_kb = len(pdf_bytes) / 1024
        print(f"  ✓ {doc['filename']}  ({size_kb:.1f} KB)")
    print(f"\nDone. {len(DOCS)} files written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

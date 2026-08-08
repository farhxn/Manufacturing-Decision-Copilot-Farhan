"""
Manufacturing Decision Copilot — Production-Like Database Seeder

Seeds 10 suppliers covering realistic and edge-case scenarios:

  Supplier         Country       Scenario / Edge Case
  ─────────────────────────────────────────────────────────────────────────
  1  Acme Precision Mfg     Germany      Baseline #1 — full certs, low risk
  2  Global Fabrication Ltd  China        25% duty, long lead time, defect 6%
  3  TechForge Industries    Taiwan       Quality premium, dual cert
  4  Reliable Parts Co       India        Mid-range, IATF 16949 bonus
  5  FastTrack Manufacturing Mexico       USMCA 0% duty, near-shore speed
  6  VoltEdge Components     South Korea  High quality, moderate price
  7  NovaCast Engineering    Poland       EU near-shore, AS9100D, audit passed
  8  SteelPath Industries    Brazil       EDGE: MOQ=2000, BB- credit, missing certs
  9  PeakMetal Solutions     Vietnam      EDGE: EXPIRED ISO cert, supply disruption
 10  AlphaForge Ltd          Canada       EDGE: NO certifications, tiny shop

Scenarios (3 total):
  A. Baseline          — default weights, Acme wins
  B. Shipping +40%     — near-shore suppliers rise; FastTrack becomes #1
  C. China Tariff +50% — GlobalFab lands below target; EU/Mexico dominate

Usage:
    cd backend
    python ../scripts/seed_db_production.py
    python ../scripts/seed_db_production.py --reset   # wipe first
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text

from app.database.session import AsyncSessionLocal
from app.models.document import Document
from app.models.organization import Organization
from app.models.project import Project
from app.models.scenario import Scenario
from app.models.supplier import (
    Supplier,
    SupplierCapability,
    SupplierCertification,
    SupplierPrice,
    SupplierRiskScore,
)
from app.models.user import User

# ── Fixed IDs ─────────────────────────────────────────────────────────────────
DEMO_ORG_ID     = "00000000-0000-4000-a000-000000000001"
DEMO_PROJECT_ID = "00000000-0000-4000-a000-000000000002"
DEMO_USER_ID    = "00000000-0000-4000-a000-000000000003"

S = {
    "acme":       "10000000-0000-4000-a000-000000000001",
    "globalfab":  "10000000-0000-4000-a000-000000000002",
    "techforge":  "10000000-0000-4000-a000-000000000003",
    "reliable":   "10000000-0000-4000-a000-000000000004",
    "fasttrack":  "10000000-0000-4000-a000-000000000005",
    "voltedge":   "10000000-0000-4000-a000-000000000006",
    "novacast":   "10000000-0000-4000-a000-000000000007",
    "steelpath":  "10000000-0000-4000-a000-000000000008",
    "peakmetal":  "10000000-0000-4000-a000-000000000009",
    "alphaforge": "10000000-0000-4000-a000-000000000010",
}

SCEN = {
    "baseline":       "20000000-0000-4000-a000-000000000001",
    "shipping_shock": "20000000-0000-4000-a000-000000000002",
    "china_tariff":   "20000000-0000-4000-a000-000000000003",
}

# ── Supplier dataset ──────────────────────────────────────────────────────────
#
# Each entry drives the scoring engines:
#   overall_score  → quality metrics (defect_rate, inspection_pass_rate, customer_rating)
#                    via supplier_mapper formula
#   risk_scores    → stored as safety scores 0-100 (higher=safer); mapper inverts to magnitude
#   certifications → compliance engine checks against DEFAULT_REQUIRED_CERTS=("ISO 9001",)
#   unit_price + shipping_cost + duty_rate → landed cost calculation
#
DEMO_SUPPLIERS = [

    # ── 1. ACME PRECISION MFG — Baseline hero supplier ────────────────────────
    # Strong on every dimension. Should rank #1 at default weights.
    # Landed: 95 + 22 + 95*0.05 = 121.75
    {
        "id": S["acme"],
        "name": "Acme Precision Mfg",
        "country": "Germany", "city": "Stuttgart",
        "unit_price": 95.0, "shipping_cost": 22.0, "duty_rate": 0.05,
        "landed_cost": 121.75,
        "currency": "USD", "lead_time_days": 14, "moq": 100,
        "overall_score": 94.0, "risk_level": "Low",
        "capabilities": [
            {"name": "CNC Machining",   "category": "Manufacturing"},
            {"name": "Assembly",        "category": "Manufacturing"},
            {"name": "Anodizing",       "category": "Surface Treatment"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "TUV Rheinland", "valid_until": "2027-06-30", "is_valid": True},
            {"name": "AS9100D",       "issuer": "TUV Rheinland", "valid_until": "2027-06-30", "is_valid": True},
            {"name": "RoHS Compliant","issuer": "TUV Rheinland", "valid_until": "2028-01-01", "is_valid": True},
        ],
        "risk_scores": {
            "financial":  95.0,  # Very stable, Dun & Bradstreet A1
            "country":    92.0,  # Germany — AAA sovereign, rule of law
            "supply":     94.0,  # Single site, but 6-month buffer stock
            "compliance": 96.0,  # AS9100D + full RoHS/REACH package
            "capacity":   95.0,  # 95% capacity utilisation, stable workforce
        },
        "notes": "Tier-1 benchmark. Full aerospace certifications. Baseline #1.",
    },

    # ── 2. GLOBAL FABRICATION LTD — High duty, defect risk ───────────────────
    # Cheapest unit price but 25% US-China tariff makes landed cost the highest.
    # Missing AS9100D and RoHS. High country risk. Tests tariff-sensitivity scenario.
    # Landed: 89 + 35 + 89*0.25 = 146.25
    {
        "id": S["globalfab"],
        "name": "Global Fabrication Ltd",
        "country": "China", "city": "Shenzhen",
        "unit_price": 89.0, "shipping_cost": 35.0, "duty_rate": 0.25,
        "landed_cost": 146.25,
        "currency": "USD", "lead_time_days": 28, "moq": 500,
        "overall_score": 64.0, "risk_level": "High",
        "capabilities": [
            {"name": "Injection Molding", "category": "Manufacturing"},
            {"name": "CNC Machining",     "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "SGS", "valid_until": "2026-12-31", "is_valid": True},
        ],
        "risk_scores": {
            "financial":  70.0,  # Moderate — private company, limited disclosure
            "country":    55.0,  # Elevated geopolitical risk, tariff exposure
            "supply":     62.0,  # 28-day lead time, sea-freight only
            "compliance": 68.0,  # No AS9100D, no RoHS cert
            "capacity":   72.0,  # Large capacity but high utilisation
        },
        "notes": "EDGE: cheapest unit price but 25% duty makes it most expensive landed. "
                 "Tests tariff scenario sensitivity. Missing RoHS/AS9100D.",
    },

    # ── 3. TECHFORGE INDUSTRIES — Quality premium ─────────────────────────────
    # Higher unit price offset by strong quality and low duty.
    # Landed: 118 + 18 + 118*0.03 = 139.54
    {
        "id": S["techforge"],
        "name": "TechForge Industries",
        "country": "Taiwan", "city": "Hsinchu",
        "unit_price": 118.0, "shipping_cost": 18.0, "duty_rate": 0.03,
        "landed_cost": 139.54,
        "currency": "USD", "lead_time_days": 21, "moq": 250,
        "overall_score": 88.0, "risk_level": "Low",
        "capabilities": [
            {"name": "CNC Machining", "category": "Manufacturing"},
            {"name": "Stamping",      "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "Bureau Veritas", "valid_until": "2027-03-31", "is_valid": True},
            {"name": "RoHS Compliant","issuer": "Bureau Veritas", "valid_until": "2028-01-01", "is_valid": True},
        ],
        "risk_scores": {
            "financial":  86.0,
            "country":    80.0,  # Taiwan — moderate geopolitical risk (strait tension)
            "supply":     83.0,
            "compliance": 88.0,
            "capacity":   87.0,
        },
        "notes": "Quality tier. RoHS+ISO cert. Taiwan geopolitical risk noted.",
    },

    # ── 4. RELIABLE PARTS CO — Mid-range, IATF 16949 ─────────────────────────
    # Solid performer. IATF 16949 adds automotive credibility.
    # Landed: 102 + 14 + 102*0.08 = 124.16
    {
        "id": S["reliable"],
        "name": "Reliable Parts Co",
        "country": "India", "city": "Pune",
        "unit_price": 102.0, "shipping_cost": 14.0, "duty_rate": 0.08,
        "landed_cost": 124.16,
        "currency": "USD", "lead_time_days": 18, "moq": 200,
        "overall_score": 82.0, "risk_level": "Medium",
        "capabilities": [
            {"name": "CNC Machining",        "category": "Manufacturing"},
            {"name": "Die Casting",          "category": "Manufacturing"},
            {"name": "Engineering Support",  "category": "Technical"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "DNV GL", "valid_until": "2027-09-30", "is_valid": True},
            {"name": "RoHS Compliant","issuer": "DNV GL", "valid_until": "2028-01-01", "is_valid": True},
            {"name": "IATF 16949",   "issuer": "DNV GL", "valid_until": "2027-09-30", "is_valid": True},
        ],
        "risk_scores": {
            "financial":  80.0,
            "country":    74.0,  # India — improving but infrastructure risk
            "supply":     79.0,
            "compliance": 82.0,
            "capacity":   81.0,
        },
        "notes": "Engineering support capability triggers bonus in capability score.",
    },

    # ── 5. FASTTRACK MANUFACTURING — Near-shore hero ──────────────────────────
    # USMCA 0% duty + truck delivery = lowest landed cost despite higher unit price.
    # Ranked #1 when shipping multiplier >= 1.4 (Shipping Shock scenario).
    # Landed: 115 + 4 + 0 = 119.00
    {
        "id": S["fasttrack"],
        "name": "FastTrack Manufacturing",
        "country": "Mexico", "city": "Monterrey",
        "unit_price": 115.0, "shipping_cost": 4.0, "duty_rate": 0.0,
        "landed_cost": 119.00,
        "currency": "USD", "lead_time_days": 10, "moq": 150,
        "overall_score": 83.0, "risk_level": "Medium",
        "capabilities": [
            {"name": "CNC Machining", "category": "Manufacturing"},
            {"name": "Stamping",      "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "Intertek",  "valid_until": "2027-08-31", "is_valid": True},
            {"name": "RoHS Compliant","issuer": "Intertek",  "valid_until": "2028-01-01", "is_valid": True},
        ],
        "risk_scores": {
            "financial":  82.0,
            "country":    76.0,  # Mexico — USMCA positive but security risks
            "supply":     80.0,
            "compliance": 85.0,
            "capacity":   82.0,
        },
        "notes": "USMCA near-shore. Shipping-shock hero: 0% duty + 4 USD/unit freight.",
    },

    # ── 6. VOLTEDGE COMPONENTS — South Korea high-quality ────────────────────
    # Strong quality scores, automotive-grade IATF 16949. Moderate landed cost.
    # Landed: 108 + 16 + 108*0.032 = 127.46
    {
        "id": S["voltedge"],
        "name": "VoltEdge Components",
        "country": "South Korea", "city": "Seoul",
        "unit_price": 108.0, "shipping_cost": 16.0, "duty_rate": 0.032,
        "landed_cost": 127.46,
        "currency": "USD", "lead_time_days": 16, "moq": 200,
        "overall_score": 90.0, "risk_level": "Low",
        "capabilities": [
            {"name": "Die Casting",         "category": "Manufacturing"},
            {"name": "CNC Machining",       "category": "Manufacturing"},
            {"name": "Anodizing",           "category": "Surface Treatment"},
            {"name": "Engineering Support", "category": "Technical"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "KAS-KOLAS",  "valid_until": "2027-11-30", "is_valid": True},
            {"name": "RoHS Compliant","issuer": "KAS-KOLAS",  "valid_until": "2028-06-01", "is_valid": True},
            {"name": "IATF 16949",   "issuer": "KAS-KOLAS",  "valid_until": "2027-11-30", "is_valid": True},
        ],
        "risk_scores": {
            "financial":  89.0,  # KOSPI-listed, strong balance sheet
            "country":    84.0,  # South Korea — strong institutions, minor NK risk
            "supply":     86.0,
            "compliance": 91.0,
            "capacity":   88.0,
        },
        "notes": "Second-highest quality. Engineering support = capability bonus.",
    },

    # ── 7. NOVACAST ENGINEERING — EU near-shore, dual-cert ───────────────────
    # Audit passed with 0 major NCRs. Gravity casting — slightly lower quality
    # floor but AS9100D certified. EUR pricing adds FX exposure.
    # Landed: 112.35 + 8.56 + 0 (EU no duty) = 120.91
    {
        "id": S["novacast"],
        "name": "NovaCast Engineering",
        "country": "Poland", "city": "Gliwice",
        "unit_price": 112.35, "shipping_cost": 8.56, "duty_rate": 0.0,
        "landed_cost": 120.91,
        "currency": "EUR", "lead_time_days": 12, "moq": 150,
        "overall_score": 89.0, "risk_level": "Low",
        "capabilities": [
            {"name": "Gravity Casting",     "category": "Manufacturing"},
            {"name": "CNC Machining",       "category": "Manufacturing"},
            {"name": "Engineering Support", "category": "Technical"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "DNV GL",  "valid_until": "2027-12-31", "is_valid": True},
            {"name": "AS9100D",       "issuer": "DNV GL",  "valid_until": "2027-12-31", "is_valid": True},
            {"name": "RoHS Compliant","issuer": "DNV GL",  "valid_until": "2028-06-01", "is_valid": True},
        ],
        "risk_scores": {
            "financial":  87.0,
            "country":    90.0,  # Poland — EU member, stable
            "supply":     88.0,
            "compliance": 92.0,
            "capacity":   86.0,
        },
        "notes": "EU near-shore competitive with Germany. AS9100D. EUR FX exposure.",
    },

    # ── 8. STEELPATH INDUSTRIES — EDGE: high MOQ + credit downgrade ──────────
    # Very low unit price but high MOQ (2000) makes it impractical for Q1/Q2.
    # Missing AS9100D and RoHS. BB- credit rating. Brazil country risk.
    # Landed: 78 + 28 + 78*0.075 = 111.85
    {
        "id": S["steelpath"],
        "name": "SteelPath Industries",
        "country": "Brazil", "city": "Sao Paulo",
        "unit_price": 78.0, "shipping_cost": 28.0, "duty_rate": 0.075,
        "landed_cost": 111.85,
        "currency": "USD", "lead_time_days": 35, "moq": 2000,
        "overall_score": 68.0, "risk_level": "High",
        "capabilities": [
            {"name": "Sand Casting",  "category": "Manufacturing"},
            {"name": "CNC Machining", "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "Bureau Veritas", "valid_until": "2027-04-30", "is_valid": True},
            # Deliberately missing AS9100D and RoHS
        ],
        "risk_scores": {
            "financial":  52.0,  # BB- Fitch rating, BRL depreciation impact
            "country":    58.0,  # Brazil — political instability, port delays
            "supply":     55.0,  # 35-day LT + 22d transit; single casting facility
            "compliance": 62.0,  # ISO 9001 only; no AS9100D, no RoHS
            "capacity":   66.0,  # 78% utilisation, overtime required for peak
        },
        "notes": "EDGE: MOQ=2000 (blocks small orders). BB- credit. "
                 "Best landed cost if volume qualifies but risk drags score down.",
    },

    # ── 9. PEAKMETAL SOLUTIONS — EDGE: EXPIRED certification ─────────────────
    # ISO 9001 expired 2024-12-31 — compliance engine scores 0 (missing req cert).
    # Typhoon supply disruption 2026. Very cheap but tests disqualification logic.
    # Landed: 71 + 30 + 71*0.10 = 108.10
    {
        "id": S["peakmetal"],
        "name": "PeakMetal Solutions",
        "country": "Vietnam", "city": "Binh Duong",
        "unit_price": 71.0, "shipping_cost": 30.0, "duty_rate": 0.10,
        "landed_cost": 108.10,
        "currency": "USD", "lead_time_days": 30, "moq": 300,
        "overall_score": 55.0, "risk_level": "High",
        "capabilities": [
            {"name": "Die Casting",   "category": "Manufacturing"},
            {"name": "CNC Machining", "category": "Manufacturing"},
        ],
        "certifications": [
            # is_valid=False simulates expired certificate
            {
                "name": "ISO 9001:2015",
                "issuer": "TUV SUD",
                "valid_until": "2024-12-31",   # EXPIRED
                "is_valid": False,             # Mapper will exclude from supplier_certs
            },
        ],
        "risk_scores": {
            "financial":  55.0,  # Private, limited financials
            "country":    60.0,  # Vietnam — improving but weather/flood risk
            "supply":     45.0,  # Typhoon Yagi damage Jan-Mar 2026, supplier changed
            "compliance": 40.0,  # Expired ISO cert — critical gap
            "capacity":   58.0,  # 70% capacity after storm damage repairs
        },
        "notes": "EDGE: ISO cert EXPIRED. is_valid=False → compliance score = 0. "
                 "Tests disqualification path and risk floor.",
    },

    # ── 10. ALPHAFORGE LTD — EDGE: zero certifications ───────────────────────
    # No ISO 9001, no AS9100D, no RoHS. Tiny shop (50-unit MOQ).
    # Tests: compliance_score=0 (missing mandatory cert).
    # Decent quality claim but no 3rd-party evidence — customer_rating stays mid.
    # Landed: 107.30 + 0 + 0 = 107.30  (DDP, all-in, CUSMA 0%)
    {
        "id": S["alphaforge"],
        "name": "AlphaForge Ltd",
        "country": "Canada", "city": "Mississauga",
        "unit_price": 107.30, "shipping_cost": 0.0, "duty_rate": 0.0,
        "landed_cost": 107.30,
        "currency": "CAD", "lead_time_days": 8, "moq": 50,
        "overall_score": 61.0, "risk_level": "Medium",
        "capabilities": [
            {"name": "CNC Machining", "category": "Manufacturing"},
        ],
        "certifications": [],   # NO certifications — compliance_score = 0
        "risk_scores": {
            "financial":  62.0,  # Small company, ~40 employees
            "country":    91.0,  # Canada — AAA sovereign, no geopolitical risk
            "supply":     65.0,  # Single 8-machine shop; no backup
            "compliance": 35.0,  # No ISO 9001 — critical compliance gap
            "capacity":   68.0,  # 80% capacity, limited scalability
        },
        "notes": "EDGE: ZERO certifications. compliance_score=0 (fails ISO 9001 check). "
                 "Cheapest landed cost but compliance failure makes it unqualified. "
                 "Country risk is excellent (Canada). Tests compliance disqualification.",
    },
]


# ── Document manifest ─────────────────────────────────────────────────────────
# Maps PDF files to suppliers. Files must exist in sample-data/documents/.
DEMO_DOCUMENTS = [
    # Quotations (10 suppliers)
    {"supplier_key": "acme",       "filename": "Acme_Precision_Quotation_Q4_2026.pdf"},
    {"supplier_key": "globalfab",  "filename": "GlobalFab_Commercial_Quotation_2026.pdf"},
    {"supplier_key": "techforge",  "filename": "TechForge_Quotation_MotorHousing_2026.pdf"},
    {"supplier_key": "reliable",   "filename": "ReliableParts_Quotation_Oct2026.pdf"},
    {"supplier_key": "fasttrack",  "filename": "FastTrack_Commercial_Quotation_2026.pdf"},
    {"supplier_key": "voltedge",   "filename": "VoltEdge_Commercial_Quotation_2026.pdf"},
    {"supplier_key": "novacast",   "filename": "NovaCast_Engineering_Quotation_2026.pdf"},
    {"supplier_key": "steelpath",  "filename": "SteelPath_Quotation_2026.pdf"},
    {"supplier_key": "peakmetal",  "filename": "PeakMetal_Quotation_2026.pdf"},
    {"supplier_key": "alphaforge", "filename": "AlphaForge_Quotation_2026.pdf"},
    # Certificates
    {"supplier_key": "acme",      "filename": "Acme_ISO9001_AS9100D_Certificate_2026.pdf"},
    {"supplier_key": "techforge", "filename": "TechForge_RoHS_Certificate_2026.pdf"},
    {"supplier_key": "fasttrack", "filename": "FastTrack_RoHS_Certificate_2026.pdf"},
    {"supplier_key": "voltedge",  "filename": "VoltEdge_ISO9001_Certificate_2026.pdf"},
    # Supporting docs (no supplier)
    {"supplier_key": None, "filename": "MotorHousing_Technical_Specification_v3.pdf"},
    {"supplier_key": None, "filename": "Purchase_Requirements_FY2027.pdf"},
    {"supplier_key": None, "filename": "NovaCast_Supplier_Audit_Report_2026.pdf"},
]

# ── Scenario definitions ──────────────────────────────────────────────────────
# These are stored in the DB so the UI can run them via the scenarios API.
DEMO_SCENARIOS = [
    {
        "id": SCEN["baseline"],
        "name": "Baseline — Default Weights",
        "description": (
            "Standard evaluation at default scoring weights "
            "(cost 30%, quality 20%, delivery 15%, risk 15%, "
            "capability 10%, compliance 10%). "
            "Expected winner: Acme Precision Mfg (Germany)."
        ),
        "shipping_multiplier": 1.0,
        "currency_rate": 1.0,
        "demand_multiplier": 1.0,
        "lead_time_adjustment_days": 0,
        "disabled_supplier_ids": [],
    },
    {
        "id": SCEN["shipping_shock"],
        "name": "Shipping Shock — Freight +40%",
        "description": (
            "Simulates a global freight crisis (e.g. Red Sea disruption) "
            "adding 40% to all shipping costs. Near-shore suppliers with "
            "truck freight gain a structural advantage. "
            "Expected winner flip: FastTrack Manufacturing (Mexico) "
            "takes #1 due to USD 4 truck freight vs Acme's USD 22 air."
        ),
        "shipping_multiplier": 1.4,
        "currency_rate": 1.0,
        "demand_multiplier": 1.0,
        "lead_time_adjustment_days": 7,   # Ports congested — everyone +7 days
        "disabled_supplier_ids": [],
    },
    {
        "id": SCEN["china_tariff"],
        "name": "China Tariff Escalation — +50% Additional Duty",
        "description": (
            "Simulates US Section 301 tariff escalation adding 50 percentage "
            "points to China-origin goods (25% → 75% effective duty). "
            "Global Fabrication becomes definitively uncompetitive. "
            "EU and Mexico suppliers dominate the top 3. "
            "GlobalFab is disabled for this scenario."
        ),
        "shipping_multiplier": 1.0,
        "currency_rate": 1.0,
        "demand_multiplier": 1.0,
        "lead_time_adjustment_days": 0,
        "disabled_supplier_ids": [S["globalfab"]],
    },
]


# ── Seed helpers ──────────────────────────────────────────────────────────────

async def _wipe(session) -> None:
    print("  Wiping all data...")
    for table in [
        "recommendation_evidence", "decision_traces", "recommendations",
        "scenario_results", "scenarios",
        "extracted_fields", "document_chunks", "documents",
        "supplier_risk_scores", "supplier_prices",
        "supplier_certifications", "supplier_capabilities", "suppliers",
        "audit_logs", "reports", "projects", "users", "organizations",
    ]:
        await session.execute(text(f"DELETE FROM {table}"))  # noqa: S608
    await session.commit()
    print("  Wiped.")


async def _seed_foundation(session) -> None:
    session.add(Organization(
        id=DEMO_ORG_ID, name="Demo Manufacturing Corp", slug="demo-mfg-corp",
    ))
    session.add(User(
        id=DEMO_USER_ID, organization_id=DEMO_ORG_ID,
        email="procurement@demo-mfg.example.com",
        full_name="Alex Chen, Senior Procurement Manager",
        role="procurement_manager",
    ))
    session.add(Project(
        id=DEMO_PROJECT_ID, organization_id=DEMO_ORG_ID,
        name="Motor Housing Component Sourcing — FY2027",
        description=(
            "Full sourcing analysis for precision motor housing assemblies. "
            "10 qualified and edge-case suppliers evaluated across cost, quality, "
            "delivery, risk, capability, and compliance dimensions. "
            "Includes 3 scenario models: baseline, shipping shock, China tariff."
        ),
        status="active",
        cost_weight=0.30,
        quality_weight=0.20,
        delivery_weight=0.15,
        risk_weight=0.15,
        capability_weight=0.10,
        compliance_weight=0.10,
    ))
    await session.flush()
    print("  Created org, user, project.")


async def _seed_suppliers(session) -> None:
    count = 0
    for s in DEMO_SUPPLIERS:
        session.add(Supplier(
            id=s["id"], project_id=DEMO_PROJECT_ID,
            name=s["name"], country=s["country"], city=s["city"],
            unit_price=s["unit_price"], landed_cost=s["landed_cost"],
            currency=s["currency"], lead_time_days=s["lead_time_days"],
            moq=s["moq"], overall_score=s["overall_score"],
            risk_level=s["risk_level"], status="evaluated",
        ))
        for cap in s["capabilities"]:
            session.add(SupplierCapability(
                supplier_id=s["id"],
                name=cap["name"], category=cap["category"], verified=True,
            ))
        for cert in s["certifications"]:
            session.add(SupplierCertification(
                supplier_id=s["id"],
                name=cert["name"], issuer=cert["issuer"],
                valid_until=cert["valid_until"], is_valid=cert["is_valid"],
            ))
        session.add(SupplierPrice(
            supplier_id=s["id"],
            tier_min_qty=s["moq"],
            unit_price=s["unit_price"],
            currency=s["currency"],
            shipping_cost=s["shipping_cost"],
            duty_rate=s["duty_rate"],
        ))
        for category, score in s["risk_scores"].items():
            detail = (
                f"{s['name']}: {category} risk score {score}/100 — "
                f"{s.get('notes', 'Production seed data.')}"
            )
            session.add(SupplierRiskScore(
                supplier_id=s["id"], category=category, score=score, details=detail,
            ))
        count += 1

    await session.flush()
    print(f"  Created {count} suppliers with capabilities, certs, prices, risk scores.")


async def _seed_documents(session) -> None:
    docs_dir = Path(__file__).parent.parent / "sample-data" / "documents"
    count = 0
    missing = []
    for doc in DEMO_DOCUMENTS:
        supplier_id = S.get(doc["supplier_key"]) if doc["supplier_key"] else None
        fpath = docs_dir / doc["filename"]
        size = fpath.stat().st_size if fpath.exists() else 102_400
        if not fpath.exists():
            missing.append(doc["filename"])
        session.add(Document(
            id=str(uuid.uuid4()),
            project_id=DEMO_PROJECT_ID,
            supplier_id=supplier_id,
            filename=doc["filename"],
            file_path=str(fpath),
            file_type="pdf",
            file_size_bytes=size,
            status="completed",
            sha256_checksum=uuid.uuid4().hex,
        ))
        count += 1
    await session.flush()
    if missing:
        print(f"  WARNING: {len(missing)} PDF(s) not found on disk: {missing}")
        print("  Run: python scripts/generate_production_pdfs.py")
    print(f"  Created {count} document records.")


async def _seed_scenarios(session) -> None:
    for sc in DEMO_SCENARIOS:
        session.add(Scenario(
            id=sc["id"], project_id=DEMO_PROJECT_ID,
            name=sc["name"], description=sc["description"],
            shipping_multiplier=sc["shipping_multiplier"],
            currency_rate=sc["currency_rate"],
            demand_multiplier=sc["demand_multiplier"],
            lead_time_adjustment_days=sc["lead_time_adjustment_days"],
            disabled_supplier_ids=sc["disabled_supplier_ids"],
        ))
    await session.flush()
    print(f"  Created {len(DEMO_SCENARIOS)} scenarios.")


# ── Main entry ────────────────────────────────────────────────────────────────

async def seed(reset: bool = False) -> None:
    print("\n=== Manufacturing Decision Copilot — Production Seeder ===\n")
    async with AsyncSessionLocal() as session:
        try:
            if reset:
                await _wipe(session)

            await _seed_foundation(session)
            await _seed_suppliers(session)
            await _seed_documents(session)
            await _seed_scenarios(session)
            await session.commit()

            print("\n" + "=" * 62)
            print("  SEED COMPLETE")
            print("=" * 62)
            print(f"  Project ID  : {DEMO_PROJECT_ID}")
            print(f"  Suppliers   : {len(DEMO_SUPPLIERS)}")
            print(f"  Documents   : {len(DEMO_DOCUMENTS)}")
            print(f"  Scenarios   : {len(DEMO_SCENARIOS)}")
            print()
            print("  Expected ranking (baseline, default weights):")
            print("    #1  Acme Precision Mfg     (Germany)     — 121.75 USD")
            print("    #2  NovaCast Engineering    (Poland)      — 120.91 USD  ← EU near-shore")
            print("    #3  FastTrack Manufacturing (Mexico)      — 119.00 USD")
            print("    #4  VoltEdge Components     (South Korea) — 127.46 USD")
            print("    #5  Reliable Parts Co       (India)       — 124.16 USD")
            print("    #6  TechForge Industries    (Taiwan)      — 139.54 USD")
            print("    #7  Global Fabrication Ltd  (China)       — 146.25 USD  ← highest landed")
            print("    #8  SteelPath Industries    (Brazil)      — 111.85 USD  ← risk drags score")
            print("    #9  PeakMetal Solutions     (Vietnam)     — compliance=0 (expired cert)")
            print("   #10  AlphaForge Ltd           (Canada)      — compliance=0 (no certs)")
            print()
            print("  Scenario: Shipping +40%")
            print("    FastTrack Manufacturing rises to #1 (near-shore USD 4 truck freight)")
            print("    Acme slips to #3 (USD 22 air freight * 1.4 = USD 30.80)")
            print()
            print("  Scenario: China Tariff +50% (GlobalFab disabled)")
            print("    GlobalFab removed. EU/Mexico top 3 dominate.")
            print("=" * 62 + "\n")

        except Exception as exc:
            await session.rollback()
            print(f"\n  SEED FAILED: {exc}")
            raise


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    asyncio.run(seed(reset=reset_flag))

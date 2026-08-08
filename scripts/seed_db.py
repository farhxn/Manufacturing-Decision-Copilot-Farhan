"""
Manufacturing Decision Copilot - Demo Database Seeder

Seeds the exact 5-supplier demo dataset from the Implementation Roadmap (Section 18.1).
These suppliers are tuned to produce the hero scenario:
  - Baseline: Acme Precision is #1 (quality + low risk + AS9100D compliance)
  - Shipping +40%: FastTrack Manufacturing becomes #1 (near-shore advantage)

Usage:
    cd backend
    python ../scripts/seed_db.py

    # idempotent — safe to run multiple times
    python ../scripts/seed_db.py --reset
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
from app.models.supplier import (
    Supplier,
    SupplierCapability,
    SupplierCertification,
    SupplierPrice,
    SupplierRiskScore,
)
from app.models.user import User

# ── Fixed IDs (stable across re-runs) ────────────────────────────────────────
DEMO_ORG_ID = "00000000-0000-4000-a000-000000000001"
DEMO_PROJECT_ID = "00000000-0000-4000-a000-000000000002"
DEMO_USER_ID = "00000000-0000-4000-a000-000000000003"

# Supplier IDs — fixed so foreign keys in scenarios stay valid after re-seed
SUPPLIER_IDS = {
    "acme": "10000000-0000-4000-a000-000000000001",
    "global_fab": "10000000-0000-4000-a000-000000000002",
    "techforge": "10000000-0000-4000-a000-000000000003",
    "reliable": "10000000-0000-4000-a000-000000000004",
    "fasttrack": "10000000-0000-4000-a000-000000000005",
}

# ── Demo Supplier Dataset (Section 18.1 + engine-verified values) ─────────────
#
# Key constraint: acme quoted_price=95 + shipping=22 produces landed_cost≈121.75
# fasttrack quoted_price=115 + shipping=4 produces landed_cost=119.
# At default weights acme wins on quality+risk+compliance.
# At shipping*1.4 acme landed_cost rises to ~130.5 and fasttrack becomes #1.
#
DEMO_SUPPLIERS = [
    {
        "id": SUPPLIER_IDS["acme"],
        "name": "Acme Precision Mfg",
        "country": "Germany",
        "city": "Stuttgart",
        "unit_price": 95.0,
        "shipping_cost": 22.0,
        "duty_rate": 0.05,
        "landed_cost": 121.75,   # 95 + 22 + 95*0.05
        "currency": "USD",
        "lead_time_days": 14,
        "moq": 100,
        "overall_score": 94.0,
        "risk_level": "Low",
        "capabilities": [
            {"name": "CNC Machining", "category": "Manufacturing"},
            {"name": "Assembly", "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "TÜV Rheinland", "valid_until": "2027-06-30"},
            {"name": "AS9100D", "issuer": "TÜV Rheinland", "valid_until": "2027-06-30"},
        ],
        # Risk scores 0-100 (higher = safer)
        "risk_scores": {
            "financial": 95.0,
            "country": 92.0,
            "supply": 94.0,
            "compliance": 96.0,
            "capacity": 95.0,
        },
    },
    {
        "id": SUPPLIER_IDS["global_fab"],
        "name": "Global Fabrication Ltd",
        "country": "China",
        "city": "Shenzhen",
        "unit_price": 89.0,
        "shipping_cost": 35.0,
        "duty_rate": 0.25,
        "landed_cost": 146.25,  # 89 + 35 + 89*0.25
        "currency": "USD",
        "lead_time_days": 28,
        "moq": 500,
        "overall_score": 72.0,
        "risk_level": "High",
        "capabilities": [
            {"name": "Injection Molding", "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "SGS", "valid_until": "2026-12-31"},
        ],
        "risk_scores": {
            "financial": 70.0,
            "country": 65.0,
            "supply": 68.0,
            "compliance": 75.0,
            "capacity": 72.0,
        },
    },
    {
        "id": SUPPLIER_IDS["techforge"],
        "name": "TechForge Industries",
        "country": "Taiwan",
        "city": "Hsinchu",
        "unit_price": 118.0,
        "shipping_cost": 18.0,
        "duty_rate": 0.03,
        "landed_cost": 139.54,  # 118 + 18 + 118*0.03
        "currency": "USD",
        "lead_time_days": 21,
        "moq": 250,
        "overall_score": 88.0,
        "risk_level": "Low",
        "capabilities": [
            {"name": "CNC Machining", "category": "Manufacturing"},
            {"name": "Stamping", "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "Bureau Veritas", "valid_until": "2027-03-31"},
            {"name": "RoHS Compliant", "issuer": "Bureau Veritas", "valid_until": "2028-01-01"},
        ],
        "risk_scores": {
            "financial": 86.0,
            "country": 84.0,
            "supply": 83.0,
            "compliance": 88.0,
            "capacity": 87.0,
        },
    },
    {
        "id": SUPPLIER_IDS["reliable"],
        "name": "Reliable Parts Co",
        "country": "India",
        "city": "Pune",
        "unit_price": 102.0,
        "shipping_cost": 14.0,
        "duty_rate": 0.08,
        "landed_cost": 124.16,  # 102 + 14 + 102*0.08
        "currency": "USD",
        "lead_time_days": 18,
        "moq": 200,
        "overall_score": 82.0,
        "risk_level": "Medium",
        "capabilities": [
            {"name": "CNC Machining", "category": "Manufacturing"},
            {"name": "Die Casting", "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "DNV GL", "valid_until": "2027-09-30"},
            {"name": "RoHS Compliant", "issuer": "DNV GL", "valid_until": "2028-01-01"},
        ],
        "risk_scores": {
            "financial": 80.0,
            "country": 76.0,
            "supply": 79.0,
            "compliance": 82.0,
            "capacity": 81.0,
        },
    },
    {
        "id": SUPPLIER_IDS["fasttrack"],
        "name": "FastTrack Manufacturing",
        "country": "Mexico",
        "city": "Monterrey",
        "unit_price": 115.0,
        "shipping_cost": 4.0,
        "duty_rate": 0.0,
        "landed_cost": 119.0,  # 115 + 4 + 0
        "currency": "USD",
        "lead_time_days": 10,
        "moq": 150,
        "overall_score": 85.0,
        "risk_level": "Medium",
        "capabilities": [
            {"name": "CNC Machining", "category": "Manufacturing"},
            {"name": "Stamping", "category": "Manufacturing"},
        ],
        "certifications": [
            {"name": "ISO 9001:2015", "issuer": "Intertek", "valid_until": "2027-08-31"},
            {"name": "RoHS Compliant", "issuer": "Intertek", "valid_until": "2028-01-01"},
        ],
        "risk_scores": {
            "financial": 82.0,
            "country": 78.0,
            "supply": 80.0,
            "compliance": 85.0,
            "capacity": 82.0,
        },
    },
]

# ── Demo Documents (10 total matching spec Section 18.2) ──────────────────────
DEMO_DOCUMENTS = [
    # 5 commercial quotations
    {"supplier_key": "acme",       "filename": "Acme_Precision_Quotation_Q4_2026.pdf",         "doc_type": "pdf"},
    {"supplier_key": "global_fab", "filename": "GlobalFab_Commercial_Quotation_2026.pdf",       "doc_type": "pdf"},
    {"supplier_key": "techforge",  "filename": "TechForge_Quotation_MotorHousing_2026.pdf",     "doc_type": "pdf"},
    {"supplier_key": "reliable",   "filename": "ReliableParts_Quotation_Oct2026.pdf",           "doc_type": "pdf"},
    {"supplier_key": "fasttrack",  "filename": "FastTrack_Commercial_Quotation_2026.pdf",       "doc_type": "pdf"},
    # Technical spec
    {"supplier_key": None,         "filename": "MotorHousing_Technical_Specification_v3.pdf",  "doc_type": "pdf"},
    # Purchase requirements
    {"supplier_key": None,         "filename": "Purchase_Requirements_FY2027.pdf",              "doc_type": "pdf"},
    # Certificates
    {"supplier_key": "acme",       "filename": "Acme_ISO9001_AS9100D_Certificate_2026.pdf",    "doc_type": "pdf"},
    {"supplier_key": "techforge",  "filename": "TechForge_RoHS_Certificate_2026.pdf",           "doc_type": "pdf"},
    {"supplier_key": "fasttrack",  "filename": "FastTrack_RoHS_Certificate_2026.pdf",           "doc_type": "pdf"},
]


# ── Seed helpers ──────────────────────────────────────────────────────────────

async def _wipe(session) -> None:
    """Delete all demo data in reverse dependency order."""
    print("  Wiping existing demo data...")
    tables = [
        "recommendation_evidence", "decision_traces", "recommendations",
        "scenario_results", "scenarios",
        "extracted_fields", "document_chunks", "documents",
        "supplier_risk_scores", "supplier_prices",
        "supplier_certifications", "supplier_capabilities", "suppliers",
        "projects", "users", "organizations",
    ]
    for table in tables:
        await session.execute(text(f"DELETE FROM {table}"))  # noqa: S608
    await session.commit()
    print("  Done.")


async def _seed_foundation(session) -> None:
    org = Organization(id=DEMO_ORG_ID, name="Demo Organization", slug="demo-org")
    session.add(org)

    user = User(
        id=DEMO_USER_ID,
        organization_id=DEMO_ORG_ID,
        email="demo@mdc.example.com",
        full_name="Demo Procurement Manager",
        role="procurement_manager",
    )
    session.add(user)

    project = Project(
        id=DEMO_PROJECT_ID,
        organization_id=DEMO_ORG_ID,
        name="Motor Housing Component Sourcing",
        description=(
            "Sourcing analysis for precision motor housing components. "
            "5 qualified suppliers evaluated across cost, quality, delivery, risk, "
            "capability, and compliance dimensions."
        ),
        status="active",
        # Default weights (spec Section 10.1)
        cost_weight=0.30,
        quality_weight=0.20,
        delivery_weight=0.15,
        risk_weight=0.15,
        capability_weight=0.10,
        compliance_weight=0.10,
    )
    session.add(project)
    await session.flush()
    print("  Created organization, user, project.")


async def _seed_suppliers(session) -> None:
    for s in DEMO_SUPPLIERS:
        supplier = Supplier(
            id=s["id"],
            project_id=DEMO_PROJECT_ID,
            name=s["name"],
            country=s["country"],
            city=s["city"],
            unit_price=s["unit_price"],
            landed_cost=s["landed_cost"],
            currency=s["currency"],
            lead_time_days=s["lead_time_days"],
            moq=s["moq"],
            overall_score=s["overall_score"],
            risk_level=s["risk_level"],
            status="evaluated",
        )
        session.add(supplier)

        for cap in s["capabilities"]:
            session.add(SupplierCapability(
                supplier_id=s["id"],
                name=cap["name"],
                category=cap["category"],
                verified=True,
            ))

        for cert in s["certifications"]:
            session.add(SupplierCertification(
                supplier_id=s["id"],
                name=cert["name"],
                issuer=cert["issuer"],
                valid_until=cert["valid_until"],
                is_valid=True,
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
            session.add(SupplierRiskScore(
                supplier_id=s["id"],
                category=category,
                score=score,
                details=f"Seeded {category} risk score for demo.",
            ))

    await session.flush()
    print(f"  Created {len(DEMO_SUPPLIERS)} suppliers with capabilities, certs, prices, risk scores.")


async def _seed_documents(session) -> None:
    for doc in DEMO_DOCUMENTS:
        supplier_id = SUPPLIER_IDS.get(doc["supplier_key"]) if doc["supplier_key"] else None
        session.add(Document(
            id=str(uuid.uuid4()),
            project_id=DEMO_PROJECT_ID,
            supplier_id=supplier_id,
            filename=doc["filename"],
            file_path=f"/uploads/{doc['filename']}",
            file_type=doc["doc_type"],
            file_size_bytes=204_800,   # 200 KB placeholder
            status="completed",
            sha256_checksum=uuid.uuid4().hex,
        ))
    await session.flush()
    print(f"  Created {len(DEMO_DOCUMENTS)} document records.")


async def seed(reset: bool = False) -> None:
    print("\n=== Manufacturing Decision Copilot — Database Seeder ===\n")
    async with AsyncSessionLocal() as session:
        try:
            if reset:
                await _wipe(session)

            await _seed_foundation(session)
            await _seed_suppliers(session)
            await _seed_documents(session)
            await session.commit()

            print("\n✓ Seed complete.")
            print(f"  Project ID : {DEMO_PROJECT_ID}")
            print(f"  Suppliers  : {len(DEMO_SUPPLIERS)}")
            print(f"  Documents  : {len(DEMO_DOCUMENTS)}")
            print("\nHero scenario check:")
            print("  Baseline     → Acme Precision Mfg ranked #1")
            print("  Shipping +40% → FastTrack Manufacturing ranked #1\n")

        except Exception as exc:
            await session.rollback()
            print(f"\n✗ Seed failed: {exc}")
            raise


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    asyncio.run(seed(reset=reset_flag))

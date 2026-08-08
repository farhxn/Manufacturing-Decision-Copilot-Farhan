"""
Manufacturing Decision Copilot - Cloud Database Deployment & Seeder

Applies Alembic migrations and seeds baseline production data directly to your
free Cloud PostgreSQL instance (Neon.tech / Supabase).

Usage:
    python scripts/deploy_cloud_db_seed.py --db-url "postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def run_migrations(db_url: str):
    """Executes Alembic migrations against the target cloud DB URL."""
    print("Running Alembic database migrations...")
    os.environ["DATABASE_URL"] = db_url
    
    from alembic.config import Config
    from alembic import command
    
    alembic_ini_path = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    
    # Run upgrade head
    command.upgrade(alembic_cfg, "head")
    print("Database schema migrated successfully!")

def seed_database(db_url: str):
    """Seeds demo dataset into target cloud database."""
    print("Seeding production baseline suppliers and scenarios...")
    os.environ["DATABASE_URL"] = db_url
    
    from scripts.seed_db import seed as seed_main
    asyncio.run(seed_main())
    print("Baseline demo data seeded successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy & Seed Cloud PostgreSQL Database")
    parser.add_argument("--db-url", required=True, help="Cloud PostgreSQL connection string (Neon/Supabase)")
    args = parser.parse_args()

    try:
        run_migrations(args.db_url)
        seed_database(args.db_url)
        print("\nCloud Database Deployment Complete! Ready for FastAPI backend connection.")
    except Exception as e:
        print(f"\nError during cloud database deployment: {e}")
        sys.exit(1)

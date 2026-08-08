"""
Phase 0 Environment & Setup Verification Script
"""
import os
import sys

def test_phase0():
    print("==========================================")
    print("  Phase 0: Environment Verification Check ")
    print("==========================================")
    
    # 1. Python Version
    print(f"[OK] Python Version: {sys.version.split()[0]}")
    
    # 2. Check directory structure
    required_dirs = [
        "backend/app",
        "backend/app/api/v1",
        "backend/app/core",
        "backend/app/models",
        "backend/app/engines",
        "sample-data",
        "docs"
    ]
    for d in required_dirs:
        if os.path.exists(d):
            print(f"[OK] Directory exists: {d}")
        else:
            print(f"[MISSING] Directory missing: {d}")
            
    # 3. Check key config files
    required_files = [
        "docs/IMPLEMENTATION_ROADMAP.md",
        "backend/pyproject.toml",
        "backend/requirements.txt",
        "backend/app/main.py",
        "backend/app/core/config.py",
        "backend/.env"
    ]
    for f in required_files:
        if os.path.exists(f):
            print(f"[OK] File exists: {f}")
        else:
            print(f"[MISSING] File missing: {f}")

    # 4. Check AI API Key (Gemini or OpenAI)
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if gemini_key and gemini_key != "AIzaSy_your_free_gemini_key_here":
        print(f"[OK] GEMINI_API_KEY set (Starts with: {gemini_key[:7]}...)")
    elif openai_key and openai_key != "sk-your-key-here":
        print(f"[OK] OPENAI_API_KEY set (Starts with: {openai_key[:7]}...)")
    else:
        print("[!] GEMINI_API_KEY / OPENAI_API_KEY not set yet in backend/.env")

    print("\nPhase 0 environment check complete.")

if __name__ == "__main__":
    test_phase0()

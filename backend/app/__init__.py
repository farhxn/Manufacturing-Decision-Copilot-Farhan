"""
Manufacturing Decision Copilot - App Package Initialization
"""
import sys

# Global patch for pydantic-ai 0.0.14 griffe import compatibility
try:
    import griffe
    import griffe.enumerations
    import griffe.models

    sys.modules["_griffe"] = griffe
    sys.modules["_griffe.enumerations"] = griffe.enumerations
    sys.modules["_griffe.models"] = griffe.models
except Exception:
    pass

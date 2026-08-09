"""
Manufacturing Decision Copilot - App Package Initialization
"""
import sys
import importlib.abc
import importlib.util

# MetaPathFinder to redirect any internal _griffe imports in pydantic-ai to griffe
class _GriffeRedirectFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "_griffe" or fullname.startswith("_griffe."):
            real_name = "griffe" + fullname[7:]
            try:
                spec = importlib.util.find_spec(real_name)
                if spec is not None:
                    return spec
            except Exception:
                pass
        return None

if not any(isinstance(f, _GriffeRedirectFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _GriffeRedirectFinder())

try:
    import griffe
    import griffe.enumerations
    import griffe.models

    sys.modules["_griffe"] = griffe
    sys.modules["_griffe.enumerations"] = griffe.enumerations
    sys.modules["_griffe.models"] = griffe.models
except Exception:
    pass

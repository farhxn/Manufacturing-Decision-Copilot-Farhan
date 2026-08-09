"""
Manufacturing Decision Copilot - App Package Initialization
"""
import sys
import types

# 1. Fallback for opentelemetry._events if missing in installed opentelemetry package
class _DummyClass:
    def __init__(self, *args, **kwargs):
        pass
    def __call__(self, *args, **kwargs):
        return self
    def __getattr__(self, item):
        return _DummyClass()

class _DummyOtelEvents(types.ModuleType):
    def __getattr__(self, name):
        return _DummyClass

try:
    import opentelemetry._events
except ImportError:
    sys.modules["opentelemetry._events"] = _DummyOtelEvents("opentelemetry._events")

# 2. Complete _griffe module aliasing for pydantic-ai compatibility
try:
    import griffe
    sys.modules["_griffe"] = griffe
    sys.modules["_griffe.enumerations"] = griffe
    sys.modules["_griffe.models"] = griffe
    sys.modules["_griffe.dataclasses"] = griffe
    sys.modules["_griffe.expressions"] = griffe
    sys.modules["_griffe.extensions"] = griffe
    sys.modules["_griffe.agents"] = griffe
    sys.modules["_griffe.docstrings"] = griffe

    setattr(griffe, "enumerations", griffe)
    setattr(griffe, "models", griffe)
    setattr(griffe, "dataclasses", griffe)
    setattr(griffe, "expressions", griffe)
except Exception:
    pass

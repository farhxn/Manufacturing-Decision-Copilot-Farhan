"""
Manufacturing Decision Copilot - App Package Initialization
"""
import sys
import types

# 1. Fallback for opentelemetry._events if missing in installed opentelemetry package
try:
    import opentelemetry._events
except ImportError:
    otel_events = types.ModuleType("opentelemetry._events")
    class Event:
        def __init__(self, *args, **kwargs):
            pass
    otel_events.Event = Event
    sys.modules["opentelemetry._events"] = otel_events

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

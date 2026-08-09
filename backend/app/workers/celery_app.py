"""
Celery application instance.

Import this module — never instantiate Celery directly elsewhere.
All tasks auto-discover from app.workers.document_worker.
"""

import sys
import types
import importlib.abc
import importlib.util

# Fallback for opentelemetry._events if missing in installed opentelemetry package
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

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mdc_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.document_worker"],
)

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Connection
    broker_connection_retry_on_startup=True,
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_concurrency=2,               # Limit worker processes to avoid memory overload on cloud containers
    worker_prefetch_multiplier=1,       # one task at a time per worker
    # Retries
    task_max_retries=3,
    task_default_retry_delay=10,        # seconds before first retry
    # Result TTL: keep job results in Redis for 24 hours
    result_expires=86_400,
    # Routing (single default queue for now)
    task_default_queue="documents",
    task_queues={
        "documents": {
            "exchange": "documents",
            "routing_key": "documents",
        }
    },
)

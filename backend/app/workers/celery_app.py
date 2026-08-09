"""
Celery application instance.

Import this module — never instantiate Celery directly elsewhere.
All tasks auto-discover from app.workers.document_worker.
"""

import sys
import importlib.abc
import importlib.util

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

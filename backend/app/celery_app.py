from celery import Celery
from .settings import settings

celery_app = Celery(
    "vuln_tracker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

# Tune serialization / timeouts if desired
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])

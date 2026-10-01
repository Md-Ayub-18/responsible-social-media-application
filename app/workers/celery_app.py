from celery import Celery

from app.config import settings

celery_app = Celery(
    "interest_social",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,          # hard limit: 5 min
    task_soft_time_limit=240,     # soft limit: 4 min
    worker_prefetch_multiplier=1, # fair dispatch
    task_acks_late=True,          # ack after completion (safer)
)
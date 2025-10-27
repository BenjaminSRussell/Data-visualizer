"""
Celery configuration for background tasks.
"""

from celery import Celery
from kombu import Exchange, Queue
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    'url_analyzer',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['server.workers.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('sitemap_processing', Exchange('sitemap'), routing_key='sitemap.process'),
    Queue('classification', Exchange('classification'), routing_key='classification.process'),
)

celery_app.conf.task_routes = {
    'server.workers.tasks.process_sitemap_task': {
        'queue': 'sitemap_processing',
        'routing_key': 'sitemap.process',
    },
}

celery_app.conf.beat_schedule = {}

if __name__ == '__main__':
    celery_app.start()

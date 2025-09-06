from celery import Celery
from ..config import settings

# Use RabbitMQ as broker, Redis as result backend
celery_app = Celery(
    'alta_data',
    broker=settings.rabbitmq_url,  # RabbitMQ for message queuing
    backend=settings.redis_url,    # Redis for result storage
    include=['app.worker.tasks']
)

# Celery configuration optimized for RabbitMQ
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # RabbitMQ specific settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_heartbeat=30,
    broker_pool_limit=10,
    
    # Task routing
    task_routes={
        'app.worker.tasks.task_process_ocr': {'queue': 'ocr_queue'},
        'app.worker.tasks.task_transcribe_audio': {'queue': 'transcription_queue'},
        'app.worker.tasks.task_send_email': {'queue': 'email_queue'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'ocr_queue': {
            'exchange': 'ocr_exchange',
            'routing_key': 'ocr',
        },
        'transcription_queue': {
            'exchange': 'transcription_exchange',
            'routing_key': 'transcription',
        },
        'email_queue': {
            'exchange': 'email_exchange',
            'routing_key': 'email',
        },
    },
    
    # Result backend settings (Redis)
    result_backend_transport_options={
        'master_name': 'mymaster',
        'retry_policy': {
            'timeout': 5.0
        }
    },
    
    # Task execution settings
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_reject_on_worker_lost=True,
)





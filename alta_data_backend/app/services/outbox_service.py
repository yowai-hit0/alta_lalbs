from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import json
import asyncio
import logging

from ..models.outbox import OutboxEvent, OutboxEventStatus, OutboxEventType
from ..worker.celery_app import celery_app
from ..config import settings

logger = logging.getLogger(__name__)


class OutboxService:
    """Service for managing outbox events and reliable message publishing"""
    
    def __init__(self):
        self.batch_size = settings.outbox_batch_size
        self.processing_interval = settings.outbox_processing_interval
        self.max_retries = settings.outbox_max_retries
        self.retry_delay = settings.outbox_retry_delay
    
    async def create_event(
        self,
        session: AsyncSession,
        event_type: OutboxEventType,
        aggregate_id: str,
        aggregate_type: str,
        payload: Dict[str, Any]
    ) -> OutboxEvent:
        """Create a new outbox event"""
        event = OutboxEvent(
            event_type=event_type.value,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            payload=json.dumps(payload),
            status=OutboxEventStatus.PENDING.value,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        session.add(event)
        await session.flush()  # Get the ID without committing
        return event
    
    async def get_pending_events(
        self,
        session: AsyncSession,
        limit: Optional[int] = None
    ) -> List[OutboxEvent]:
        """Get pending outbox events for processing"""
        query = select(OutboxEvent).where(
            OutboxEvent.status == OutboxEventStatus.PENDING.value
        ).order_by(OutboxEvent.created_at)
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_failed_events(
        self,
        session: AsyncSession,
        limit: Optional[int] = None
    ) -> List[OutboxEvent]:
        """Get failed outbox events that can be retried"""
        query = select(OutboxEvent).where(
            and_(
                OutboxEvent.status == OutboxEventStatus.FAILED.value,
                OutboxEvent.retry_count < OutboxEvent.max_retries
            )
        ).order_by(OutboxEvent.created_at)
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def mark_event_processing(
        self,
        session: AsyncSession,
        event_id: str
    ) -> None:
        """Mark an event as being processed"""
        await session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=OutboxEventStatus.PROCESSING.value,
                last_attempt_at=datetime.now(timezone.utc).isoformat()
            )
        )
    
    async def mark_event_completed(
        self,
        session: AsyncSession,
        event_id: str
    ) -> None:
        """Mark an event as completed"""
        await session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                status=OutboxEventStatus.COMPLETED.value,
                processed_at=datetime.now(timezone.utc).isoformat()
            )
        )
    
    async def mark_event_failed(
        self,
        session: AsyncSession,
        event_id: str,
        error_message: str,
        increment_retry: bool = True
    ) -> None:
        """Mark an event as failed"""
        update_values = {
            "status": OutboxEventStatus.FAILED.value,
            "error_message": error_message,
            "last_attempt_at": datetime.now(timezone.utc).isoformat()
        }
        
        if increment_retry:
            update_values["retry_count"] = OutboxEvent.retry_count + 1
        
        await session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(**update_values)
        )
    
    async def publish_event_to_queue(
        self,
        event: OutboxEvent
    ) -> bool:
        """Publish an outbox event to the appropriate RabbitMQ queue"""
        try:
            payload = json.loads(event.payload)
            
            # Map event types to Celery tasks and queues
            task_mapping = {
                OutboxEventType.DOCUMENT_OCR_REQUESTED.value: {
                    "task": "app.worker.tasks.task_process_ocr",
                    "queue": "ocr_queue",
                    "routing_key": "ocr",
                    "args": lambda payload, aggregate_id: [aggregate_id],
                    "kwargs": lambda payload: {}
                },
                OutboxEventType.VOICE_TRANSCRIPTION_REQUESTED.value: {
                    "task": "app.worker.tasks.task_transcribe_audio",
                    "queue": "transcription_queue",
                    "routing_key": "transcription",
                    "args": lambda payload, aggregate_id: [aggregate_id],
                    "kwargs": lambda payload: {}
                },
                OutboxEventType.EMAIL_SEND_REQUESTED.value: {
                    "task": "app.worker.tasks.task_send_email",
                    "queue": "email_queue",
                    "routing_key": "email",
                    "args": lambda payload, aggregate_id: [payload.get("to_email"), payload.get("subject"), payload.get("body")],
                    "kwargs": lambda payload: {"email_type": payload.get("email_type", "general")}
                }
            }
            
            if event.event_type not in task_mapping:
                logger.warning(f"No task mapping found for event type: {event.event_type}")
                return False
            
            task_config = task_mapping[event.event_type]
            
            # Send task to Celery with RabbitMQ
            celery_app.send_task(
                task_config["task"],
                args=task_config["args"](payload, event.aggregate_id),
                kwargs=task_config["kwargs"](payload),
                queue=task_config["queue"],
                routing_key=task_config["routing_key"]
            )
            
            logger.info(f"Published event {event.id} to queue {task_config['queue']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {str(e)}")
            return False
    
    async def process_outbox_events(
        self,
        session: AsyncSession
    ) -> int:
        """Process pending outbox events"""
        processed_count = 0
        
        # Get pending events
        pending_events = await self.get_pending_events(session, self.batch_size)
        
        for event in pending_events:
            try:
                # Mark as processing
                await self.mark_event_processing(session, event.id)
                await session.commit()
                
                # Publish to queue
                success = await self.publish_event_to_queue(event)
                
                if success:
                    await self.mark_event_completed(session, event.id)
                    processed_count += 1
                else:
                    await self.mark_event_failed(
                        session, 
                        event.id, 
                        "Failed to publish to queue"
                    )
                
                await session.commit()
                
            except Exception as e:
                logger.error(f"Error processing event {event.id}: {str(e)}")
                await self.mark_event_failed(
                    session, 
                    event.id, 
                    str(e)
                )
                await session.commit()
        
        # Process failed events for retry
        failed_events = await self.get_failed_events(session, self.batch_size)
        
        for event in failed_events:
            try:
                # Check if enough time has passed since last attempt
                last_attempt = datetime.fromisoformat(event.last_attempt_at) if event.last_attempt_at else datetime.min
                time_since_last = (datetime.now(timezone.utc) - last_attempt).total_seconds()
                
                if time_since_last >= self.retry_delay:
                    await self.mark_event_processing(session, event.id)
                    await session.commit()
                    
                    success = await self.publish_event_to_queue(event)
                    
                    if success:
                        await self.mark_event_completed(session, event.id)
                        processed_count += 1
                    else:
                        await self.mark_event_failed(
                            session, 
                            event.id, 
                            "Retry failed to publish to queue"
                        )
                    
                    await session.commit()
                    
            except Exception as e:
                logger.error(f"Error retrying event {event.id}: {str(e)}")
                await self.mark_event_failed(
                    session, 
                    event.id, 
                    str(e)
                )
                await session.commit()
        
        return processed_count


# Global outbox service instance
outbox_service = OutboxService()

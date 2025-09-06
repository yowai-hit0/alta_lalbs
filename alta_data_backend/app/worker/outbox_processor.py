import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from ..config import settings
from ..services.outbox_service import outbox_service

logger = logging.getLogger(__name__)


class OutboxProcessor:
    """Background processor for outbox events"""
    
    def __init__(self):
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.running = False
        self.processing_interval = settings.outbox_processing_interval
    
    async def start(self):
        """Start the outbox processor"""
        self.running = True
        logger.info("Outbox processor started")
        
        while self.running:
            try:
                await self.process_events()
                await asyncio.sleep(self.processing_interval)
            except Exception as e:
                logger.error(f"Error in outbox processor: {str(e)}")
                await asyncio.sleep(self.processing_interval)
    
    async def stop(self):
        """Stop the outbox processor"""
        self.running = False
        logger.info("Outbox processor stopped")
    
    async def process_events(self):
        """Process outbox events"""
        async with self.session_factory() as session:
            try:
                processed_count = await outbox_service.process_outbox_events(session)
                if processed_count > 0:
                    logger.info(f"Processed {processed_count} outbox events")
            except Exception as e:
                logger.error(f"Error processing outbox events: {str(e)}")
                await session.rollback()


# Global outbox processor instance
outbox_processor = OutboxProcessor()


async def start_outbox_processor():
    """Start the outbox processor (called from main.py)"""
    await outbox_processor.start()


async def stop_outbox_processor():
    """Stop the outbox processor (called from main.py)"""
    await outbox_processor.stop()

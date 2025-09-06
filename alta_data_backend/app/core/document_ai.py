from google.cloud import documentai
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from typing import Optional
import tempfile
import os
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class DocumentAIService:
    """Service for Google Document AI OCR processing"""
    
    def __init__(self):
        self.client = None
        self.storage_client = None
        self._available = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize clients with error handling"""
        try:
            # Check if Document AI is configured
            if not settings.document_ai_processor_id or not settings.document_ai_location:
                logger.warning("Document AI not configured: Missing processor_id or location")
                self._available = False
                return
            
            # Check if GCS is available (required for Document AI)
            from .storage import is_gcs_available
            if not is_gcs_available():
                logger.warning("Document AI not available: Google Cloud Storage is not configured")
                self._available = False
                return
            
            # Initialize clients
            self.client = documentai.DocumentProcessorServiceClient()
            self.storage_client = storage.Client(project=settings.gcs_project_id)
            self._available = True
            logger.info("Document AI service is available and configured")
            
        except Exception as e:
            logger.warning(f"Document AI not available: {str(e)}")
            self._available = False
    
    def is_available(self) -> bool:
        """Check if Document AI service is available"""
        return self._available is True
    
    def process_document(self, gcs_uri: str, processor_id: str = None, location: str = None) -> Optional[str]:
        """
        Process a document using Google Document AI
        
        Args:
            gcs_uri: GCS URI of the document to process
            processor_id: Document AI processor ID (optional, uses settings if not provided)
            location: Processor location (optional, uses settings if not provided)
            
        Returns:
            Extracted text or None if processing failed
        """
        if not self.is_available():
            logger.warning("Document AI service is not available. Cannot process document.")
            return None
        
        try:
            # Use settings if parameters not provided
            processor_id = processor_id or settings.document_ai_processor_id
            location = location or settings.document_ai_location
            
            # Parse GCS URI
            if not gcs_uri.startswith('gs://'):
                logger.error(f"Invalid GCS URI: {gcs_uri}")
                return None
            
            uri_parts = gcs_uri[5:].split('/', 1)
            if len(uri_parts) != 2:
                logger.error(f"Invalid GCS URI format: {gcs_uri}")
                return None
            
            bucket_name, blob_name = uri_parts
            
            # Configure the request
            processor_name = f"projects/{settings.gcs_project_id}/locations/{location}/processors/{processor_id}"
            
            # Create document reference
            gcs_document = documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type=self._get_mime_type(blob_name)
            )
            
            # Create the request
            request = documentai.ProcessRequest(
                name=processor_name,
                gcs_document=gcs_document
            )
            
            # Process the document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract text
            if document and document.text:
                logger.info(f"Successfully processed document: {gcs_uri}")
                return document.text.strip()
            
            logger.warning(f"No text extracted from document: {gcs_uri}")
            return None
            
        except GoogleCloudError as e:
            logger.error(f"Document AI processing failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during Document AI processing: {str(e)}")
            return None
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type based on file extension"""
        ext = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'tiff': 'image/tiff',
            'tif': 'image/tiff',
            'bmp': 'image/bmp',
            'gif': 'image/gif',
        }
        return mime_types.get(ext, 'application/octet-stream')


# Global instance
document_ai_service = DocumentAIService()

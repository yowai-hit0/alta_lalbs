from google.cloud import documentai
from google.cloud import storage
from typing import Optional
import tempfile
import os
from ..config import settings


class DocumentAIService:
    """Service for Google Document AI OCR processing"""
    
    def __init__(self):
        self.client = documentai.DocumentProcessorServiceClient()
        self.storage_client = storage.Client(project=settings.gcs_project_id)
    
    def process_document(self, gcs_uri: str, processor_id: str, location: str = "us") -> Optional[str]:
        """
        Process a document using Google Document AI
        
        Args:
            gcs_uri: GCS URI of the document to process
            processor_id: Document AI processor ID
            location: Processor location (default: us)
            
        Returns:
            Extracted text or None if processing failed
        """
        try:
            # Parse GCS URI
            if not gcs_uri.startswith('gs://'):
                raise ValueError(f"Invalid GCS URI: {gcs_uri}")
            
            uri_parts = gcs_uri[5:].split('/', 1)
            bucket_name = uri_parts[0]
            blob_name = uri_parts[1]
            
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
                return document.text.strip()
            
            return None
            
        except Exception as e:
            print(f"Document AI processing failed: {e}")
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

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from ..config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Global flag to track GCS availability
_gcs_available = None
_gcs_client = None

def is_gcs_available() -> bool:
    """Check if Google Cloud Storage is available and configured"""
    global _gcs_available
    
    if _gcs_available is not None:
        return _gcs_available
    
    try:
        # Check if credentials are configured
        if not settings.gcs_project_id or not settings.gcs_bucket_name:
            logger.warning("GCS not configured: Missing project_id or bucket_name")
            _gcs_available = False
            return False
        
        # Check if credentials file exists
        if settings.google_application_credentials and not os.path.exists(settings.google_application_credentials):
            logger.warning(f"GCS not available: Credentials file not found at {settings.google_application_credentials}")
            _gcs_available = False
            return False
        
        # Try to create a client
        client = storage.Client(project=settings.gcs_project_id)
        # Test connection by listing buckets
        list(client.list_buckets())
        
        _gcs_available = True
        logger.info("Google Cloud Storage is available and configured")
        return True
        
    except Exception as e:
        logger.warning(f"Google Cloud Storage not available: {str(e)}")
        _gcs_available = False
        return False

def get_gcs_client() -> storage.Client:
    """Get GCS client with error handling"""
    global _gcs_client
    
    if not is_gcs_available():
        raise RuntimeError("Google Cloud Storage is not available. Please check your configuration.")
    
    if _gcs_client is None:
        _gcs_client = storage.Client(project=settings.gcs_project_id)
    
    return _gcs_client

def upload_bytes(bucket_name: str, blob_path: str, data: bytes, content_type: str) -> str:
    """Upload bytes to GCS with error handling"""
    if not is_gcs_available():
        raise RuntimeError("Google Cloud Storage is not available. Cannot upload file.")
    
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(data, content_type=content_type)
        return f'gs://{bucket_name}/{blob_path}'
    except GoogleCloudError as e:
        logger.error(f"GCS upload failed: {str(e)}")
        raise RuntimeError(f"Failed to upload file to Google Cloud Storage: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during GCS upload: {str(e)}")
        raise RuntimeError(f"Unexpected error during file upload: {str(e)}")

def delete_file(gcs_uri: str) -> bool:
    """Delete file from GCS with error handling"""
    if not is_gcs_available():
        logger.warning("Google Cloud Storage is not available. Cannot delete file.")
        return False
    
    try:
        if not gcs_uri.startswith('gs://'):
            logger.warning(f"Invalid GCS URI: {gcs_uri}")
            return False
        
        uri_parts = gcs_uri[5:].split('/', 1)
        if len(uri_parts) != 2:
            logger.warning(f"Invalid GCS URI format: {gcs_uri}")
            return False
        
        bucket_name, blob_name = uri_parts
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
        
        logger.info(f"Successfully deleted file: {gcs_uri}")
        return True
        
    except GoogleCloudError as e:
        logger.error(f"GCS delete failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during GCS delete: {str(e)}")
        return False



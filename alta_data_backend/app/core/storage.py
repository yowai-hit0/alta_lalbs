from google.cloud import storage
from ..config import settings


def get_gcs_client() -> storage.Client:
    return storage.Client(project=settings.gcs_project_id)


def upload_bytes(bucket_name: str, blob_path: str, data: bytes, content_type: str) -> str:
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(data, content_type=content_type)
    return f'gs://{bucket_name}/{blob_path}'



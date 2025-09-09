from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator, computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8', 
        case_sensitive=False,
        env_parse_none_str='',
        extra='ignore'
    )

    app_env: str = 'development'
    app_name: str = 'alta_data'
    secret_key: str = '8x4W0Iu7yzw0UwLRADAfhH2bflyh5R2a'
    jwt_alg: str = 'HS256'

    postgres_host: str = 'db'
    postgres_port: int = 5432
    postgres_db: str = 'alta_data'
    postgres_user: str = 'postgres'
    postgres_password: str = 'postgres'

    # Redis Configuration (for caching, rate limiting, sessions)
    redis_url: str = 'redis://redis:6379/0'
    redis_host: str = 'redis'
    redis_port: int = 6379
    redis_db: int = 0

    # RabbitMQ Configuration (for background processing)
    rabbitmq_url: str = 'amqp://guest:guest@rabbitmq:5672//'
    rabbitmq_host: str = 'rabbitmq'
    rabbitmq_port: int = 5672
    rabbitmq_user: str = 'guest'
    rabbitmq_password: str = 'guest'
    rabbitmq_vhost: str = '/'

    # Outbox Pattern Configuration
    outbox_batch_size: int = 100
    outbox_processing_interval: int = 5  # seconds
    outbox_max_retries: int = 3
    outbox_retry_delay: int = 60  # seconds

    smtp_host: str = 'localhost'
    smtp_port: int = 25
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = 'no-reply@altadata.local'

    # Google Cloud Configuration (Optional - app will run without these)
    gcs_project_id: str | None = None
    gcs_bucket_name: str | None = None
    google_application_credentials: str | None = None

    # Document AI Configuration (Optional - app will run without these)
    document_ai_processor_id: str | None = None
    document_ai_location: str = 'us'

    webauthn_rp_id: str = 'localhost'
    webauthn_rp_name: str = 'Alta Data'

    cors_origins_raw: str = 'http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000'

    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string to list"""
        v = self.cors_origins_raw
        if isinstance(v, str):
            if not v or v.strip() == '':
                return ['http://localhost:3000']
            
            # Try to parse as JSON first (in case it's a JSON string)
            if v.strip().startswith('[') and v.strip().endswith(']'):
                try:
                    import json
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed if str(origin).strip()]
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # If not JSON, treat as comma-separated string
            origins = [origin.strip() for origin in v.split(',') if origin.strip()]
            return origins if origins else ['http://localhost:3000']
        elif isinstance(v, list):
            # Already a list, return as is
            return [str(origin).strip() for origin in v if str(origin).strip()]
        else:
            # Fallback to default
            return ['http://localhost:3000']

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()





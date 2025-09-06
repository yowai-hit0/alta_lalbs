from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False)

    app_env: str = 'development'
    app_name: str = 'alta_data'
    secret_key: str = 'changeme'
    jwt_alg: str = 'HS256'

    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'alta_data'
    postgres_user: str = 'postgres'
    postgres_password: str = 'postgres'

    # Redis Configuration (for caching, rate limiting, sessions)
    redis_url: str = 'redis://localhost:6379/0'
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0

    # RabbitMQ Configuration (for background processing)
    rabbitmq_url: str = 'amqp://guest:guest@localhost:5672//'
    rabbitmq_host: str = 'localhost'
    rabbitmq_port: int = 5672
    rabbitmq_user: str = 'guest'
    rabbitmq_password: str = 'guest'
    rabbitmq_vhost: str = '/'

    # Outbox Pattern Configuration
    outbox_batch_size: int = 100
    outbox_processing_interval: int = 20  # seconds
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

    cors_origins: List[str] = ['http://localhost:3000']

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()





from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, JSON
from uuid import uuid4
from ..database import Base


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor_user_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(16))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    metadata: Mapped[dict | None] = mapped_column(JSON, default=None)



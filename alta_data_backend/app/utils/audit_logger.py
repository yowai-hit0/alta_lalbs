from ..logs import logger


def log_audit_event(action: str, status: str, resource_type: str, resource_id: str | None = None, metadata: dict | None = None, actor_user_id: str | None = None):
    logger.bind(action=action, status=status, resource_type=resource_type, resource_id=resource_id, actor_user_id=actor_user_id).info('audit', **(metadata or {}))





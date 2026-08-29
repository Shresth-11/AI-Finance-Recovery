import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.base import AuditLog
from app.core.logging import logger

def log_audit(
    db: Session,
    entity_type: str,
    action: str,
    entity_id: str = None,
    performed_by: str = "System",
    reason: str = None,
    metadata: dict = None
) -> AuditLog:
    meta_json = json.dumps(metadata) if metadata else None
    audit_entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        performed_by=performed_by,
        reason=reason,
        metadata_json=meta_json,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    
    logger.info(f"AUDIT LOG [{action}] on {entity_type}:{entity_id or 'N/A'} by {performed_by}")
    return audit_entry

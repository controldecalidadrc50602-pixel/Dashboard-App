from sqlalchemy.orm import Session
from app.models import AuditLog
from typing import Optional, Dict, Any

def log_audit_action(
    db: Session,
    username: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Registra una acción administrativa relevante en la tabla audit_logs."""
    try:
        log_entry = AuditLog(
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details or {},
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        db.rollback()
        print(f"[AUDIT LOG ERROR] Error registrando auditoría: {str(e)}")
        return None

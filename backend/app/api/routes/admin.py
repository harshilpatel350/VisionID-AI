from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, require_roles
from app.models.user import User
from app.models.recognition import AuditLog

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
def users(db: Session = Depends(get_db), _user=Depends(require_roles("admin"))):
    rows = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role, "is_active": u.is_active} for u in rows]

@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db), _user=Depends(require_roles("admin"))):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)).all()
    return [{
        "id": a.id, "actor_user_id": a.actor_user_id, "action": a.action, "entity_type": a.entity_type,
        "entity_id": a.entity_id, "metadata_json": a.metadata_json, "ip_address": a.ip_address,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in rows]

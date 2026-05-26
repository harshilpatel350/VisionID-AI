from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, require_roles
from app.models.user import User
from app.models.recognition import AuditLog
from app.schemas.response_envelope import ResponseEnvelope, PaginatedResponse, PaginatedMeta
from app.utils.validators import validate_pagination

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=PaginatedResponse[dict])
def users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), 
    _user=Depends(require_roles("admin"))
):
    offset, limit = validate_pagination(page, page_size)
    from sqlalchemy import func
    
    total = db.scalar(select(func.count(User.id))) or 0
    rows = db.scalars(select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)).all()
    
    data = [{"id": u.id, "full_name": u.full_name, "username": u.username, "role": u.role, "is_active": u.is_active} for u in rows]
    
    meta = PaginatedMeta(
        total=total,
        page=page,
        page_size=limit,
        has_more=(offset + limit) < total
    )
    return PaginatedResponse(data=data, meta=meta)

@router.get("/audit-logs", response_model=PaginatedResponse[dict])
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db), 
    _user=Depends(require_roles("admin"))
):
    offset, limit = validate_pagination(page, page_size, max_page_size=500)
    from sqlalchemy import func
    
    total = db.scalar(select(func.count(AuditLog.id))) or 0
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)).all()
    
    data = [{
        "id": a.id, "actor_user_id": a.actor_user_id, "action": a.action, "entity_type": a.entity_type,
        "entity_id": a.entity_id, "metadata_json": a.metadata_json, "ip_address": a.ip_address,
        "created_at": a.created_at.isoformat() if a.created_at else None
    } for a in rows]
    
    meta = PaginatedMeta(
        total=total,
        page=page,
        page_size=limit,
        has_more=(offset + limit) < total
    )
    return PaginatedResponse(data=data, meta=meta)

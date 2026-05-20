from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])
svc = AnalyticsService()

@router.get("/dashboard/stats")
def stats(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    return svc.dashboard_stats(db)

@router.get("/analytics/overview")
def overview(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    return svc.overview(db)

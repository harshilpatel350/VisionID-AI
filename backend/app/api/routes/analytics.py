from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.schemas.response_envelope import ResponseEnvelope
from app.schemas.dashboard import DashboardStats, AnalyticsOverview
from app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])
svc = AnalyticsService()

@router.get("/dashboard/stats", response_model=ResponseEnvelope[DashboardStats])
def stats(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    return ResponseEnvelope(data=svc.dashboard_stats(db))

@router.get("/analytics/overview", response_model=ResponseEnvelope[AnalyticsOverview])
def overview(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    return ResponseEnvelope(data=svc.overview(db))

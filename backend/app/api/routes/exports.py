from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])
svc = ExportService()

@router.get("/recognition.csv")
def export_csv(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    # Returns raw CSV bytes so doesn't use ResponseEnvelope
    return Response(
        content=svc.export_csv_bytes(db), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=recognition_logs.csv"}
    )

@router.get("/recognition.xlsx")
def export_xlsx(db: Session = Depends(get_db), _user=Depends(require_roles("admin", "operator", "viewer"))):
    # Returns raw XLSX bytes so doesn't use ResponseEnvelope
    return Response(
        content=svc.export_xlsx_bytes(db), 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=recognition_logs.xlsx"}
    )

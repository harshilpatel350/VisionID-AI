from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])
svc = ExportService()

@router.get("/recognition.csv")
def export_csv(
    start: str | None = Query(None),
    end: str | None = Query(None),
    mood: str | None = Query(None),
    is_unknown: bool | None = Query(None),
    person_name: str | None = Query(None),
    sort: str | None = Query("desc"),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator", "viewer"))
):
    start_dt = None
    end_dt = None
    try:
        if start:
            start_dt = datetime.fromisoformat(start)
        if end:
            end_dt = datetime.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")
    # Returns raw CSV bytes so doesn't use ResponseEnvelope
    return Response(
        content=svc.export_csv_bytes(db, start=start_dt, end=end_dt, mood=mood, is_unknown=is_unknown, person_name=person_name, sort=sort),
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=recognition_logs.csv"}
    )

@router.get("/recognition.xlsx")
def export_xlsx(
    start: str | None = Query(None),
    end: str | None = Query(None),
    mood: str | None = Query(None),
    is_unknown: bool | None = Query(None),
    person_name: str | None = Query(None),
    sort: str | None = Query("desc"),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator", "viewer"))
):
    start_dt = None
    end_dt = None
    try:
        if start:
            start_dt = datetime.fromisoformat(start)
        if end:
            end_dt = datetime.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")
    # Returns raw XLSX bytes so doesn't use ResponseEnvelope
    return Response(
        content=svc.export_xlsx_bytes(db, start=start_dt, end=end_dt, mood=mood, is_unknown=is_unknown, person_name=person_name, sort=sort),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=recognition_logs.xlsx"}
    )

@router.get("/persons.csv")
def export_persons_csv(
    name: str | None = Query(None),
    department: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator", "viewer"))
):
    return Response(
        content=svc.export_persons_csv_bytes(db, name=name, department=department, is_active=is_active),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=persons.csv"}
    )

@router.get("/persons.xlsx")
def export_persons_xlsx(
    name: str | None = Query(None),
    department: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator", "viewer"))
):
    return Response(
        content=svc.export_persons_xlsx_bytes(db, name=name, department=department, is_active=is_active),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=persons.xlsx"}
    )

@router.get("/unknowns.csv")
def export_unknowns_csv(
    start: str | None = Query(None),
    end: str | None = Query(None),
    mood: str | None = Query(None),
    is_reviewed: bool | None = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator", "viewer"))
):
    start_dt = None
    end_dt = None
    try:
        if start:
            start_dt = datetime.fromisoformat(start)
        if end:
            end_dt = datetime.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")
    return Response(
        content=svc.export_unknowns_csv_bytes(db, start=start_dt, end=end_dt, mood=mood, is_reviewed=is_reviewed),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=unknowns.csv"}
    )

@router.get("/unknowns.xlsx")
def export_unknowns_xlsx(
    start: str | None = Query(None),
    end: str | None = Query(None),
    mood: str | None = Query(None),
    is_reviewed: bool | None = Query(None),
    db: Session = Depends(get_db),
    _user=Depends(require_roles("admin", "operator", "viewer"))
):
    start_dt = None
    end_dt = None
    try:
        if start:
            start_dt = datetime.fromisoformat(start)
        if end:
            end_dt = datetime.fromisoformat(end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")
    return Response(
        content=svc.export_unknowns_xlsx_bytes(db, start=start_dt, end=end_dt, mood=mood, is_reviewed=is_reviewed),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=unknowns.xlsx"}
    )

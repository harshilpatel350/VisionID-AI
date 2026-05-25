from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.recognition import RecognitionLog
from app.models.face import Person, FaceSample
from app.models.user import User
from app.repositories.recognition_repo import RecognitionRepository

class AnalyticsService:
    def __init__(self):
        self.repo = RecognitionRepository()

    def dashboard_stats(self, db: Session) -> dict:
        total_persons = db.scalar(select(func.count(Person.id))) or 0
        total_samples = db.scalar(select(func.count(FaceSample.id))) or 0
        total_recognitions = db.scalar(select(func.count(RecognitionLog.id))) or 0
        unknown_detections = db.scalar(select(func.count(RecognitionLog.id)).where(RecognitionLog.is_unknown.is_(True))) or 0
        
        # System Accuracy Monitoring
        recognition_rate = float((total_recognitions - unknown_detections) / total_recognitions) if total_recognitions > 0 else 0.0
        
        # Log accuracy metrics for monitoring
        if total_recognitions % 100 == 0 and total_recognitions > 0:
            print(f"[MONITOR] Current System Accuracy (Recognition Rate): {recognition_rate * 100:.2f}%")
            
        active_users = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_recognitions = db.scalar(select(func.count(RecognitionLog.id)).where(RecognitionLog.occurred_at >= start)) or 0
        recent_unknowns = db.scalar(select(func.count(RecognitionLog.id)).where(RecognitionLog.is_unknown.is_(True), RecognitionLog.occurred_at >= now - timedelta(days=7))) or 0
        avg_confidence = db.scalar(select(func.avg(RecognitionLog.confidence))) or 0.0
        top_persons = [{"name": name, "hits": int(hits)} for name, hits in self.repo.top_persons(db)]
        logs = self.repo.logs_by_day(db, days=14)
        daily_activity = [{"day": str(day), "count": int(count)} for day, count in logs]
        return {
            "total_persons": int(total_persons),
            "total_samples": int(total_samples),
            "total_recognitions": int(total_recognitions),
            "unknown_detections": int(unknown_detections),
            "active_users": int(active_users),
            "today_recognitions": int(today_recognitions),
            "recent_unknowns": int(recent_unknowns),
            "recognition_rate": round(recognition_rate, 4),
            "avg_confidence": round(float(avg_confidence or 0.0), 4),
            "top_persons": top_persons,
            "daily_activity": daily_activity,
        }

    def overview(self, db: Session) -> dict:
        logs_by_day = [{"day": str(day), "count": int(count)} for day, count in self.repo.logs_by_day(db, days=30)]
        stmt = select(
            func.floor(RecognitionLog.confidence * 5) / 5.0,
            func.count(RecognitionLog.id)
        ).group_by(func.floor(RecognitionLog.confidence * 5) / 5.0)
        conf = [{"bucket": float(bucket), "count": int(count)} for bucket, count in db.execute(stmt).all()]
        src = db.execute(select(RecognitionLog.source_type, func.count(RecognitionLog.id)).group_by(RecognitionLog.source_type)).all()
        source_breakdown = [{"source": s, "count": int(c)} for s, c in src]
        unk = db.execute(
            select(func.date(RecognitionLog.occurred_at), func.count(RecognitionLog.id))
            .where(RecognitionLog.is_unknown.is_(True))
            .group_by(func.date(RecognitionLog.occurred_at))
            .order_by(func.date(RecognitionLog.occurred_at))
        ).all()
        unknown_trend = [{"day": str(day), "count": int(count)} for day, count in unk]
        return {
            "logs_by_day": logs_by_day,
            "confidence_buckets": conf,
            "source_breakdown": source_breakdown,
            "unknown_trend": unknown_trend,
        }

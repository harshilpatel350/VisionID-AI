from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.recognition import RecognitionLog
from app.models.face import Person, FaceSample
from app.models.user import User
from app.repositories.recognition_repo import RecognitionRepository
from app.repositories.mood_repo import MoodRepository

class AnalyticsService:
    def __init__(self):
        self.repo = RecognitionRepository()
        self.mood_repo = MoodRepository()

    def faces_per_hour(self, db: Session, hours: int = 24) -> list[dict[str, int | str]]:
        now = datetime.now(timezone.utc)
        end = now.replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(hours=hours - 1)

        rows = db.scalars(
            select(RecognitionLog.occurred_at)
            .where(RecognitionLog.occurred_at >= start)
        ).all()

        buckets: dict[str, int] = {}
        for ts in rows:
            if ts is None:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            bucket = ts.replace(minute=0, second=0, microsecond=0)
            key = bucket.strftime("%Y-%m-%d %H:00")
            buckets[key] = buckets.get(key, 0) + 1

        result = []
        for i in range(hours):
            hour = start + timedelta(hours=i)
            key = hour.strftime("%Y-%m-%d %H:00")
            result.append({"hour": key, "count": int(buckets.get(key, 0))})
        return result

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
        mood_distribution = self.mood_repo.get_mood_stats(db)
        top_persons = [{"name": name, "hits": int(hits)} for name, hits in self.repo.top_persons(db, limit=8)]
        faces_per_hour = self.faces_per_hour(db, hours=24)
        return {
            "logs_by_day": logs_by_day,
            "confidence_buckets": conf,
            "source_breakdown": source_breakdown,
            "unknown_trend": unknown_trend,
            "faces_per_hour": faces_per_hour,
            "mood_distribution": mood_distribution,
            "top_persons": top_persons,
        }

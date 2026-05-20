from __future__ import annotations
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import load_settings
from app.models.dataset import Dataset
from app.utils.files import unique_filename

class DatasetService:
    def __init__(self):
        self.settings = load_settings()

    def create_dataset(self, db: Session, name: str, description: str | None, created_by: int | None) -> Dataset:
        ds = Dataset(name=name, description=description, created_by=created_by, status="uploaded")
        db.add(ds); db.flush()
        return ds

    def save_folder_upload(self, upload: UploadFile, name_hint: str) -> Path:
        dest = self.settings.abs_upload_dir / "datasets" / name_hint
        dest.mkdir(parents=True, exist_ok=True)
        raw = upload.file.read()
        path = dest / unique_filename("dataset", Path(upload.filename or ".zip").suffix or ".zip")
        path.write_bytes(raw)
        return path

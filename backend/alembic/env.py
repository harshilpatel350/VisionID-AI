from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import load_settings
from app.db.base import Base
from app.models.user import User
from app.models.dataset import Dataset
from app.models.face import Person, FaceSample, FaceEmbedding
from app.models.recognition import RecognitionLog, AuditLog

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata
settings = load_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

def run_migrations_offline():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config({"sqlalchemy.url": settings.database_url}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

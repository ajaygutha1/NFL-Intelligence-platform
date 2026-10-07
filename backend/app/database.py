from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_derived_tables(bind=None):
    """Create the pipeline-owned tables, rebuilding any whose columns are outdated.

    `weekly_predictions` and `prediction_runs` are written by
    `src/predict_week.py` and survive re-seeding, so `create_all` alone would
    leave an old-schema table in place and the API would crash on missing
    columns. They only hold regenerable data, so a mismatch drops the table.
    """
    from sqlalchemy import inspect

    from app import models

    bind = bind or engine
    inspector = inspect(bind)

    for table in (models.WeeklyPrediction.__table__, models.PredictionRun.__table__):
        if inspector.has_table(table.name):
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            if existing != {c.name for c in table.columns}:
                print(f"Rebuilding outdated table '{table.name}' (regenerable data).")
                table.drop(bind)

    Base.metadata.create_all(bind=bind)

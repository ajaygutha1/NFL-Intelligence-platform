from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import WeeklyPrediction
from app.schemas import WeeklyPredictionOut


router = APIRouter(
    prefix="/api/predictions",
    tags=["predictions"]
)


@router.get(
    "/week/{season}/{week}",
    response_model=list[WeeklyPredictionOut]
)
def get_week_predictions(
    season: int,
    week: int,
    db: Session = Depends(get_db)
):
    return (
        db.query(WeeklyPrediction)
        .filter(
            WeeklyPrediction.season == season,
            WeeklyPrediction.week == week
        )
        .order_by(
            WeeklyPrediction.id
        )
        .all()
    )


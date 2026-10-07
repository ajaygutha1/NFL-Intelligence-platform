import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml import get_model_info
from app.models import Game, WeeklyPrediction
from app.schemas import WeeklyGameOut, WeeklyPredictionsOut, WeekSummaryOut

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/weeks", response_model=list[WeekSummaryOut])
def list_prediction_weeks(db: Session = Depends(get_db)):
    """Every (season, week) that has stored predictions, newest first."""
    rows = (
        db.query(
            WeeklyPrediction.season,
            WeeklyPrediction.week,
            func.count(WeeklyPrediction.id),
            func.max(WeeklyPrediction.generated_at),
        )
        .group_by(WeeklyPrediction.season, WeeklyPrediction.week)
        .order_by(WeeklyPrediction.season.desc(), WeeklyPrediction.week.desc())
        .all()
    )
    return [
        WeekSummaryOut(season=s, week=w, games=n, generated_at=g)
        for s, w, n, g in rows
    ]


@router.get("/week/{season}/{week}", response_model=WeeklyPredictionsOut)
def get_week_predictions(season: int, week: int, db: Session = Depends(get_db)):
    rows = (
        db.query(WeeklyPrediction, Game)
        .outerjoin(Game, WeeklyPrediction.game_id == Game.game_id)
        .filter(WeeklyPrediction.season == season, WeeklyPrediction.week == week)
        .order_by(WeeklyPrediction.game_date, WeeklyPrediction.game_id)
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No stored predictions for {season} week {week}",
        )

    games = []
    for pred, game in rows:
        played = game is not None and game.home_score is not None
        games.append(
            WeeklyGameOut(
                game_id=pred.game_id,
                game_date=pred.game_date,
                home_team=pred.home_team,
                away_team=pred.away_team,
                home_prob=pred.home_prob,
                away_prob=pred.away_prob,
                predicted_winner=pred.predicted_winner,
                confidence=max(pred.home_prob, pred.away_prob),
                drivers=json.loads(pred.drivers),
                home_score=game.home_score if played else None,
                away_score=game.away_score if played else None,
                correct=(
                    (pred.predicted_winner == pred.home_team) == bool(game.home_win)
                    if played
                    else None
                ),
            )
        )

    first = rows[0][0]
    return WeeklyPredictionsOut(
        season=season,
        week=week,
        generated_at=first.generated_at,
        model_version=first.model_version,
        in_sample=season in get_model_info()["training_seasons"],
        games=games,
    )

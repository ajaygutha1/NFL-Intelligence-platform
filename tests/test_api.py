import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    BacktestMetric,
    BacktestPrediction,
    Game,
    ModelInsight,
    PredictionRun,
    WeeklyPrediction,
)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    db = Session()
    db.add_all(
        [
            Game(game_id="2025_06_A_B", season=2025, week=6, game_date="2025-10-12",
                 home_team="B", away_team="A", home_score=20, away_score=10, home_win=1),
            BacktestPrediction(game_id="2025_06_A_B", test_season=2025, home_prob=0.7,
                               predicted_home_win=1, correct=1, confidence=0.7),
            BacktestMetric(test_season=2025, games=1, accuracy=1.0, baseline_accuracy=1.0,
                           log_loss=0.3, brier=0.1, roc_auc=0.9),
            ModelInsight(feature="diff_off_epa", coefficient=0.4,
                         permutation_importance=0.02, holdout_season=2025),
            ModelInsight(feature="diff_def_epa", coefficient=-0.3,
                         permutation_importance=0.07, holdout_season=2025),
            WeeklyPrediction(
                season=2025, week=6, generated_at="2026-10-07T00:00:00", model_version="v1",
                game_id="2025_06_A_B", game_date="2025-10-12", home_team="B", away_team="A",
                home_prob=0.7, away_prob=0.3, predicted_winner="B",
                drivers=json.dumps([{"feature": "diff_off_epa", "contribution": 0.2}]),
            ),
            PredictionRun(season=2026, week=6, run_at="2026-10-07T00:00:00+00:00",
                          first_kickoff="2026-10-11", scheduled_games=2, predicted_games=1,
                          message="1 of 2 games predicted"),
            PredictionRun(season=2026, week=5, run_at="2026-10-01T00:00:00+00:00",
                          first_kickoff="2026-10-04", scheduled_games=2, predicted_games=0,
                          message="older"),
            WeeklyPrediction(
                season=2025, week=7, generated_at="2025-10-01T00:00:00+00:00",
                model_version="v1", game_id="2025_07_E_F", game_date="2025-10-19",
                home_team="F", away_team="E", home_prob=0.6, away_prob=0.4,
                predicted_winner="F", drivers="[]",
            ),
            WeeklyPrediction(
                season=2026, week=6, generated_at="2026-10-07T00:00:00", model_version="v1",
                game_id="2026_06_C_D", game_date="2026-10-11", home_team="D", away_team="C",
                home_prob=0.4, away_prob=0.6, predicted_winner="C",
                drivers="[]",
            ),
        ]
    )
    db.commit()
    db.close()

    def override():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_backtest_predictions_include_game_context(client):
    row = client.get("/api/backtest/predictions?season=2025").json()[0]
    assert row["week"] == 6 and row["home_score"] == 20 and row["correct"] == 1


def test_model_insights_sorted_by_permutation_importance(client):
    rows = client.get("/api/model/insights").json()
    assert [r["feature"] for r in rows] == ["diff_def_epa", "diff_off_epa"]


def test_prediction_weeks_newest_first(client):
    weeks = client.get("/api/predictions/weeks").json()
    assert [(w["season"], w["week"]) for w in weeks] == [(2026, 6), (2025, 7), (2025, 6)]


def test_week_replay_has_result_and_in_sample_flag(client):
    body = client.get("/api/predictions/week/2025/6").json()
    game = body["games"][0]
    assert body["in_sample"] is True
    assert game["home_score"] == 20 and game["correct"] is True
    assert game["confidence"] == pytest.approx(0.7)


def test_unplayed_week_has_no_result(client):
    body = client.get("/api/predictions/week/2026/6").json()
    game = body["games"][0]
    assert body["in_sample"] is False
    assert game["correct"] is None and game["home_score"] is None


def test_missing_week_is_404(client):
    assert client.get("/api/predictions/week/2019/3").status_code == 404


def test_status_returns_latest_run(client):
    body = client.get("/api/predictions/status").json()
    assert (body["season"], body["week"]) == (2026, 6)
    assert body["predicted_games"] == 1 and body["scheduled_games"] == 2


def test_forecast_made_before_kickoff_is_not_in_sample_even_for_trained_season(client):
    # 2025 is in the model's training seasons, but this week was predicted
    # (2025-10-01) before its games (2025-10-19): a genuine forecast.
    assert client.get("/api/predictions/week/2025/7").json()["in_sample"] is False
    # Generated after the games were played: a replay.
    assert client.get("/api/predictions/week/2025/6").json()["in_sample"] is True


def test_outdated_derived_tables_are_rebuilt():
    from sqlalchemy import inspect, text

    from app.database import ensure_derived_tables

    engine = create_engine("sqlite://", poolclass=StaticPool)
    with engine.begin() as conn:
        conn.execute(text("create table weekly_predictions (id integer primary key, season integer)"))
        conn.execute(text("insert into weekly_predictions values (1, 2025)"))

    ensure_derived_tables(engine)

    cols = {c["name"] for c in inspect(engine).get_columns("weekly_predictions")}
    assert {"drivers", "model_version", "game_date"} <= cols
    assert inspect(engine).has_table("prediction_runs")
    with engine.connect() as conn:
        assert conn.execute(text("select count(*) from weekly_predictions")).scalar() == 0

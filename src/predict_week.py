"""Weekly prediction pipeline.

Builds leak-free matchup features for one (or several) weeks of NFL games,
scores them with the saved model, and stores the results in the platform's
`weekly_predictions` table so the API never has to call nflreadpy per request.

    python src/predict_week.py                    # next unplayed week, current season
    python src/predict_week.py --season 2025 --week 12
    python src/predict_week.py --season 2025 --weeks 6-18
    python src/predict_week.py --dry-run          # print only, don't touch the DB

Needs `data/processed/team_game.csv` (notebook 01) and `models/nfl_win_model_v1.joblib`
(notebook 03). The DB tables are created by `backend/scripts/seed_db.py`.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import nflreadpy as nfl
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

ROLLING_WINDOW = 5


def load_bundle():
    return joblib.load(ROOT / "models" / "nfl_win_model_v1.joblib")


def load_team_game():
    team_game = pd.read_csv(ROOT / "data" / "processed" / "team_game.csv")
    team_game["game_date"] = pd.to_datetime(team_game["game_date"])
    return team_game


def get_team_features(team_game, team, season, game_date):
    """Rolling-5 features for `team` using only games strictly before `game_date`.

    Mirrors notebook 01 (`shift(1).rolling(5)` within a season): the current
    game, and anything after it, can never leak in. Returns None when the team
    does not yet have five prior games this season.
    """
    history = team_game[
        (team_game["team"] == team)
        & (team_game["season"] == season)
        & (team_game["game_date"] < game_date)
    ].sort_values("game_date")

    history = history.tail(ROLLING_WINDOW)

    if len(history) < ROLLING_WINDOW:
        return None

    return {
        "roll5_off_epa": history["off_epa"].mean(),
        "roll5_def_epa": history["def_epa"].mean(),
        "roll5_pass_epa": history["pass_epa"].mean(),
        "roll5_rush_epa": history["rush_epa"].mean(),
        "roll5_success_rate": history["success_rate"].mean(),
        "rest_days": (game_date - history["game_date"].max()).days,
    }


def build_matchup_features(team_game, week_games, season):
    """One row per game with home-minus-away difference features.

    Games where either team lacks a full five-game history are skipped.
    """
    rows = []

    for _, game in week_games.iterrows():
        home = get_team_features(team_game, game["home_team"], season, game["game_date"])
        away = get_team_features(team_game, game["away_team"], season, game["game_date"])

        if home is None or away is None:
            continue

        rows.append(
            {
                "game_id": game["game_id"],
                "game_date": game["game_date"].strftime("%Y-%m-%d"),
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "diff_off_epa": home["roll5_off_epa"] - away["roll5_off_epa"],
                "diff_def_epa": home["roll5_def_epa"] - away["roll5_def_epa"],
                "diff_pass_epa": home["roll5_pass_epa"] - away["roll5_pass_epa"],
                "diff_rush_epa": home["roll5_rush_epa"] - away["roll5_rush_epa"],
                "diff_success_rate": (
                    home["roll5_success_rate"] - away["roll5_success_rate"]
                ),
                "diff_rest_days": home["rest_days"] - away["rest_days"],
            }
        )

    return pd.DataFrame(rows)


def score_matchups(bundle, matchups):
    """Add probabilities, the predicted winner, and per-feature drivers.

    A driver is the feature's contribution to the home team's log-odds
    (standardized value x logistic coefficient): positive pushes toward the
    home team, negative toward the away team.
    """
    model = bundle["model"]
    feature_cols = list(bundle["feature_cols"])

    X = matchups[feature_cols]

    scored = matchups.copy()
    scored["home_prob"] = model.predict_proba(X)[:, 1]
    scored["away_prob"] = 1 - scored["home_prob"]

    assert np.allclose(scored["home_prob"] + scored["away_prob"], 1.0)

    scored["predicted_winner"] = np.where(
        scored["home_prob"] >= 0.5, scored["home_team"], scored["away_team"]
    )

    coefs = model.named_steps["logistic_regression"].coef_[0]
    contributions = model.named_steps["scaler"].transform(X) * coefs

    scored["drivers"] = [
        json.dumps(
            [
                {"feature": f, "contribution": float(c)}
                for f, c in zip(feature_cols, row)
            ]
        )
        for row in contributions
    ]

    return scored


def load_week_games(schedule, week):
    games = schedule[
        (schedule["game_type"] == "REG") & (schedule["week"] == week)
    ].copy()
    games["game_date"] = pd.to_datetime(games["gameday"])
    return games


def next_unplayed_week(schedule):
    """First regular-season week with an unplayed game; the last week if none."""
    reg = schedule[schedule["game_type"] == "REG"]
    unplayed = reg[reg["home_score"].isna()]
    return int(unplayed["week"].min()) if len(unplayed) else int(reg["week"].max())


def save_to_db(season, week, scored, model_version):
    from app.database import Base, SessionLocal, engine
    from app.models import WeeklyPrediction

    Base.metadata.create_all(bind=engine)
    generated_at = datetime.now().isoformat(timespec="seconds")

    db = SessionLocal()
    try:
        # Idempotent: re-running a week replaces its rows.
        db.query(WeeklyPrediction).filter(
            WeeklyPrediction.season == season, WeeklyPrediction.week == week
        ).delete()
        db.add_all(
            WeeklyPrediction(
                season=season,
                week=week,
                generated_at=generated_at,
                model_version=model_version,
                game_id=row["game_id"],
                game_date=row["game_date"],
                home_team=row["home_team"],
                away_team=row["away_team"],
                home_prob=float(row["home_prob"]),
                away_prob=float(row["away_prob"]),
                predicted_winner=row["predicted_winner"],
                drivers=row["drivers"],
            )
            for _, row in scored.iterrows()
        )
        db.commit()
    finally:
        db.close()


def parse_weeks(args, schedule):
    if args.weeks:
        start, _, end = args.weeks.partition("-")
        return list(range(int(start), int(end or start) + 1))
    if args.week:
        return [args.week]
    return [next_unplayed_week(schedule)]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", type=int, default=nfl.get_current_season())
    parser.add_argument("--week", type=int)
    parser.add_argument("--weeks", help="inclusive range, e.g. 6-18")
    parser.add_argument("--dry-run", action="store_true", help="print, don't write to DB")
    args = parser.parse_args()

    bundle = load_bundle()
    team_game = load_team_game()

    if args.season not in set(team_game["season"].astype(int)):
        sys.exit(
            f"team_game.csv has no {args.season} data - rerun "
            "notebooks/01_team-gameexploration.py first."
        )

    if args.season in bundle["training_seasons"]:
        print(
            f"Note: {args.season} is in the model's training data, so these "
            "are in-sample replays, not out-of-sample forecasts."
        )

    schedule = nfl.load_schedules(args.season).to_pandas()

    for week in parse_weeks(args, schedule):
        week_games = load_week_games(schedule, week)
        matchups = build_matchup_features(team_game, week_games, args.season)

        if matchups.empty:
            print(
                f"\n{args.season} week {week}: no predictable games "
                f"({len(week_games)} scheduled; each team needs "
                f"{ROLLING_WINDOW} prior games this season)."
            )
            continue

        scored = score_matchups(bundle, matchups)

        print(f"\n{args.season} WEEK {week} PREDICTIONS ({len(scored)} games)")
        print(
            scored[
                ["away_team", "home_team", "away_prob", "home_prob", "predicted_winner"]
            ].to_string(index=False)
        )

        if not args.dry_run:
            save_to_db(args.season, week, scored, bundle["model_version"])
            print(f"Saved to weekly_predictions ({args.season} week {week}).")


if __name__ == "__main__":
    main()

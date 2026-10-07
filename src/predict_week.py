"""Weekly prediction pipeline.

Builds leak-free matchup features for one (or several) weeks of NFL games,
scores them with the saved model, and stores the results in the platform's
`weekly_predictions` table so the API never has to call nflreadpy per request.

    python src/predict_week.py                    # next unplayed week, current season
                                                  # (refreshes stale team stats first)
    python src/predict_week.py --season 2025 --week 12
    python src/predict_week.py --season 2025 --weeks 6-18
    python src/predict_week.py --dry-run          # print only, don't touch the DB
    python src/predict_week.py --no-refresh       # skip the data-freshness check

Needs `data/processed/team_game.csv` (notebook 01) and `models/nfl_win_model_v1.joblib`
(notebook 03). The DB tables are created by `backend/scripts/seed_db.py`.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
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


def played_game_count(schedule):
    """Regular-season games with a final score according to the schedule."""
    reg = schedule[schedule["game_type"] == "REG"]
    return int(reg["home_score"].notna().sum())


def team_game_is_stale(team_game, schedule, season):
    """True when the schedule has more finished games than team_game.csv knows about."""
    known = team_game[team_game["season"] == season]["game_id"].nunique()
    return played_game_count(schedule) > known


def refresh_team_game():
    """Rebuild team_game.csv by rerunning notebook 01 (pulls the latest nflverse data)."""
    print("Team stats are out of date - refreshing from nflverse (about a minute)...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "notebooks" / "01_team-gameexploration.py")],
        env={**os.environ, "MPLBACKEND": "Agg"},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(f"Refresh failed:\n{result.stderr[-1500:]}")
    return load_team_game()


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
    from app.database import SessionLocal, ensure_derived_tables
    from app.models import WeeklyPrediction

    ensure_derived_tables()
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

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
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def games_played_before(team_game, season, week_games):
    """Most games any team has played this season before the week's first kickoff."""
    first = week_games["game_date"].min()
    prior = team_game[(team_game["season"] == season) & (team_game["game_date"] < first)]
    return int(prior.groupby("team").size().max()) if len(prior) else 0


def run_message(scheduled, predicted, max_played):
    if predicted == scheduled:
        return f"All {scheduled} games predicted."
    if predicted == 0:
        return (
            f"No games predictable yet: each team needs {ROLLING_WINDOW} prior games "
            f"this season and the most any team has played is {max_played}. "
            "The weekly update will generate them once enough games are in."
        )
    return (
        f"{predicted} of {scheduled} games predicted; the rest involve a team with "
        f"fewer than {ROLLING_WINDOW} prior games (for example after a bye)."
    )


def save_run(season, week, week_games, predicted, message):
    from app.database import SessionLocal, ensure_derived_tables
    from app.models import PredictionRun

    ensure_derived_tables()
    db = SessionLocal()
    try:
        db.query(PredictionRun).filter(
            PredictionRun.season == season, PredictionRun.week == week
        ).delete()
        db.add(
            PredictionRun(
                season=season,
                week=week,
                run_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                first_kickoff=week_games["game_date"].min().strftime("%Y-%m-%d"),
                scheduled_games=len(week_games),
                predicted_games=predicted,
                message=message,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
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
    parser.add_argument(
        "--no-refresh", action="store_true", help="don't refresh stale team stats"
    )
    args = parser.parse_args()

    bundle = load_bundle()
    team_game = load_team_game()
    schedule = nfl.load_schedules(args.season).to_pandas()

    if not args.no_refresh and team_game_is_stale(team_game, schedule, args.season):
        team_game = refresh_team_game()
        if team_game_is_stale(team_game, schedule, args.season):
            print(
                "Note: nflverse play-by-play has not caught up with the schedule yet; "
                "using the data available."
            )

    if args.season not in set(team_game["season"].astype(int)):
        sys.exit(f"No {args.season} data available from nflverse yet.")

    if args.season in bundle["training_seasons"]:
        print(
            f"Note: {args.season} is in the model's training data, so replays of "
            "completed weeks are in-sample, not out-of-sample forecasts."
        )

    for week in parse_weeks(args, schedule):
        week_games = load_week_games(schedule, week)
        matchups = build_matchup_features(team_game, week_games, args.season)

        message = run_message(
            len(week_games),
            len(matchups),
            games_played_before(team_game, args.season, week_games),
        )

        if not args.dry_run and not week_games.empty:
            save_run(args.season, week, week_games, len(matchups), message)

        if matchups.empty:
            print(f"\n{args.season} week {week}: {message}")
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

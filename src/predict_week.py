from pathlib import Path
from datetime import datetime, timezone
import sys

import pandas as pd
import numpy as np
import nflreadpy as nfl
import joblib

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT / "backend")
)

from app.database import SessionLocal
from app.models import WeeklyPrediction


bundle = joblib.load(
    ROOT
    / "models"
    / "nfl_win_model_v1.joblib"
)


model = bundle["model"]

feature_cols = (
    bundle["feature_cols"]
)


team_game = pd.read_csv(
    ROOT
    / "data"
    / "processed"
    / "team_game.csv"
)


team_game["game_date"] = pd.to_datetime(
    team_game["game_date"]
)


# function for last 5 games
def get_team_features(
    team,
    season,
    game_date
):

    history = team_game[
        (team_game["team"] == team)
        & (team_game["season"] == season)
        & (
            team_game["game_date"]
            < game_date
        )
    ].sort_values(
        "game_date"
    )


    history = history.tail(5)


    if len(history) < 5:
        return None


    return {

        "roll5_off_epa":
            history[
                "off_epa"
            ].mean(),

        "roll5_def_epa":
            history[
                "def_epa"
            ].mean(),

        "roll5_pass_epa":
            history[
                "pass_epa"
            ].mean(),

        "roll5_rush_epa":
            history[
                "rush_epa"
            ].mean(),

        "roll5_success_rate":
            history[
                "success_rate"
            ].mean(),

        "rest_days":
            (
                game_date
                -
                history[
                    "game_date"
                ].max()
            ).days
    }

# test week 12 of 2025

SEASON = 2025
WEEK = 12


schedule = nfl.load_schedules(
    SEASON
).to_pandas()


week_games = schedule[
    (schedule["game_type"] == "REG")
    & (schedule["week"] == WEEK)
].copy()


week_games[
    "game_date"
] = pd.to_datetime(
    week_games["gameday"]
)

rows = []


for _, game in week_games.iterrows():

    home_features = get_team_features(
        game["home_team"],
        SEASON,
        game["game_date"]
    )

    away_features = get_team_features(
        game["away_team"],
        SEASON,
        game["game_date"]
    )


    if (
        home_features is None
        or away_features is None
    ):
        continue


    row = {
        "game_id":
            game["game_id"],

        "home_team":
            game["home_team"],

        "away_team":
            game["away_team"]
    }


    row["diff_off_epa"] = (
        home_features["roll5_off_epa"]
        -
        away_features["roll5_off_epa"]
    )


    row["diff_def_epa"] = (
        home_features["roll5_def_epa"]
        -
        away_features["roll5_def_epa"]
    )


    row["diff_pass_epa"] = (
        home_features["roll5_pass_epa"]
        -
        away_features["roll5_pass_epa"]
    )


    row["diff_rush_epa"] = (
        home_features["roll5_rush_epa"]
        -
        away_features["roll5_rush_epa"]
    )


    row["diff_success_rate"] = (
        home_features[
            "roll5_success_rate"
        ]
        -
        away_features[
            "roll5_success_rate"
        ]
    )


    row["diff_rest_days"] = (
        home_features["rest_days"]
        -
        away_features["rest_days"]
    )


    rows.append(row)

# generate probabilities

weekly = pd.DataFrame(
    rows
)

X_week = weekly[
    feature_cols
]

weekly[
    "home_prob"
] = model.predict_proba(
    X_week
)[:, 1]

weekly[
    "away_prob"
] = (
        1
        - weekly["home_prob"]
)

assert np.allclose(
    weekly["home_prob"]
    + weekly["away_prob"],
    1.0
)

# print weekly predictions
weekly[
    "predicted_winner"
] = np.where(
    weekly["home_prob"] >= 0.5,

    weekly["home_team"],

    weekly["away_team"]
)

# save weekly predictions to database
generated_at = datetime.now(
    timezone.utc
).isoformat()

db = SessionLocal()

try:
    # remove old predictions for this season and week
    db.query(
        WeeklyPrediction
    ).filter(
        WeeklyPrediction.season == SEASON,
        WeeklyPrediction.week == WEEK
    ).delete(
        synchronize_session=False
    )

    prediction_rows = [
        WeeklyPrediction(
            season=SEASON,
            week=WEEK,
            generated_at=generated_at,
            game_id=str(row["game_id"]),
            home_team=str(row["home_team"]),
            away_team=str(row["away_team"]),
            home_prob=float(row["home_prob"]),
            away_prob=float(row["away_prob"]),
            predicted_winner=str(
                row["predicted_winner"]
            )
        )
        for _, row in weekly.iterrows()
    ]

    db.add_all(
        prediction_rows
    )

    db.commit()

    print(
        f"\nSaved {len(prediction_rows)} "
        "weekly predictions to database."
    )

except Exception:
    db.rollback()
    raise

finally:
    db.close()



print(
    "\n=============================="
)

print(
    f"{SEASON} WEEK {WEEK} PREDICTIONS"
)

print(
    "=============================="
)

print(
    weekly[
        [
            "away_team",
            "home_team",
            "away_prob",
            "home_prob",
            "predicted_winner"
        ]
    ].to_string(
        index=False
    )
)


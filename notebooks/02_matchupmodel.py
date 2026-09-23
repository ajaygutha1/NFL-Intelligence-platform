from pathlib import Path

import pandas as pd
import numpy as np
import nflreadpy as nfl

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    brier_score_loss
)


#load data set
ROOT = Path(__file__).resolve().parents[1]

team_game_path = (
    ROOT / "data" / "processed" / "team_game.csv"
)

team_game = pd.read_csv(team_game_path)

team_game["game_date"] = pd.to_datetime(
    team_game["game_date"]
)

print(team_game.head().to_string())
print("\nShape:", team_game.shape)


# define game features
team_features = [
    "roll5_off_epa",
    "roll5_def_epa",
    "roll5_pass_epa",
    "roll5_rush_epa",
    "roll5_success_rate",
    "rest_days"
]


# extract home teams row
home = team_game[
    team_game["team"] == team_game["home_team"]
].copy()

home = home[
    [
        "game_id",
        "season",
        "week",
        "game_date",
        "home_team",
        "away_team",
    ] + team_features
]


#rename features
home = home.rename(
    columns={
        feature: f"home_{feature}"
        for feature in team_features
    }
)

print("\nHOME:")
print(home.head().to_string())


# away team rows
away = team_game[
    team_game["team"] == team_game["away_team"]
].copy()

away = away[
    ["game_id"] + team_features
]

away = away.rename(
    columns={
        feature: f"away_{feature}"
        for feature in team_features
    }
)

print("\nAWAY:")
print(away.head().to_string())


# merge into 1 matchup row
matchups = home.merge(
    away,
    on="game_id",
    how="inner"
)

print("\nMATCHUPS:")
print(matchups.head().to_string())

print("\nNumber of team-game rows:", len(team_game))
print("Number of matchup rows:", len(matchups))

# make sure every matchup has exactly 2 team-game rows
assert len(team_game) == 2 * len(matchups), (
    "Row-count invariant failed: every matchup should have exactly "
    "2 team-game rows."
)

print("Row-count invariant passed")


# difference features
matchups["diff_off_epa"] = (
    matchups["home_roll5_off_epa"]
    - matchups["away_roll5_off_epa"]
)

matchups["diff_def_epa"] = (
    matchups["home_roll5_def_epa"]
    - matchups["away_roll5_def_epa"]
)

matchups["diff_pass_epa"] = (
    matchups["home_roll5_pass_epa"]
    - matchups["away_roll5_pass_epa"]
)

matchups["diff_rush_epa"] = (
    matchups["home_roll5_rush_epa"]
    - matchups["away_roll5_rush_epa"]
)

matchups["diff_success_rate"] = (
    matchups["home_roll5_success_rate"]
    - matchups["away_roll5_success_rate"]
)

matchups["diff_rest_days"] = (
    matchups["home_rest_days"]
    - matchups["away_rest_days"]
)


feature_cols = [
    "diff_off_epa",
    "diff_def_epa",
    "diff_pass_epa",
    "diff_rush_epa",
    "diff_success_rate",
    "diff_rest_days"
]

print(
    matchups[
        [
            "game_id",
            "home_team",
            "away_team"
        ] + feature_cols
    ].head(10).to_string(index=False)
)


# load schedule/results data
seasons = sorted(
    matchups["season"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

print("\nSeasons being loaded:")
print(seasons)

schedule = nfl.load_schedules(
    seasons
).to_pandas()


#keeping regular season games
schedule = schedule[
    schedule["game_type"] == "REG"
].copy()

results = schedule[
    [
        "game_id",
        "home_score",
        "away_score"
    ]
].copy()


#merge
matchups = matchups.merge(
    results,
    on="game_id",
    how="left"
)

print(
    matchups[
        [
            "game_id",
            "home_team",
            "away_team",
            "home_score",
            "away_score"
        ]
    ].head(10).to_string(index=False)
)


# remove games without scores
matchups = matchups.dropna(
    subset=[
        "home_score",
        "away_score"
    ]
).copy()


# Removing tie games for model
tie_games = matchups[
    matchups["home_score"]
    == matchups["away_score"]
]

print("\nTie games being removed:", len(tie_games))

matchups = matchups[
    matchups["home_score"]
    != matchups["away_score"]
].copy()


# Create home_win
matchups["home_win"] = (
    matchups["home_score"]
    > matchups["away_score"]
).astype(int)

print(
    matchups[
        [
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "home_win"
        ]
    ].head(10).to_string(index=False)
)


#remove early season from model training
model_data = matchups.dropna(
    subset=feature_cols + ["home_win"]
).copy()

print("\nTotal matchups:", len(matchups))
print("Usable model games:", len(model_data))


# sort chronologically
model_data = model_data.sort_values(
    "game_date"
).reset_index(drop=True)


# make sure game date is datetime
model_data["game_date"] = pd.to_datetime(
    model_data["game_date"]
)


# Save complete multi-season model dataset for Session 3
model_data_path = (
    ROOT
    / "data"
    / "processed"
    / "model_data.csv"
)

model_data.to_csv(
    model_data_path,
    index=False
)

print(
    "\nSaved model_data:",
    model_data_path
)

print("\nSeasons in model_data:")
print(
    model_data["season"]
    .value_counts()
    .sort_index()
)

print("\nFull model_data date range:")
print(
    model_data["game_date"].min(),
    "to",
    model_data["game_date"].max()
)

print("\nmodel_data shape:")
print(model_data.shape)


#make temporal split
unique_dates = np.sort(
    model_data["game_date"].unique()
)


# find an 80% cutoff
cutoff_index = int(
    len(unique_dates) * 0.8
)

cutoff_date = unique_dates[
    cutoff_index
]

print(
    "\n80% cutoff date:",
    cutoff_date
)


# everything before cutoff is training
train = model_data[
    model_data["game_date"] < cutoff_date
].copy()


# everything after cutoff is validation
val = model_data[
    model_data["game_date"] >= cutoff_date
].copy()


print("\nTrain period:")
print(
    train["game_date"].min(),
    "to",
    train["game_date"].max()
)

print("\nValidation period:")
print(
    val["game_date"].min(),
    "to",
    val["game_date"].max()
)

print("\nTraining games:", len(train))
print("Validation games:", len(val))


# make sure train and validation do not overlap
assert (
    train["game_date"].max()
    < val["game_date"].min()
)


# Create x and y. It is an ML convention.
# Where: X= inputs/features , Y = answer

X_train = train[feature_cols]
y_train = train["home_win"]

X_val = val[feature_cols]
y_val = val["home_win"]


#baseline prediction
baseline_predictions = np.ones(
    len(y_val),
    dtype=int
)

baseline_accuracy = accuracy_score(
    y_val,
    baseline_predictions
)

print(
    "\nHome-team baseline accuracy:",
    baseline_accuracy
)


# Create logistic regression model
model = Pipeline([
    (
        "scaler",
        StandardScaler()
    ),
    (
        "logistic_regression",
        LogisticRegression(
            max_iter=1000
        )
    )
])


#train the model
model.fit(
    X_train,
    y_train
)


#make predictions
val_predictions = model.predict(
    X_val
)

model_accuracy = accuracy_score(
    y_val,
    val_predictions
)

print(
    "\nModel validation accuracy:",
    model_accuracy
)

print(
    "Baseline accuracy:",
    baseline_accuracy
)


# win probabilities
home_win_probabilities = (
    model.predict_proba(X_val)[:, 1]
)


# check probability accuracy
model_log_loss = log_loss(
    y_val,
    home_win_probabilities
)

model_brier_score = brier_score_loss(
    y_val,
    home_win_probabilities
)

print(
    "\nModel log loss:",
    model_log_loss
)

print(
    "Model Brier score:",
    model_brier_score
)


# Printing prediction output
prediction_results = val[
    [
        "game_id",
        "game_date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "home_win"
    ]
].copy()

prediction_results[
    "home_win_probability"
] = home_win_probabilities

prediction_results[
    "predicted_home_win"
] = val_predictions


# check if prediction was correct
prediction_results[
    "correct_prediction"
] = (
    prediction_results["home_win"]
    == prediction_results["predicted_home_win"]
).astype(int)


print("\npredictions:")

print(
    prediction_results.head(15)
    .to_string(index=False)
)


print(
    "\nCorrect predictions:",
    prediction_results["correct_prediction"].sum(),
    "/",
    len(prediction_results)
)

print(
    "Prediction accuracy:",
    prediction_results["correct_prediction"].mean()
)


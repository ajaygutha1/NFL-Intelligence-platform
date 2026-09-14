from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    log_loss,
    brier_score_loss,
    roc_auc_score
)

from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance

# The Project root: NFL-Intelligence-platform/
ROOT = Path(__file__).resolve().parent.parent

# Load the dataset built in session 2
model_data = pd.read_csv(
    ROOT
    / "data"
    / "processed"
    / "model_data.csv"
)

model_data["game_date"] = pd.to_datetime(
    model_data["game_date"]
)

feature_cols = [
    "diff_off_epa",
    "diff_def_epa",
    "diff_pass_epa",
    "diff_rush_epa",
    "diff_success_rate",
    "diff_rest_days"
]


print("\nSeasons:")
print(
    model_data["season"]
    .value_counts()
    .sort_index()
)

# reusable model function
def make_model():
    return Pipeline(
        [ (
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


seasons = sorted(
    model_data["season"]
    .astype(int)
    .unique()
)

backtest_rows = []
all_predictions = []

for test_season in seasons[1:]:

    print(
        f"\nBacktesting {test_season}..."
    )

    # All previous seasons
    train = model_data[
        model_data["season"] < test_season
    ].copy()

    # Only season we're testing
    test = model_data[
        model_data["season"] == test_season
    ].copy()

    X_train = train[feature_cols]
    y_train = train["home_win"]

    X_test = test[feature_cols]
    y_test = test["home_win"]

    # New model for this backtest
    model = make_model()

    model.fit(
        X_train,
        y_train
    )

    # Home win probabilities
    home_prob = (
        model.predict_proba(X_test)[:, 1]
    )

    # Convert probability to 0/1 winner
    predictions = (
        home_prob >= 0.5
    ).astype(int)

    # Metrics
    accuracy = accuracy_score(
        y_test,
        predictions
    )

    ll = log_loss(
        y_test,
        home_prob
    )

    brier = brier_score_loss(
        y_test,
        home_prob
    )

    auc = roc_auc_score(
        y_test,
        home_prob
    )

    baseline_accuracy = (
        y_test.mean()
    )

    backtest_rows.append({
        "test_season": test_season,
        "games": len(test),
        "accuracy": accuracy,
        "baseline_accuracy":
            baseline_accuracy,
        "log_loss": ll,
        "brier": brier,
        "roc_auc": auc
    })

    # Save individual predictions
    season_predictions = test.copy()

    season_predictions[
        "home_prob"
    ] = home_prob

    season_predictions[
        "predicted_home_win"
    ] = predictions

    all_predictions.append(
        season_predictions
    )

    backtest_results = pd.DataFrame(
        backtest_rows
    )

    oos_predictions = pd.concat(
        all_predictions,
        ignore_index=True
    )

    print("\n==============================")
    print("WALK-FORWARD BACKTEST")
    print("==============================")

    print(
        backtest_results.to_string(
            index=False
        )
    )


fraction_positive, mean_predicted = (
    calibration_curve(
        oos_predictions[
            "home_win"
        ],
        oos_predictions[
            "home_prob"
        ],
        n_bins=8,
        strategy="quantile"
    )
)

models_dir = ROOT / "models"

models_dir.mkdir(
    parents=True,
    exist_ok=True
)


plt.figure()

# Perfect calibration line
plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    label="Perfect calibration"
)

# Our model
plt.plot(
    mean_predicted,
    fraction_positive,
    marker="o",
    label="NFL model"
)

plt.xlabel(
    "Predicted home win probability"
)

plt.ylabel(
    "Actual home win rate"
)

plt.title(
    "NFL Win Probability Calibration"
)

plt.legend()

plt.savefig(
    models_dir
    / "calibration.png",
    bbox_inches="tight"
)

plt.show()

importance_train = model_data[
    model_data["season"] < 2025
].copy()

importance_test = model_data[
    model_data["season"] == 2025
].copy()


importance_model = make_model()

importance_model.fit(
    importance_train[feature_cols],
    importance_train["home_win"]
)

logistic_model = (
    importance_model
    .named_steps[
        "logistic_regression"
    ]
)


coefficients = pd.DataFrame({
    "feature":
        feature_cols,

    "coefficient":
        logistic_model.coef_[0]
})


coefficients[
    "abs_coefficient"
] = coefficients[
    "coefficient"
].abs()


coefficients = (
    coefficients
    .sort_values(
        "abs_coefficient",
        ascending=False
    )
)


print("\n==============================")
print("MODEL COEFFICIENTS")
print("==============================")

print(
    coefficients.to_string(
        index=False
    )
)

perm = permutation_importance(
    importance_model,

    importance_test[
        feature_cols
    ],

    importance_test[
        "home_win"
    ],

    n_repeats=20,
    random_state=42,
    scoring="neg_log_loss"
)


perm_df = pd.DataFrame({
    "feature":
        feature_cols,

    "permutation_importance":
        perm.importances_mean
})


perm_df = perm_df.sort_values(
    "permutation_importance",
    ascending=False
)


print("\n==============================")
print("PERMUTATION IMPORTANCE")
print("==============================")

print(
    perm_df.to_string(
        index=False
    )
)


oos_predictions[
    "correct"
] = (
    oos_predictions[
        "predicted_home_win"
    ]
    ==
    oos_predictions[
        "home_win"
    ]
)

oos_predictions[
    "confidence"
] = np.where(
    oos_predictions[
        "predicted_home_win"
    ] == 1,

    oos_predictions[
        "home_prob"
    ],

    1
    - oos_predictions[
        "home_prob"
    ]
)

most_wrong = (
    oos_predictions[
        ~oos_predictions["correct"]
    ]
    .sort_values(
        "confidence",
        ascending=False
    )
    .head(10)
)


most_right = (
    oos_predictions[
        oos_predictions["correct"]
    ]
    .sort_values(
        "confidence",
        ascending=False
    )
    .head(10)
)


display_cols = [
    "season",
    "week",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "home_prob",
    "confidence",
    "diff_off_epa",
    "diff_def_epa",
    "diff_pass_epa",
    "diff_rush_epa",
    "diff_success_rate",
    "diff_rest_days"
]


print("\n==============================")
print("10 MOST CONFIDENT WRONG")
print("==============================")

print(
    most_wrong[
        display_cols
    ].to_string(index=False)
)


print("\n==============================")
print("10 MOST CONFIDENT RIGHT")
print("==============================")

print(
    most_right[
        display_cols
    ].to_string(index=False)
)


# save final model
final_model = make_model()

final_model.fit(
    model_data[feature_cols],
    model_data["home_win"]
)

# bundle
model_bundle = {

    "model":
        final_model,

    "feature_cols":
        feature_cols,

    "training_seasons":
        sorted(
            model_data[
                "season"
            ]
            .astype(int)
            .unique()
            .tolist()
        ),

    "backtest_metrics":
        backtest_results
        .to_dict(
            orient="records"
        )
}

model_path = (
    ROOT
    / "models"
    / "nfl_win_model_v1.joblib"
)


joblib.dump(
    model_bundle,
    model_path
)


print(
    "\nSaved final model:",
    model_path
)

#save backtest predictions
predictions_dir = (
    ROOT
    / "data"
    / "predictions"
)

predictions_dir.mkdir(
    parents=True,
    exist_ok=True
)


oos_predictions.to_csv(
    predictions_dir
    / "backtest_predictions.csv",
    index=False
)


backtest_results.to_csv(
    predictions_dir
    / "backtest_metrics.csv",
    index=False
)


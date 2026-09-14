# NFL Intelligence Platform

An NFL weekly game predictor: given a matchup, it estimates the home team's win
probability using team efficiency stats (EPA, success rate) built from
[nflverse](https://nflverse.nflverse.com/) play-by-play data.

## How it works (pipeline)

1. `notebooks/01_team-gameexploration.py` — loads play-by-play data, computes
   offensive/defensive/passing/rushing EPA and success rate per team per game,
   and builds leak-free rolling 5-game features (`shift(1).rolling(5)`, so a
   game never sees its own result).
2. `notebooks/02_matchupmodel.py` — turns the two team-game rows per game into
   one matchup row with home-vs-away difference features, builds the
   `home_win` target, and trains a first logistic regression model with a
   proper chronological (not random) train/validation split.
3. `notebooks/03_backtest.py` — walk-forward backtest (train on all prior
   seasons, predict the next one, repeat), calibration check, feature
   coefficients vs. permutation importance, error analysis on the most
   confident right/wrong predictions, and saves the final model
   (`models/nfl_win_model_v1.joblib`).
4. `src/predict_week.py` — loads the saved model and produces win
   probabilities for a real week of games.

## How to run

```bash
pip install -r requirements.txt
python notebooks/01_team-gameexploration.py
python notebooks/02_matchupmodel.py
python notebooks/03_backtest.py
python src/predict_week.py
```

## Results (walk-forward backtest, 2022-2025)

| Season | Games | Accuracy | Baseline (always home) | Log Loss | Brier | ROC AUC |
|---|---|---|---|---|---|---|
| 2022 | 190 | 65.8% | 57.9% | 0.626 | 0.218 | 0.699 |
| 2023 | 190 | 62.1% | 58.9% | 0.660 | 0.234 | 0.631 |
| 2024 | 190 | 68.4% | 54.2% | 0.622 | 0.215 | 0.726 |
| 2025 | 190 | 60.5% | 52.6% | 0.635 | 0.224 | 0.689 |

The model beats the "always predict home team" baseline in every backtested
season.

## Prediction explanations

<!--
SHARAT — TASK 2/2: write this section in plain English.

Below is a real example of what src/predict_week.py actually outputs for one
game (2025 Week 12, Jets @ Ravens):

    away_team home_team  away_prob  home_prob predicted_winner
          NYJ       BAL   0.205159   0.794841              BAL

That means the model thinks the Ravens (home) have about a 79% chance to beat
the Jets.

Your job: explain what a prediction like this actually means to someone who
has never seen this project before. Ideas to cover:
  - What does "79% home win probability" mean in plain English? (It does NOT
    mean the Ravens will win by a specific score — it's a probability.)
  - Pick one or two of the model's real features (see the coefficients in
    notebooks/03_backtest.py's output, e.g. diff_off_epa, diff_def_epa) and
    describe in plain English what a "positive" vs "negative" value of that
    feature for the home team means for the prediction.
  - Do NOT say a coefficient directly equals a percentage-point swing unless
    you've actually calculated that properly — logistic regression
    coefficients don't work that way (they affect the log-odds, not the raw
    probability, and the relationship isn't linear). Describe direction and
    relative importance instead: "a bigger passing EPA advantage tends to
    push the prediction toward the home team" is safe. "Every 0.1 EPA is
    worth 5 percentage points" is not, unless proven.

Replace this whole comment with your actual writeup.
-->

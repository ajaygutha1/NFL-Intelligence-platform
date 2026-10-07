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
4. `src/predict_week.py` — loads the saved model, builds leak-free features
   for a week of games, and stores win probabilities (plus the per-feature
   drivers behind each one) in the platform database.

## How to run

```bash
pip install -r requirements.txt
python notebooks/01_team-gameexploration.py
python notebooks/02_matchupmodel.py
python notebooks/03_backtest.py
python src/predict_week.py            # next unplayed week of the current season
```

`predict_week.py` also takes `--season 2025 --week 12`, `--weeks 6-18`, and
`--dry-run`. A game is only predicted once both teams have five prior games in
that season, so the first predictable week of a season is usually week 6.

## Run the platform (local)

Needs Python 3.10+ and Node 20+.

```bash
# 1. backend: load the ML outputs into SQLite, then serve the API
python backend/scripts/seed_db.py
cd backend && uvicorn app.main:app --port 8000

# 2. weekly predictions (needs notebooks 01-03 to have run)
python src/predict_week.py --season 2025 --weeks 6-18

# 3. frontend
cd frontend && npm install && npm run dev      # http://localhost:3000
```

Pages: **Model Performance**, **Weekly Predictions**, **Prediction History**
(every backtested game, filterable), and **Model Insights** (coefficients vs.
permutation importance). Re-run `seed_db.py` whenever notebook 03 regenerates
its CSVs; it leaves stored weekly predictions untouched.

Tests: `pip install -r requirements.txt && pytest` (feature leakage checks,
parity between the weekly features and the training features, API endpoints).

## Results (walk-forward backtest, 2017-2025)

Each season is predicted by a model trained only on earlier seasons.

| Season | Games | Accuracy | Baseline (always home) | Log Loss | Brier | ROC AUC |
|---|---|---|---|---|---|---|
| 2017 | 174 | 67.8% | 59.2% | 0.595 | 0.204 | 0.730 |
| 2018 | 175 | 69.7% | 57.1% | 0.580 | 0.198 | 0.765 |
| 2019 | 174 | 61.5% | 55.2% | 0.666 | 0.235 | 0.654 |
| 2020 | 174 | 65.5% | 48.3% | 0.644 | 0.226 | 0.714 |
| 2021 | 191 | 60.2% | 52.9% | 0.668 | 0.237 | 0.655 |
| 2022 | 190 | 66.8% | 57.9% | 0.614 | 0.213 | 0.701 |
| 2023 | 190 | 62.1% | 58.9% | 0.666 | 0.236 | 0.626 |
| 2024 | 190 | 68.9% | 54.2% | 0.608 | 0.208 | 0.740 |
| 2025 | 190 | 62.6% | 52.6% | 0.626 | 0.219 | 0.706 |
| **All** | **1,648** | **65.0%** | **55.2%** | **0.630** | **0.220** | **0.698** |

**Headline: 65.0% accuracy vs. a 55.2% always-pick-the-home-team baseline
(+9.8 points) over 1,648 out-of-sample games.** The model beats the baseline in
all 9 backtested seasons. The "All" row is the game-weighted average of the
seasons. Weekly predictions for a season the model was trained on (such as the
2025 replays on the Weekly Predictions page) are in-sample and are labeled as
such; the numbers above are the honest ones.

## Prediction explanations

When the model outputs something like:

    away_team home_team  away_prob  home_prob predicted_winner
          NYJ       BAL   0.205159   0.794841              BAL


the 79% is a probability, not a guarantee. It means the model estimates
that Baltimore has about a 79% chance of winning based on the statistical
features available for this matchup. A loss would not necessarily mean the
prediction was "wrong"—it would simply be an outcome that was considered
less likely.

Two of the model's features help illustrate how this works:

`diff_off_epa` (home team's recent offensive efficiency minus the away
team's) has one of the largest coefficients in the model (second only to
`diff_success_rate`). When this value is
positive, the home team has been generating more expected points per play
on offense recently than the away team, so the model shifts its prediction
toward a home win. When it is negative, the shift goes in the opposite
direction.

`diff_def_epa` (home team's recent EPA allowed minus the away team's) works
in the opposite direction. Because a lower EPA allowed indicates a better
defense, a negative `diff_def_epa` means the home team's defense has been
performing better than the away team's. This also pushes the prediction
toward a home win.

Interestingly, `diff_success_rate` and `diff_off_epa` have the largest raw
coefficients, but when we test feature usefulness by scrambling each feature
and measuring how much log loss rises (permutation importance), `diff_def_epa`
comes out well ahead (about 0.070, versus 0.017 for `diff_success_rate`). The
offensive features are highly correlated with each other, so they share credit
in the coefficients, while defense carries information nothing else does. This is a reminder that a larger coefficient does not automatically
mean a feature is the most useful in practice.

We also avoid interpreting a coefficient as a fixed probability conversion.
For example, we would not say that "a 0.1 increase in `diff_off_epa` equals
a 5 percentage point increase in win probability." Logistic regression
coefficients operate on the log-odds scale rather than directly on
probability, so the same feature change can have different effects on
predicted probability depending on where the original prediction starts.
For this reason, we describe these features primarily in terms of their
direction and relative importance rather than using a fixed probability
conversion.

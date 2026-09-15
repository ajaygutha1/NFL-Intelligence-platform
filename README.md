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
team's) has the largest coefficient in the model. When this value is
positive, the home team has been generating more expected points per play
on offense recently than the away team, so the model shifts its prediction
toward a home win. When it is negative, the shift goes in the opposite
direction.

`diff_def_epa` (home team's recent EPA allowed minus the away team's) works
in the opposite direction. Because a lower EPA allowed indicates a better
defense, a negative `diff_def_epa` means the home team's defense has been
performing better than the away team's. This also pushes the prediction
toward a home win.

Interestingly, `diff_off_epa` has the largest raw coefficient, but when we
test feature usefulness by scrambling each feature and measuring how much
accuracy drops (permutation importance), `diff_def_epa` comes out slightly
ahead. This is a reminder that a larger coefficient does not automatically
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

## Early-season rolling features

Rolling features require five previous games.

For each team's first five games of a season, the rolling-5 features
are left as NaN because five prior games are not available.

For the initial model, games without a complete five-game history will
not be used when rolling-5 features are required.

This keeps the amount of historical information consistent and ensures
that the current game's performance is never used to predict itself.

## Tied games

Tied games are excluded from the V1 prediction model.

The current target is binary:
- 1 = home team wins
- 0 = away team wins

A tied game does not belong to either class, so ties are removed
for the initial model.

## Platform architecture (backend/frontend)

The platform backend (FastAPI + SQLAlchemy + SQLite) does not recompute anything
the ML pipeline already produced. `notebooks/03_backtest.py` remains the single
source of truth for training and evaluation; `backend/scripts/seed_db.py` loads its
CSV/joblib outputs into SQLite, and the API only reads from that database.

Weekly predictions are a DB-backed pipeline rather than a live per-request
computation: the plan is for `predict_week.py` to write into a `weekly_predictions`
table, with the API reading from it. Calling `nflreadpy` inside an API request would
make the endpoint slow and dependent on an external data source being up at request
time — fine for an offline script, not for a live demo.

The SQLite file itself is gitignored and rebuilt from CSVs via the seed script,
consistent with `data/processed/*.csv` already being treated as a build artifact
rather than a committed source of truth.

No deployment tooling (Docker, hosting configs, CI) is part of this repo's scope —
that work is owned by Sharat once the app runs locally.

## Weekly predictions and model insights (2026-10-07)

**Weekly predictions are stored, not computed per request.** `src/predict_week.py`
is a CLI that builds leak-free matchup features, scores them, and writes rows to
`weekly_predictions` (replacing any existing rows for that season/week, so it is
safe to re-run). Each row also stores the per-feature log-odds contributions
(standardized feature x coefficient), which the page uses to show the two biggest
drivers of each pick. `seed_db.py` no longer drops `weekly_predictions`, so
re-seeding after a retrain does not erase stored predictions.

**Tests guard the no-leakage rule.** The weekly feature builder is tested to ignore
the game itself and anything after it, and to reproduce the exact feature values in
`model_data.csv` that the model trained on, so training and prediction cannot drift.

**In-sample replays are labeled.** The final model is trained on every season in
`model_data.csv`, so predicting a past week with it is in-sample. The API returns
`in_sample` (season is in the bundle's `training_seasons`) and the page shows a
notice; honest accuracy lives on Model Performance and Prediction History, which are
walk-forward. The current-season (2026) games are predictable only once teams have
five prior games, so the first predictable 2026 week is 6.

**Current season is loaded in notebook 01.** `SEASONS` now runs through
`nfl.get_current_season()` so `team_game.csv` has this year's history. Unfinished and
early-season games have no score or no complete rolling features, so notebook 02
drops them and the training set and backtest are unchanged (verified: backtest
metrics identical before and after).

**Model insights are persisted by the training script.** `03_backtest.py` writes
`data/predictions/model_insights.csv` (coefficients plus permutation importance on
the final holdout season); the seed script loads it. The API never recomputes
permutation importance.

## Weekly prediction re-runs

Weekly predictions use overwrite behavior for the same season and week.

When `src/predict_week.py` is run again for an existing season/week,
the old rows for that season/week are deleted before the newly generated
predictions are inserted.

This prevents duplicate predictions from appearing in the platform while
still preserving predictions from other weeks and seasons.

`generated_at` records when the current set of weekly predictions was
produced.


## In-season readiness (2026-10-07)

**The weekly command refreshes its own data.** `predict_week.py` compares finished
games in the schedule with what `team_game.csv` holds and reruns notebook 01 only
when it is behind, so a stale or missing current season no longer breaks the run.

**Empty weeks explain themselves.** Each attempt is recorded in `prediction_runs`
(games scheduled, games predicted, plain-English reason) and served at
`/api/predictions/status`; the page shows it as a banner. The five-prior-game rule
means week 5 of 2026 (kickoff Oct 8) cannot be predicted, and week 6 only partly, so
silence would have looked like a bug.

**"In-sample" now means trained on it *and* predicted after kickoff.** Judging by
season alone would have mislabeled genuine 2026 forecasts as replays as soon as the
model was retrained on 2026 games. A forecast generated before the first kickoff of
its week stays a forecast.

**Pipeline-owned tables rebuild when their columns change.** `weekly_predictions` and
`prediction_runs` survive re-seeding, so an old database kept a stale schema and the
API returned 500. `ensure_derived_tables()` drops and recreates a table only when its
columns differ; both hold regenerable data.

**Open question (not changed):** an early-season window that reaches back into the
previous season would make weeks 1-5 predictable, but it changes the feature
definition, so the model and every backtest number would have to be rebuilt.

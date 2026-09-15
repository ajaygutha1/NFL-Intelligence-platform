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
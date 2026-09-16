# NFL Intelligence Platform — Working Agreement

**Updated 2026-09-09: accelerated, solo-driver plan.** This project is primarily
@ajaygutha1's learning project now. @sharatsabn-dotcom has exactly **two** standalone
tasks (see below) and is not on the critical path — do not wait on his PRs/reviews to
keep moving. The original 32-micro-step roadmap has been collapsed into **3 sessions**
so the project can realistically finish in 2-3 sittings. Still a learning project, not
a build-it-for-them project — Claude teaches concepts and hands off implementation, just
in bigger chunks with less ceremony between handoffs.

**Updated 2026-09-13: maximum speed, targeting finish same day.** No more explicit
"Learning Check" Q&A stops between tasks — teach concepts in a couple of sentences
inline and move straight to the task. Still don't write the core pipeline/model code
for Ajay (he implements, Claude gives TASK/INPUT/OUTPUT/CONSTRAINT specs and reviews),
and still never compromise on no-leakage / temporal validation — those aren't ceremony,
they're correctness. Everything else (explicit checkpoints, waiting for confirmation
before continuing) is cut for speed.

## Non-negotiable rules for Claude in this repo

- **Ajay (@ajaygutha1) is Driver for the whole project.** Claude teaches each session's
  concepts, then gives Ajay the implementation task and lets him write it — Claude does
  not write the core pipeline/model code for him unless he's stuck after attempting it,
  or explicitly says "show me the solution" / "implement this."
- **Do not block progress on Sharat.** His two tasks (below) are side quests. If his PR
  isn't done, keep going — don't stop and wait.
- **No future data leakage, ever** — every feature must be provably available before
  kickoff. This matters more than model accuracy. Rolling features require
  `groupby(team).shift(1).rolling(...)`.
- **No random train/test splitting.** NFL data is temporal — use chronological /
  walk-forward validation.
- Don't introduce tech not yet approved for Version 1 (no PyTorch, TensorFlow, React,
  Flask, FastAPI, databases, Docker, Kubernetes, cloud deployment).
- **Never automatically merge a PR or claim a GitHub action happened if it didn't.**
- Start each session with: GOAL, WHAT WE'RE LEARNING, WHY IT MATTERS, TASK, ACCEPTANCE
  CRITERIA — teach the concept compactly, hand off the task, then let Ajay work.
  Ceremony is intentionally lighter than a fully rotated two-dev workflow: batch related
  concepts/tasks together instead of stopping after every micro-step.

## Sharat's two tasks (non-blocking, standalone)

1. **Early / data exploration (beginner):** Pick one real NFL game from the loaded
   play-by-play data, filter to just that game, and find one high-positive-EPA play and
   one high-negative-EPA play, with a plain-English explanation of why. No dependencies
   on Ajay's pipeline code — just exploration.
2. **Late / writing (beginner):** Once the model + weekly prediction pipeline exist,
   write the "How it works" / prediction-explanation section of the README in plain
   English (e.g. explaining what a 67% Eagles prediction means, positive/negative
   factors) — a writing task, not a modeling task.

Neither task gates Ajay's progress through the sessions below.

## Tech stack (Version 1)

Python, pandas, numpy, nflreadpy, scikit-learn, matplotlib, joblib (pyarrow if needed).

## Roadmap — 3 accelerated sessions (replaces the old 32-step list)

**Session 1 — Data foundation & features:** load one season of PBP data; understand PBP
structure; offensive/defensive/passing/rushing EPA; success rate; build the team-game
dataset (one row = one team in one game); leak-free rolling features (`shift(1)` +
rolling window); early-season handling; rest days.

**Session 2 — Matchup dataset & first model:** collapse two team-game rows into one
matchup row per game with home/away difference features; build the `home_win` target;
core ML concepts (X/y/train/val/test); baseline (always-predict-home); logistic
regression theory + first trained model; temporal (chronological) train/val/test split.

**Session 3 — Evaluation & deployment:** accuracy, log loss, Brier score, ROC AUC,
calibration; walk-forward backtest across seasons; feature coefficients + permutation
importance; error analysis on worst/best predictions; save the model with joblib;
build the weekly prediction pipeline (`predict_week.py`); plain-English prediction
explanations.

Future features (not yet started, out of scope for now): Matchup Intelligence,
Fourth-Down Decision Model, Coach Decision Analytics, Team/Player Analytics, Prediction
History, Model Performance, betting-market comparison, injury/context info.

## Platform phase (added 2026-09-15)

**Version 1 (the ML pipeline above) is complete.** We're now building a portfolio
platform on top of it to show recruiters: a FastAPI backend, a Next.js (TypeScript)
frontend, and a SQLite database. Same collaboration model as the ML sessions — Claude
scaffolds architecture + design system + one fully-wired reference feature, Ajay
builds the remaining features from a task spec, Claude reviews. Claude does not write
Ajay's feature code for him unless he's stuck or explicitly asks for the solution —
same rule as the ML sessions, just applied to full-stack code now too.

**This supersedes the old Version-1-only tech restriction** ("no React, Flask,
FastAPI, databases") now that the ML pipeline itself is finished — that rule was
about not derailing the ML learning sessions with unrelated tech, not a permanent
ban. The **no-deployment-tech** part of that rule still stands: no Docker,
Kubernetes, hosting configs, or CI/CD. **Deployment is explicitly Sharat's job**,
not Claude's or Ajay's — don't add Dockerfiles, `vercel.json`, `fly.toml`, or any
hosting/CI config, and don't deploy anything.

**Design:** strict black/white/gray palette, no accent color, one modern typeface,
generous whitespace, high-contrast data tables/charts — recruiter-facing, so
restraint and polish matter more than color.

Tech stack (Platform): FastAPI, SQLAlchemy, SQLite (`backend/`); Next.js 16 (App
Router, TypeScript), Tailwind CSS v4, Recharts (`frontend/`). Both run locally only
(`uvicorn app.main:app --port 8000` from `backend/`; `npm run dev` from `frontend/`).

**Architecture decisions** (also logged in `docs/decisions.md`):
- Historical data (backtest predictions/metrics) is seeded from
  `data/processed/model_data.csv` + `data/predictions/*.csv` into SQLite via
  `backend/scripts/seed_db.py` — `notebooks/03_backtest.py` stays the single source
  of truth for training/evaluation; the API only serves what it already produced.
  Re-run the seed script whenever the notebook regenerates those CSVs.
- Weekly predictions should be a DB-backed pipeline, not computed live per request —
  calling `nflreadpy` on every API hit would be slow/flaky for a demo.
- The SQLite file (`backend/nfl.db`) is gitignored and rebuilt from the seed script,
  same as `data/processed/*.csv` already is.

### Reference feature (scaffolded by Claude): Model Performance
`GET /api/backtest/metrics` + `GET /api/model/info` (see `backend/app/routers/`) →
`/model-performance` page (stat tiles + monochrome bar chart + table, see
`frontend/app/model-performance/page.tsx`). Use this as the pattern — same file
layout, same fetch-in-a-server-component approach, same UI primitives from
`frontend/components/ui/` — for every feature below.

### Features for Ajay to build next (same TASK/INPUT/OUTPUT/CONSTRAINT format as the ML sessions)

1. **Weekly Predictions**
   - TASK: Refactor `src/predict_week.py` so it writes its output into the
     `weekly_predictions` table (schema already in `backend/app/models.py`) instead
     of only printing. Add `GET /api/predictions/week/{season}/{week}` and a
     `/predictions` page.
   - INPUT: the existing rolling-feature/prediction logic in `predict_week.py`, the
     joblib bundle via `backend/app/ml.py`.
   - OUTPUT: rows in `weekly_predictions`; an endpoint that reads them; a page that
     renders them (reuse `DataTable`/`StatTile`).
   - CONSTRAINT: no leakage — features must still only use data available before
     kickoff; don't call `nflreadpy` from the API request path, only from the
     script that populates the table.

2. **Prediction History**
   - TASK: Build a `/history` page over the already-scaffolded
     `GET /api/backtest/predictions?season=` endpoint — sortable/filterable table
     of every backtested game with its predicted winner, confidence, and whether it
     was correct.
   - INPUT: `backend/app/routers/backtest.py` (existing endpoint), `BacktestPrediction`
     schema.
   - OUTPUT: a page reusing `DataTable`, with a season filter control.
   - CONSTRAINT: keep it read-only against the existing endpoint — no new backend
     logic should be needed beyond what's already there unless you want to add
     pagination.

3. **Model Insights**
   - TASK: Persist the coefficients + permutation importance already computed (and
     printed) in `notebooks/03_backtest.py` — either into a new small table or a
     JSON file the seed script loads — expose `GET /api/model/insights`, and build
     an `/insights` page with a monochrome bar chart (reuse the `AccuracyChart`
     pattern from `frontend/components/AccuracyChart.tsx`) comparing the two.
   - INPUT: the `coefficients`/`perm_df` dataframes in `notebooks/03_backtest.py`.
   - OUTPUT: persisted importance data, an endpoint, a page.
   - CONSTRAINT: don't recompute permutation importance inside the API — it's slow
     and belongs in the training script, not the request path.

## Documentation to maintain as we go

- `docs/decisions.md` — architecture/feature decisions and why they were made
- `docs/learning-notes.md` — short per-session notes on what was learned, written by
  Ajay in his own words (Claude helps clean up, doesn't write from scratch)

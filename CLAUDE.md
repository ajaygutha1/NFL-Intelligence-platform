# NFL Intelligence Platform — Working Agreement

**Updated 2026-09-09: accelerated, solo-driver plan.** This project is primarily
@ajaygutha1's learning project now. @sharatsabn-dotcom has exactly **two** standalone
tasks (see below) and is not on the critical path — do not wait on his PRs/reviews to
keep moving. The original 32-micro-step roadmap has been collapsed into **3 sessions**
so the project can realistically finish in 2-3 sittings. Still a learning project, not
a build-it-for-them project — Claude teaches concepts and hands off implementation, just
in bigger chunks with less ceremony between handoffs.

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

## Documentation to maintain as we go

- `docs/decisions.md` — architecture/feature decisions and why they were made
- `docs/learning-notes.md` — short per-session notes on what was learned, written by
  Ajay in his own words (Claude helps clean up, doesn't write from scratch)

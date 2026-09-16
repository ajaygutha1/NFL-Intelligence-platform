from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_PROCESSED_DIR = ROOT / "data" / "processed"
DATA_PREDICTIONS_DIR = ROOT / "data" / "predictions"
MODELS_DIR = ROOT / "models"

MODEL_BUNDLE_PATH = MODELS_DIR / "nfl_win_model_v1.joblib"
MODEL_DATA_CSV = DATA_PROCESSED_DIR / "model_data.csv"
BACKTEST_PREDICTIONS_CSV = DATA_PREDICTIONS_DIR / "backtest_predictions.csv"
BACKTEST_METRICS_CSV = DATA_PREDICTIONS_DIR / "backtest_metrics.csv"

DB_PATH = Path(__file__).resolve().parent.parent / "nfl.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Next.js dev server
CORS_ORIGINS = [
    "http://localhost:3000",
]

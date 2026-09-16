import json

import joblib

from app.config import MODEL_BUNDLE_PATH

_bundle = joblib.load(MODEL_BUNDLE_PATH)


def get_model_info() -> dict:
    return {
        "model_version": _bundle.get("model_version", "unknown"),
        "training_date": _bundle.get("training_date", "unknown"),
        "feature_cols": list(_bundle["feature_cols"]),
        "training_seasons": [int(s) for s in _bundle["training_seasons"]],
    }


def get_model():
    return _bundle["model"]


def get_feature_cols() -> list[str]:
    return list(_bundle["feature_cols"])

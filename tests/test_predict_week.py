import json

import numpy as np
import pandas as pd
import pytest

import predict_week as pw
from predict_week import ROOT


def _synthetic_team_game(n_games=8):
    dates = pd.date_range("2025-09-07", periods=n_games, freq="7D")
    return pd.DataFrame(
        {
            "team": "AAA",
            "season": 2025,
            "game_date": dates,
            "off_epa": np.arange(n_games, dtype=float),
            "def_epa": np.arange(n_games, dtype=float) * 2,
            "pass_epa": np.arange(n_games, dtype=float) * 3,
            "rush_epa": np.arange(n_games, dtype=float) * 4,
            "success_rate": np.linspace(0.3, 0.6, n_games),
        }
    )


def test_features_need_five_prior_games():
    tg = _synthetic_team_game()
    # game on index 4 has only 4 prior games
    assert pw.get_team_features(tg, "AAA", 2025, tg.game_date[4]) is None
    assert pw.get_team_features(tg, "AAA", 2025, tg.game_date[5]) is not None


def test_features_never_see_the_game_itself_or_later():
    tg = _synthetic_team_game()
    target = tg.game_date[6]
    before = pw.get_team_features(tg, "AAA", 2025, target)

    # Corrupt the target game and everything after it: features must not change.
    corrupted = tg.copy()
    corrupted.loc[corrupted.game_date >= target, ["off_epa", "def_epa", "success_rate"]] = 999.0
    after = pw.get_team_features(corrupted, "AAA", 2025, target)

    assert before == after
    # Window is exactly the five games before the target (indices 1..5).
    assert before["roll5_off_epa"] == pytest.approx(np.mean([1, 2, 3, 4, 5]))
    assert before["rest_days"] == 7


@pytest.mark.skipif(
    not (ROOT / "data/processed/model_data.csv").exists(),
    reason="run notebooks 01-02 first",
)
def test_weekly_features_match_training_features():
    """The prediction pipeline must build the exact features the model trained on."""
    team_game = pw.load_team_game()
    model_data = pd.read_csv(ROOT / "data/processed/model_data.csv")
    model_data["game_date"] = pd.to_datetime(model_data["game_date"])
    cols = list(pw.load_bundle()["feature_cols"])

    sample = model_data[model_data.season == 2024].head(40)
    games = sample.assign(game_date=sample["game_date"])[
        ["game_id", "game_date", "home_team", "away_team"]
    ]
    rebuilt = pw.build_matchup_features(team_game, games, 2024).set_index("game_id")
    expected = sample.set_index("game_id")

    assert len(rebuilt) == len(sample)
    np.testing.assert_allclose(
        rebuilt.loc[expected.index, cols].to_numpy(),
        expected[cols].to_numpy(),
        atol=1e-9,
    )


@pytest.mark.skipif(
    not (ROOT / "models/nfl_win_model_v1.joblib").exists(), reason="train the model first"
)
def test_scoring_probabilities_and_drivers():
    bundle = pw.load_bundle()
    cols = list(bundle["feature_cols"])
    matchups = pd.DataFrame(
        [
            {"game_id": "g1", "game_date": "2025-10-05", "home_team": "HHH", "away_team": "AAA",
             **{c: 0.5 for c in cols}},
            {"game_id": "g2", "game_date": "2025-10-05", "home_team": "BBB", "away_team": "CCC",
             **{c: -0.5 for c in cols}},
        ]
    )
    scored = pw.score_matchups(bundle, matchups)

    assert scored.home_prob.between(0, 1).all()
    np.testing.assert_allclose(scored.home_prob + scored.away_prob, 1.0)

    # Drivers + intercept reproduce the model's own log-odds exactly.
    intercept = bundle["model"].named_steps["logistic_regression"].intercept_[0]
    for _, row in scored.iterrows():
        logit = intercept + sum(d["contribution"] for d in json.loads(row.drivers))
        assert 1 / (1 + np.exp(-logit)) == pytest.approx(row.home_prob)

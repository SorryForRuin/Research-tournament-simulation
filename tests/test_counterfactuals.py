"""Small tests for counterfactual payoff helpers."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from tournament_sim.analysis import add_derived_variables  # noqa: E402
from tournament_sim.counterfactuals import (  # noqa: E402
    add_counterfactual_columns,
    counterfactual_payoffs_for_record,
)


def test_counterfactual_payoffs_for_record_has_expected_columns():
    record = {
        "initial_quality": 90,
        "opponent_final_quality": 95,
        "V": 100,
        "c": 20,
        "h": 0,
    }
    payoffs = counterfactual_payoffs_for_record(record)
    assert payoffs["cf_payoff_if_reveal"] == 0
    assert payoffs["cf_payoff_if_hide_stop"] == 0
    assert payoffs["cf_payoff_if_hide_improve"] == 30
    assert payoffs["cf_reveal_gain_vs_best_hide"] == -30


def test_add_counterfactual_columns_infers_opponent_final_quality():
    df = pd.DataFrame(
        [
            {
                "match_id": 1,
                "subject_id": 1,
                "initial_quality": 90,
                "final_quality": 90,
                "V": 100,
                "c": 20,
                "h": 0,
                "reveal_decision": True,
                "opponent_reveal_decision": False,
                "opponent_revealed_quality_if_observed": None,
                "improve_decision_if_applicable": None,
                "won": False,
            },
            {
                "match_id": 1,
                "subject_id": 2,
                "initial_quality": 95,
                "final_quality": 95,
                "V": 100,
                "c": 20,
                "h": 0,
                "reveal_decision": False,
                "opponent_reveal_decision": True,
                "opponent_revealed_quality_if_observed": 90,
                "improve_decision_if_applicable": False,
                "won": True,
            },
        ]
    )
    df["q_norm"] = df["initial_quality"] / 100
    df["k"] = 0.2
    prepared = add_derived_variables(df)
    cf_df = add_counterfactual_columns(prepared)
    assert "opponent_final_quality" in cf_df.columns
    assert "cf_reveal_gain_vs_best_hide" in cf_df.columns


if __name__ == "__main__":
    test_counterfactual_payoffs_for_record_has_expected_columns()
    test_add_counterfactual_columns_infers_opponent_final_quality()
    print("All counterfactual tests passed.")

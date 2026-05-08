"""Small tests for summary statistics.

Run with:
    python tests/test_summary.py
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.summary import (  # noqa: E402
    deterrence_rate,
    estimate_empirical_reveal_cutoff,
    improvement_rate_by_revealed_opponent_quality,
    quality_bin_label,
    reveal_rate_by_quality_bin,
    summarize_by_treatment_and_type,
    treatment_comparison_summary,
)


def _record(q, reveal, improve, payoff=0, won=False, opponent_reveal=False, opponent_q=None):
    return {
        "subject_id": 1,
        "round": 1,
        "treatment_id": "baseline_low_cost",
        "V": 100,
        "c": 20,
        "h": 0,
        "k": 0.2,
        "player_type": "TestAgent",
        "opponent_id": 2,
        "initial_quality": q,
        "q_norm": q / 100,
        "reveal_decision": reveal,
        "opponent_reveal_decision": opponent_reveal,
        "opponent_revealed_quality_if_observed": opponent_q,
        "improve_decision_if_applicable": improve,
        "final_quality": q,
        "won": won,
        "payoff": payoff,
        "paid_improvement_cost": bool(improve),
        "eligible_for_hype": False,
        "hype_paid": False,
    }


def test_quality_bin_label():
    assert quality_bin_label(0, 10) == "0-9"
    assert quality_bin_label(86, 10) == "80-89"
    assert quality_bin_label(100, 10) == "100-100"


def test_basic_summary_rates():
    records = [
        _record(80, True, None, payoff=100, won=True),
        _record(40, False, True, payoff=-20, won=False),
        _record(30, False, False, payoff=0, won=False),
    ]

    rows = summarize_by_treatment_and_type(records)
    row = rows[0]

    assert row["n_player_records"] == 3
    assert row["reveal_rate"] == 1 / 3
    assert row["improvement_rate"] == 1 / 2
    assert row["average_payoff"] == 80 / 3
    assert row["win_rate"] == 1 / 3


def test_reveal_rate_by_quality_bin_and_empirical_cutoff():
    records = [
        _record(10, False, False),
        _record(20, False, False),
        _record(80, True, None),
        _record(81, True, None),
    ]

    rows = reveal_rate_by_quality_bin(records, bin_size=10)

    assert rows[0]["quality_bin"] == "10-19"
    assert estimate_empirical_reveal_cutoff(records, bin_size=10) == 84.5


def test_improvement_rate_after_revealed_opponent_quality():
    records = [
        _record(40, False, True, opponent_reveal=True, opponent_q=80),
        _record(40, False, False, opponent_reveal=True, opponent_q=85),
        _record(40, True, None, opponent_reveal=True, opponent_q=85),
    ]

    rows = improvement_rate_by_revealed_opponent_quality(records, bin_size=10)

    assert len(rows) == 1
    assert rows[0]["opponent_quality_bin"] == "80-89"
    assert rows[0]["improvement_rate"] == 0.5


def test_deterrence_rate():
    records = [
        _record(40, False, False, opponent_reveal=True, opponent_q=90),
        _record(40, False, True, opponent_reveal=True, opponent_q=90),
        _record(40, False, True, opponent_reveal=True, opponent_q=70),
    ]

    assert deterrence_rate(records, high_reveal_threshold=80) == 0.5


def test_summary_with_simulated_experiment():
    result = simulate_experiment(
        num_subjects=40,
        num_rounds=3,
        population_composition={"EquilibriumAgent": 1.0},
        rng_seed=123,
    )

    treatment_rows = treatment_comparison_summary(result.player_records)
    type_rows = summarize_by_treatment_and_type(result.player_records)

    assert len(treatment_rows) == 4
    assert len(type_rows) == 4


if __name__ == "__main__":
    test_quality_bin_label()
    test_basic_summary_rates()
    test_reveal_rate_by_quality_bin_and_empirical_cutoff()
    test_improvement_rate_after_revealed_opponent_quality()
    test_deterrence_rate()
    test_summary_with_simulated_experiment()
    print("All summary tests passed.")

"""Small tests for experiment-level simulation.

Run with:
    python tests/test_experiment.py
"""

from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import (  # noqa: E402
    create_subjects,
    simulate_experiment,
)
from tournament_sim.treatment import default_treatments  # noqa: E402


def test_create_subjects_assigns_treatments_evenly():
    subjects = create_subjects(
        num_subjects=8,
        treatments=default_treatments(),
        population_composition={"EquilibriumAgent": 1.0},
        rng=random.Random(1),
    )

    counts = {}
    for subject in subjects:
        counts[subject.treatment_id] = counts.get(subject.treatment_id, 0) + 1

    assert counts["baseline_low_cost"] == 2
    assert counts["baseline_high_cost"] == 2
    assert counts["hype_low_cost"] == 2
    assert counts["hype_high_cost"] == 2


def test_create_subjects_uses_population_composition():
    subjects = create_subjects(
        num_subjects=8,
        treatments=default_treatments(),
        population_composition={
            "EquilibriumAgent": 0.5,
            "AlwaysRevealAgent": 0.5,
        },
        rng=random.Random(1),
    )

    counts = {}
    for subject in subjects:
        counts[subject.player_type] = counts.get(subject.player_type, 0) + 1

    assert counts["EquilibriumAgent"] == 4
    assert counts["AlwaysRevealAgent"] == 4


def test_simulate_experiment_record_counts():
    result = simulate_experiment(
        num_subjects=8,
        num_rounds=3,
        population_composition={"EquilibriumAgent": 1.0},
        rng_seed=1,
    )

    # Eight subjects split into four treatments means two subjects per treatment.
    # Each treatment has one match per round, so 4 treatments * 3 rounds = 12.
    assert len(result.match_records) == 12
    assert len(result.player_records) == 24
    assert len(result.subjects) == 8


def test_simulation_is_reproducible_with_seed():
    result_1 = simulate_experiment(
        num_subjects=8,
        num_rounds=2,
        population_composition={"EquilibriumAgent": 1.0},
        rng_seed=123,
    )
    result_2 = simulate_experiment(
        num_subjects=8,
        num_rounds=2,
        population_composition={"EquilibriumAgent": 1.0},
        rng_seed=123,
    )

    assert result_1.player_records == result_2.player_records
    assert result_1.match_records == result_2.match_records


if __name__ == "__main__":
    test_create_subjects_assigns_treatments_evenly()
    test_create_subjects_uses_population_composition()
    test_simulate_experiment_record_counts()
    test_simulation_is_reproducible_with_seed()
    print("All experiment tests passed.")

"""Small tests for regression-analysis helpers.

Run with:
    python tests/test_analysis.py
"""

from pathlib import Path
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.analysis import add_derived_variables, run_all_tests  # noqa: E402
from tournament_sim.experiment import simulate_experiment  # noqa: E402


def test_add_derived_variables_creates_deterrence_sample_fields():
    result = simulate_experiment(
        num_subjects=40,
        num_rounds=3,
        population_composition={"EquilibriumAgent": 1.0},
        rng_seed=123,
    )

    df = add_derived_variables(_records_to_dataframe(result.player_records))

    assert "eligible_to_improve" in df.columns
    assert "opponent_revealed_quality_norm" in df.columns
    assert "predicted_reveal" in df.columns
    assert "distance_to_reveal_cutoff" in df.columns


def test_run_all_tests_writes_outputs():
    result = simulate_experiment(
        num_subjects=40,
        num_rounds=4,
        population_composition={
            "EquilibriumAgent": 0.5,
            "OverRevealerAgent": 0.5,
        },
        rng_seed=456,
    )

    df = add_derived_variables(_records_to_dataframe(result.player_records))
    output_dir = PROJECT_ROOT / "outputs" / "test_analysis"
    results = run_all_tests(df, output_dir)

    assert results["deterrence"]["sample_n"] > 0
    assert (output_dir / "descriptive_tables" / "treatment_summary.csv").exists()
    assert (output_dir / "plots" / "reveal_rate_by_quality_bin.png").exists()
    assert (output_dir / "coefficient_tables" / "quality_dependent_reveal__lpm_simple.csv").exists()

    shutil.rmtree(output_dir)


def _records_to_dataframe(records):
    import pandas as pd

    return pd.DataFrame(records)


if __name__ == "__main__":
    test_add_derived_variables_creates_deterrence_sample_fields()
    test_run_all_tests_writes_outputs()
    print("All analysis tests passed.")

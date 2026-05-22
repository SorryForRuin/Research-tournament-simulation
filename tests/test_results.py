"""Small tests for the paper-results extraction pipeline."""

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.results import compile_results_for_paper  # noqa: E402


def test_compile_results_for_paper_writes_core_outputs():
    base_dir = PROJECT_ROOT / "outputs" / "test_results_project"
    data_dir = base_dir / "outputs" / "full_simulation" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    result = simulate_experiment(
        num_subjects=80,
        num_rounds=8,
        population_composition={
            "EquilibriumAgent": 0.40,
            "NoisyEquilibriumAgent": 0.20,
            "UnderRevealerAgent": 0.15,
            "OverRevealerAgent": 0.15,
            "MyopicHeuristicAgent": 0.10,
        },
        rng_seed=777,
    )
    pd.DataFrame(result.player_records).to_csv(data_dir / "player_round_records.csv", index=False)
    pd.DataFrame(result.match_records).to_csv(data_dir / "match_round_records.csv", index=False)

    output_dir = base_dir / "outputs" / "results_for_paper"
    compiled = compile_results_for_paper(base_dir, output_dir=output_dir)

    assert compiled is not None
    expected_files = [
        "paper_results_summary.md",
        "main_descriptive_table.csv",
        "main_regression_table.csv",
        "deterrence_results_table.csv",
        "equilibrium_compliance_table.csv",
        "equilibrium_compliance_by_type_table.csv",
        "agent_type_results_table.csv",
        "counterfactual_results_table.csv",
        "hype_responsive_comparison_table.csv",
        "hype_responsive_contrasts.csv",
        "robustness_summary_table.csv",
    ]
    for filename in expected_files:
        assert (output_dir / filename).exists()

    main_regression = pd.read_csv(output_dir / "main_regression_table.csv")
    assert set(["test_name", "coefficient_name", "coefficient", "p_value"]).issubset(
        main_regression.columns
    )
    assert len(main_regression) == 6

    figure_files = [
        "reveal_by_quality_bin.csv",
        "improvement_by_opponent_revealed_quality.csv",
        "theoretical_vs_empirical_cutoff.csv",
        "counterfactual_gain_by_quality_bin.csv",
        "reveal_rate_by_treatment.csv",
    ]
    for filename in figure_files:
        assert (output_dir / "figure_data" / filename).exists()


if __name__ == "__main__":
    test_compile_results_for_paper_writes_core_outputs()
    print("All results extraction tests passed.")

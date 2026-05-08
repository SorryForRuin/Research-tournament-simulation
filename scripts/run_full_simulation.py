"""Run the full 200-subject simulation and export CSV tables and plots."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.export import export_experiment_outputs  # noqa: E402
from tournament_sim.plots import generate_all_plots  # noqa: E402
from tournament_sim.summary import (  # noqa: E402
    cutoff_comparison_summary,
    treatment_comparison_summary,
)


POPULATION_COMPOSITION = {
    "EquilibriumAgent": 0.40,
    "NoisyEquilibriumAgent": 0.20,
    "UnderRevealerAgent": 0.15,
    "OverRevealerAgent": 0.15,
    "MyopicHeuristicAgent": 0.10,
}


def main():
    experiment = simulate_experiment(
        num_subjects=200,
        num_rounds=100,
        population_composition=POPULATION_COMPOSITION,
        rng_seed=12345,
    )

    output_dir = PROJECT_ROOT / "outputs" / "full_simulation"
    csv_paths = export_experiment_outputs(experiment, output_dir)
    plot_paths = generate_all_plots(experiment.player_records, output_dir / "plots")

    print("Full simulation complete.")
    print("subjects=", len(experiment.subjects))
    print("matches=", len(experiment.match_records))
    print("player_records=", len(experiment.player_records))

    print()
    print("Treatment summary:")
    for row in treatment_comparison_summary(experiment.player_records):
        print(
            row["treatment_id"],
            "reveal_rate=",
            round(row["reveal_rate"], 3),
            "improvement_rate=",
            round(row["improvement_rate"], 3),
            "avg_payoff=",
            round(row["average_payoff"], 2),
        )

    print()
    print("Model vs simulated cutoff comparison:")
    for row in cutoff_comparison_summary(experiment.player_records):
        empirical = row["simulated_empirical_cutoff"]
        difference = row["cutoff_difference_empirical_minus_model"]
        if empirical is None:
            empirical_text = "None"
            difference_text = "None"
        else:
            empirical_text = str(round(empirical, 2))
            difference_text = str(round(difference, 2))

        print(
            row["treatment_id"],
            row["player_type"],
            "model=",
            round(row["model_reveal_cutoff"], 2),
            "simulated=",
            empirical_text,
            "difference=",
            difference_text,
        )

    print()
    print("CSV files:")
    for path in csv_paths:
        print(path)

    print()
    print("Plot files:")
    for path in plot_paths:
        print(path)


if __name__ == "__main__":
    main()

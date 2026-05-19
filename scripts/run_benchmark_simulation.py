"""Run a 100% EquilibriumAgent benchmark simulation."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.export import export_experiment_outputs  # noqa: E402
from tournament_sim.plots import generate_all_plots  # noqa: E402


def main():
    result = simulate_experiment(
        num_subjects=200,
        num_rounds=100,
        population_composition={"EquilibriumAgent": 1.0},
        rng_seed=12345,
    )
    output_dir = PROJECT_ROOT / "outputs" / "robustness" / "benchmark_equilibrium"
    export_experiment_outputs(result, output_dir)
    generate_all_plots(result.player_records, output_dir / "plots")
    print("Benchmark simulation complete.")
    print("outputs=", output_dir)


if __name__ == "__main__":
    main()

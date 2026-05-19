"""Run a full simulation with hype-responsive benchmark agents."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.export import export_experiment_outputs  # noqa: E402
from tournament_sim.plots import generate_all_plots  # noqa: E402


POPULATION_COMPOSITION = {
    "HypeResponsiveEquilibriumAgent": 0.60,
    "HypeResponsiveNoisyEquilibriumAgent": 0.20,
    "EquilibriumAgent": 0.20,
}


def main():
    result = simulate_experiment(
        num_subjects=200,
        num_rounds=100,
        population_composition=POPULATION_COMPOSITION,
        rng_seed=12345,
    )
    output_dir = PROJECT_ROOT / "outputs" / "hype_responsive_simulation"
    export_experiment_outputs(result, output_dir)
    generate_all_plots(result.player_records, output_dir / "plots")
    print("Hype-responsive simulation complete.")
    print("outputs=", output_dir)


if __name__ == "__main__":
    main()

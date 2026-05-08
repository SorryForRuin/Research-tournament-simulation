"""Generate plots from a small development simulation."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.plots import generate_all_plots  # noqa: E402


def main():
    experiment = simulate_experiment(
        num_subjects=40,
        num_rounds=5,
        population_composition={
            "EquilibriumAgent": 0.4,
            "UnderRevealerAgent": 0.2,
            "OverRevealerAgent": 0.2,
            "MyopicHeuristicAgent": 0.2,
        },
        rng_seed=123,
    )

    output_dir = PROJECT_ROOT / "outputs" / "plots" / "small_example"
    paths = generate_all_plots(experiment.player_records, output_dir)

    print("Generated plots:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()

"""Run population-composition robustness checks."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.robustness import run_population_robustness  # noqa: E402


SCENARIOS = {
    "benchmark_equilibrium": {"EquilibriumAgent": 1.0},
    "mixed_baseline": {
        "EquilibriumAgent": 0.40,
        "NoisyEquilibriumAgent": 0.20,
        "UnderRevealerAgent": 0.15,
        "OverRevealerAgent": 0.15,
        "MyopicHeuristicAgent": 0.10,
    },
    "hype_responsive": {
        "HypeResponsiveEquilibriumAgent": 0.50,
        "HypeResponsiveNoisyEquilibriumAgent": 0.25,
        "EquilibriumAgent": 0.25,
    },
}


def main():
    output_dir = PROJECT_ROOT / "outputs" / "robustness" / "population_robustness"
    result = run_population_robustness(SCENARIOS, output_dir=output_dir)
    print("Population robustness complete.")
    for path in result["paths"]:
        print(path)


if __name__ == "__main__":
    main()

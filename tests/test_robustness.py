"""Small tests for robustness runners."""

from pathlib import Path
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.robustness import run_population_robustness, run_seed_robustness  # noqa: E402


def test_seed_robustness_small_run_writes_outputs():
    output_dir = PROJECT_ROOT / "outputs" / "test_seed_robustness"
    result = run_seed_robustness(
        seeds=[1, 2],
        output_dir=output_dir,
        num_subjects=40,
        num_rounds=3,
        population_composition={"EquilibriumAgent": 1.0},
    )
    assert len(result["paths"]) == 2
    for path in result["paths"]:
        assert path.exists()
    shutil.rmtree(output_dir)


def test_population_robustness_small_run_writes_outputs():
    output_dir = PROJECT_ROOT / "outputs" / "test_population_robustness"
    result = run_population_robustness(
        {
            "equilibrium": {"EquilibriumAgent": 1.0},
            "hype_responsive": {"HypeResponsiveEquilibriumAgent": 1.0},
        },
        output_dir=output_dir,
        num_subjects=40,
        num_rounds=3,
    )
    assert len(result["paths"]) == 2
    for path in result["paths"]:
        assert path.exists()
    shutil.rmtree(output_dir)


if __name__ == "__main__":
    test_seed_robustness_small_run_writes_outputs()
    test_population_robustness_small_run_writes_outputs()
    print("All robustness tests passed.")

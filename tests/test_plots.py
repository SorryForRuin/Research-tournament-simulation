"""Small tests for plot generation.

Run with:
    python tests/test_plots.py
"""

from pathlib import Path
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.plots import generate_all_plots  # noqa: E402


def test_generate_all_plots_creates_png_files():
    result = simulate_experiment(
        num_subjects=40,
        num_rounds=3,
        population_composition={
            "EquilibriumAgent": 0.4,
            "UnderRevealerAgent": 0.2,
            "OverRevealerAgent": 0.2,
            "MyopicHeuristicAgent": 0.2,
        },
        rng_seed=321,
    )

    output_dir = PROJECT_ROOT / "outputs" / "test_plots"
    paths = generate_all_plots(result.player_records, output_dir)

    assert len(paths) == 5
    for path in paths:
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 0

    shutil.rmtree(output_dir)


if __name__ == "__main__":
    test_generate_all_plots_creates_png_files()
    print("All plot tests passed.")

"""Small tests for CSV export helpers.

Run with:
    python tests/test_export.py
"""

from pathlib import Path
import csv
import shutil
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.experiment import simulate_experiment  # noqa: E402
from tournament_sim.export import export_experiment_outputs  # noqa: E402


def test_export_experiment_outputs_writes_csv_files():
    result = simulate_experiment(
        num_subjects=40,
        num_rounds=3,
        population_composition={"EquilibriumAgent": 1.0},
        rng_seed=123,
    )

    output_dir = PROJECT_ROOT / "outputs" / "test_exports"
    paths = export_experiment_outputs(result, output_dir)

    assert len(paths) == 7
    for path in paths:
        assert path.exists()
        assert path.suffix == ".csv"
        assert path.stat().st_size > 0

    with paths[0].open("r", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == len(result.player_records)
    assert "subject_id" in rows[0]
    assert "reveal_decision" in rows[0]

    shutil.rmtree(output_dir)


if __name__ == "__main__":
    test_export_experiment_outputs_writes_csv_files()
    print("All export tests passed.")

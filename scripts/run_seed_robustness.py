"""Run seed robustness checks for the main simulation design."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.robustness import run_seed_robustness  # noqa: E402


def main():
    output_dir = PROJECT_ROOT / "outputs" / "robustness" / "seed_robustness"
    result = run_seed_robustness(
        seeds=[101, 202, 303, 404, 505],
        output_dir=output_dir,
    )
    print("Seed robustness complete.")
    for path in result["paths"]:
        print(path)


if __name__ == "__main__":
    main()

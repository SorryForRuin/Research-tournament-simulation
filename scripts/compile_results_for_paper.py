"""Compile compact tables and notes for writing the paper results section."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.results import compile_results_for_paper  # noqa: E402


def main():
    compile_results_for_paper(PROJECT_ROOT)


if __name__ == "__main__":
    main()

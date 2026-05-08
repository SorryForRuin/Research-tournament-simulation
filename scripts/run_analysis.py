"""Run all regression and descriptive tests on the full simulated data."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.analysis import load_and_prepare_data, run_all_tests  # noqa: E402


def main():
    data_path = PROJECT_ROOT / "outputs" / "full_simulation" / "data" / "player_round_records.csv"
    output_dir = PROJECT_ROOT / "outputs" / "analysis"

    df = load_and_prepare_data(data_path)
    results = run_all_tests(df, output_dir)

    print("Analysis complete.")
    print("observations=", len(df))
    print("deterrence_sample_n=", results["deterrence"]["sample_n"])
    print("outputs=", output_dir)


if __name__ == "__main__":
    main()

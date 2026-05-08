"""CSV export helpers for simulation records and summaries."""

import csv
from pathlib import Path

from tournament_sim.summary import (
    cutoff_comparison_summary,
    improvement_rate_by_revealed_opponent_quality,
    reveal_rate_by_quality_bin,
    summarize_by_treatment_and_type,
    treatment_comparison_summary,
)


def export_rows_csv(rows, path):
    """Write a list of dictionaries to a CSV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = _collect_fieldnames(rows)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return path


def export_experiment_outputs(experiment_result, output_dir):
    """Export raw records and summary tables for an experiment result."""
    output_dir = Path(output_dir)
    data_dir = output_dir / "data"
    summary_dir = output_dir / "summary_tables"

    paths = []
    player_records = experiment_result.player_records
    match_records = experiment_result.match_records

    paths.append(export_rows_csv(player_records, data_dir / "player_round_records.csv"))
    paths.append(export_rows_csv(match_records, data_dir / "match_round_records.csv"))
    paths.append(
        export_rows_csv(
            treatment_comparison_summary(player_records),
            summary_dir / "treatment_summary.csv",
        )
    )
    paths.append(
        export_rows_csv(
            summarize_by_treatment_and_type(player_records),
            summary_dir / "treatment_by_player_type_summary.csv",
        )
    )
    paths.append(
        export_rows_csv(
            cutoff_comparison_summary(player_records),
            summary_dir / "cutoff_comparison_by_player_type.csv",
        )
    )
    paths.append(
        export_rows_csv(
            reveal_rate_by_quality_bin(player_records),
            summary_dir / "reveal_rate_by_quality_bin.csv",
        )
    )
    paths.append(
        export_rows_csv(
            improvement_rate_by_revealed_opponent_quality(player_records),
            summary_dir / "improvement_by_revealed_quality.csv",
        )
    )

    return paths


def _collect_fieldnames(rows):
    fieldnames = []

    for row in rows:
        for fieldname in row.keys():
            if fieldname not in fieldnames:
                fieldnames.append(fieldname)

    return fieldnames

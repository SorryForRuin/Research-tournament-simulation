"""Plot generation for tournament simulation outputs."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from tournament_sim.probabilities import theoretical_reveal_cutoff
from tournament_sim.summary import (
    improvement_rate_by_revealed_opponent_quality,
    reveal_rate_by_quality_bin,
    summarize_by_treatment_and_type,
)


PLOT_COLORS = {
    "blue": "#356AA0",
    "green": "#4F8A5B",
    "red": "#B54A4A",
    "gold": "#C9973A",
    "gray": "#666666",
}


def generate_all_plots(player_records, output_dir):
    """Generate the main requested plots and return their file paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    paths.append(plot_reveal_probability_by_quality_bin(player_records, output_dir))
    paths.append(plot_improvement_after_revealed_quality(player_records, output_dir))
    paths.append(plot_reveal_region(output_dir))
    paths.append(plot_payoff_distribution(player_records, output_dir))
    paths.append(plot_theoretical_vs_empirical_cutoff(player_records, output_dir))

    return paths


def plot_reveal_probability_by_quality_bin(player_records, output_dir, bin_size=10):
    """Plot reveal probability by initial quality bin for each treatment."""
    rows = reveal_rate_by_quality_bin(player_records, bin_size=bin_size)
    treatments = _unique(row["treatment_id"] for row in rows)

    fig, ax = plt.subplots(figsize=(10, 6))

    for treatment in treatments:
        treatment_rows = [row for row in rows if row["treatment_id"] == treatment]
        treatment_rows = _sort_by_bin_midpoint(treatment_rows, "quality_bin")
        x_values = [_bin_midpoint(row["quality_bin"]) for row in treatment_rows]
        y_values = [row["reveal_rate"] for row in treatment_rows]
        ax.plot(x_values, y_values, marker="o", linewidth=2, label=treatment)

    ax.set_title("Reveal Probability by Initial Quality")
    ax.set_xlabel("Initial quality bin midpoint")
    ax.set_ylabel("Reveal probability")
    ax.set_ylim(-0.03, 1.03)
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)

    return _save(fig, output_dir, "reveal_probability_by_quality_bin.png")


def plot_improvement_after_revealed_quality(player_records, output_dir, bin_size=10):
    """Plot improvement probability after observing a revealed opponent."""
    rows = improvement_rate_by_revealed_opponent_quality(player_records, bin_size=bin_size)
    treatments = _unique(row["treatment_id"] for row in rows)

    fig, ax = plt.subplots(figsize=(10, 6))

    for treatment in treatments:
        treatment_rows = [row for row in rows if row["treatment_id"] == treatment]
        treatment_rows = _sort_by_bin_midpoint(treatment_rows, "opponent_quality_bin")
        x_values = [_bin_midpoint(row["opponent_quality_bin"]) for row in treatment_rows]
        y_values = [row["improvement_rate"] for row in treatment_rows]
        ax.plot(x_values, y_values, marker="o", linewidth=2, label=treatment)

    ax.set_title("Improvement After Observing Revealed Opponent Quality")
    ax.set_xlabel("Opponent revealed quality bin midpoint")
    ax.set_ylabel("Improvement probability")
    ax.set_ylim(-0.03, 1.03)
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)

    return _save(fig, output_dir, "improvement_after_revealed_quality.png")


def plot_reveal_region(output_dir):
    """Plot theoretical reveal/hide regions over k and normalized quality."""
    k_values = [index / 100 for index in range(1, 34)]
    cutoffs = [theoretical_reveal_cutoff(k) for k in k_values]

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.fill_between(k_values, 0, cutoffs, color=PLOT_COLORS["red"], alpha=0.25, label="Hide")
    ax.fill_between(k_values, cutoffs, 1, color=PLOT_COLORS["green"], alpha=0.30, label="Reveal")
    ax.plot(k_values, cutoffs, color=PLOT_COLORS["gray"], linewidth=2.5, label="r* cutoff")

    ax.set_title("Theoretical Reveal Region")
    ax.set_xlabel("Cost ratio k = c / V")
    ax.set_ylabel("Normalized quality q")
    ax.set_xlim(0.01, 0.33)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)

    return _save(fig, output_dir, "theoretical_reveal_region.png")


def plot_payoff_distribution(player_records, output_dir):
    """Plot payoff distributions by treatment."""
    treatments = _unique(record["treatment_id"] for record in player_records)
    data = []

    for treatment in treatments:
        data.append([record["payoff"] for record in player_records if record["treatment_id"] == treatment])

    fig, ax = plt.subplots(figsize=(10, 6))
    box = ax.boxplot(data, labels=treatments, patch_artist=True)

    for patch in box["boxes"]:
        patch.set_facecolor("#DCE7F2")
        patch.set_edgecolor(PLOT_COLORS["blue"])

    ax.set_title("Payoff Distribution by Treatment")
    ax.set_xlabel("Treatment")
    ax.set_ylabel("Payoff")
    ax.grid(True, axis="y", alpha=0.25)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")

    return _save(fig, output_dir, "payoff_distribution_by_treatment.png")


def plot_theoretical_vs_empirical_cutoff(player_records, output_dir):
    """Compare theoretical and empirical reveal cutoffs."""
    rows = summarize_by_treatment_and_type(player_records)
    rows = [row for row in rows if row["empirical_reveal_cutoff"] is not None]

    labels = [row["treatment_id"] + "\n" + row["player_type"] for row in rows]
    theoretical = [100 * row["theoretical_reveal_cutoff"] for row in rows]
    empirical = [row["empirical_reveal_cutoff"] for row in rows]
    x_values = list(range(len(rows)))
    width = 0.38

    fig, ax = plt.subplots(figsize=(max(10, len(rows) * 0.8), 6))
    left = [x - width / 2 for x in x_values]
    right = [x + width / 2 for x in x_values]

    ax.bar(left, theoretical, width=width, color=PLOT_COLORS["gray"], label="Theoretical")
    ax.bar(right, empirical, width=width, color=PLOT_COLORS["gold"], label="Empirical")

    ax.set_title("Theoretical vs Empirical Reveal Cutoff")
    ax.set_xlabel("Treatment and player type")
    ax.set_ylabel("Quality cutoff on 0-100 grid")
    ax.set_ylim(0, 105)
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(frameon=False)

    return _save(fig, output_dir, "theoretical_vs_empirical_cutoff.png")


def _save(fig, output_dir, filename):
    path = Path(output_dir) / filename
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _unique(values):
    seen = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def _sort_by_bin_midpoint(rows, field_name):
    return sorted(rows, key=lambda row: _bin_midpoint(row[field_name]))


def _bin_midpoint(label):
    low_text, high_text = label.split("-")
    return (int(low_text) + int(high_text)) / 2

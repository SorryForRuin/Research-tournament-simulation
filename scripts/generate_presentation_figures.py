"""Generate slide-ready figures for the main simulation tests."""

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.analysis import add_derived_variables  # noqa: E402


RESULTS_DIR = PROJECT_ROOT / "outputs" / "results_for_paper"
FIGURE_DATA_DIR = RESULTS_DIR / "figure_data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "presentation_figures"
PLAYER_DATA = PROJECT_ROOT / "outputs" / "full_simulation" / "data" / "player_round_records.csv"


COLORS = {
    "baseline_low_cost": "#2E6F95",
    "baseline_high_cost": "#D1495B",
    "hype_low_cost": "#4D9078",
    "hype_high_cost": "#F2A541",
    "main_mixed_population": "#2E6F95",
    "hype_responsive_extension": "#4D9078",
}


def main():
    if not RESULTS_DIR.exists():
        print("Missing paper-results outputs.")
        print("Please run: python scripts/compile_results_for_paper.py")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = [
        plot_quality_dependent_disclosure(),
        plot_cost_effect(),
        plot_hype_effect_comparison(),
        plot_deterrence(),
        plot_equilibrium_cutoffs(),
        plot_under_over_reveal(),
        plot_payoff_by_quality_and_reveal(),
        plot_main_regression_summary(),
    ]

    print("Presentation figures written to:", OUTPUT_DIR)
    for path in paths:
        print(path)


def plot_quality_dependent_disclosure():
    df = pd.read_csv(FIGURE_DATA_DIR / "reveal_by_quality_bin.csv")
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for treatment_id, group in df.groupby("treatment_id", observed=True):
        group = group.sort_values("q_bin_midpoint")
        yerr = [
            group["reveal_rate"] - group["ci_low"],
            group["ci_high"] - group["reveal_rate"],
        ]
        ax.errorbar(
            group["q_bin_midpoint"],
            group["reveal_rate"],
            yerr=yerr,
            marker="o",
            linewidth=2.4,
            capsize=3,
            label=clean_label(treatment_id),
            color=COLORS.get(treatment_id),
        )
    style_axes(
        ax,
        "Test 1: Higher Quality Players Reveal More",
        "Initial quality, normalized",
        "Reveal probability",
    )
    ax.set_ylim(-0.03, 1.03)
    ax.legend(frameon=False, ncol=2)
    return save(fig, "01_quality_dependent_disclosure.png")


def plot_cost_effect():
    df = pd.read_csv(RESULTS_DIR / "main_descriptive_table.csv")
    order = ["baseline_low_cost", "baseline_high_cost", "hype_low_cost", "hype_high_cost"]
    df = df.set_index("treatment_id").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(10.5, 6))
    x_values = range(len(df))
    yerr = [
        df["reveal_rate"] - df["reveal_rate_ci_low"],
        df["reveal_rate_ci_high"] - df["reveal_rate"],
    ]
    ax.bar(
        x_values,
        df["reveal_rate"],
        yerr=yerr,
        capsize=5,
        color=[COLORS.get(value) for value in df["treatment_id"]],
    )
    ax.set_xticks(list(x_values))
    ax.set_xticklabels([clean_label(value) for value in df["treatment_id"]], rotation=15, ha="right")
    style_axes(
        ax,
        "Test 2: Higher Improvement Cost Raises Disclosure",
        "Treatment",
        "Reveal probability",
    )
    ax.set_ylim(0, max(0.35, df["reveal_rate"].max() * 1.25))
    add_value_labels(ax, x_values, df["reveal_rate"])
    return save(fig, "02_cost_effect_reveal_rates.png")


def plot_hype_effect_comparison():
    contrasts = pd.read_csv(RESULTS_DIR / "hype_responsive_contrasts.csv")
    contrasts = contrasts[
        contrasts["contrast"].isin(
            ["hype_low_minus_baseline_low", "hype_high_minus_baseline_high"]
        )
    ].copy()
    contrasts["contrast_label"] = contrasts["contrast"].map(
        {
            "hype_low_minus_baseline_low": "Low cost: hype - baseline",
            "hype_high_minus_baseline_high": "High cost: hype - baseline",
        }
    )

    fig, ax = plt.subplots(figsize=(10.5, 6))
    labels = ["Low cost: hype - baseline", "High cost: hype - baseline"]
    x_values = list(range(len(labels)))
    width = 0.36
    for offset, simulation_type in [(-width / 2, "main_mixed_population"), (width / 2, "hype_responsive_extension")]:
        group = contrasts[contrasts["simulation_type"] == simulation_type]
        values = [
            group[group["contrast_label"] == label]["reveal_rate_difference"].iloc[0]
            for label in labels
        ]
        positions = [x + offset for x in x_values]
        ax.bar(
            positions,
            values,
            width,
            label=clean_label(simulation_type),
            color=COLORS.get(simulation_type),
        )
        add_value_labels(ax, positions, values, decimals=3)

    ax.axhline(0, color="#333333", linewidth=1)
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels)
    style_axes(
        ax,
        "Test 3: Hype Effect Depends on Agent Responsiveness",
        "Reveal-rate contrast",
        "Difference in reveal probability",
    )
    ax.legend(frameon=False)
    return save(fig, "03_hype_effect_comparison.png")


def plot_deterrence():
    df = pd.read_csv(RESULTS_DIR / "deterrence_results_table.csv")
    df = df[df["treatment_id"] == "all"].copy()
    order = ["low", "medium", "high"]
    df["opponent_quality_group"] = pd.Categorical(df["opponent_quality_group"], order, ordered=True)
    df = df.sort_values("opponent_quality_group")

    fig, ax = plt.subplots(figsize=(9.5, 6))
    x_values = range(len(df))
    yerr_low = df["improvement_rate"] - df["improvement_rate_ci_low"]
    yerr_high = df["improvement_rate_ci_high"] - df["improvement_rate"]
    yerr_low = yerr_low.fillna(0)
    yerr_high = yerr_high.fillna(0)
    ax.bar(
        x_values,
        df["improvement_rate"].fillna(0),
        yerr=[yerr_low, yerr_high],
        capsize=5,
        color=["#B8C0C2", "#F2A541", "#D1495B"],
    )
    ax.set_xticks(list(x_values))
    ax.set_xticklabels(["Low", "Medium", "High"])
    style_axes(
        ax,
        "Test 4: High Revealed Quality Deters Improvement",
        "Opponent revealed quality",
        "Improvement probability",
    )
    ax.set_ylim(0, 1)
    add_value_labels(ax, x_values, df["improvement_rate"])
    return save(fig, "04_deterrence_by_revealed_quality.png")


def plot_equilibrium_cutoffs():
    df = pd.read_csv(RESULTS_DIR / "equilibrium_compliance_table.csv")
    df = df.sort_values("theoretical_reveal_cutoff_mean")
    x_values = range(len(df))
    fig, ax = plt.subplots(figsize=(10.5, 6))
    ax.scatter(
        x_values,
        df["theoretical_reveal_cutoff_mean"],
        s=90,
        label="Theoretical cutoff",
        color="#333333",
    )
    ax.scatter(
        x_values,
        df["preferred_empirical_q50"],
        s=90,
        label="Empirical q50",
        color="#2E6F95",
    )
    for x, theoretical, empirical in zip(
        x_values,
        df["theoretical_reveal_cutoff_mean"],
        df["preferred_empirical_q50"],
    ):
        ax.plot([x, x], [theoretical, empirical], color="#999999", linewidth=1.6)
    ax.set_xticks(list(x_values))
    ax.set_xticklabels([clean_label(value) for value in df["treatment_id"]], rotation=15, ha="right")
    style_axes(
        ax,
        "Test 5: Empirical Reveal Cutoffs Track Theory",
        "Treatment",
        "Reveal cutoff, normalized quality",
    )
    ax.set_ylim(0.65, 0.9)
    ax.legend(frameon=False)
    return save(fig, "05_theoretical_vs_empirical_cutoffs.png")


def plot_under_over_reveal():
    df = pd.read_csv(RESULTS_DIR / "equilibrium_compliance_table.csv")
    order = ["baseline_low_cost", "baseline_high_cost", "hype_low_cost", "hype_high_cost"]
    df = df.set_index("treatment_id").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(10.5, 6))
    x_values = list(range(len(df)))
    width = 0.36
    ax.bar(
        [x - width / 2 for x in x_values],
        df["under_reveal_rate"],
        width,
        label="Under-reveal",
        color="#D1495B",
    )
    ax.bar(
        [x + width / 2 for x in x_values],
        df["over_reveal_rate"],
        width,
        label="Over-reveal",
        color="#2E6F95",
    )
    ax.set_xticks(x_values)
    ax.set_xticklabels([clean_label(value) for value in df["treatment_id"]], rotation=15, ha="right")
    style_axes(
        ax,
        "Test 6: Deviations Are Small and Mostly Under-Reveal",
        "Treatment",
        "Deviation rate",
    )
    ax.legend(frameon=False)
    return save(fig, "06_under_over_reveal.png")


def plot_payoff_by_quality_and_reveal():
    if not PLAYER_DATA.exists():
        print("Missing full player data. Please run: python scripts/run_full_simulation.py")
        return None

    df = add_derived_variables(pd.read_csv(PLAYER_DATA))
    plot_df = df.groupby(["q_bin", "revealed_label"], observed=True).agg(
        average_payoff=("payoff", "mean"),
        n=("payoff", "size"),
    ).reset_index()
    plot_df["q_bin_midpoint"] = plot_df["q_bin"].apply(interval_midpoint)

    fig, ax = plt.subplots(figsize=(10.5, 6))
    for label, color in [("Hide", "#2E6F95"), ("Reveal", "#D1495B")]:
        group = plot_df[plot_df["revealed_label"] == label].sort_values("q_bin_midpoint")
        ax.plot(
            group["q_bin_midpoint"],
            group["average_payoff"],
            marker="o",
            linewidth=2.4,
            label=label,
            color=color,
        )
    style_axes(
        ax,
        "Test 7: Payoffs by Quality and Reveal Choice",
        "Initial quality, normalized",
        "Average payoff",
    )
    ax.legend(frameon=False)
    return save(fig, "07_payoff_by_quality_and_reveal.png")


def plot_main_regression_summary():
    df = pd.read_csv(RESULTS_DIR / "main_regression_table.csv")
    df = df[df["test_name"] != "Payoff effect of reveal"].copy()
    df["ci_low"] = df["coefficient"] - 1.96 * df["standard_error"]
    df["ci_high"] = df["coefficient"] + 1.96 * df["standard_error"]
    df["label"] = df["test_name"].map(
        {
            "Quality-dependent disclosure": "Quality -> reveal",
            "Cost effect, high-cost dummy": "High cost -> reveal",
            "Cost effect, continuous k": "k -> reveal",
            "Hype effect": "Hype -> reveal",
            "Deterrence": "Opponent quality -> improve",
        }
    )
    df = df.iloc[::-1]

    fig, ax = plt.subplots(figsize=(11, 6))
    y_values = list(range(len(df)))
    ax.errorbar(
        df["coefficient"],
        y_values,
        xerr=[df["coefficient"] - df["ci_low"], df["ci_high"] - df["coefficient"]],
        fmt="o",
        markersize=8,
        capsize=4,
        color="#2E6F95",
    )
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_yticks(y_values)
    ax.set_yticklabels(df["label"])
    style_axes(
        ax,
        "Main Regression Coefficients with 95% Confidence Intervals",
        "Coefficient",
        "",
    )
    return save(fig, "08_main_regression_coefficients.png")


def style_axes(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=16, weight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def add_value_labels(ax, x_values, values, decimals=2):
    for x, value in zip(x_values, values):
        if pd.isna(value):
            label = "NA"
            y = 0.02
        else:
            label = f"{value:.{decimals}f}"
            y = value
        va = "bottom" if y >= 0 else "top"
        offset = 0.01 if y >= 0 else -0.01
        ax.text(x, y + offset, label, ha="center", va=va, fontsize=10)


def interval_midpoint(value):
    text = str(value).strip("()[]")
    parts = text.split(",")
    if len(parts) != 2:
        return None
    left = max(0.0, float(parts[0]))
    right = min(1.0, float(parts[1]))
    return (left + right) / 2


def clean_label(value):
    labels = {
        "baseline_low_cost": "Baseline, low cost",
        "baseline_high_cost": "Baseline, high cost",
        "hype_low_cost": "Hype, low cost",
        "hype_high_cost": "Hype, high cost",
        "main_mixed_population": "Main mixed population",
        "hype_responsive_extension": "Hype-responsive extension",
    }
    return labels.get(str(value), str(value).replace("_", " ").title())


def save(fig, filename):
    path = OUTPUT_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


if __name__ == "__main__":
    main()

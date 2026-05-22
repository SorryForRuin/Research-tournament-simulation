"""Paper-ready result extraction tables for the tournament simulation."""

from pathlib import Path
import math
import warnings

import pandas as pd
import statsmodels.formula.api as smf

from tournament_sim.analysis import add_derived_variables, run_lpm
from tournament_sim.counterfactuals import add_counterfactual_columns


MAIN_PLAYER_DATA = Path("outputs/full_simulation/data/player_round_records.csv")
MAIN_MATCH_DATA = Path("outputs/full_simulation/data/match_round_records.csv")
HYPE_PLAYER_DATA = Path("outputs/hype_responsive_simulation/data/player_round_records.csv")
SEED_TREATMENT_DATA = Path("outputs/robustness/seed_robustness/seed_level_treatment_summary.csv")
SEED_COEFFICIENT_DATA = Path("outputs/robustness/seed_robustness/seed_level_key_coefficients.csv")
POP_TREATMENT_DATA = Path("outputs/robustness/population_robustness/population_treatment_summary.csv")
POP_COEFFICIENT_DATA = Path("outputs/robustness/population_robustness/population_key_coefficients.csv")


def compile_results_for_paper(project_root=".", output_dir=None):
    """Compile compact CSV, Markdown, and LaTeX outputs for paper writing."""
    project_root = Path(project_root)
    if output_dir is None:
        output_dir = project_root / "outputs" / "results_for_paper"
    else:
        output_dir = Path(output_dir)

    player_path = project_root / MAIN_PLAYER_DATA
    match_path = project_root / MAIN_MATCH_DATA
    if not player_path.exists() or not match_path.exists():
        print("Missing full simulation files.")
        print("Please run: python scripts/run_full_simulation.py")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir = output_dir / "figure_data"
    figure_dir.mkdir(parents=True, exist_ok=True)

    df = load_player_data(player_path)
    match_df = pd.read_csv(match_path)
    warnings_list = []

    tables = {
        "main_descriptive_table": main_descriptive_table(df, match_df),
        "main_regression_table": main_regression_table(df),
        "deterrence_results_table": deterrence_results_table(df),
        "equilibrium_compliance_table": equilibrium_compliance_table(df),
        "equilibrium_compliance_by_type_table": equilibrium_compliance_by_type_table(df),
        "agent_type_results_table": agent_type_results_table(df),
    }

    counterfactual_tables = counterfactual_results_tables(df)
    hype_tables, hype_warnings = hype_responsive_tables(project_root, df)
    robustness_tables, robustness_warnings = robustness_summary_tables(project_root)
    figure_tables = figure_data_tables(df)

    warnings_list.extend(hype_warnings)
    warnings_list.extend(robustness_warnings)

    save_table(tables["main_descriptive_table"], output_dir / "main_descriptive_table.csv")
    save_table(tables["main_regression_table"], output_dir / "main_regression_table.csv")
    save_table(tables["deterrence_results_table"], output_dir / "deterrence_results_table.csv")
    save_table(tables["equilibrium_compliance_table"], output_dir / "equilibrium_compliance_table.csv")
    save_table(
        tables["equilibrium_compliance_by_type_table"],
        output_dir / "equilibrium_compliance_by_type_table.csv",
    )
    save_table(tables["agent_type_results_table"], output_dir / "agent_type_results_table.csv")

    save_table(counterfactual_tables["combined"], output_dir / "counterfactual_results_table.csv")
    for name, table in counterfactual_tables.items():
        if name != "combined":
            save_table(table, output_dir / ("counterfactual_" + name + ".csv"))

    save_table(hype_tables["comparison"], output_dir / "hype_responsive_comparison_table.csv")
    save_table(hype_tables["contrasts"], output_dir / "hype_responsive_contrasts.csv")
    save_table(robustness_tables["combined"], output_dir / "robustness_summary_table.csv")

    for name, table in figure_tables.items():
        save_table(table, figure_dir / (name + ".csv"))

    write_latex(tables["main_regression_table"], output_dir / "main_regression_table.tex")
    write_latex(tables["main_descriptive_table"], output_dir / "main_descriptive_table.tex")

    summary = paper_results_summary(
        df=df,
        descriptive=tables["main_descriptive_table"],
        regressions=tables["main_regression_table"],
        deterrence=tables["deterrence_results_table"],
        compliance=tables["equilibrium_compliance_table"],
        by_type=tables["agent_type_results_table"],
        counterfactuals=counterfactual_tables,
        hype_tables=hype_tables,
        robustness_tables=robustness_tables,
        warnings_list=warnings_list,
    )
    (output_dir / "paper_results_summary.md").write_text(summary, encoding="utf-8")

    for warning in warnings_list:
        print("Warning:", warning)
    print("Paper results written to:", output_dir)
    return {
        "output_dir": output_dir,
        "tables": tables,
        "counterfactual_tables": counterfactual_tables,
        "hype_tables": hype_tables,
        "robustness_tables": robustness_tables,
        "figure_tables": figure_tables,
        "warnings": warnings_list,
    }


def load_player_data(path):
    """Load player-round data and add analysis variables."""
    df = pd.read_csv(path)
    return add_derived_variables(df)


def main_descriptive_table(df, match_df):
    rows = []
    matches_by_treatment = match_df.groupby("treatment_id", observed=True).size().to_dict()
    for treatment_id, group in df.groupby("treatment_id", observed=True):
        hidden = group[group["eligible_to_improve"] == 1]
        deterrence_sample = group[
            (group["eligible_to_improve"] == 1) & (group["opponent_revealed"] == 1)
        ]
        reveal_ci = proportion_ci(group["revealed"])
        improve_ci = proportion_ci(hidden["improved"])
        rows.append(
            {
                "treatment_id": treatment_id,
                "V": group["V"].iloc[0],
                "c": group["c"].iloc[0],
                "h": group["h"].iloc[0],
                "k": group["k"].iloc[0],
                "n_player_rounds": len(group),
                "n_matches": matches_by_treatment.get(treatment_id, len(group) / 2),
                "reveal_rate": group["revealed"].mean(),
                "reveal_rate_ci_low": reveal_ci["ci_low"],
                "reveal_rate_ci_high": reveal_ci["ci_high"],
                "improvement_rate": hidden["improved"].mean(),
                "improvement_rate_ci_low": improve_ci["ci_low"],
                "improvement_rate_ci_high": improve_ci["ci_high"],
                "win_rate": group["won"].mean(),
                "average_payoff": group["payoff"].mean(),
                "average_initial_quality": group["initial_quality"].mean(),
                "average_final_quality": group["final_quality"].mean(),
                "deterrence_sample_n": len(deterrence_sample),
                "deterrence_opportunity_rate": len(deterrence_sample) / len(group),
            }
        )
    return pd.DataFrame(rows).sort_values("treatment_id")


def main_regression_table(df):
    specs = [
        {
            "test_name": "Quality-dependent disclosure",
            "formula": "revealed ~ q_norm",
            "sample_restriction": "All player-rounds",
            "coefficient_name": "q_norm",
            "expected_sign": "positive",
            "sample": df,
        },
        {
            "test_name": "Cost effect, high-cost dummy",
            "formula": "revealed ~ high_cost + q_norm + hype_treatment",
            "sample_restriction": "All player-rounds",
            "coefficient_name": "high_cost",
            "expected_sign": "positive",
            "sample": df,
        },
        {
            "test_name": "Cost effect, continuous k",
            "formula": "revealed ~ k + q_norm + hype_treatment",
            "sample_restriction": "All player-rounds",
            "coefficient_name": "k",
            "expected_sign": "positive",
            "sample": df,
        },
        {
            "test_name": "Hype effect",
            "formula": "revealed ~ hype_treatment + q_norm + k",
            "sample_restriction": "All player-rounds",
            "coefficient_name": "hype_treatment",
            "expected_sign": "positive",
            "sample": df,
        },
        {
            "test_name": "Deterrence",
            "formula": "improved ~ opponent_revealed_quality_norm + q_norm + k + hype_treatment",
            "sample_restriction": "Hidden players who observed an opponent reveal",
            "coefficient_name": "opponent_revealed_quality_norm",
            "expected_sign": "negative",
            "sample": deterrence_sample(df),
        },
        {
            "test_name": "Payoff effect of reveal",
            "formula": "payoff ~ revealed + q_norm + k + hype_treatment + round + C(player_type)",
            "sample_restriction": "All player-rounds",
            "coefficient_name": "revealed",
            "expected_sign": "NA",
            "sample": df,
        },
    ]

    rows = []
    for spec in specs:
        model = run_lpm(spec["formula"], spec["sample"])
        term = spec["coefficient_name"]
        coefficient = model.params[term]
        rows.append(
            {
                "test_name": spec["test_name"],
                "formula": spec["formula"],
                "sample_restriction": spec["sample_restriction"],
                "coefficient_name": term,
                "coefficient": coefficient,
                "standard_error": model.bse[term],
                "p_value": model.pvalues[term],
                "nobs": model.nobs,
                "expected_sign": spec["expected_sign"],
                "sign_matches_prediction": sign_matches(coefficient, spec["expected_sign"]),
                "significance_5pct": bool(model.pvalues[term] < 0.05),
            }
        )
    return pd.DataFrame(rows)


def deterrence_results_table(df):
    sample = deterrence_sample(df).copy()
    sample["opponent_quality_group"] = pd.cut(
        sample["opponent_revealed_quality_norm"],
        bins=[0, 1 / 3, 2 / 3, 1],
        labels=["low", "medium", "high"],
        include_lowest=True,
    )
    overall = _deterrence_group_table(sample, ["opponent_quality_group"])
    overall.insert(0, "treatment_id", "all")
    by_treatment = _deterrence_group_table(sample, ["treatment_id", "opponent_quality_group"])
    table = pd.concat([overall, by_treatment], ignore_index=True)
    treatment_ids = ["all"] + sorted(df["treatment_id"].unique().tolist())
    return _complete_deterrence_table(table, treatment_ids)


def equilibrium_compliance_table(df):
    compliance = _compliance_table(df, ["treatment_id"])
    cutoffs = _empirical_cutoffs(df, ["treatment_id"])
    table = compliance.merge(cutoffs, on="treatment_id", how="left")
    table["cutoff_difference_preferred_minus_theory"] = (
        table["preferred_empirical_q50"] - table["theoretical_reveal_cutoff_mean"]
    )
    return table


def equilibrium_compliance_by_type_table(df):
    compliance = _compliance_table(df, ["treatment_id", "player_type"])
    cutoffs = _empirical_cutoffs(df, ["treatment_id", "player_type"])
    table = compliance.merge(cutoffs, on=["treatment_id", "player_type"], how="left")
    table = table.rename(columns={"preferred_empirical_q50": "empirical_cutoff_if_available"})
    return table


def agent_type_results_table(df):
    rows = []
    for (treatment_id, player_type), group in df.groupby(["treatment_id", "player_type"], observed=True):
        hidden = group[group["eligible_to_improve"] == 1]
        observed = deterrence_sample(group)
        empirical = empirical_q50(group)["preferred_empirical_q50"]
        theoretical = group["r_star"].mean()
        rows.append(
            {
                "treatment_id": treatment_id,
                "player_type": player_type,
                "n_player_rounds": len(group),
                "reveal_rate": group["revealed"].mean(),
                "improvement_rate": hidden["improved"].mean(),
                "improvement_rate_after_opponent_reveal": observed["improved"].mean(),
                "average_payoff": group["payoff"].mean(),
                "win_rate": group["won"].mean(),
                "empirical_reveal_cutoff": empirical,
                "theoretical_reveal_cutoff": theoretical,
                "cutoff_difference": None if pd.isna(empirical) else empirical - theoretical,
                "deterrence_rate": 1 - observed["improved"].mean() if len(observed) else None,
            }
        )
    return pd.DataFrame(rows).sort_values(["treatment_id", "player_type"])


def counterfactual_results_tables(df):
    cf_df = add_counterfactual_columns(df)
    cf_df["positive_cf_reveal_gain"] = (cf_df["cf_reveal_gain_vs_best_hide"] > 0).astype(int)

    overall = pd.DataFrame(
        [
            {
                "section": "overall",
                "n": len(cf_df),
                "mean_cf_reveal_gain_vs_best_hide": cf_df["cf_reveal_gain_vs_best_hide"].mean(),
                "median_cf_reveal_gain_vs_best_hide": cf_df["cf_reveal_gain_vs_best_hide"].median(),
                "share_positive_cf_reveal_gain": cf_df["positive_cf_reveal_gain"].mean(),
                "correlation_actual_reveal_cf_gain": safe_corr(
                    cf_df["revealed"],
                    cf_df["cf_reveal_gain_vs_best_hide"],
                ),
                "prob_action_matches_cf_gain": cf_df["actual_reveal_matches_cf_gain"].mean(),
            }
        ]
    )
    by_treatment = _counterfactual_group_table(cf_df, ["treatment_id"], "by_treatment")
    by_quality_bin = _counterfactual_group_table(cf_df, ["q_bin"], "by_quality_bin")
    by_player_type = _counterfactual_group_table(cf_df, ["player_type"], "by_player_type")
    combined = pd.concat([overall, by_treatment, by_quality_bin, by_player_type], ignore_index=True)
    return {
        "combined": combined,
        "overall": overall,
        "by_treatment": by_treatment,
        "by_quality_bin": by_quality_bin,
        "by_player_type": by_player_type,
    }


def hype_responsive_tables(project_root, main_df):
    warnings_list = []
    hype_path = project_root / HYPE_PLAYER_DATA
    main_summary = _simulation_summary(main_df, "main_mixed_population")
    if hype_path.exists():
        hype_df = load_player_data(hype_path)
        hype_summary = _simulation_summary(hype_df, "hype_responsive_extension")
        comparison = pd.concat([main_summary, hype_summary], ignore_index=True)
    else:
        warnings_list.append(
            "Missing hype-responsive output. Run: python scripts/run_hype_responsive_simulation.py"
        )
        comparison = main_summary
    contrasts = _hype_contrasts(comparison)
    return {"comparison": comparison, "contrasts": contrasts}, warnings_list


def robustness_summary_tables(project_root):
    warnings_list = []
    rows = []

    seed_coef_path = project_root / SEED_COEFFICIENT_DATA
    seed_treatment_path = project_root / SEED_TREATMENT_DATA
    pop_coef_path = project_root / POP_COEFFICIENT_DATA
    pop_treatment_path = project_root / POP_TREATMENT_DATA

    if seed_coef_path.exists():
        seed_coef = pd.read_csv(seed_coef_path)
        for (model, term), group in seed_coef.groupby(["model", "term"], observed=True):
            signs = group["coef"].apply(lambda value: 1 if value >= 0 else -1)
            rows.append(
                {
                    "section": "seed_key_coefficients",
                    "model": model,
                    "term": term,
                    "mean_coef": group["coef"].mean(),
                    "min_coef": group["coef"].min(),
                    "max_coef": group["coef"].max(),
                    "mean_p_value": group["p_value"].mean(),
                    "share_significant_5pct": (group["p_value"] < 0.05).mean(),
                    "sign_stable": signs.nunique() == 1,
                }
            )
    else:
        warnings_list.append("Missing seed coefficient output. Run: python scripts/run_seed_robustness.py")

    if seed_treatment_path.exists():
        seed_treatment = pd.read_csv(seed_treatment_path)
        for treatment_id, group in seed_treatment.groupby("treatment_id", observed=True):
            rows.append(
                {
                    "section": "seed_treatment_reveal_rates",
                    "treatment_id": treatment_id,
                    "mean_reveal_rate": group["reveal_rate"].mean(),
                    "min_reveal_rate": group["reveal_rate"].min(),
                    "max_reveal_rate": group["reveal_rate"].max(),
                    "sd_reveal_rate": group["reveal_rate"].std(),
                }
            )
    else:
        warnings_list.append("Missing seed treatment output. Run: python scripts/run_seed_robustness.py")

    if pop_coef_path.exists():
        pop_coef = pd.read_csv(pop_coef_path)
        for _, row in pop_coef.iterrows():
            rows.append(
                {
                    "section": "population_key_coefficients",
                    "scenario": row["scenario"],
                    "model": row["model"],
                    "term": row["term"],
                    "coef": row["coef"],
                    "std_error": row["std_error"],
                    "p_value": row["p_value"],
                    "sign_matches_prediction": _population_sign_match(row),
                }
            )
    else:
        warnings_list.append(
            "Missing population coefficient output. Run: python scripts/run_population_robustness.py"
        )

    if pop_treatment_path.exists():
        pop_treatment = pd.read_csv(pop_treatment_path)
        for _, row in pop_treatment.iterrows():
            rows.append(
                {
                    "section": "population_treatment_reveal_rates",
                    "scenario": row["scenario"],
                    "treatment_id": row["treatment_id"],
                    "reveal_rate": row["reveal_rate"],
                    "improvement_rate": row["improvement_rate"],
                    "average_payoff": row["average_payoff"],
                }
            )
    else:
        warnings_list.append(
            "Missing population treatment output. Run: python scripts/run_population_robustness.py"
        )

    return {"combined": pd.DataFrame(rows)}, warnings_list


def figure_data_tables(df):
    cf_df = add_counterfactual_columns(df)
    reveal = _rate_by_interval(
        df,
        ["treatment_id", "q_bin"],
        "revealed",
        "q_bin",
        "q_bin_midpoint",
        "reveal_rate",
    )
    improve_sample = deterrence_sample(df)
    improve = _rate_by_interval(
        improve_sample,
        ["treatment_id", "opponent_revealed_quality_bin"],
        "improved",
        "opponent_revealed_quality_bin",
        "opponent_quality_bin_midpoint",
        "improvement_rate",
    ).rename(columns={"opponent_revealed_quality_bin": "opponent_quality_bin"})
    cutoff = equilibrium_compliance_by_type_table(df)[
        [
            "treatment_id",
            "player_type",
            "theoretical_reveal_cutoff_mean",
            "empirical_cutoff_if_available",
        ]
    ].copy()
    cutoff = cutoff.rename(
        columns={
            "theoretical_reveal_cutoff_mean": "theoretical_cutoff",
            "empirical_cutoff_if_available": "empirical_cutoff",
        }
    )
    cutoff["cutoff_difference"] = cutoff["empirical_cutoff"] - cutoff["theoretical_cutoff"]
    cf_gain = _mean_ci_by_interval(
        cf_df,
        ["q_bin"],
        "cf_reveal_gain_vs_best_hide",
        "q_bin",
        "q_bin_midpoint",
        "mean_cf_reveal_gain_vs_best_hide",
    )
    reveal_treatment = _rate_table(df, ["treatment_id"], "revealed", "reveal_rate")
    return {
        "reveal_by_quality_bin": reveal,
        "improvement_by_opponent_revealed_quality": improve,
        "theoretical_vs_empirical_cutoff": cutoff,
        "counterfactual_gain_by_quality_bin": cf_gain,
        "reveal_rate_by_treatment": reveal_treatment,
    }


def paper_results_summary(
    df,
    descriptive,
    regressions,
    deterrence,
    compliance,
    by_type,
    counterfactuals,
    hype_tables,
    robustness_tables,
    warnings_list,
):
    treatment_count = df["treatment_id"].nunique()
    player_rounds = len(df)
    matches = int(df["match_id"].nunique()) if "match_id" in df.columns else int(player_rounds / 2)
    subjects = df["subject_id"].nunique()
    rounds = df["round"].nunique()

    highest_reveal = descriptive.sort_values("reveal_rate", ascending=False).iloc[0]
    low_cost = _contrast_from_table(descriptive, "baseline_low_cost", "baseline_high_cost", "reveal_rate")
    hype_low = _contrast_from_table(descriptive, "baseline_low_cost", "hype_low_cost", "reveal_rate")
    hype_high = _contrast_from_table(descriptive, "baseline_high_cost", "hype_high_cost", "reveal_rate")
    deterrence_coef = regressions[regressions["test_name"] == "Deterrence"].iloc[0]
    quality_coef = regressions[regressions["test_name"] == "Quality-dependent disclosure"].iloc[0]
    cost_coef = regressions[regressions["test_name"] == "Cost effect, high-cost dummy"].iloc[0]
    hype_coef = regressions[regressions["test_name"] == "Hype effect"].iloc[0]
    payoff_coef = regressions[regressions["test_name"] == "Payoff effect of reveal"].iloc[0]
    cf_overall = counterfactuals["overall"].iloc[0]
    average_accuracy = compliance["accuracy"].mean()
    average_deviation = compliance["mean_reveal_deviation"].mean()
    type_rates = by_type.groupby("player_type", observed=True)["reveal_rate"].mean().sort_values(ascending=False)

    lines = [
        "# Paper Results Summary",
        "",
        "These results describe simulated behavior. They validate the proposed experimental design rather than provide evidence about human subjects.",
        "",
        "## Simulation Size",
        "",
        f"- Subjects: {subjects}",
        f"- Rounds: {rounds}",
        f"- Matches: {matches}",
        f"- Player-round observations: {player_rounds}",
        f"- Treatments: {treatment_count}",
        "",
        "## Treatment-Level Descriptives",
        "",
        f"- Highest reveal rate: {highest_reveal['treatment_id']} ({fmt_pct(highest_reveal['reveal_rate'])}).",
        f"- In the mixed-agent simulation, high cost raises reveal by {fmt_decimal(low_cost)} in high cost relative to low cost among baseline treatments.",
        f"- Hype changes reveal by {fmt_decimal(hype_low)} in low cost and {fmt_decimal(hype_high)} in high cost in the main mixed-population simulation.",
        "",
        markdown_table(
            descriptive[
                ["treatment_id", "reveal_rate", "improvement_rate", "average_payoff"]
            ]
        ),
        "",
        "## Main Regression Findings",
        "",
        f"- Quality-dependent disclosure: q_norm coefficient {fmt_decimal(quality_coef['coefficient'])}, p={fmt_p(quality_coef['p_value'])}.",
        f"- Cost effect: high_cost coefficient {fmt_decimal(cost_coef['coefficient'])}, p={fmt_p(cost_coef['p_value'])}.",
        f"- Hype effect under the mixed-agent specification: coefficient {fmt_decimal(hype_coef['coefficient'])}, p={fmt_p(hype_coef['p_value'])}.",
        f"- Deterrence: opponent revealed quality coefficient {fmt_decimal(deterrence_coef['coefficient'])}, p={fmt_p(deterrence_coef['p_value'])}.",
        f"- Payoff effect of reveal, conditional on controls: coefficient {fmt_decimal(payoff_coef['coefficient'])}, p={fmt_p(payoff_coef['p_value'])}.",
        "",
        "## Mechanism: Deterrence",
        "",
        f"- Deterrence sample size: {int(deterrence_coef['nobs'])}.",
        "- Improvement rates by revealed opponent quality group:",
        markdown_table(
            deterrence[deterrence["treatment_id"] == "all"][
                ["opponent_quality_group", "n", "improvement_rate"]
            ]
        ),
        "",
        "The negative deterrence coefficient means that, among hidden players who observed an opponent reveal, higher revealed opponent quality sharply reduces the probability of improving.",
        "",
        "## Equilibrium Compliance",
        "",
        f"- Average treatment-level benchmark accuracy: {fmt_pct(average_accuracy)}.",
        f"- Average reveal deviation is {fmt_decimal(average_deviation)}; negative values indicate under-revealing relative to the no-hype benchmark.",
        "- Preferred empirical cutoffs are reported in `equilibrium_compliance_table.csv`.",
        "",
        "## Agent Types",
        "",
        f"- Highest average reveal type: {type_rates.index[0]} ({fmt_pct(type_rates.iloc[0])}).",
        f"- Lowest average reveal type: {type_rates.index[-1]} ({fmt_pct(type_rates.iloc[-1])}).",
        "- UnderRevealerAgent and OverRevealerAgent are separated in the table so their intended cutoff shifts can be checked directly.",
        "",
        "## Counterfactuals",
        "",
        f"- Mean reveal gain relative to best hidden action: {fmt_decimal(cf_overall['mean_cf_reveal_gain_vs_best_hide'])}.",
        f"- Share with positive counterfactual reveal gain: {fmt_pct(cf_overall['share_positive_cf_reveal_gain'])}.",
        f"- Actual action matches the sign of counterfactual reveal gain in {fmt_pct(cf_overall['prob_action_matches_cf_gain'])} of observations.",
        "Reveal is generally payoff-justified mainly at higher quality levels; the quality-bin table gives the exact pattern.",
        "",
        "## Hype-Responsive Extension",
        "",
        _hype_summary_text(hype_tables),
        "",
        "The main mixed-population simulation includes EquilibriumAgent, which uses no-hype cutoffs even in hype treatments. The hype-responsive extension should therefore be interpreted separately.",
        "",
        "## Robustness",
        "",
        _robustness_summary_text(robustness_tables),
    ]
    if warnings_list:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings_list:
            lines.append("- " + warning)
    return "\n".join(lines) + "\n"


def deterrence_sample(df):
    sample = df[(df["eligible_to_improve"] == 1) & (df["opponent_revealed"] == 1)].copy()
    return sample.dropna(subset=["opponent_revealed_quality_norm"])


def proportion_ci(series):
    clean = series.dropna()
    n = len(clean)
    if n == 0:
        return {"se": None, "ci_low": None, "ci_high": None}
    p = clean.mean()
    se = math.sqrt(p * (1 - p) / n)
    return {"se": se, "ci_low": max(0.0, p - 1.96 * se), "ci_high": min(1.0, p + 1.96 * se)}


def safe_corr(left, right):
    """Return correlation, or None when one side has no variation."""
    left = left.dropna()
    right = right.dropna()
    common_index = left.index.intersection(right.index)
    left = left.loc[common_index]
    right = right.loc[common_index]
    if len(left) < 2 or left.nunique() < 2 or right.nunique() < 2:
        return None
    return left.corr(right)


def markdown_table(table):
    """Small dependency-free Markdown table helper."""
    if table.empty:
        return "_No rows._"

    columns = list(table.columns)
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in table.iterrows():
        cells = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                cells.append(fmt_decimal(value))
            else:
                cells.append(str(value))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def mean_ci(series):
    clean = series.dropna()
    n = len(clean)
    if n < 2:
        return {"ci_low": None, "ci_high": None}
    mean = clean.mean()
    se = clean.std() / math.sqrt(n)
    return {"ci_low": mean - 1.96 * se, "ci_high": mean + 1.96 * se}


def empirical_q50(group):
    result = {
        "empirical_q50_lpm": None,
        "empirical_q50_logit": None,
        "preferred_empirical_q50": None,
        "preferred_method": None,
    }
    if group["revealed"].nunique() < 2:
        return result

    try:
        lpm = smf.ols("revealed ~ q_norm", data=group).fit()
        beta = lpm.params.get("q_norm")
        alpha = lpm.params.get("Intercept")
        if beta is not None and beta != 0:
            result["empirical_q50_lpm"] = (0.5 - alpha) / beta
    except Exception:
        pass

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            logit = smf.logit("revealed ~ q_norm", data=group).fit(disp=False, maxiter=200)
        beta = logit.params.get("q_norm")
        alpha = logit.params.get("Intercept")
        if beta is not None and beta != 0:
            result["empirical_q50_logit"] = -alpha / beta
    except Exception:
        pass

    logit_q50 = result["empirical_q50_logit"]
    lpm_q50 = result["empirical_q50_lpm"]
    if logit_q50 is not None and 0 <= logit_q50 <= 1:
        result["preferred_empirical_q50"] = logit_q50
        result["preferred_method"] = "logit"
    elif lpm_q50 is not None and 0 <= lpm_q50 <= 1:
        result["preferred_empirical_q50"] = lpm_q50
        result["preferred_method"] = "lpm"
    return result


def save_table(table, path):
    table = table.copy()
    for column in table.columns:
        if pd.api.types.is_categorical_dtype(table[column]):
            table[column] = table[column].astype(str)
    table.to_csv(path, index=False)


def write_latex(table, path):
    try:
        path.write_text(table.to_latex(index=False), encoding="utf-8")
    except Exception as exc:
        path.write_text("LaTeX export failed: " + str(exc), encoding="utf-8")


def sign_matches(coefficient, expected_sign):
    if expected_sign == "positive":
        return bool(coefficient > 0)
    if expected_sign == "negative":
        return bool(coefficient < 0)
    return pd.NA


def _deterrence_group_table(sample, group_cols):
    rows = []
    for key, group in sample.groupby(group_cols, observed=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(group_cols, key))
        ci = proportion_ci(group["improved"])
        row.update(
            {
                "n": len(group),
                "improvement_rate": group["improved"].mean(),
                "improvement_rate_ci_low": ci["ci_low"],
                "improvement_rate_ci_high": ci["ci_high"],
                "average_own_quality": group["q_norm"].mean(),
                "average_opponent_revealed_quality": group["opponent_revealed_quality_norm"].mean(),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _compliance_table(df, group_cols):
    return df.groupby(group_cols, observed=True).agg(
        n=("revealed", "size"),
        theoretical_reveal_cutoff_mean=("r_star", "mean"),
        actual_reveal_rate=("revealed", "mean"),
        predicted_reveal_rate=("predicted_reveal", "mean"),
        accuracy=("correct_reveal_action", "mean"),
        under_reveal_rate=("under_reveal_mistake", "mean"),
        over_reveal_rate=("over_reveal_mistake", "mean"),
        mean_reveal_deviation=("reveal_deviation", "mean"),
    ).reset_index()


def _empirical_cutoffs(df, group_cols):
    rows = []
    for key, group in df.groupby(group_cols, observed=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(group_cols, key))
        row.update(empirical_q50(group))
        rows.append(row)
    return pd.DataFrame(rows)


def _counterfactual_group_table(df, group_cols, section):
    rows = []
    for key, group in df.groupby(group_cols, observed=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = {"section": section}
        row.update(dict(zip(group_cols, key)))
        row.update(
            {
                "n": len(group),
                "mean_cf_reveal_gain_vs_best_hide": group["cf_reveal_gain_vs_best_hide"].mean(),
                "median_cf_reveal_gain_vs_best_hide": group["cf_reveal_gain_vs_best_hide"].median(),
                "share_positive_cf_reveal_gain": group["positive_cf_reveal_gain"].mean(),
                "correlation_actual_reveal_cf_gain": safe_corr(
                    group["revealed"],
                    group["cf_reveal_gain_vs_best_hide"],
                ),
                "prob_action_matches_cf_gain": group["actual_reveal_matches_cf_gain"].mean(),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _simulation_summary(df, simulation_type):
    rows = []
    for treatment_id, group in df.groupby("treatment_id", observed=True):
        hidden = group[group["eligible_to_improve"] == 1]
        rows.append(
            {
                "simulation_type": simulation_type,
                "treatment_id": treatment_id,
                "reveal_rate": group["revealed"].mean(),
                "improvement_rate": hidden["improved"].mean(),
                "average_payoff": group["payoff"].mean(),
                "n_player_rounds": len(group),
            }
        )
    return pd.DataFrame(rows)


def _hype_contrasts(comparison):
    rows = []
    for simulation_type, group in comparison.groupby("simulation_type", observed=True):
        rates = group.set_index("treatment_id")["reveal_rate"].to_dict()
        definitions = [
            ("hype_low_minus_baseline_low", "hype_low_cost", "baseline_low_cost"),
            ("hype_high_minus_baseline_high", "hype_high_cost", "baseline_high_cost"),
            ("baseline_high_minus_baseline_low", "baseline_high_cost", "baseline_low_cost"),
            ("hype_high_minus_hype_low", "hype_high_cost", "hype_low_cost"),
        ]
        for name, high, low in definitions:
            rows.append(
                {
                    "simulation_type": simulation_type,
                    "contrast": name,
                    "reveal_rate_difference": rates.get(high) - rates.get(low)
                    if high in rates and low in rates
                    else None,
                }
            )
    return pd.DataFrame(rows)


def _rate_table(df, group_cols, outcome_col, rate_name):
    rows = []
    for key, group in df.groupby(group_cols, observed=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(group_cols, key))
        ci = proportion_ci(group[outcome_col])
        row.update({"n": len(group), rate_name: group[outcome_col].mean(), "ci_low": ci["ci_low"], "ci_high": ci["ci_high"]})
        rows.append(row)
    return pd.DataFrame(rows)


def _rate_by_interval(df, group_cols, outcome_col, interval_col, midpoint_col, rate_name):
    table = _rate_table(df, group_cols, outcome_col, rate_name)
    table[midpoint_col] = table[interval_col].apply(interval_midpoint)
    return table


def _mean_ci_by_interval(df, group_cols, value_col, interval_col, midpoint_col, mean_name):
    rows = []
    for key, group in df.groupby(group_cols, observed=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = dict(zip(group_cols, key))
        ci = mean_ci(group[value_col])
        row.update(
            {
                "n": len(group),
                mean_name: group[value_col].mean(),
                "ci_low": ci["ci_low"],
                "ci_high": ci["ci_high"],
                midpoint_col: interval_midpoint(row[interval_col]),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def interval_midpoint(value):
    if hasattr(value, "mid"):
        left = max(0.0, float(value.left))
        right = min(1.0, float(value.right))
        return (left + right) / 2
    if pd.isna(value):
        return None
    text = str(value).strip("()[]")
    parts = text.split(",")
    if len(parts) != 2:
        return None
    return (float(parts[0]) + float(parts[1])) / 2


def _complete_deterrence_table(table, treatment_ids):
    groups = ["low", "medium", "high"]
    rows = []
    for treatment_id in treatment_ids:
        for group_name in groups:
            existing = table[
                (table["treatment_id"] == treatment_id)
                & (table["opponent_quality_group"].astype(str) == group_name)
            ]
            if existing.empty:
                rows.append(
                    {
                        "treatment_id": treatment_id,
                        "opponent_quality_group": group_name,
                        "n": 0,
                        "improvement_rate": None,
                        "improvement_rate_ci_low": None,
                        "improvement_rate_ci_high": None,
                        "average_own_quality": None,
                        "average_opponent_revealed_quality": None,
                    }
                )
            else:
                rows.append(existing.iloc[0].to_dict())
    return pd.DataFrame(rows)


def _population_sign_match(row):
    if row["term"] == "high_cost":
        return bool(row["coef"] > 0)
    if row["term"] == "opponent_revealed_quality_norm":
        return bool(row["coef"] < 0)
    return pd.NA


def _contrast_from_table(table, low_treatment, high_treatment, column):
    values = table.set_index("treatment_id")[column].to_dict()
    return values.get(high_treatment) - values.get(low_treatment)


def _hype_summary_text(hype_tables):
    comparison = hype_tables["comparison"]
    contrasts = hype_tables["contrasts"]
    lines = []
    for simulation_type, group in contrasts.groupby("simulation_type", observed=True):
        low = _contrast_value(group, "hype_low_minus_baseline_low")
        high = _contrast_value(group, "hype_high_minus_baseline_high")
        lines.append(
            f"- {simulation_type}: hype changes reveal by {fmt_decimal(low)} in low cost and {fmt_decimal(high)} in high cost."
        )
    if comparison.empty:
        return "No hype-responsive comparison data were available."
    return "\n".join(lines)


def _robustness_summary_text(robustness_tables):
    table = robustness_tables["combined"]
    if table.empty:
        return "No robustness outputs were available."
    seed = table[table["section"] == "seed_key_coefficients"]
    lines = []
    for _, row in seed.iterrows():
        lines.append(
            f"- Seed robustness for {row['model']} / {row['term']}: mean coefficient {fmt_decimal(row['mean_coef'])}, sign stable = {row['sign_stable']}."
        )
    if not lines:
        lines.append("- Seed robustness was not available.")
    lines.append("- Population-composition details are reported in `robustness_summary_table.csv`.")
    return "\n".join(lines)


def _contrast_value(group, contrast_name):
    row = group[group["contrast"] == contrast_name]
    if row.empty:
        return None
    return row["reveal_rate_difference"].iloc[0]


def fmt_decimal(value):
    if value is None or pd.isna(value):
        return "NA"
    return f"{value:.3f}"


def fmt_pct(value):
    if value is None or pd.isna(value):
        return "NA"
    return f"{100 * value:.1f}%"


def fmt_p(value):
    if value is None or pd.isna(value):
        return "NA"
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"

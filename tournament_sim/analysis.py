"""Regression and descriptive analysis for simulated tournament data."""

from pathlib import Path
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402

from tournament_sim.counterfactuals import add_counterfactual_columns
from tournament_sim.probabilities import theoretical_reveal_cutoff


def load_and_prepare_data(path_or_df):
    """Load player-round records and add derived analysis variables."""
    if isinstance(path_or_df, pd.DataFrame):
        df = path_or_df.copy()
    else:
        df = pd.read_csv(path_or_df)
    return add_derived_variables(df)


def add_derived_variables(df):
    """Add binary indicators, cutoff variables, bins, and test helpers."""
    df = df.copy()
    bool_columns = [
        "reveal_decision",
        "opponent_reveal_decision",
        "improve_decision_if_applicable",
        "won",
        "paid_improvement_cost",
        "eligible_for_hype",
        "hype_paid",
    ]
    for column in bool_columns:
        if column in df.columns:
            df[column] = df[column].map(_to_bool_or_missing)

    df["revealed"] = df["reveal_decision"].astype(int)
    df["opponent_revealed"] = df["opponent_reveal_decision"].astype(int)
    df["eligible_to_improve"] = (df["revealed"] == 0).astype(int)
    df["improved"] = df["improve_decision_if_applicable"].fillna(False).astype(int)
    df["high_cost"] = (df["k"] > df["k"].median()).astype(int)
    df["hype_treatment"] = (df["h"] > 0).astype(int)
    df["opponent_revealed_quality"] = df["opponent_revealed_quality_if_observed"]
    df["opponent_revealed_quality_norm"] = df["opponent_revealed_quality"] / 100
    df["r_star"] = df["k"].apply(theoretical_reveal_cutoff)
    df["predicted_reveal"] = (df["q_norm"] >= df["r_star"]).astype(int)
    df["distance_to_reveal_cutoff"] = df["q_norm"] - df["r_star"]
    df["correct_reveal_action"] = (df["revealed"] == df["predicted_reveal"]).astype(int)
    df["reveal_deviation"] = df["revealed"] - df["predicted_reveal"]
    df["under_reveal_mistake"] = ((df["revealed"] == 0) & (df["predicted_reveal"] == 1)).astype(int)
    df["over_reveal_mistake"] = ((df["revealed"] == 1) & (df["predicted_reveal"] == 0)).astype(int)
    df["q_bin"] = pd.cut(df["q_norm"], bins=[i / 10 for i in range(11)], include_lowest=True)
    df["opponent_revealed_quality_bin"] = pd.cut(
        df["opponent_revealed_quality_norm"],
        bins=[i / 10 for i in range(11)],
        include_lowest=True,
    )
    df["distance_bin"] = pd.cut(
        df["distance_to_reveal_cutoff"],
        bins=[-1.0, -0.5, -0.25, -0.1, 0.0, 0.1, 0.25, 0.5, 1.0],
        include_lowest=True,
    )
    df["revealed_label"] = df["revealed"].map({0: "Hide", 1: "Reveal"})
    return df


def run_lpm(formula, df, cluster_col="subject_id"):
    """Run OLS/LPM with clustered standard errors by subject."""
    return smf.ols(formula, data=df).fit(
        cov_type="cluster",
        cov_kwds={"groups": df[cluster_col]},
    )


def run_logit(formula, df):
    """Run logit if possible; return None if separation or convergence fails."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return smf.logit(formula, data=df).fit(disp=False, maxiter=200)
    except Exception as exc:
        warnings.warn("Skipping logit for formula '" + formula + "': " + str(exc))
        return None


def test_quality_dependent_reveal(df):
    return {
        "lpm_simple": run_lpm("revealed ~ q_norm", df),
        "lpm_rich": run_lpm(
            "revealed ~ q_norm + high_cost + hype_treatment + q_norm:high_cost + q_norm:hype_treatment",
            df,
        ),
        "lpm_player_type_interactions": run_lpm(
            "revealed ~ q_norm * C(player_type) + high_cost + hype_treatment",
            df,
        ),
        "logit_simple": run_logit("revealed ~ q_norm", df),
    }


def test_cost_effect(df):
    return {
        "lpm_high_cost": run_lpm("revealed ~ high_cost + q_norm + hype_treatment", df),
        "lpm_k": run_lpm("revealed ~ k + q_norm + hype_treatment", df),
        "lpm_high_cost_player_type": run_lpm(
            "revealed ~ high_cost * C(player_type) + q_norm + hype_treatment",
            df,
        ),
        "logit_high_cost": run_logit("revealed ~ high_cost + q_norm + hype_treatment", df),
    }


def test_hype_effect(df):
    return {
        "lpm_hype": run_lpm("revealed ~ hype_treatment + q_norm + k", df),
        "lpm_hype_interaction": run_lpm(
            "revealed ~ hype_treatment + q_norm + k + hype_treatment:q_norm",
            df,
        ),
        "lpm_hype_player_type": run_lpm(
            "revealed ~ hype_treatment * C(player_type) + q_norm + k",
            df,
        ),
        "logit_hype": run_logit("revealed ~ hype_treatment + q_norm + k", df),
    }


def test_deterrence(df):
    sample = df[(df["eligible_to_improve"] == 1) & (df["opponent_revealed"] == 1)].copy()
    sample = sample.dropna(subset=["opponent_revealed_quality_norm"])
    return {
        "sample_n": len(sample),
        "lpm_deterrence": run_lpm(
            "improved ~ opponent_revealed_quality_norm + q_norm + k + hype_treatment",
            sample,
        ),
        "lpm_deterrence_player_type": run_lpm(
            "improved ~ opponent_revealed_quality_norm * C(player_type) + q_norm + k + hype_treatment",
            sample,
        ),
        "logit_deterrence": run_logit(
            "improved ~ opponent_revealed_quality_norm + q_norm + k + hype_treatment",
            sample,
        ),
        "low_medium_high": _low_medium_high_deterrence(sample),
    }


def test_equilibrium_compliance(df):
    return {
        "overall_accuracy": pd.DataFrame([{"overall_accuracy": df["correct_reveal_action"].mean()}]),
        "by_treatment": _equilibrium_compliance_table(df, ["treatment_id"]),
        "by_treatment_type": _equilibrium_compliance_table(df, ["treatment_id", "player_type"]),
        "confusion_matrix": pd.crosstab(
            df["predicted_reveal"],
            df["revealed"],
            rownames=["predicted_reveal"],
            colnames=["actual_revealed"],
        ).reset_index(),
        "empirical_cutoffs": _empirical_cutoffs_by_treatment(df),
    }


def test_under_over_reveal(df):
    return {
        "lpm_deviation": run_lpm("reveal_deviation ~ hype_treatment + k + q_norm", df),
        "by_treatment": df.groupby("treatment_id", observed=True)
        .agg(
            n=("reveal_deviation", "size"),
            mean_reveal_deviation=("reveal_deviation", "mean"),
            under_reveal_rate=("under_reveal_mistake", "mean"),
            over_reveal_rate=("over_reveal_mistake", "mean"),
        )
        .reset_index(),
    }


def test_payoff_effect(df):
    return {
        "lpm_payoff": run_lpm(
            "payoff ~ revealed + q_norm + k + hype_treatment + round + C(player_type)",
            df,
        ),
        "payoff_by_reveal_quality_bin": df.groupby(["q_bin", "revealed_label"], observed=True)
        .agg(n=("payoff", "size"), average_payoff=("payoff", "mean"))
        .reset_index(),
    }


def test_counterfactual_reveal_gain(df):
    """Analyze ex-post counterfactual gain from reveal vs best hidden action."""
    cf_df = add_counterfactual_columns(df)
    return {
        "overall": pd.DataFrame(
            [
                {
                    "n": len(cf_df),
                    "mean_cf_reveal_gain_vs_best_hide": cf_df["cf_reveal_gain_vs_best_hide"].mean(),
                    "correlation_actual_reveal_cf_gain": cf_df["revealed"].corr(
                        cf_df["cf_reveal_gain_vs_best_hide"]
                    ),
                    "prob_action_matches_cf_gain": cf_df["actual_reveal_matches_cf_gain"].mean(),
                }
            ]
        ),
        "by_treatment": cf_df.groupby("treatment_id", observed=True)
        .agg(
            n=("cf_reveal_gain_vs_best_hide", "size"),
            mean_cf_reveal_gain_vs_best_hide=("cf_reveal_gain_vs_best_hide", "mean"),
            prob_action_matches_cf_gain=("actual_reveal_matches_cf_gain", "mean"),
        )
        .reset_index(),
        "by_quality_bin": cf_df.groupby("q_bin", observed=True)
        .agg(
            n=("cf_reveal_gain_vs_best_hide", "size"),
            mean_cf_reveal_gain_vs_best_hide=("cf_reveal_gain_vs_best_hide", "mean"),
        )
        .reset_index(),
        "by_player_type": cf_df.groupby("player_type", observed=True)
        .agg(
            n=("cf_reveal_gain_vs_best_hide", "size"),
            mean_cf_reveal_gain_vs_best_hide=("cf_reveal_gain_vs_best_hide", "mean"),
            prob_action_matches_cf_gain=("actual_reveal_matches_cf_gain", "mean"),
        )
        .reset_index(),
    }


def make_descriptive_tables(df):
    deterrence_sample = df[(df["eligible_to_improve"] == 1) & (df["opponent_revealed"] == 1)].copy()
    return {
        "treatment_summary": df.groupby("treatment_id", observed=True)
        .agg(
            n=("revealed", "size"),
            reveal_rate=("revealed", "mean"),
            improve_rate=("improved", "mean"),
            win_rate=("won", "mean"),
            average_payoff=("payoff", "mean"),
            average_initial_quality=("initial_quality", "mean"),
            average_final_quality=("final_quality", "mean"),
        )
        .reset_index(),
        "treatment_by_player_type_summary": df.groupby(["treatment_id", "player_type"], observed=True)
        .agg(
            n=("revealed", "size"),
            reveal_rate=("revealed", "mean"),
            improve_rate=("improved", "mean"),
            win_rate=("won", "mean"),
            average_payoff=("payoff", "mean"),
            average_initial_quality=("initial_quality", "mean"),
            average_final_quality=("final_quality", "mean"),
        )
        .reset_index(),
        "quality_bin_summary": df.groupby(["treatment_id", "q_bin"], observed=True)
        .agg(
            count=("revealed", "size"),
            reveal_rate=("revealed", "mean"),
            improve_rate=("improved", "mean"),
            win_rate=("won", "mean"),
            average_payoff=("payoff", "mean"),
        )
        .reset_index(),
        "deterrence_by_opponent_quality_bin": deterrence_sample.groupby(
            ["opponent_revealed_quality_bin"],
            observed=True,
        )
        .agg(count=("improved", "size"), improvement_rate=("improved", "mean"))
        .reset_index(),
        "deterrence_by_own_quality_bin": deterrence_sample.groupby(["q_bin"], observed=True)
        .agg(count=("improved", "size"), improvement_rate=("improved", "mean"))
        .reset_index(),
        "deterrence_by_treatment": deterrence_sample.groupby("treatment_id", observed=True)
        .agg(count=("improved", "size"), improvement_rate=("improved", "mean"))
        .reset_index(),
        "equilibrium_compliance_by_treatment_type": _equilibrium_compliance_table(
            df,
            ["treatment_id", "player_type"],
        ),
    }


def make_plots(df, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        _plot_reveal_rate_by_quality_bin(df, output_dir / "reveal_rate_by_quality_bin.png"),
        _plot_reveal_rate_by_quality_bin_by_treatment(
            df,
            output_dir / "reveal_rate_by_quality_bin_by_treatment.png",
        ),
        _plot_reveal_rate_by_cost(df, output_dir / "reveal_rate_by_cost_treatment.png"),
        _plot_reveal_rate_by_hype(df, output_dir / "reveal_rate_by_hype_treatment.png"),
        _plot_improve_rate_by_opponent_quality(
            df,
            output_dir / "improve_rate_by_opponent_revealed_quality.png",
        ),
        _plot_reveal_probability_vs_distance(
            df,
            output_dir / "reveal_probability_vs_distance_to_cutoff.png",
        ),
        _plot_under_over(df, output_dir / "under_over_reveal_by_treatment.png"),
        _plot_payoff_by_quality_bin_and_reveal(
            df,
            output_dir / "payoff_by_quality_bin_and_reveal.png",
        ),
        _plot_cf_reveal_gain_by_quality_bin(
            add_counterfactual_columns(df),
            output_dir / "cf_reveal_gain_by_quality_bin.png",
        ),
    ]
    return paths


def run_all_tests(df, output_dir):
    df = add_derived_variables(df)
    output_dir = Path(output_dir)
    regression_dir = output_dir / "regression_summaries"
    coefficient_dir = output_dir / "coefficient_tables"
    descriptive_dir = output_dir / "descriptive_tables"
    plot_dir = output_dir / "plots"
    regression_dir.mkdir(parents=True, exist_ok=True)
    coefficient_dir.mkdir(parents=True, exist_ok=True)
    descriptive_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "quality_dependent_reveal": test_quality_dependent_reveal(df),
        "cost_effect": test_cost_effect(df),
        "hype_effect": test_hype_effect(df),
        "deterrence": test_deterrence(df),
        "equilibrium_compliance": test_equilibrium_compliance(df),
        "under_over_reveal": test_under_over_reveal(df),
        "payoff_effect": test_payoff_effect(df),
        "counterfactual_reveal_gain": test_counterfactual_reveal_gain(df),
    }
    results["descriptive_tables"] = make_descriptive_tables(df)
    results["plots"] = make_plots(df, plot_dir)
    _save_results(results, regression_dir, coefficient_dir, descriptive_dir)
    return results


def _save_results(results, regression_dir, coefficient_dir, descriptive_dir):
    for test_name, test_results in results.items():
        if test_name in ["descriptive_tables", "plots"]:
            continue
        for result_name, result in test_results.items():
            base_name = test_name + "__" + result_name
            if result is None:
                continue
            if hasattr(result, "summary"):
                (regression_dir / (base_name + ".txt")).write_text(
                    result.summary().as_text(),
                    encoding="utf-8",
                )
                _coefficient_table(result).to_csv(coefficient_dir / (base_name + ".csv"), index=False)
            elif isinstance(result, pd.DataFrame):
                result.to_csv(descriptive_dir / (base_name + ".csv"), index=False)
    for table_name, table in results["descriptive_tables"].items():
        table.to_csv(descriptive_dir / (table_name + ".csv"), index=False)


def _coefficient_table(model):
    return pd.DataFrame(
        {
            "term": model.params.index,
            "coef": model.params.values,
            "std_error": model.bse.values,
            "p_value": model.pvalues.values,
        }
    )


def _low_medium_high_deterrence(sample):
    sample = sample.copy()
    sample["opponent_quality_group"] = pd.cut(
        sample["opponent_revealed_quality_norm"],
        bins=[0, 1 / 3, 2 / 3, 1],
        labels=["low", "medium", "high"],
        include_lowest=True,
    )
    return sample.groupby("opponent_quality_group", observed=True).agg(
        count=("improved", "size"),
        improvement_rate=("improved", "mean"),
    ).reset_index()


def _equilibrium_compliance_table(df, group_cols):
    return df.groupby(group_cols, observed=True).agg(
        n=("revealed", "size"),
        actual_reveal_rate=("revealed", "mean"),
        predicted_reveal_rate=("predicted_reveal", "mean"),
        accuracy=("correct_reveal_action", "mean"),
        under_reveal_rate=("under_reveal_mistake", "mean"),
        over_reveal_rate=("over_reveal_mistake", "mean"),
        mean_reveal_deviation=("reveal_deviation", "mean"),
    ).reset_index()


def _empirical_cutoffs_by_treatment(df):
    rows = []
    for treatment_id, group in df.groupby("treatment_id", observed=True):
        lpm_model = run_lpm("revealed ~ q_norm", group)
        lpm_alpha = lpm_model.params.get("Intercept")
        lpm_beta = lpm_model.params.get("q_norm")
        lpm_q50 = None
        if lpm_beta is not None and lpm_beta != 0:
            lpm_q50 = (0.5 - lpm_alpha) / lpm_beta

        logit_model = run_logit("revealed ~ q_norm", group)
        logit_q50 = None
        if logit_model is not None:
            logit_alpha = logit_model.params.get("Intercept")
            logit_beta = logit_model.params.get("q_norm")
            if logit_beta is not None and logit_beta != 0:
                logit_q50 = -logit_alpha / logit_beta

        preferred_method = None
        preferred_q50 = None
        if logit_q50 is not None and 0 <= logit_q50 <= 1:
            preferred_method = "logit"
            preferred_q50 = logit_q50
        elif lpm_q50 is not None and 0 <= lpm_q50 <= 1:
            preferred_method = "lpm"
            preferred_q50 = lpm_q50

        rows.append(
            {
                "treatment_id": treatment_id,
                "r_star_mean": group["r_star"].mean(),
                "empirical_q50_lpm": lpm_q50,
                "lpm_q50_out_of_bounds": not (lpm_q50 is not None and 0 <= lpm_q50 <= 1),
                "difference_lpm_minus_theory": None if lpm_q50 is None else lpm_q50 - group["r_star"].mean(),
                "empirical_q50_logit": logit_q50,
                "logit_q50_out_of_bounds": not (logit_q50 is not None and 0 <= logit_q50 <= 1),
                "difference_logit_minus_theory": None if logit_q50 is None else logit_q50 - group["r_star"].mean(),
                "preferred_empirical_q50": preferred_q50,
                "preferred_method": preferred_method,
            }
        )
    return pd.DataFrame(rows)


def _plot_reveal_rate_by_quality_bin(df, path):
    plot_df = df.groupby("q_bin", observed=True).agg(reveal_rate=("revealed", "mean")).reset_index()
    return _line_plot(plot_df, "q_bin", "reveal_rate", path, "Reveal Rate by Quality Bin")


def _plot_reveal_rate_by_quality_bin_by_treatment(df, path):
    plot_df = df.groupby(["treatment_id", "q_bin"], observed=True).agg(
        reveal_rate=("revealed", "mean")
    ).reset_index()
    return _multi_line_plot(plot_df, "q_bin", "reveal_rate", "treatment_id", path, "Reveal Rate by Quality Bin and Treatment")


def _plot_reveal_rate_by_cost(df, path):
    plot_df = df.groupby("high_cost", observed=True).agg(reveal_rate=("revealed", "mean")).reset_index()
    plot_df["high_cost"] = plot_df["high_cost"].map({0: "Low cost", 1: "High cost"})
    return _bar_plot(plot_df, "high_cost", "reveal_rate", path, "Reveal Rate by Cost Treatment")


def _plot_reveal_rate_by_hype(df, path):
    plot_df = df.groupby("hype_treatment", observed=True).agg(reveal_rate=("revealed", "mean")).reset_index()
    plot_df["hype_treatment"] = plot_df["hype_treatment"].map({0: "No hype", 1: "Hype"})
    return _bar_plot(plot_df, "hype_treatment", "reveal_rate", path, "Reveal Rate by Hype Treatment")


def _plot_improve_rate_by_opponent_quality(df, path):
    sample = df[(df["eligible_to_improve"] == 1) & (df["opponent_revealed"] == 1)].copy()
    plot_df = sample.groupby("opponent_revealed_quality_bin", observed=True).agg(
        count=("improved", "size"),
        improvement_rate=("improved", "mean"),
    ).reset_index()
    plot_df = plot_df[plot_df["count"] >= 20]
    return _line_plot(plot_df, "opponent_revealed_quality_bin", "improvement_rate", path, "Improvement Rate by Opponent Revealed Quality")


def _plot_reveal_probability_vs_distance(df, path):
    plot_df = df.groupby("distance_bin", observed=True).agg(reveal_rate=("revealed", "mean")).reset_index()
    return _line_plot(plot_df, "distance_bin", "reveal_rate", path, "Reveal Probability vs Distance to Cutoff")


def _plot_under_over(df, path):
    plot_df = df.groupby("treatment_id", observed=True).agg(
        under_reveal_rate=("under_reveal_mistake", "mean"),
        over_reveal_rate=("over_reveal_mistake", "mean"),
    ).reset_index()
    fig, ax = plt.subplots(figsize=(10, 6))
    x_values = range(len(plot_df))
    width = 0.38
    ax.bar([x - width / 2 for x in x_values], plot_df["under_reveal_rate"], width, label="Under-reveal")
    ax.bar([x + width / 2 for x in x_values], plot_df["over_reveal_rate"], width, label="Over-reveal")
    ax.set_xticks(list(x_values))
    ax.set_xticklabels(plot_df["treatment_id"], rotation=20, ha="right")
    ax.set_ylabel("Rate")
    ax.set_title("Under- and Over-Reveal Rates by Treatment")
    ax.legend(frameon=False)
    ax.grid(True, axis="y", alpha=0.25)
    return _save_plot(fig, path)


def _plot_payoff_by_quality_bin_and_reveal(df, path):
    plot_df = df.groupby(["q_bin", "revealed_label"], observed=True).agg(
        average_payoff=("payoff", "mean")
    ).reset_index()
    return _multi_line_plot(plot_df, "q_bin", "average_payoff", "revealed_label", path, "Average Payoff by Quality Bin and Reveal Action")


def _plot_cf_reveal_gain_by_quality_bin(df, path):
    plot_df = df.groupby("q_bin", observed=True).agg(
        mean_cf_reveal_gain=("cf_reveal_gain_vs_best_hide", "mean")
    ).reset_index()
    return _line_plot(
        plot_df,
        "q_bin",
        "mean_cf_reveal_gain",
        path,
        "Counterfactual Reveal Gain by Quality Bin",
    )


def _line_plot(plot_df, x_col, y_col, path, title):
    fig, ax = plt.subplots(figsize=(10, 6))
    x_values = [str(value) for value in plot_df[x_col]]
    ax.plot(x_values, plot_df[y_col], marker="o", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(True, alpha=0.25)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    return _save_plot(fig, path)


def _multi_line_plot(plot_df, x_col, y_col, group_col, path, title):
    fig, ax = plt.subplots(figsize=(11, 6))
    for group_value, group in plot_df.groupby(group_col, observed=True):
        x_values = [str(value) for value in group[x_col]]
        ax.plot(x_values, group[y_col], marker="o", linewidth=2, label=str(group_value))
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    return _save_plot(fig, path)


def _bar_plot(plot_df, x_col, y_col, path, title):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(plot_df[x_col].astype(str), plot_df[y_col], color="#356AA0")
    ax.set_title(title)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_ylim(0, max(1, plot_df[y_col].max() * 1.15))
    ax.grid(True, axis="y", alpha=0.25)
    return _save_plot(fig, path)


def _save_plot(fig, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _to_bool_or_missing(value):
    if pd.isna(value):
        return pd.NA
    if value in [True, "True", "true", 1, "1"]:
        return True
    if value in [False, "False", "false", 0, "0"]:
        return False
    return pd.NA

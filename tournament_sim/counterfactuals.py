"""Counterfactual payoff calculations for player-round records."""

import pandas as pd

from tournament_sim.probabilities import improve_win_probability, stop_win_probability


def counterfactual_payoffs_for_record(record):
    """
    Compute ex-post counterfactual expected payoffs against observed opponent final quality.

    These counterfactuals are simulation diagnostics. They use the realized
    opponent final quality as the target and compare reveal, hide-stop, and
    hide-improve actions for the focal player's initial quality.
    """
    q = int(record["initial_quality"])
    opponent_final = int(record.get("opponent_final_quality", record.get("final_quality", q)))
    V = float(record["V"])
    c = float(record["c"])
    h = float(record["h"])
    quality_max = 100

    reveal_win_prob = stop_win_probability(q, opponent_final)
    hide_stop_win_prob = stop_win_probability(q, opponent_final)
    hide_improve_win_prob = improve_win_probability(q, opponent_final, quality_max)

    cf_payoff_if_reveal = reveal_win_prob * (V + h)
    cf_payoff_if_hide_stop = hide_stop_win_prob * V
    cf_payoff_if_hide_improve = hide_improve_win_prob * V - c
    cf_payoff_if_best_hide = max(cf_payoff_if_hide_stop, cf_payoff_if_hide_improve)

    return {
        "cf_payoff_if_reveal": cf_payoff_if_reveal,
        "cf_payoff_if_hide_stop": cf_payoff_if_hide_stop,
        "cf_payoff_if_hide_improve": cf_payoff_if_hide_improve,
        "cf_payoff_if_best_hide": cf_payoff_if_best_hide,
        "cf_reveal_gain_vs_best_hide": cf_payoff_if_reveal - cf_payoff_if_best_hide,
    }


def add_counterfactual_columns(df):
    """Add counterfactual payoff columns to a prepared or raw player-record DataFrame."""
    df = df.copy()

    if "opponent_final_quality" not in df.columns:
        df["opponent_final_quality"] = _infer_opponent_final_quality(df)

    rows = []
    for _, record in df.iterrows():
        rows.append(counterfactual_payoffs_for_record(record))

    cf_df = pd.DataFrame(rows, index=df.index)
    for column in cf_df.columns:
        df[column] = cf_df[column]

    df["actual_reveal_matches_cf_gain"] = (
        ((df["cf_reveal_gain_vs_best_hide"] >= 0) & (df["revealed"] == 1))
        | ((df["cf_reveal_gain_vs_best_hide"] < 0) & (df["revealed"] == 0))
    ).astype(int)
    return df


def _infer_opponent_final_quality(df):
    if "match_id" not in df.columns:
        return pd.NA

    opponent_final = {}
    for _, group in df.groupby("match_id"):
        if len(group) != 2:
            continue
        index_1, index_2 = group.index.tolist()
        opponent_final[index_1] = group.loc[index_2, "final_quality"]
        opponent_final[index_2] = group.loc[index_1, "final_quality"]

    return df.index.to_series().map(opponent_final)

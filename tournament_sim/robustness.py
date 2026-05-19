"""Robustness helpers for seeds and population compositions."""

from pathlib import Path

import pandas as pd

from tournament_sim.analysis import add_derived_variables, test_cost_effect, test_deterrence
from tournament_sim.experiment import simulate_experiment
from tournament_sim.export import export_rows_csv
from tournament_sim.summary import treatment_comparison_summary


DEFAULT_POPULATION = {
    "EquilibriumAgent": 0.40,
    "NoisyEquilibriumAgent": 0.20,
    "UnderRevealerAgent": 0.15,
    "OverRevealerAgent": 0.15,
    "MyopicHeuristicAgent": 0.10,
}


def run_seed_robustness(
    seeds,
    output_dir,
    num_subjects=200,
    num_rounds=100,
    population_composition=None,
):
    """Run the same design across multiple random seeds and export summaries."""
    if population_composition is None:
        population_composition = DEFAULT_POPULATION

    treatment_rows = []
    coefficient_rows = []

    for seed in seeds:
        result = simulate_experiment(
            num_subjects=num_subjects,
            num_rounds=num_rounds,
            population_composition=population_composition,
            rng_seed=seed,
        )
        for row in treatment_comparison_summary(result.player_records):
            copied = dict(row)
            copied["seed"] = seed
            treatment_rows.append(copied)

        df = add_derived_variables(pd.DataFrame(result.player_records))
        coefficient_rows.extend(_key_coefficients(df, seed=seed, scenario="seed_robustness"))

    output_dir = Path(output_dir)
    paths = [
        export_rows_csv(treatment_rows, output_dir / "seed_level_treatment_summary.csv"),
        export_rows_csv(coefficient_rows, output_dir / "seed_level_key_coefficients.csv"),
    ]
    return {"treatment_summary": treatment_rows, "key_coefficients": coefficient_rows, "paths": paths}


def run_population_robustness(
    scenarios,
    output_dir,
    num_subjects=200,
    num_rounds=100,
    rng_seed=12345,
):
    """Run several population compositions and export comparison summaries."""
    treatment_rows = []
    coefficient_rows = []

    for scenario_name, composition in scenarios.items():
        result = simulate_experiment(
            num_subjects=num_subjects,
            num_rounds=num_rounds,
            population_composition=composition,
            rng_seed=rng_seed,
        )
        for row in treatment_comparison_summary(result.player_records):
            copied = dict(row)
            copied["scenario"] = scenario_name
            treatment_rows.append(copied)

        df = add_derived_variables(pd.DataFrame(result.player_records))
        coefficient_rows.extend(_key_coefficients(df, seed=rng_seed, scenario=scenario_name))

    output_dir = Path(output_dir)
    paths = [
        export_rows_csv(treatment_rows, output_dir / "population_treatment_summary.csv"),
        export_rows_csv(coefficient_rows, output_dir / "population_key_coefficients.csv"),
    ]
    return {"treatment_summary": treatment_rows, "key_coefficients": coefficient_rows, "paths": paths}


def _key_coefficients(df, seed, scenario):
    rows = []
    models = {
        "cost_high_cost": test_cost_effect(df)["lpm_high_cost"],
        "deterrence": test_deterrence(df)["lpm_deterrence"],
    }
    terms = {
        "cost_high_cost": "high_cost",
        "deterrence": "opponent_revealed_quality_norm",
    }

    for model_name, model in models.items():
        term = terms[model_name]
        rows.append(
            {
                "scenario": scenario,
                "seed": seed,
                "model": model_name,
                "term": term,
                "coef": model.params[term],
                "std_error": model.bse[term],
                "p_value": model.pvalues[term],
                "nobs": model.nobs,
            }
        )
    return rows

"""Small example script for the current project stage."""

from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.agents import (
    AlwaysHideStopAgent,
    AlwaysRevealAgent,
    EquilibriumAgent,
)
from tournament_sim.experiment import simulate_experiment
from tournament_sim.probabilities import (
    theoretical_hidden_cutoff,
    theoretical_reveal_cutoff,
)
from tournament_sim.round import simulate_round
from tournament_sim.treatment import default_treatments


def main():
    treatments = default_treatments()

    print("Default treatment cutoffs")
    print("-------------------------")
    for treatment in treatments:
        r_star = theoretical_reveal_cutoff(treatment.k)
        s_star = theoretical_hidden_cutoff(treatment.k)
        print(
            treatment.treatment_id,
            "k=",
            round(treatment.k, 3),
            "r*=",
            round(r_star, 4),
            "s*=",
            round(s_star, 4),
        )

    print()
    print("One example round")
    print("-----------------")
    treatment = treatments[2]
    result = simulate_round(
        AlwaysRevealAgent(),
        AlwaysHideStopAgent(),
        treatment,
        rng=random.Random(123),
        round_number=1,
        subject_ids=(1, 2),
        forced_qualities=(80, 70),
    )

    for player_record in result.player_records:
        print(player_record)

    print("Match:", result.match_record)

    print()
    print("EquilibriumAgent decisions")
    print("--------------------------")
    agent = EquilibriumAgent()
    treatment = treatments[0]
    for q in [28, 29, 85, 86]:
        print(
            "q=",
            q,
            "reveal=",
            agent.decide_reveal(q, treatment),
            "improve_if_both_hide=",
            agent.decide_improve(q, treatment, False, None),
        )

    print()
    print("One EquilibriumAgent round per treatment")
    print("----------------------------------------")
    for index, treatment in enumerate(treatments, start=1):
        result = simulate_round(
            EquilibriumAgent(),
            EquilibriumAgent(),
            treatment,
            rng=random.Random(100 + index),
            round_number=index,
            subject_ids=(1, 2),
            forced_qualities=(86, 70),
        )
        print(
            treatment.treatment_id,
            "winner=",
            result.match_record["winner"],
            "payoffs=",
            [record["payoff"] for record in result.player_records],
            "reveals=",
            [record["reveal_decision"] for record in result.player_records],
        )

    print()
    print("Small experiment simulation")
    print("---------------------------")
    experiment = simulate_experiment(
        num_subjects=40,
        num_rounds=5,
        population_composition={
            "EquilibriumAgent": 0.7,
            "AlwaysRevealAgent": 0.3,
        },
        rng_seed=123,
    )
    print("subjects=", len(experiment.subjects))
    print("matches=", len(experiment.match_records))
    print("player_records=", len(experiment.player_records))
    print("first_player_record=", experiment.player_records[0])


if __name__ == "__main__":
    main()

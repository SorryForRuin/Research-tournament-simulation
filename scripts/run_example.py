"""Small example script for the current project stage."""

import random

from tournament_sim.agents import AlwaysHideStopAgent, AlwaysRevealAgent
from tournament_sim.probabilities import (
    theoretical_hidden_cutoff,
    theoretical_reveal_cutoff,
)
from tournament_sim.round import simulate_round
from tournament_sim.treatment import default_treatments


def main():
    print("Default treatment cutoffs")
    print("-------------------------")
    for treatment in default_treatments():
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
    treatment = default_treatments()[2]
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


if __name__ == "__main__":
    main()

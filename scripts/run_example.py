"""Small placeholder script.

The real example simulation will be added after the one-round simulator exists.
For now this script prints the default treatments and theoretical cutoffs.
"""

from tournament_sim.probabilities import (
    theoretical_hidden_cutoff,
    theoretical_reveal_cutoff,
)
from tournament_sim.treatment import default_treatments


def main():
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


if __name__ == "__main__":
    main()

"""Small tests for treatment definitions.

Run with:
    python tests/test_treatments.py
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.agents import EquilibriumAgent  # noqa: E402
from tournament_sim.treatment import default_treatments  # noqa: E402


def test_default_treatments_have_expected_parameters():
    treatments = default_treatments()

    assert len(treatments) == 4
    assert treatments[0].treatment_id == "baseline_low_cost"
    assert treatments[0].V == 100
    assert treatments[0].c == 20
    assert treatments[0].h == 0

    assert treatments[1].treatment_id == "baseline_high_cost"
    assert treatments[1].V == 100
    assert treatments[1].c == 30
    assert treatments[1].h == 0

    assert treatments[2].treatment_id == "hype_low_cost"
    assert treatments[2].V == 100
    assert treatments[2].c == 20
    assert treatments[2].h == 20

    assert treatments[3].treatment_id == "hype_high_cost"
    assert treatments[3].V == 100
    assert treatments[3].c == 30
    assert treatments[3].h == 20


def test_custom_hype_bonus_is_easy_to_change():
    treatments = default_treatments(hype_bonus=35)

    assert treatments[2].h == 35
    assert treatments[3].h == 35


def test_equilibrium_cutoffs_ignore_hype_for_now():
    agent = EquilibriumAgent()
    treatments = default_treatments()

    baseline_low = treatments[0]
    hype_low = treatments[2]
    baseline_high = treatments[1]
    hype_high = treatments[3]

    assert agent.reveal_cutoff(baseline_low) == agent.reveal_cutoff(hype_low)
    assert agent.hidden_cutoff(baseline_low) == agent.hidden_cutoff(hype_low)
    assert agent.reveal_cutoff(baseline_high) == agent.reveal_cutoff(hype_high)
    assert agent.hidden_cutoff(baseline_high) == agent.hidden_cutoff(hype_high)


if __name__ == "__main__":
    test_default_treatments_have_expected_parameters()
    test_custom_hype_bonus_is_easy_to_change()
    test_equilibrium_cutoffs_ignore_hype_for_now()
    print("All treatment tests passed.")

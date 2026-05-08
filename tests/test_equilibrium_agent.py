"""Small tests for the benchmark EquilibriumAgent.

Run with:
    python tests/test_equilibrium_agent.py
"""

from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.agents import EquilibriumAgent  # noqa: E402
from tournament_sim.round import simulate_round  # noqa: E402
from tournament_sim.treatment import Treatment  # noqa: E402


def test_reveal_decision_uses_theoretical_cutoff():
    agent = EquilibriumAgent()
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)

    # For k=0.20, r* is about 0.8571.
    assert not agent.decide_reveal(85, treatment)
    assert agent.decide_reveal(86, treatment)


def test_both_hidden_improvement_uses_hidden_cutoff():
    agent = EquilibriumAgent()
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)

    # For k=0.20, s* is about 0.2857.
    assert not agent.decide_improve(
        28,
        treatment,
        observed_opponent_reveal=False,
        observed_quality_if_any=None,
    )
    assert agent.decide_improve(
        29,
        treatment,
        observed_opponent_reveal=False,
        observed_quality_if_any=None,
    )


def test_revealed_opponent_uses_payoff_comparison():
    agent = EquilibriumAgent()
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)

    # From 90 against revealed 95:
    # improve win probability is 5.5 / 11 = 0.5.
    # improve payoff is 100 * 0.5 - 20 = 30.
    # stop payoff is 0, so the agent improves.
    assert agent.decide_improve(
        90,
        treatment,
        observed_opponent_reveal=True,
        observed_quality_if_any=95,
    )

    # If already ahead, stopping wins for sure. Paying to improve is wasteful.
    assert not agent.decide_improve(
        90,
        treatment,
        observed_opponent_reveal=True,
        observed_quality_if_any=80,
    )


def test_round_with_equilibrium_agents_runs():
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)
    result = simulate_round(
        EquilibriumAgent(),
        EquilibriumAgent(),
        treatment,
        rng=random.Random(123),
        forced_qualities=(86, 28),
    )

    player_1 = result.player_records[0]
    player_2 = result.player_records[1]

    assert player_1["player_type"] == "EquilibriumAgent"
    assert player_1["reveal_decision"]
    assert not player_1["paid_improvement_cost"]

    assert player_2["player_type"] == "EquilibriumAgent"
    assert not player_2["reveal_decision"]
    assert player_2["opponent_revealed_quality_if_observed"] == 86


if __name__ == "__main__":
    test_reveal_decision_uses_theoretical_cutoff()
    test_both_hidden_improvement_uses_hidden_cutoff()
    test_revealed_opponent_uses_payoff_comparison()
    test_round_with_equilibrium_agents_runs()
    print("All equilibrium agent tests passed.")

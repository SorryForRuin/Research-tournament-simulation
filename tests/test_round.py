"""Small dependency-free tests for one-round simulation.

Run with:
    python tests/test_round.py
"""

from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.agents import (  # noqa: E402
    AlwaysHideImproveAgent,
    AlwaysHideStopAgent,
    AlwaysRevealAgent,
)
from tournament_sim.round import simulate_round  # noqa: E402
from tournament_sim.treatment import Treatment  # noqa: E402


class SpyHideStopAgent(AlwaysHideStopAgent):
    """Test helper that records what it saw before deciding whether to improve."""

    agent_type = "SpyHideStopAgent"

    def __init__(self):
        self.last_observed_opponent_reveal = None
        self.last_observed_quality = None

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        self.last_observed_opponent_reveal = observed_opponent_reveal
        self.last_observed_quality = observed_quality_if_any
        return False


def test_reveal_locks_quality_and_hype_is_winner_contingent():
    treatment = Treatment("hype_test", V=100, c=20, h=20)
    result = simulate_round(
        AlwaysRevealAgent(),
        AlwaysHideStopAgent(),
        treatment,
        rng=random.Random(1),
        forced_qualities=(80, 70),
    )

    player_1 = result.player_records[0]
    player_2 = result.player_records[1]

    assert player_1["reveal_decision"]
    assert player_1["final_quality"] == 80
    assert player_1["won"]
    assert player_1["payoff"] == 120
    assert player_1["hype_paid"]

    assert not player_2["reveal_decision"]
    assert not player_2["won"]
    assert player_2["payoff"] == 0
    assert not player_2["hype_paid"]


def test_hidden_winner_gets_no_hype():
    treatment = Treatment("hype_test", V=100, c=20, h=20)
    result = simulate_round(
        AlwaysRevealAgent(),
        AlwaysHideStopAgent(),
        treatment,
        rng=random.Random(1),
        forced_qualities=(70, 80),
    )

    player_1 = result.player_records[0]
    player_2 = result.player_records[1]

    assert not player_1["won"]
    assert player_1["payoff"] == 0
    assert not player_1["hype_paid"]

    assert player_2["won"]
    assert player_2["payoff"] == 100
    assert not player_2["hype_paid"]


def test_improvement_cost_is_paid_even_when_losing():
    treatment = Treatment("cost_test", V=100, c=20, h=0)
    result = simulate_round(
        AlwaysHideImproveAgent(),
        AlwaysRevealAgent(),
        treatment,
        rng=random.Random(1),
        forced_qualities=(100, 100),
    )

    player_1 = result.player_records[0]

    assert player_1["improve_decision_if_applicable"]
    assert player_1["paid_improvement_cost"]
    assert player_1["payoff"] in [80, -20]


def test_match_record_marks_tie_before_random_tiebreak():
    treatment = Treatment("tie_test", V=100, c=20, h=0)
    result = simulate_round(
        AlwaysHideStopAgent(),
        AlwaysHideStopAgent(),
        treatment,
        rng=random.Random(1),
        forced_qualities=(50, 50),
    )

    assert result.match_record["tie"]
    assert result.match_record["winner"] in [1, 2]
    assert result.player_records[0]["won"] != result.player_records[1]["won"]


def test_hidden_player_observes_revealed_opponent_quality():
    treatment = Treatment("info_test", V=100, c=20, h=0)
    hidden_agent = SpyHideStopAgent()

    simulate_round(
        AlwaysRevealAgent(),
        hidden_agent,
        treatment,
        rng=random.Random(1),
        forced_qualities=(70, 55),
    )

    assert hidden_agent.last_observed_opponent_reveal
    assert hidden_agent.last_observed_quality == 70


def test_both_hidden_players_do_not_observe_private_quality():
    treatment = Treatment("info_test", V=100, c=20, h=0)
    agent_1 = SpyHideStopAgent()
    agent_2 = SpyHideStopAgent()

    simulate_round(
        agent_1,
        agent_2,
        treatment,
        rng=random.Random(1),
        forced_qualities=(70, 55),
    )

    assert not agent_1.last_observed_opponent_reveal
    assert agent_1.last_observed_quality is None
    assert not agent_2.last_observed_opponent_reveal
    assert agent_2.last_observed_quality is None


if __name__ == "__main__":
    test_reveal_locks_quality_and_hype_is_winner_contingent()
    test_hidden_winner_gets_no_hype()
    test_improvement_cost_is_paid_even_when_losing()
    test_match_record_marks_tie_before_random_tiebreak()
    test_hidden_player_observes_revealed_opponent_quality()
    test_both_hidden_players_do_not_observe_private_quality()
    print("All round tests passed.")

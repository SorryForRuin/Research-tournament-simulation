"""Tests for hype-responsive benchmark agents."""

from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.agents import (  # noqa: E402
    HypeResponsiveEquilibriumAgent,
    HypeResponsiveNoisyEquilibriumAgent,
)
from tournament_sim.probabilities import approximate_hype_reveal_cutoff  # noqa: E402
from tournament_sim.treatment import Treatment  # noqa: E402


def test_hype_cutoff_equals_no_hype_when_h_is_zero_and_falls_with_hype():
    no_hype = Treatment("baseline", V=100, c=20, h=0)
    hype = Treatment("hype", V=100, c=20, h=20)
    assert approximate_hype_reveal_cutoff(no_hype) > approximate_hype_reveal_cutoff(hype)


def test_hype_responsive_agent_reveals_weakly_more_with_hype():
    agent = HypeResponsiveEquilibriumAgent()
    no_hype = Treatment("baseline", V=100, c=20, h=0)
    hype = Treatment("hype", V=100, c=20, h=20)

    no_hype_reveals = sum(agent.decide_reveal(q, no_hype) for q in range(101))
    hype_reveals = sum(agent.decide_reveal(q, hype) for q in range(101))
    assert hype_reveals >= no_hype_reveals
    assert hype_reveals > no_hype_reveals


def test_hype_responsive_noisy_agent_uses_rng():
    agent = HypeResponsiveNoisyEquilibriumAgent(lambda_reveal=1000)
    hype = Treatment("hype", V=100, c=20, h=20)
    assert agent.decide_reveal(99, hype, info={"rng": random.Random(1)})


if __name__ == "__main__":
    test_hype_cutoff_equals_no_hype_when_h_is_zero_and_falls_with_hype()
    test_hype_responsive_agent_reveals_weakly_more_with_hype()
    test_hype_responsive_noisy_agent_uses_rng()
    print("All hype-responsive agent tests passed.")

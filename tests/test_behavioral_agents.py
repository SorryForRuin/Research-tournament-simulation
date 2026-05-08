"""Small tests for behavioral agent variants.

Run with:
    python tests/test_behavioral_agents.py
"""

from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.agents import (  # noqa: E402
    MyopicHeuristicAgent,
    NoisyEquilibriumAgent,
    OverRevealerAgent,
    UnderRevealerAgent,
    logistic,
)
from tournament_sim.experiment import create_subjects  # noqa: E402
from tournament_sim.treatment import Treatment, default_treatments  # noqa: E402


def test_under_revealer_has_higher_reveal_cutoff():
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)
    agent = UnderRevealerAgent(delta=0.10)

    # Equilibrium reveals at 86 for k=0.20. With +0.10, cutoff is about 0.9571.
    assert not agent.decide_reveal(95, treatment)
    assert agent.decide_reveal(96, treatment)


def test_over_revealer_has_lower_reveal_cutoff():
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)
    agent = OverRevealerAgent(delta=0.10)

    # Equilibrium reveals at 86 for k=0.20. With -0.10, cutoff is about 0.7571.
    assert not agent.decide_reveal(75, treatment)
    assert agent.decide_reveal(76, treatment)


def test_myopic_agent_uses_simple_thresholds():
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)
    agent = MyopicHeuristicAgent(
        reveal_threshold=80,
        both_hidden_improve_threshold=60,
    )

    assert not agent.decide_reveal(79, treatment)
    assert agent.decide_reveal(80, treatment)
    assert not agent.decide_improve(59, treatment, False, None)
    assert agent.decide_improve(60, treatment, False, None)


def test_noisy_agent_can_be_made_almost_deterministic():
    treatment = Treatment("baseline_low_cost", V=100, c=20, h=0)
    agent = NoisyEquilibriumAgent(lambda_reveal=1000, lambda_improve=1000)

    assert not agent.decide_reveal(70, treatment, info={"rng": random.Random(1)})
    assert agent.decide_reveal(99, treatment, info={"rng": random.Random(1)})


def test_logistic_midpoint():
    assert logistic(0) == 0.5


def test_experiment_registry_knows_new_agents():
    subjects = create_subjects(
        num_subjects=20,
        treatments=default_treatments(),
        population_composition={
            "NoisyEquilibriumAgent": 0.25,
            "UnderRevealerAgent": 0.25,
            "OverRevealerAgent": 0.25,
            "MyopicHeuristicAgent": 0.25,
        },
        rng=random.Random(1),
    )

    player_types = set()
    for subject in subjects:
        player_types.add(subject.player_type)

    assert "NoisyEquilibriumAgent" in player_types
    assert "UnderRevealerAgent" in player_types
    assert "OverRevealerAgent" in player_types
    assert "MyopicHeuristicAgent" in player_types


if __name__ == "__main__":
    test_under_revealer_has_higher_reveal_cutoff()
    test_over_revealer_has_lower_reveal_cutoff()
    test_myopic_agent_uses_simple_thresholds()
    test_noisy_agent_can_be_made_almost_deterministic()
    test_logistic_midpoint()
    test_experiment_registry_knows_new_agents()
    print("All behavioral agent tests passed.")

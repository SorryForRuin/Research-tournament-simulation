"""Agent decision rules."""

import math

from tournament_sim.probabilities import (
    expected_improve_payoff,
    expected_stop_payoff,
    quality_to_norm,
    should_improve_against_revealed,
    theoretical_hidden_cutoff,
    theoretical_reveal_cutoff,
)


class Agent:
    """Base class for simulated behavioral agents."""

    agent_type = "Agent"

    def decide_reveal(self, q, treatment, info=None):
        """Choose whether to reveal the initial quality."""
        raise NotImplementedError

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        """Choose whether to improve after hiding."""
        raise NotImplementedError


class EquilibriumAgent(Agent):
    """Benchmark agent using the no-hype continuous-theory cutoffs."""

    agent_type = "EquilibriumAgent"

    def reveal_cutoff(self, treatment):
        """Quality cutoff above which this agent reveals."""
        return _clamp(theoretical_reveal_cutoff(treatment.k))

    def hidden_cutoff(self, treatment):
        """Quality cutoff above which this agent improves when both hide."""
        return _clamp(theoretical_hidden_cutoff(treatment.k))

    def decide_reveal(self, q, treatment, info=None):
        q_norm = quality_to_norm(q, treatment.quality_max)
        return q_norm >= self.reveal_cutoff(treatment)

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        if observed_opponent_reveal:
            return should_improve_against_revealed(
                q,
                observed_quality_if_any,
                treatment.V,
                treatment.c,
                treatment.quality_max,
            )

        q_norm = quality_to_norm(q, treatment.quality_max)
        return q_norm >= self.hidden_cutoff(treatment)


class NoisyEquilibriumAgent(EquilibriumAgent):
    """Equilibrium-style agent with logistic noise around decision cutoffs."""

    agent_type = "NoisyEquilibriumAgent"

    def __init__(self, lambda_reveal=20.0, lambda_improve=10.0):
        self.lambda_reveal = lambda_reveal
        self.lambda_improve = lambda_improve

    def decide_reveal(self, q, treatment, info=None):
        q_norm = quality_to_norm(q, treatment.quality_max)
        probability = logistic(self.lambda_reveal * (q_norm - self.reveal_cutoff(treatment)))
        return _random_draw(probability, info)

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        if observed_opponent_reveal:
            improve_payoff = expected_improve_payoff(
                q,
                observed_quality_if_any,
                treatment.V,
                treatment.c,
                treatment.quality_max,
            )
            stop_payoff = expected_stop_payoff(q, observed_quality_if_any, treatment.V)
            delta = improve_payoff - stop_payoff
            probability = logistic(self.lambda_improve * delta / treatment.V)
            return _random_draw(probability, info)

        q_norm = quality_to_norm(q, treatment.quality_max)
        probability = logistic(self.lambda_improve * (q_norm - self.hidden_cutoff(treatment)))
        return _random_draw(probability, info)


class UnderRevealerAgent(EquilibriumAgent):
    """Equilibrium-style agent with a higher reveal cutoff."""

    agent_type = "UnderRevealerAgent"

    def __init__(self, delta=0.10):
        self.delta = delta

    def reveal_cutoff(self, treatment):
        return _clamp(super().reveal_cutoff(treatment) + self.delta)


class OverRevealerAgent(EquilibriumAgent):
    """Equilibrium-style agent with a lower reveal cutoff."""

    agent_type = "OverRevealerAgent"

    def __init__(self, delta=0.10):
        self.delta = delta

    def reveal_cutoff(self, treatment):
        return _clamp(super().reveal_cutoff(treatment) - self.delta)


class MyopicHeuristicAgent(Agent):
    """Simple threshold agent that does not use equilibrium cutoffs."""

    agent_type = "MyopicHeuristicAgent"

    def __init__(self, reveal_threshold=80, both_hidden_improve_threshold=60):
        self.reveal_threshold = reveal_threshold
        self.both_hidden_improve_threshold = both_hidden_improve_threshold

    def decide_reveal(self, q, treatment, info=None):
        return q >= self.reveal_threshold

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        if observed_opponent_reveal:
            return should_improve_against_revealed(
                q,
                observed_quality_if_any,
                treatment.V,
                treatment.c,
                treatment.quality_max,
            )

        return q >= self.both_hidden_improve_threshold


class AlwaysRevealAgent(Agent):
    """Simple test agent that always reveals."""

    agent_type = "AlwaysRevealAgent"

    def decide_reveal(self, q, treatment, info=None):
        return True

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        return False


class AlwaysHideStopAgent(Agent):
    """Simple test agent that always hides and then stops."""

    agent_type = "AlwaysHideStopAgent"

    def decide_reveal(self, q, treatment, info=None):
        return False

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        return False


class AlwaysHideImproveAgent(Agent):
    """Simple test agent that always hides and then improves."""

    agent_type = "AlwaysHideImproveAgent"

    def decide_reveal(self, q, treatment, info=None):
        return False

    def decide_improve(
        self,
        q,
        treatment,
        observed_opponent_reveal,
        observed_quality_if_any=None,
        info=None,
    ):
        return True


def _clamp(value, lower=0.0, upper=1.0):
    """Keep theoretical cutoffs inside the quality range."""
    return max(lower, min(upper, value))


def logistic(value):
    """Stable logistic transform."""
    if value >= 0:
        return 1 / (1 + math.exp(-value))

    exp_value = math.exp(value)
    return exp_value / (1 + exp_value)


def _random_draw(probability, info):
    """Return True with the requested probability."""
    rng = None
    if info is not None:
        rng = info.get("rng")

    if rng is None:
        raise ValueError("Noisy agents need info={'rng': rng} for random choices")

    return rng.random() < probability

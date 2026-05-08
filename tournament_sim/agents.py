"""Agent decision rules."""

from tournament_sim.probabilities import (
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

"""Agent decision rules.

This file will grow slowly. For now it defines a small base class so the later
round simulator has a clear interface to call.
"""


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

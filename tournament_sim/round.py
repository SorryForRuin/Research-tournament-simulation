"""Basic round-level data structures.

The full round simulator will be implemented in the next step. These simple
objects make it clear what information a player carries through a round.
"""

from dataclasses import dataclass


@dataclass
class PlayerState:
    subject_id: int
    player_type: str
    q_initial: int
    revealed: bool = False
    improved: bool = False
    final_quality: int = None
    won: bool = False
    payoff: float = 0.0

    @property
    def paid_improvement_cost(self):
        return self.improved

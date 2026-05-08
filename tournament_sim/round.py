"""Single-round simulator for the research tournament."""

from dataclasses import dataclass
import random

from tournament_sim.probabilities import quality_to_norm


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


@dataclass
class RoundResult:
    """Data returned by one simulated match."""

    player_records: list
    match_record: dict
    player_states: list


def simulate_round(
    agent1,
    agent2,
    treatment,
    rng=None,
    round_number=1,
    subject_ids=(1, 2),
    forced_qualities=None,
):
    """
    Simulate one two-player tournament round.

    The function follows the experiment timing:
    qualities are drawn, reveal decisions are simultaneous, hidden players then
    decide whether to improve, final qualities are compared, and payoffs are
    computed.
    """
    if rng is None:
        rng = random.Random()

    q1, q2 = _draw_initial_qualities(treatment, rng, forced_qualities)
    state1 = PlayerState(subject_ids[0], _agent_type(agent1), q1)
    state2 = PlayerState(subject_ids[1], _agent_type(agent2), q2)

    state1.revealed = bool(agent1.decide_reveal(q1, treatment, info=None))
    state2.revealed = bool(agent2.decide_reveal(q2, treatment, info=None))

    _decide_improvement(agent1, state1, state2, treatment)
    _decide_improvement(agent2, state2, state1, treatment)

    _set_final_quality(state1, treatment, rng)
    _set_final_quality(state2, treatment, rng)

    tie = state1.final_quality == state2.final_quality
    winner_index = _choose_winner(state1.final_quality, state2.final_quality, rng)
    state1.won = winner_index == 0
    state2.won = winner_index == 1

    _set_payoff(state1, treatment)
    _set_payoff(state2, treatment)

    player_records = [
        _player_record(state1, state2, treatment, round_number),
        _player_record(state2, state1, treatment, round_number),
    ]
    match_record = _match_record(state1, state2, treatment, round_number, tie)

    return RoundResult(player_records, match_record, [state1, state2])


def _agent_type(agent):
    return getattr(agent, "agent_type", agent.__class__.__name__)


def _draw_initial_qualities(treatment, rng, forced_qualities):
    if forced_qualities is not None:
        return forced_qualities

    q1 = rng.randint(0, treatment.quality_max)
    q2 = rng.randint(0, treatment.quality_max)
    return q1, q2


def _decide_improvement(agent, state, opponent_state, treatment):
    if state.revealed:
        state.improved = False
        return

    if opponent_state.revealed:
        observed_quality = opponent_state.q_initial
    else:
        observed_quality = None

    state.improved = bool(
        agent.decide_improve(
            state.q_initial,
            treatment,
            observed_opponent_reveal=opponent_state.revealed,
            observed_quality_if_any=observed_quality,
            info=None,
        )
    )


def _set_final_quality(state, treatment, rng):
    if state.improved:
        state.final_quality = rng.randint(state.q_initial, treatment.quality_max)
    else:
        state.final_quality = state.q_initial


def _choose_winner(final_q1, final_q2, rng):
    if final_q1 > final_q2:
        return 0
    if final_q2 > final_q1:
        return 1
    return rng.choice([0, 1])


def _set_payoff(state, treatment):
    payoff = 0.0

    if state.won:
        payoff += treatment.V
        if state.revealed:
            payoff += treatment.h

    if state.improved:
        payoff -= treatment.c

    state.payoff = payoff


def _player_record(state, opponent_state, treatment, round_number):
    opponent_revealed_quality = None
    if opponent_state.revealed:
        opponent_revealed_quality = opponent_state.q_initial

    return {
        "subject_id": state.subject_id,
        "round": round_number,
        "treatment_id": treatment.treatment_id,
        "V": treatment.V,
        "c": treatment.c,
        "h": treatment.h,
        "k": treatment.k,
        "player_type": state.player_type,
        "opponent_id": opponent_state.subject_id,
        "initial_quality": state.q_initial,
        "q_norm": quality_to_norm(state.q_initial, treatment.quality_max),
        "reveal_decision": state.revealed,
        "opponent_reveal_decision": opponent_state.revealed,
        "opponent_revealed_quality_if_observed": opponent_revealed_quality,
        "improve_decision_if_applicable": None if state.revealed else state.improved,
        "final_quality": state.final_quality,
        "won": state.won,
        "payoff": state.payoff,
        "paid_improvement_cost": state.paid_improvement_cost,
        "eligible_for_hype": state.revealed and treatment.h > 0,
        "hype_paid": state.revealed and state.won and treatment.h > 0,
    }


def _match_record(state1, state2, treatment, round_number, tie):
    winner = None
    if state1.won:
        winner = state1.subject_id
    elif state2.won:
        winner = state2.subject_id

    return {
        "round": round_number,
        "treatment_id": treatment.treatment_id,
        "V": treatment.V,
        "c": treatment.c,
        "h": treatment.h,
        "subject_id_1": state1.subject_id,
        "subject_id_2": state2.subject_id,
        "initial_quality_1": state1.q_initial,
        "initial_quality_2": state2.q_initial,
        "reveal_decision_1": state1.revealed,
        "reveal_decision_2": state2.revealed,
        "improve_decision_1": state1.improved,
        "improve_decision_2": state2.improved,
        "final_quality_1": state1.final_quality,
        "final_quality_2": state2.final_quality,
        "winner": winner,
        "tie": tie,
    }

"""Exact discrete probability helpers for the tournament model."""


def quality_to_norm(q, quality_max=100):
    """Convert grid quality, such as 86, to normalized quality, such as 0.86."""
    return q / quality_max


def theoretical_reveal_cutoff(k):
    """No-hype continuous-theory reveal cutoff."""
    return (1 - k**2) / (1 + 3 * k**2)


def theoretical_hidden_cutoff(k):
    """No-hype continuous-theory continuation cutoff when both players hide."""
    return ((1 - k) * (1 - 3 * k)) / (1 + 3 * k**2)


def stop_win_probability(q, opponent_q):
    """Win probability if the player stops against a fixed revealed quality."""
    if q > opponent_q:
        return 1.0
    if q == opponent_q:
        return 0.5
    return 0.0


def improve_win_probability(q, opponent_q, quality_max=100):
    """
    Exact win probability after improving against a fixed revealed quality.

    Improvement draws uniformly from the integer grid:
    {q, q+1, ..., quality_max}.

    A draw above the opponent wins, an equal draw ties and wins with probability
    one half, and a draw below the opponent loses.
    """
    possible_draws = quality_max - q + 1
    wins = 0
    ties = 0

    for draw in range(q, quality_max + 1):
        if draw > opponent_q:
            wins += 1
        elif draw == opponent_q:
            ties += 1

    return (wins + 0.5 * ties) / possible_draws


def expected_stop_payoff(q, opponent_q, V):
    """Expected payoff from stopping against a fixed revealed quality."""
    return V * stop_win_probability(q, opponent_q)


def expected_improve_payoff(q, opponent_q, V, c, quality_max=100):
    """Expected payoff from improving against a fixed revealed quality."""
    win_probability = improve_win_probability(q, opponent_q, quality_max)
    return V * win_probability - c


def should_improve_against_revealed(q, opponent_q, V, c, quality_max=100):
    """Return True if improving is at least as good as stopping."""
    improve_payoff = expected_improve_payoff(q, opponent_q, V, c, quality_max)
    stop_payoff = expected_stop_payoff(q, opponent_q, V)
    return improve_payoff >= stop_payoff

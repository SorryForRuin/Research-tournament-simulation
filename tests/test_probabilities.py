"""Small dependency-free tests for the probability helpers.

Run with:
    python tests/test_probabilities.py
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tournament_sim.probabilities import (
    improve_win_probability,
    should_improve_against_revealed,
    stop_win_probability,
    theoretical_hidden_cutoff,
    theoretical_reveal_cutoff,
)


def test_theoretical_cutoffs():
    r_low = theoretical_reveal_cutoff(0.20)
    s_low = theoretical_hidden_cutoff(0.20)
    r_high = theoretical_reveal_cutoff(0.30)
    s_high = theoretical_hidden_cutoff(0.30)

    assert round(r_low, 4) == 0.8571
    assert round(s_low, 4) == 0.2857
    assert round(r_high, 4) == 0.7165
    assert round(s_high, 4) == 0.0551


def test_stop_win_probability():
    assert stop_win_probability(60, 50) == 1.0
    assert stop_win_probability(50, 50) == 0.5
    assert stop_win_probability(40, 50) == 0.0


def test_improve_win_probability_exact_grid():
    # From q=90 against opponent 95, draws are 90,...,100.
    # Winning draws: 96,97,98,99,100 = 5.
    # Tie draw: 95 = 1, counted as half a win.
    # Total draws: 11.
    assert improve_win_probability(90, 95) == 5.5 / 11

    # From q=100 against opponent 100, the only draw is a tie.
    assert improve_win_probability(100, 100) == 0.5

    # From q=100 against opponent 99, the only draw wins.
    assert improve_win_probability(100, 99) == 1.0


def test_should_improve_against_revealed():
    # Improving from 90 against 95 with V=100, c=20:
    # expected improve payoff = 100 * 0.5 - 20 = 30.
    # expected stop payoff = 0, so improvement is worthwhile.
    assert should_improve_against_revealed(90, 95, V=100, c=20)

    # If already ahead, stopping wins for sure. Improving is costly and cannot
    # increase the win probability above one, so improvement is not worthwhile.
    assert not should_improve_against_revealed(90, 80, V=100, c=20)


if __name__ == "__main__":
    test_theoretical_cutoffs()
    test_stop_win_probability()
    test_improve_win_probability_exact_grid()
    test_should_improve_against_revealed()
    print("All probability tests passed.")

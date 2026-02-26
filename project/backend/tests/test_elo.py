"""Unit tests for ELO rating calculation."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elo import calculate_elo_simple


def test_calculate_elo_simple_winner_gains_25():
    new_winner, _ = calculate_elo_simple(1200, 1200)
    assert new_winner == 1225


def test_calculate_elo_simple_loser_loses_25():
    _, new_loser = calculate_elo_simple(1200, 1200)
    assert new_loser == 1175


def test_calculate_elo_simple_preserves_sum():
    """The total rating points in the system should remain constant."""
    winner_rating = 1400
    loser_rating = 1100
    new_winner, new_loser = calculate_elo_simple(winner_rating, loser_rating)
    assert new_winner + new_loser == winner_rating + loser_rating


def test_calculate_elo_simple_returns_two_values():
    result = calculate_elo_simple(1200, 1200)
    assert len(result) == 2


def test_calculate_elo_simple_any_ratings():
    new_winner, new_loser = calculate_elo_simple(1500, 900)
    assert new_winner == 1525
    assert new_loser == 875

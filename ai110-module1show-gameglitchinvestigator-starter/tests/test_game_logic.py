"""Tests for game logic in logic_utils. Run with: pytest"""

from logic_utils import check_guess


def test_winning_guess():
    """If the secret is 50 and guess is 50, outcome should be Win."""
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert "Correct" in message


def test_guess_too_high():
    """If secret is 50 and guess is 60, outcome should be Too High and message says go lower."""
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert "LOWER" in message.upper()


def test_guess_too_low():
    """If secret is 50 and guess is 40, outcome should be Too Low and message says go higher."""
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in message.upper()


def test_guess_below_range_still_gets_correct_hint():
    """Guess 0 when secret is 50 should be Too Low and tell user to go higher (not lower)."""
    outcome, message = check_guess(0, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in message.upper()

"""Game logic for the number-guessing game. Refactored from app.py and fixed hint/type bugs."""


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    """
    Parse user input into an int guess.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess: int, secret: int):
    """
    Compare guess to secret and return (outcome, message).
    Both guess and secret must be ints so comparison is numeric, not string.

    outcome: "Win" | "Too High" | "Too Low"
    message: user-facing hint (e.g. "Go LOWER!" when guess is too high).
    """
    # FIX: Ensure we always compare int to int so hints are correct.
    guess_int = int(guess) if guess is not None else None
    secret_int = int(secret) if secret is not None else None
    if guess_int is None or secret_int is None:
        return "Error", "Invalid comparison."
    if guess_int == secret_int:
        return "Win", "🎉 Correct!"
    if guess_int > secret_int:
        # Guess is too high → tell user to go LOWER (was wrongly "Go HIGHER!").
        return "Too High", "📉 Go LOWER!"
    # Guess is too low → tell user to go HIGHER (was wrongly "Go LOWER!").
    return "Too Low", "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score

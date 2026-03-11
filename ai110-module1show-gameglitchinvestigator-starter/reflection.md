# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

**What the game looked like:** The app ran and showed a guess input, Submit/New Game buttons, and a hint area. The Developer Debug Info showed the secret number. After submitting a guess, hints and score updated, but several things were wrong.

**Bugs identified:**

1. **Hints were backwards (wrong direction).** When the guess was too high, the app said "Go HIGHER!" instead of "Go LOWER!". When the guess was too low, it said "Go LOWER!" instead of "Go HIGHER!". So the outcome label (Too High / Too Low) was correct but the message told the player to move in the wrong direction. Example: guessing 0 (below the valid range) still produced "Go LOWER!", which is nonsensical.

2. **Secret number type changed every other attempt.** The code converted the secret to a string on even-numbered attempts and left it as an int on odd attempts. So `check_guess` sometimes compared an int guess to a string secret. That led to type errors and string comparison instead of numeric comparison (e.g. "9" > "50" in string order), so hints could be wrong or inconsistent.

3. **New Game and displayed range ignored difficulty.** The info box always said "Guess a number between 1 and 100" even on Easy (1–20) or Hard (1–50). Clicking "New Game" always picked a new secret from 1–100 instead of the current difficulty's range, so the game didn't match the chosen difficulty.

---

## 2. How did you use AI as a teammate?

**Tools used:** Cursor (AI assistant with access to the codebase) was used to refactor logic, fix bugs, and add tests.

The AI identified that `check_guess` was returning the wrong hint messages: for "Too High" it said "Go HIGHER!" instead of "Go LOWER!". It suggested swapping the messages so that a too-high guess gets "Go LOWER!" and a too-low guess gets "Go HIGHER!". Verification: ran pytest (including a test that guess 0 vs secret 50 returns Too Low with "HIGHER" in the message) and played the game manually; hints now matched the direction needed to reach the secret.

---

## 3. Debugging and testing your fixes

**Deciding if a bug was fixed:** For each fix, (1) ran `pytest tests/test_game_logic.py` to ensure the logic behaved correctly, and (2) ran the app with `python -m streamlit run app.py` and played several rounds to confirm behavior in the UI.

**Example test:** `test_guess_too_high` calls `check_guess(60, 50)` and asserts the outcome is "Too High" and the message contains "LOWER". This locks in the fix that the hint direction matches the outcome. Running pytest showed all four tests passing after the refactor.

**AI and tests:** The AI added `test_guess_below_range_still_gets_correct_hint` to lock in the fix for the "guess 0 → Go LOWER!" bug (now 0 vs secret 50 correctly returns Too Low with "Go HIGHER!").

---

## 4. What did you learn about Streamlit and state?

**Why the secret kept changing:** If the secret was a normal variable (e.g. `secret = random.randint(1, 100)`), it would be re-created on every Streamlit rerun. Storing it in `st.session_state.secret` and only setting it when missing (or when starting a new game) keeps it stable across reruns.

**Explaining reruns and session state:** "Streamlit re-runs your script from top to bottom every time the user does something. Session state is a dictionary Streamlit keeps between reruns for that browser tab. Put the secret in `st.session_state.secret` and it stays the same until you change it."

**Change that gave a stable secret:** Always passing the secret as an int to `check_guess` (no more converting to string on even attempts), and when starting a new game using `random.randint(low, high)` so the secret respects the current difficulty range.

---

## 5. Looking ahead: your developer habits

**Habit to reuse:** Writing a small pytest that targets the exact bug (e.g. "guess 60 vs secret 50 → Too High and message says LOWER") before or right after fixing it, so the fix is locked in and regressions are caught.

**Do differently:** When asking the AI to refactor, specify "keep the same function signatures" or "return (outcome, message)" so tests and call sites don't break; then run tests right after to verify.

**AI-generated code takeaway:** AI-generated code can have subtle bugs (wrong hint text, type inconsistencies, hardcoded values). Using session state, tests, and manual play-throughs makes it possible to find and fix those bugs and still benefit from the generated structure.

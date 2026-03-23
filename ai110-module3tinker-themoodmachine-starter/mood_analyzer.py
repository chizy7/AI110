# mood_analyzer.py
"""
Rule based mood analyzer for short text snippets.

This class starts with very simple logic:
  - Preprocess the text
  - Look for positive and negative words
  - Compute a numeric score
  - Convert that score into a mood label
"""

from typing import List, Dict, Tuple, Optional

from dataset import POSITIVE_WORDS, NEGATIVE_WORDS


class MoodAnalyzer:
    """
    A very simple, rule based mood classifier.
    """

    def __init__(
        self,
        positive_words: Optional[List[str]] = None,
        negative_words: Optional[List[str]] = None,
    ) -> None:
        # Use the default lists from dataset.py if none are provided.
        positive_words = positive_words if positive_words is not None else POSITIVE_WORDS
        negative_words = negative_words if negative_words is not None else NEGATIVE_WORDS

        # Store as sets for faster lookup.
        self.positive_words = set(w.lower() for w in positive_words)
        self.negative_words = set(w.lower() for w in negative_words)

    # ---------------------------------------------------------------------
    # Preprocessing
    # ---------------------------------------------------------------------

    # Emoji-to-sentiment mapping used during preprocessing and scoring.
    POSITIVE_EMOJIS = {"🔥", "🎉", "😌", "😂", "❤️", ":)", "😊", "🥳", "💪"}
    NEGATIVE_EMOJIS = {"😩", "😭", "💀", ":(", "🥲", "😤", "😡"}

    # Slang that carries clear sentiment but isn't in the keyword lists.
    POSITIVE_SLANG = {"fire", "lit", "goat", "slay", "immaculate", "bussin", "w", "sick", "wicked"}
    NEGATIVE_SLANG = {"mid", "trash", "l", "bruh", "ugh"}

    def preprocess(self, text: str) -> List[str]:
        """
        Convert raw text into a list of tokens the model can work with.

        Improvements over the starter version:
          - Strips punctuation from each token (commas, periods, etc.)
          - Preserves emoji characters as their own tokens
          - Normalizes repeated characters ("soooo" → "soo")
        """
        import re

        cleaned = text.strip().lower()

        # Split on whitespace first.
        raw_tokens = cleaned.split()

        tokens: List[str] = []
        for raw in raw_tokens:
            # Pull out any emoji characters as separate tokens.
            # Walk through the string, collecting emoji chars and text runs.
            buf = ""
            for ch in raw:
                if ch in self.POSITIVE_EMOJIS or ch in self.NEGATIVE_EMOJIS:
                    if buf:
                        tokens.append(buf)
                        buf = ""
                    tokens.append(ch)
                else:
                    buf += ch
            if buf:
                # Strip trailing punctuation from text tokens.
                stripped = buf.strip(".,!?;:\"'()")
                if stripped:
                    tokens.append(stripped)

        # Normalize repeated characters: 3+ of the same char → 2
        tokens = [re.sub(r"(.)\1{2,}", r"\1\1", t) for t in tokens]

        return tokens

    # ---------------------------------------------------------------------
    # Scoring logic
    # ---------------------------------------------------------------------

    def score_text(self, text: str) -> int:
        """
        Compute a numeric "mood score" for the given text.

        Positive words increase the score.
        Negative words decrease the score.

        TODO: You must choose AT LEAST ONE modeling improvement to implement.
        For example:
          - Handle simple negation such as "not happy" or "not bad"
          - Count how many times each word appears instead of just presence
          - Give some words higher weights than others (for example "hate" < "annoyed")
          - Treat emojis or slang (":)", "lol", "💀") as strong signals
        """
        tokens = self.preprocess(text)
        score = 0
        pos_hits: List[str] = []
        neg_hits: List[str] = []
        negators = {"not", "no", "never", "don't", "doesn't", "isn't", "wasn't", "aren't"}

        for i, token in enumerate(tokens):
            is_negated = i > 0 and tokens[i - 1] in negators

            # --- keyword matches ---
            if token in self.positive_words or token in self.POSITIVE_SLANG:
                if is_negated:
                    score -= 1
                    neg_hits.append(f"not {token}")
                else:
                    score += 1
                    pos_hits.append(token)
            elif token in self.negative_words or token in self.NEGATIVE_SLANG:
                if is_negated:
                    score += 1
                    pos_hits.append(f"not {token}")
                else:
                    score -= 1
                    neg_hits.append(token)

            # --- emoji signals ---
            elif token in self.POSITIVE_EMOJIS:
                score += 1
                pos_hits.append(token)
            elif token in self.NEGATIVE_EMOJIS:
                score -= 1
                neg_hits.append(token)

        # Stash hits for explain() to reuse without re-computing.
        self._last_pos_hits = pos_hits
        self._last_neg_hits = neg_hits
        self._last_score = score

        return score

    # ---------------------------------------------------------------------
    # Label prediction
    # ---------------------------------------------------------------------

    def predict_label(self, text: str) -> str:
        """
        Turn the numeric score for a piece of text into a mood label.

        The default mapping is:
          - score > 0  -> "positive"
          - score < 0  -> "negative"
          - score == 0 -> "neutral"

        TODO: You can adjust this mapping if it makes sense for your model.
        For example:
          - Use different thresholds (for example score >= 2 to be "positive")
          - Add a "mixed" label for scores close to zero
        Just remember that whatever labels you return should match the labels
        you use in TRUE_LABELS in dataset.py if you care about accuracy.
        """
        score = self.score_text(text)
        has_pos = len(self._last_pos_hits) > 0
        has_neg = len(self._last_neg_hits) > 0

        # If both positive and negative signals found, call it mixed.
        if has_pos and has_neg:
            return "mixed"

        if score > 0:
            return "positive"
        elif score < 0:
            return "negative"
        else:
            return "neutral"

    # ---------------------------------------------------------------------
    # Explanations (optional but recommended)
    # ---------------------------------------------------------------------

    def explain(self, text: str) -> str:
        """
        Return a short string explaining WHY the model chose its label.

        TODO:
          - Look at the tokens and identify which ones counted as positive
            and which ones counted as negative.
          - Show the final score.
          - Return a short human readable explanation.

        Example explanation (your exact wording can be different):
          'Score = 2 (positive words: ["love", "great"]; negative words: [])'

        The current implementation is a placeholder so the code runs even
        before you implement it.
        """
        # Run scoring to populate cached hits.
        score = self.score_text(text)
        return (
            f"Score = {score} "
            f"(positive: {self._last_pos_hits or '[]'}, "
            f"negative: {self._last_neg_hits or '[]'})"
        )

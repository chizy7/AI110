"""
Shared data for the Mood Machine lab.

This file defines:
  - POSITIVE_WORDS: starter list of positive words
  - NEGATIVE_WORDS: starter list of negative words
  - SAMPLE_POSTS: short example posts for evaluation and training
  - TRUE_LABELS: human labels for each post in SAMPLE_POSTS
"""

# ---------------------------------------------------------------------
# Starter word lists
# ---------------------------------------------------------------------

POSITIVE_WORDS = [
    "happy",
    "great",
    "good",
    "love",
    "excited",
    "awesome",
    "fun",
    "chill",
    "relaxed",
    "amazing",
    "proud",
    "best",
    "wonderful",
    "fantastic",
    "happier",
    "hopeful",
    "beautiful",
    "thankful",
    "grateful",
]

NEGATIVE_WORDS = [
    "sad",
    "bad",
    "terrible",
    "awful",
    "angry",
    "upset",
    "tired",
    "stressed",
    "hate",
    "boring",
    "worst",
    "exhausted",
    "failed",
    "miserable",
    "frustrated",
    "annoyed",
    "depressed",
    "stuck",
    "hard",
]

# ---------------------------------------------------------------------
# Starter labeled dataset
# ---------------------------------------------------------------------

# Short example posts written as if they were social media updates or messages.
SAMPLE_POSTS = [
    "I love this class so much",
    "Today was a terrible day",
    "Feeling tired but kind of hopeful",
    "This is fine",
    "So excited for the weekend",
    "I am not happy about this",
    # --- new posts below ---
    "lowkey stressed but we move 💀",
    "this song is absolute fire no cap 🔥",
    "I absolutely love sitting in traffic for two hours",
    "ngl today was mid at best",
    "just got the internship offer omggg 😭🎉",
    "idk how to feel about this whole situation tbh",
    "why does everything have to be so hard bruh 😩",
    "vibes are immaculate today honestly chill day 😌",
    # --- round 2: extra posts for model comparison ---
    "I'm not even mad just disappointed",
    "can't complain life is decent rn",
    "lmaooo this group project is a disaster 💀😂",
    "honestly just grateful to be here ❤️",
    "pain but make it aesthetic 🥲",
]

# Human labels for each post above.
# Allowed labels in the starter:
#   - "positive"
#   - "negative"
#   - "neutral"
#   - "mixed"
TRUE_LABELS = [
    "positive",  # "I love this class so much"
    "negative",  # "Today was a terrible day"
    "mixed",     # "Feeling tired but kind of hopeful"
    "neutral",   # "This is fine"
    "positive",  # "So excited for the weekend"
    "negative",  # "I am not happy about this"
    # --- new labels below ---
    "mixed",     # "lowkey stressed but we move 💀" — stressed but resilient
    "positive",  # "this song is absolute fire no cap 🔥" — slang praise
    "negative",  # "I absolutely love sitting in traffic..." — sarcasm
    "negative",  # "ngl today was mid at best" — disappointed
    "positive",  # "just got the internship offer omggg 😭🎉" — happy tears
    "neutral",   # "idk how to feel about this whole situation tbh" — uncertain
    "negative",  # "why does everything have to be so hard bruh 😩" — frustrated
    "positive",  # "vibes are immaculate today honestly chill day 😌" — relaxed/happy
    # --- round 2 labels ---
    "negative",  # "I'm not even mad just disappointed" — negative despite denying anger
    "positive",  # "can't complain life is decent rn" — understated positive
    "mixed",     # "lmaooo this group project is a disaster 💀😂" — laughing at misery
    "positive",  # "honestly just grateful to be here ❤️" — sincere gratitude
    "mixed",     # "pain but make it aesthetic 🥲" — ironic self-aware sadness
]

# TODO: Add 5-10 more posts and labels.
#
# Requirements:
#   - For every new post you add to SAMPLE_POSTS, you must add one
#     matching label to TRUE_LABELS.
#   - SAMPLE_POSTS and TRUE_LABELS must always have the same length.
#   - Include a variety of language styles, such as:
#       * Slang ("lowkey", "highkey", "no cap")
#       * Emojis (":)", ":(", "🥲", "😂", "💀")
#       * Sarcasm ("I absolutely love getting stuck in traffic")
#       * Ambiguous or mixed feelings
#
# Tips:
#   - Try to create some examples that are hard to label even for you.
#   - Make a note of any examples that you and a friend might disagree on.
#     Those "edge cases" are interesting to inspect for both the rule based
#     and ML models.
#
# Example of how you might extend the lists:
#
# SAMPLE_POSTS.append("Lowkey stressed but kind of proud of myself")
# TRUE_LABELS.append("mixed")
#
# Remember to keep them aligned:
#   len(SAMPLE_POSTS) == len(TRUE_LABELS)

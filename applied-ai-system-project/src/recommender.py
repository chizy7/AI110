"""
Scoring engine for the music recommender.

Evolved from the Module 3 recommender. Scores songs against a structured
user profile using weighted categorical matches and numerical proximity.
"""

import logging
from dataclasses import dataclass
from src.catalog import Song

logger = logging.getLogger(__name__)

# --- Scoring Weights ---
WEIGHT_GENRE = 3.0
WEIGHT_MOOD = 2.0
WEIGHT_ENERGY = 1.5
WEIGHT_VALENCE = 0.5
WEIGHT_DANCEABILITY = 0.5
WEIGHT_ACOUSTIC = 1.0
MAX_SCORE = WEIGHT_GENRE + WEIGHT_MOOD + WEIGHT_ENERGY + WEIGHT_VALENCE + WEIGHT_DANCEABILITY + WEIGHT_ACOUSTIC


@dataclass
class UserProfile:
    """Structured taste profile extracted from a user request."""
    genre: str = ""
    mood: str = ""
    energy: float = 0.5
    likes_acoustic: bool = False


def score_song(user: UserProfile, song: Song) -> tuple[float, list[str]]:
    """
    Score a single song against a user profile.
    Returns (score, list_of_reasons).
    """
    score = 0.0
    reasons = []

    if user.genre and song.genre.lower() == user.genre.lower():
        score += WEIGHT_GENRE
        reasons.append(f"genre match: {song.genre} (+{WEIGHT_GENRE:.1f})")

    if user.mood and song.mood.lower() == user.mood.lower():
        score += WEIGHT_MOOD
        reasons.append(f"mood match: {song.mood} (+{WEIGHT_MOOD:.1f})")

    energy_score = WEIGHT_ENERGY * (1 - abs(song.energy - user.energy))
    score += energy_score
    reasons.append(f"energy closeness (+{energy_score:.2f})")

    valence_score = WEIGHT_VALENCE * song.valence
    score += valence_score

    dance_score = WEIGHT_DANCEABILITY * song.danceability
    score += dance_score

    if user.likes_acoustic and song.acousticness > 0.6:
        score += WEIGHT_ACOUSTIC
        reasons.append(f"acoustic bonus (+{WEIGHT_ACOUSTIC:.1f})")

    return round(score, 2), reasons


def rank_songs(
    user: UserProfile,
    songs: list[Song],
    top_k: int = 5,
) -> list[tuple[Song, float, list[str]]]:
    """Score all songs and return the top k with scores and reasons."""
    scored = []
    for song in songs:
        s, reasons = score_song(user, song)
        scored.append((song, s, reasons))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def confidence_score(top_score: float) -> float:
    """
    Return a 0.0-1.0 confidence rating based on how close the top
    recommendation's score is to the theoretical maximum.
    """
    return round(min(top_score / MAX_SCORE, 1.0), 2)

import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


# --- Scoring Weights ---
WEIGHT_GENRE = 3.0
WEIGHT_MOOD = 2.0
WEIGHT_ENERGY = 1.5
WEIGHT_VALENCE = 0.5
WEIGHT_DANCEABILITY = 0.5
WEIGHT_ACOUSTIC = 1.0


def score_song(user: UserProfile, song: Song) -> Tuple[float, str]:
    """
    Scores a single song against a user profile.
    Returns (score, explanation).

    Scoring Rule:
      - Genre match:  +3.0 (exact match)
      - Mood match:   +2.0 (exact match)
      - Energy proximity: up to 1.5  (closer to user's target = higher)
      - Valence proximity: up to 0.5
      - Danceability proximity: up to 0.5
      - Acoustic bonus: +1.0 if user likes acoustic and song is acoustic (>0.6)

    Proximity formula: weight * (1 - |song_value - user_value|)
    This rewards songs that are *close* to the user's preference, not just higher.
    """
    score = 0.0
    reasons = []

    # Categorical matches
    if song.genre.lower() == user.favorite_genre.lower():
        score += WEIGHT_GENRE
        reasons.append(f"genre match (+{WEIGHT_GENRE:.1f})")

    if song.mood.lower() == user.favorite_mood.lower():
        score += WEIGHT_MOOD
        reasons.append(f"mood match (+{WEIGHT_MOOD:.1f})")

    # Numerical proximity scores
    energy_score = WEIGHT_ENERGY * (1 - abs(song.energy - user.target_energy))
    score += energy_score
    reasons.append(f"energy closeness (+{energy_score:.2f})")

    valence_score = WEIGHT_VALENCE * song.valence
    score += valence_score
    reasons.append(f"valence (+{valence_score:.2f})")

    dance_score = WEIGHT_DANCEABILITY * song.danceability
    score += dance_score
    reasons.append(f"danceability (+{dance_score:.2f})")

    # Acoustic bonus
    if user.likes_acoustic and song.acousticness > 0.6:
        score += WEIGHT_ACOUSTIC
        reasons.append(f"acoustic bonus (+{WEIGHT_ACOUSTIC:.1f})")

    explanation = "; ".join(reasons)
    return round(score, 2), explanation


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Rank all songs by score and return the top k."""
        scored = [(song, score_song(user, song)[0]) for song in self.songs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation for why this song was recommended."""
        score, explanation = score_song(user, song)
        return f"Score {score:.2f} — {explanation}"


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["energy"] = float(row["energy"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            row["valence"] = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            songs.append(row)
    return songs


def _dict_to_song(d: Dict) -> Song:
    return Song(
        id=d["id"], title=d["title"], artist=d["artist"],
        genre=d["genre"], mood=d["mood"], energy=d["energy"],
        tempo_bpm=d["tempo_bpm"], valence=d["valence"],
        danceability=d["danceability"], acousticness=d["acousticness"],
    )


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Ranking Rule: Score every song, sort descending, return top k.
    """
    user = UserProfile(
        favorite_genre=user_prefs.get("genre", ""),
        favorite_mood=user_prefs.get("mood", ""),
        target_energy=user_prefs.get("energy", 0.5),
        likes_acoustic=user_prefs.get("likes_acoustic", False),
    )

    scored = []
    for song_dict in songs:
        song_obj = _dict_to_song(song_dict)
        s, explanation = score_song(user, song_obj)
        scored.append((song_dict, s, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]

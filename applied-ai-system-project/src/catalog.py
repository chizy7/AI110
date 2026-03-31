"""
Song catalog: loads CSV data and provides a retrieval index for RAG.

This module handles the data layer — loading songs from CSV, building
a keyword index for fast lookup, and retrieving candidate songs based
on natural language queries.
"""

import csv
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "about", "up", "down", "if", "or", "and",
    "but", "not", "no", "so", "yet", "both", "all", "any", "some", "such",
    "than", "too", "very", "just", "also", "how", "what", "which", "who",
    "when", "where", "why", "this", "that", "these", "those", "there",
    "here", "i", "you", "he", "she", "it", "we", "they", "me", "him",
    "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "want", "need", "like", "give", "get", "make", "know", "think",
    "something", "songs", "song", "music", "recommend", "play", "listen",
    "find", "show", "tell", "please",
}


@dataclass
class Song:
    """Represents a song with all its audio and metadata attributes."""
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

    def description(self) -> str:
        """Human-readable description for RAG context."""
        return (
            f'"{self.title}" by {self.artist} — '
            f"genre: {self.genre}, mood: {self.mood}, "
            f"energy: {self.energy}, tempo: {self.tempo_bpm} BPM, "
            f"valence: {self.valence}, danceability: {self.danceability}, "
            f"acousticness: {self.acousticness}"
        )


def load_songs(csv_path: str) -> list[Song]:
    """Load songs from a CSV file and return a list of Song objects."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = Song(
                id=int(row["id"]),
                title=row["title"],
                artist=row["artist"],
                genre=row["genre"],
                mood=row["mood"],
                energy=float(row["energy"]),
                tempo_bpm=float(row["tempo_bpm"]),
                valence=float(row["valence"]),
                danceability=float(row["danceability"]),
                acousticness=float(row["acousticness"]),
            )
            songs.append(song)
    logger.info("Loaded %d songs from %s", len(songs), csv_path)
    return songs


def build_song_index(songs: list[Song]) -> dict[str, list[int]]:
    """
    Build an inverted index mapping keywords to song IDs.
    Indexes genre, mood, artist, and title words.
    """
    index: dict[str, list[int]] = {}
    for song in songs:
        text = f"{song.title} {song.artist} {song.genre} {song.mood}".lower()
        words = set()
        for raw in text.split():
            cleaned = raw.strip(".,;:!?()[]{}\"'`#*-_>/\\")
            if cleaned and cleaned not in STOP_WORDS:
                words.add(cleaned)
        for word in words:
            if word not in index:
                index[word] = []
            if song.id not in index[word]:
                index[word].append(song.id)
    return index


def retrieve_songs(
    query: str,
    songs: list[Song],
    index: dict[str, list[int]],
    top_k: int = 10,
) -> list[tuple[Song, int]]:
    """
    Retrieve songs relevant to a natural language query using the index.
    Returns a list of (Song, relevance_score) sorted by score descending.
    """
    query_words = set()
    for raw in query.lower().split():
        cleaned = raw.strip(".,;:!?()[]{}\"'`#*-_>/\\")
        if cleaned and cleaned not in STOP_WORDS:
            query_words.add(cleaned)

    if not query_words:
        return []

    song_map = {s.id: s for s in songs}
    scores: dict[int, int] = {}

    for word in query_words:
        if word in index:
            for song_id in index[word]:
                scores[song_id] = scores.get(song_id, 0) + 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(song_map[sid], score) for sid, score in ranked[:top_k]]

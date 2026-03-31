"""
Automated test suite for the AI Music Recommender.

Tests the core components: catalog loading, scoring logic, retrieval,
guardrails, and the agent pipeline.
"""

import pytest
from src.catalog import Song, load_songs, build_song_index, retrieve_songs
from src.recommender import UserProfile, score_song, rank_songs, confidence_score
from src.guardrails import validate_query, check_confidence


# --- Fixtures ---

@pytest.fixture
def sample_songs():
    return load_songs("data/songs.csv")


@pytest.fixture
def sample_index(sample_songs):
    return build_song_index(sample_songs)


@pytest.fixture
def pop_song():
    return Song(
        id=1, title="Test Pop", artist="Artist", genre="pop",
        mood="happy", energy=0.8, tempo_bpm=120, valence=0.9,
        danceability=0.8, acousticness=0.2,
    )


@pytest.fixture
def lofi_song():
    return Song(
        id=2, title="Test Lofi", artist="Artist", genre="lofi",
        mood="chill", energy=0.35, tempo_bpm=75, valence=0.6,
        danceability=0.5, acousticness=0.85,
    )


# --- Catalog Tests ---

def test_load_songs_count(sample_songs):
    assert len(sample_songs) == 20


def test_load_songs_types(sample_songs):
    song = sample_songs[0]
    assert isinstance(song.title, str)
    assert isinstance(song.energy, float)
    assert 0.0 <= song.energy <= 1.0


def test_build_index_contains_genres(sample_index):
    assert "pop" in sample_index
    assert "rock" in sample_index
    assert "jazz" in sample_index


def test_retrieve_pop_songs(sample_songs, sample_index):
    results = retrieve_songs("pop music", sample_songs, sample_index)
    genres = [s.genre for s, _ in results]
    assert "pop" in genres


def test_retrieve_empty_query(sample_songs, sample_index):
    results = retrieve_songs("", sample_songs, sample_index)
    assert results == []


# --- Scoring Tests ---

def test_score_perfect_match(pop_song):
    user = UserProfile(genre="pop", mood="happy", energy=0.8, likes_acoustic=False)
    score, reasons = score_song(user, pop_song)
    assert score > 6.0  # genre(3) + mood(2) + energy(~1.5) + extras
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_score_no_match(lofi_song):
    user = UserProfile(genre="metal", mood="aggressive", energy=0.95, likes_acoustic=False)
    score, reasons = score_song(user, lofi_song)
    assert score < 2.0  # no genre/mood match, energy far off


def test_score_acoustic_bonus(lofi_song):
    user = UserProfile(genre="lofi", mood="chill", energy=0.35, likes_acoustic=True)
    score, _ = score_song(user, lofi_song)
    user_no_acoustic = UserProfile(genre="lofi", mood="chill", energy=0.35, likes_acoustic=False)
    score_no, _ = score_song(user_no_acoustic, lofi_song)
    assert score > score_no  # acoustic bonus adds points


def test_rank_songs_order(sample_songs):
    user = UserProfile(genre="pop", mood="happy", energy=0.8, likes_acoustic=False)
    ranked = rank_songs(user, sample_songs, top_k=5)
    scores = [s for _, s, _ in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_songs_pop_first(sample_songs):
    user = UserProfile(genre="pop", mood="happy", energy=0.8, likes_acoustic=False)
    ranked = rank_songs(user, sample_songs, top_k=1)
    assert ranked[0][0].genre == "pop"


def test_confidence_score_range():
    assert 0.0 <= confidence_score(0.0) <= 1.0
    assert 0.0 <= confidence_score(5.0) <= 1.0
    assert confidence_score(8.5) == 1.0


# --- Guardrail Tests ---

def test_validate_empty_query():
    valid, msg = validate_query("")
    assert not valid
    assert "Empty" in msg


def test_validate_short_query():
    valid, msg = validate_query("hi")
    assert not valid


def test_validate_good_query():
    valid, msg = validate_query("I want happy pop music")
    assert valid
    assert msg == ""


def test_low_confidence_warning():
    warning = check_confidence(0.2)
    assert warning is not None
    assert "Low confidence" in warning


def test_high_confidence_no_warning():
    warning = check_confidence(0.8)
    assert warning is None

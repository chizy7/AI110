"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


# --- User Profiles ---
# Each profile tests a different "taste shape" so we can verify
# the recommender differentiates between them.

USER_PROFILES = {
    # --- Core profiles ---
    "Energetic Pop Fan": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "likes_acoustic": False,
    },
    "Chill Lofi Listener": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.35,
        "likes_acoustic": True,
    },
    "Intense Rock Lover": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.9,
        "likes_acoustic": False,
    },
    "Mellow Jazz Explorer": {
        "genre": "jazz",
        "mood": "relaxed",
        "energy": 0.4,
        "likes_acoustic": True,
    },
    # --- Edge-case / adversarial profiles ---
    "EDGE: Sad but High-Energy": {
        "genre": "pop",
        "mood": "melancholy",
        "energy": 0.95,
        "likes_acoustic": False,
    },
    "EDGE: Genre That Doesn't Exist": {
        "genre": "reggaeton",
        "mood": "happy",
        "energy": 0.7,
        "likes_acoustic": False,
    },
    "EDGE: Wants Everything Acoustic + Intense": {
        "genre": "metal",
        "mood": "aggressive",
        "energy": 0.95,
        "likes_acoustic": True,
    },
}


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for profile_name, prefs in USER_PROFILES.items():
        print(f"\n{'='*50}")
        print(f"  {profile_name}")
        print(f"  Prefs: genre={prefs['genre']}, mood={prefs['mood']}, "
              f"energy={prefs['energy']}, acoustic={prefs['likes_acoustic']}")
        print(f"{'='*50}\n")

        recommendations = recommend_songs(prefs, songs, k=5)

        for rec in recommendations:
            song, score, explanation = rec
            print(f"  {song['title']} by {song['artist']} — Score: {score:.2f}")
            print(f"    Because: {explanation}")
            print()


if __name__ == "__main__":
    main()

"""
Evaluation harness: runs the system on predefined inputs and prints
a summary of pass/fail scores, confidence ratings, and retrieval quality.

Usage:
    python evaluation.py
"""

from dotenv import load_dotenv
load_dotenv()

from src.guardrails import setup_logging
from src.agent import MusicAgent

# Test cases: (query, expected_top_genre, expected_min_confidence)
TEST_CASES = [
    ("I want upbeat pop music for working out", "pop", 0.2),
    ("Something chill and lofi for studying", "lofi", 0.2),
    ("Give me intense rock music", "rock", 0.2),
    ("Relaxed jazz for a coffee shop", "jazz", 0.2),
    ("High energy electronic dance music", "electronic", 0.2),
    ("Acoustic country music, something nostalgic", "country", 0.2),
    ("Happy latin music for a party", "latin", 0.2),
    ("Dark moody synthwave for a night drive", "synthwave", 0.2),
]

# Edge cases that should still produce results (no crash)
EDGE_CASES = [
    "",                          # empty — should be rejected
    "ab",                        # too short — should be rejected
    "asdfghjkl qwertyuiop",     # nonsense — should produce low confidence
    "I want happy sad loud quiet music",  # contradictory
]


def run_evaluation():
    setup_logging()
    agent = MusicAgent()

    print("\n" + "=" * 65)
    print("  EVALUATION HARNESS — AI Music Recommender")
    print("=" * 65)

    # Standard test cases
    passes = 0
    total = len(TEST_CASES)
    confidences = []

    print(f"\n--- Standard Test Cases ({total}) ---\n")

    for query, expected_genre, min_confidence in TEST_CASES:
        result = agent.recommend(query)

        top_genre = ""
        if result.recommendations:
            top_genre = result.recommendations[0]["genre"]

        genre_match = top_genre.lower() == expected_genre.lower()
        conf_ok = result.confidence >= min_confidence
        passed = genre_match and conf_ok

        if passed:
            passes += 1
        confidences.append(result.confidence)

        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {query[:50]:<50}")
        print(f"         Expected genre: {expected_genre:<12} Got: {top_genre:<12} "
              f"Confidence: {result.confidence:.0%}")

    # Edge cases
    print(f"\n--- Edge Cases ({len(EDGE_CASES)}) ---\n")
    edge_passes = 0

    for query in EDGE_CASES:
        try:
            result = agent.recommend(query)
            if not result.is_valid:
                status = "PASS (rejected)"
                edge_passes += 1
            elif result.confidence < 0.4:
                status = "PASS (low confidence)"
                edge_passes += 1
            else:
                status = "WARN (unexpected high confidence)"
            print(f"  [{status}] {query[:50]!r}")
        except Exception as e:
            print(f"  [FAIL (crash)] {query[:50]!r} -> {e}")

    # Summary
    print("\n" + "=" * 65)
    print("  SUMMARY")
    print("=" * 65)
    print(f"\n  Standard tests:  {passes}/{total} passed")
    print(f"  Edge cases:      {edge_passes}/{len(EDGE_CASES)} handled correctly")
    if confidences:
        avg_conf = sum(confidences) / len(confidences)
        print(f"  Avg confidence:  {avg_conf:.0%}")
        print(f"  Min confidence:  {min(confidences):.0%}")
        print(f"  Max confidence:  {max(confidences):.0%}")
    print()


if __name__ == "__main__":
    run_evaluation()

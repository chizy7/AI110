"""
CLI entry point for the AI Music Recommender.

Supports two modes:
  1. Interactive — ask questions in natural language
  2. Demo — run preset queries to showcase the system
"""

from dotenv import load_dotenv
load_dotenv()

from src.guardrails import setup_logging
from src.agent import MusicAgent


def print_result(result):
    """Pretty-print an agent result."""
    print()

    # Show the agentic reasoning steps
    print("Agent Reasoning Chain:")
    for step in result.steps:
        print(f"  {step}")
    print()

    if not result.is_valid:
        print(f"Error: {result.error}")
        return

    # Show parsed profile
    p = result.parsed_profile
    print(f"Parsed Profile: genre={p.get('genre', '')!r}, "
          f"mood={p.get('mood', '')!r}, "
          f"energy={p.get('energy', 0.5)}, "
          f"acoustic={p.get('likes_acoustic', False)}")
    print()

    # Show recommendations
    print(f"Top {len(result.recommendations)} Recommendations "
          f"(confidence: {result.confidence:.0%}):")
    print("-" * 55)
    for i, r in enumerate(result.recommendations, 1):
        print(f"  {i}. {r['title']} by {r['artist']} — {r['score']:.2f}")
        print(f"     {', '.join(r['reasons'])}")
    print()

    # Show confidence warning if any
    if result.confidence_warning:
        print(f"WARNING: {result.confidence_warning}")
        print()

    # Show LLM explanation
    print("AI Explanation:")
    print(result.explanation)


def demo_mode(agent):
    """Run preset demo queries."""
    queries = [
        "I want upbeat pop music for a morning workout",
        "Something chill and acoustic for studying late at night",
        "Give me aggressive high-energy metal",
        "I'm feeling nostalgic, maybe some country vibes",
        "Happy danceable music for a party",
    ]

    for query in queries:
        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print("=" * 60)
        result = agent.recommend(query)
        print_result(result)


def interactive_mode(agent):
    """Interactive question loop."""
    print("\nAsk for music recommendations in natural language.")
    print("Type 'quit' to exit.\n")

    while True:
        query = input("What do you want to hear? > ").strip()
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        result = agent.recommend(query)
        print_result(result)
        print()


def main():
    setup_logging()

    print("AI Music Recommender")
    print("=" * 40)
    print()
    print("  1) Demo mode (preset queries)")
    print("  2) Interactive mode")
    print("  q) Quit")
    print()

    choice = input("Choose mode: ").strip().lower()

    agent = MusicAgent()

    if choice == "1":
        demo_mode(agent)
    elif choice == "2":
        interactive_mode(agent)
    elif choice == "q":
        print("Goodbye!")
    else:
        print("Unknown choice.")


if __name__ == "__main__":
    main()

"""
Agentic workflow: the multi-step reasoning pipeline.

The agent orchestrates the full recommendation process:
1. VALIDATE — check the user's input
2. PARSE — use LLM to extract structured preferences from natural language
3. RETRIEVE — search the song catalog for relevant candidates (RAG)
4. SCORE — rank candidates using the weighted scoring engine
5. EXPLAIN — use LLM to generate a grounded explanation (RAG)
6. EVALUATE — self-check confidence and flag low-quality results

Each step is logged with its intermediate output so the reasoning
chain is fully observable.
"""

import logging
from dataclasses import dataclass, field

from src.catalog import Song, load_songs, build_song_index, retrieve_songs
from src.recommender import UserProfile, rank_songs, confidence_score
from src import llm_client
from src.guardrails import validate_query, check_confidence

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Complete output of one agent run, with all intermediate steps."""
    query: str
    is_valid: bool = True
    error: str = ""
    parsed_profile: dict = field(default_factory=dict)
    retrieved_count: int = 0
    recommendations: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    confidence_warning: str | None = None
    explanation: str = ""
    steps: list[str] = field(default_factory=list)


class MusicAgent:
    """
    Agentic music recommendation system.

    Orchestrates a multi-step pipeline: validate -> parse -> retrieve ->
    score -> explain -> evaluate. Each step produces observable output.
    """

    def __init__(self, csv_path: str = "data/songs.csv"):
        logger.info("Initializing MusicAgent...")
        self.songs = load_songs(csv_path)
        self.index = build_song_index(self.songs)
        self.llm_ready = llm_client.init_gemini()
        logger.info(
            "Agent ready: %d songs, LLM %s",
            len(self.songs),
            "enabled" if self.llm_ready else "disabled",
        )

    def recommend(self, query: str, top_k: int = 5) -> AgentResult:
        """Run the full agentic pipeline on a user query."""
        result = AgentResult(query=query)

        # Step 1: VALIDATE
        result.steps.append("STEP 1: VALIDATE input")
        is_valid, error = validate_query(query)
        if not is_valid:
            result.is_valid = False
            result.error = error
            result.steps.append(f"  -> REJECTED: {error}")
            logger.warning("Query rejected: %s", error)
            return result
        result.steps.append("  -> Input accepted")

        # Step 2: PARSE natural language into structured profile
        result.steps.append("STEP 2: PARSE user request into preferences")
        parsed = llm_client.parse_user_request(query)
        result.parsed_profile = parsed
        result.steps.append(
            f"  -> Extracted: genre={parsed.get('genre', '')!r}, "
            f"mood={parsed.get('mood', '')!r}, "
            f"energy={parsed.get('energy', 0.5)}, "
            f"acoustic={parsed.get('likes_acoustic', False)}"
        )

        user = UserProfile(
            genre=parsed.get("genre", ""),
            mood=parsed.get("mood", ""),
            energy=parsed.get("energy", 0.5),
            likes_acoustic=parsed.get("likes_acoustic", False),
        )

        # Step 3: RETRIEVE candidates from catalog using keyword search
        result.steps.append("STEP 3: RETRIEVE candidate songs from catalog")
        retrieved = retrieve_songs(query, self.songs, self.index, top_k=10)
        result.retrieved_count = len(retrieved)
        result.steps.append(f"  -> Found {len(retrieved)} candidates via keyword search")

        # Use all songs for scoring (retrieval narrows the initial set,
        # but scoring uses the structured profile for precision)
        candidates = [s for s, _ in retrieved] if retrieved else self.songs
        result.steps.append(f"  -> Scoring {len(candidates)} candidates")

        # Step 4: SCORE candidates using weighted recommender
        result.steps.append("STEP 4: SCORE and rank candidates")
        ranked = rank_songs(user, candidates, top_k=top_k)

        recs = []
        for song, score, reasons in ranked:
            recs.append({
                "title": song.title,
                "artist": song.artist,
                "genre": song.genre,
                "mood": song.mood,
                "energy": song.energy,
                "score": score,
                "reasons": reasons,
            })
        result.recommendations = recs

        if recs:
            result.steps.append(
                f"  -> Top pick: \"{recs[0]['title']}\" (score: {recs[0]['score']:.2f})"
            )

        # Step 5: EVALUATE confidence
        result.steps.append("STEP 5: EVALUATE recommendation confidence")
        top_score = recs[0]["score"] if recs else 0
        result.confidence = confidence_score(top_score)
        result.confidence_warning = check_confidence(result.confidence)
        result.steps.append(f"  -> Confidence: {result.confidence:.0%}")
        if result.confidence_warning:
            result.steps.append(f"  -> WARNING: {result.confidence_warning}")

        # Step 6: EXPLAIN using LLM + retrieved data (RAG)
        result.steps.append("STEP 6: EXPLAIN recommendations using LLM (RAG)")
        result.explanation = llm_client.explain_recommendations(
            query, recs, result.confidence
        )
        result.steps.append("  -> Explanation generated")

        logger.info(
            "Pipeline complete for %r: %d recs, confidence=%.0f%%",
            query, len(recs), result.confidence * 100,
        )
        return result

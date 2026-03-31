"""
Gemini LLM client for natural language understanding and explanation.

Handles two tasks:
1. Parse a natural language request into a structured UserProfile
2. Generate a human-friendly explanation of recommendations using
   retrieved song data (RAG)
"""

import os
import json
import logging
import time

logger = logging.getLogger(__name__)

# Will be set to True if Gemini is available
_gemini_available = False
_model = None

try:
    import google.generativeai as genai
    _gemini_available = True
except ImportError:
    pass

GEMINI_MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAY = 12  # seconds between retries on rate limit


def _call_with_retry(prompt: str) -> str:
    """Call Gemini with automatic retry on rate limit (429) errors."""
    for attempt in range(MAX_RETRIES):
        try:
            response = _model.generate_content(prompt)
            return (response.text or "").strip()
        except Exception as e:
            if "429" in str(e) and attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning("Rate limited, retrying in %ds (attempt %d/%d)",
                               wait, attempt + 1, MAX_RETRIES)
                time.sleep(wait)
            else:
                raise
    return ""


def init_gemini() -> bool:
    """Initialize the Gemini client. Returns True if successful."""
    global _model, _gemini_available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        logger.warning("GEMINI_API_KEY not set — LLM features disabled")
        _gemini_available = False
        return False
    if not _gemini_available:
        logger.warning("google-generativeai not installed — LLM features disabled")
        return False
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    logger.info("Gemini client initialized with model %s", GEMINI_MODEL_NAME)
    return True


def is_available() -> bool:
    return _gemini_available and _model is not None


def parse_user_request(request: str) -> dict:
    """
    Use Gemini to parse a natural language music request into structured
    preferences. Returns a dict with genre, mood, energy, likes_acoustic.

    Falls back to empty preferences if LLM is unavailable.
    """
    if not is_available():
        logger.info("LLM unavailable — returning empty profile for: %s", request)
        return {"genre": "", "mood": "", "energy": 0.5, "likes_acoustic": False}

    prompt = f"""You are a music preference parser. Extract structured preferences from the user's request.

User request: "{request}"

Return ONLY a JSON object with these fields (no markdown, no explanation):
- "genre": the music genre they want (e.g., "pop", "rock", "jazz", "lofi", "electronic", "hip-hop", "classical", "r&b", "metal", "country", "reggae", "latin", "ambient", "synthwave", "indie pop"). Use empty string "" if not specified.
- "mood": the mood they want (e.g., "happy", "chill", "intense", "relaxed", "focused", "moody", "romantic", "hype", "peaceful", "nostalgic", "aggressive", "euphoric", "melancholy", "dark"). Use empty string "" if not specified.
- "energy": a float 0.0-1.0 representing how energetic they want the music (0.0=very calm, 1.0=very intense). Default 0.5 if unclear.
- "likes_acoustic": true if they mention acoustic, unplugged, or similar. Default false.

JSON only:"""

    try:
        text = _call_with_retry(prompt)
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
        result = json.loads(text.strip())
        logger.info("Parsed request -> %s", result)
        return result
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to parse LLM response: %s", e)
        return {"genre": "", "mood": "", "energy": 0.5, "likes_acoustic": False}


def explain_recommendations(
    request: str,
    recommendations: list[dict],
    confidence: float,
) -> str:
    """
    Use Gemini to generate a natural language explanation of the
    recommendations, grounded in the actual song data (RAG).

    Falls back to a formatted summary if LLM is unavailable.
    """
    if not is_available():
        return _fallback_explanation(recommendations, confidence)

    song_context = "\n".join(
        f"- {r['title']} by {r['artist']} (genre: {r['genre']}, mood: {r['mood']}, "
        f"energy: {r['energy']}, score: {r['score']}) — reasons: {', '.join(r['reasons'])}"
        for r in recommendations
    )

    prompt = f"""You are a friendly music recommendation assistant. A user asked:
"{request}"

Based on their preferences, here are the top recommendations with scores and reasons:
{song_context}

Confidence in these recommendations: {confidence:.0%}

Write a brief, conversational response (3-5 sentences) that:
1. Acknowledges what the user asked for
2. Highlights the top 1-2 picks and why they match
3. Mentions the confidence level naturally
4. ONLY reference songs from the list above — do not invent songs

Keep it concise and helpful."""

    try:
        return _call_with_retry(prompt)
    except Exception as e:
        logger.error("LLM explanation failed: %s", e)
        return _fallback_explanation(recommendations, confidence)


def _fallback_explanation(recommendations: list[dict], confidence: float) -> str:
    """Plain text fallback when LLM is unavailable."""
    lines = [f"Confidence: {confidence:.0%}\n"]
    for r in recommendations:
        lines.append(f"  {r['title']} by {r['artist']} — Score: {r['score']:.2f}")
        lines.append(f"    Reasons: {', '.join(r['reasons'])}")
    return "\n".join(lines)

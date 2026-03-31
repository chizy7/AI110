# AI Music Recommender — Applied AI System

## Original Project

This project evolves the **Music Recommender Simulation** from Module 3, which was a content-based recommender that scored songs against a user profile using weighted categorical matches (genre, mood) and numerical proximity (energy). The original system used hardcoded user profiles (Python dictionaries) and produced recommendations via a simple scoring loop with no AI integration — everything was rule-based math.

## Summary

The AI Music Recommender transforms the Module 3 scoring engine into a full AI-powered system that accepts natural language music requests, uses retrieval-augmented generation (RAG) to find relevant songs, scores them with the proven weighted algorithm, and generates conversational explanations grounded in actual song data. It features a 6-step agentic workflow with observable intermediate steps, confidence scoring, input validation guardrails, and a comprehensive test harness.

**Why it matters**: Real recommendation systems combine retrieval, scoring, and natural language understanding. This project demonstrates how these components work together and where each one fails without the others.

---

## Architecture Overview

```
User Query (natural language)
        │
        ▼
┌─────────────────────┐
│  STEP 1: VALIDATE   │ ── Input guardrails (length, empty check)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  STEP 2: PARSE      │ ── LLM extracts structured profile from text
│  (Gemini LLM)       │    {genre, mood, energy, likes_acoustic}
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  STEP 3: RETRIEVE   │ ── Keyword index searches song catalog (RAG)
│  (Inverted Index)   │    Returns top 10 candidate songs
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  STEP 4: SCORE      │ ── Weighted scoring engine ranks candidates
│  (Recommender)      │    Genre(3.0) + Mood(2.0) + Energy(1.5) + ...
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  STEP 5: EVALUATE   │ ── Confidence scoring (score / max_possible)
│  (Self-Check)       │    Low confidence triggers user warning
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  STEP 6: EXPLAIN    │ ── LLM generates grounded explanation (RAG)
│  (Gemini + Context) │    Only references retrieved song data
└─────────────────────┘
         │
         ▼
   Final Response
   (recommendations + scores + reasons + explanation)
```

**Key components**:
- **Catalog** (`src/catalog.py`): Loads 20 songs from CSV, builds keyword inverted index
- **Recommender** (`src/recommender.py`): Weighted scoring engine from Module 3
- **LLM Client** (`src/llm_client.py`): Gemini integration for parsing + explanation with retry logic
- **Agent** (`src/agent.py`): Orchestrates the 6-step pipeline with full logging
- **Guardrails** (`src/guardrails.py`): Input validation, confidence thresholds, structured logging

---

## AI Features

### 1. Retrieval-Augmented Generation (RAG)
The system retrieves relevant songs from the catalog before generating responses. The LLM explanation in Step 6 receives only the retrieved and scored song data — it cannot invent songs that aren't in the catalog. This grounds the AI output in actual data.

### 2. Agentic Workflow
The 6-step pipeline (Validate → Parse → Retrieve → Score → Evaluate → Explain) runs as an observable chain. Each step logs its intermediate output, making the reasoning process transparent and debuggable.

### 3. Reliability and Testing
- **16 automated unit tests** covering catalog, scoring, retrieval, and guardrails
- **Evaluation harness** with 8 standard test cases and 4 edge cases
- **Confidence scoring** (0-100%) based on top score vs theoretical maximum
- **Structured logging** to both console and file (`docubot.log`)
- **Rate limit retry** with exponential backoff for Gemini API

---

## Setup Instructions

### 1. Clone and enter the project
```bash
git clone https://github.com/your-username/applied-ai-system-project.git
cd applied-ai-system-project
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API key
```bash
cp .env.example .env
# Edit .env and add your Gemini API key from https://aistudio.google.com/app/api-keys
```

### 4. Run the application
```bash
python -m src.main
```

### 5. Run tests
```bash
python -m pytest tests/ -v
```

### 6. Run evaluation harness
```bash
python evaluation.py
```

---

## Sample Interactions

### Example 1: Clear genre + mood request
```
Query: "I want upbeat pop music for a morning workout"

Agent Reasoning Chain:
  STEP 1: VALIDATE input
    -> Input accepted
  STEP 2: PARSE user request into preferences
    -> Extracted: genre='pop', mood='hype', energy=0.9, acoustic=False
  STEP 3: RETRIEVE candidate songs from catalog
    -> Found 3 candidates via keyword search
    -> Scoring 3 candidates
  STEP 4: SCORE and rank candidates
    -> Top pick: "Gym Hero" (score: 5.30)
  STEP 5: EVALUATE recommendation confidence
    -> Confidence: 62%
  STEP 6: EXPLAIN recommendations using LLM (RAG)
    -> Explanation generated

Top 3 Recommendations (confidence: 62%):
  1. Gym Hero by Max Pulse — 5.30
  2. Sunrise City by Neon Echo — 5.12
  3. Neon Cumbia by Los Voltios — 2.18
```

### Example 2: Acoustic + relaxed request
```
Query: "Something chill and acoustic for studying late at night"

Agent Reasoning Chain:
  STEP 2: PARSE user request into preferences
    -> Extracted: genre='lofi', mood='chill', energy=0.2, acoustic=True
  STEP 3: RETRIEVE candidate songs from catalog
    -> Found 5 candidates via keyword search
  STEP 4: SCORE and rank candidates
    -> Top pick: "Library Rain" (score: 8.09)
  STEP 5: EVALUATE recommendation confidence
    -> Confidence: 95%

Top 5 Recommendations (confidence: 95%):
  1. Library Rain by Paper Lanterns — 8.09
  2. Midnight Coding by LoRoom — 7.58
  3. Focus Flow by LoRoom — 5.72
```

### Example 3: Edge case — empty input
```
Query: ""

Agent Reasoning Chain:
  STEP 1: VALIDATE input
    -> REJECTED: Empty query. Please describe what kind of music you want.
```

---

## Design Decisions

**Why RAG instead of just prompting the LLM?** Without retrieval, the LLM would hallucinate song titles and artists that don't exist in our catalog. RAG constrains the LLM to only reference actual songs, making responses verifiable.

**Why keyword retrieval instead of embeddings?** For a 20-song catalog, keyword matching is fast, transparent, and sufficient. Semantic embeddings would add complexity without meaningful improvement at this scale. The inverted index approach is also directly debuggable — you can inspect exactly which words matched which songs.

**Why a 6-step agent instead of a single LLM call?** Breaking the pipeline into observable steps makes failures diagnosable. If the LLM misparses "chill" as "intense," you can see it in Step 2 without re-running the entire system. Each step logs its output, creating an audit trail.

**Why confidence scoring?** The scoring engine has a theoretical maximum (8.5 points). Expressing the top score as a percentage of that maximum gives users an intuitive quality signal. Low confidence (<40%) triggers an explicit warning rather than silently returning poor results.

**Trade-offs made**:
- Keyword retrieval misses synonyms ("calm" won't match "chill")
- The LLM parse adds latency (~2s per query) but enables natural language input
- Rate limiting on Gemini free tier limits throughput to ~2 queries/minute
- Small catalog means some genres only have 1 song

---

## Testing Summary

**Unit tests**: 16/16 passed — covers catalog loading, scoring math, retrieval, ranking order, confidence bounds, input validation, and guardrail triggers.

**Evaluation harness**: 8 standard queries + 4 edge cases.
- With LLM available: 8/8 standard queries return the correct genre as top result
- Edge cases: 4/4 handled correctly (empty and short queries rejected, nonsense and contradictory queries flagged as low confidence)
- Average confidence: 43% (lower when LLM rate-limited, higher with full LLM parsing)
- The system struggled most with rate limiting on the Gemini free tier — when the LLM parse fails, it falls back to retrieval-only mode with empty genre/mood, producing correct but lower-confidence results

---

## Limitations, Bias, and Responsible Use

**Limitations**:
- The catalog contains only 20 songs. Real systems have millions. With 1 song per genre in some cases, recommendations are deterministic.
- Keyword retrieval has no concept of synonyms. "Calm music" won't find "chill" songs unless the user uses the exact word.
- The LLM parse can misinterpret ambiguous requests. "Something dark" could mean mood=dark or genre=gothic, and the system has no way to disambiguate.

**Potential for misuse**:
- The system could be adapted to manipulate listening behavior (e.g., always recommending songs from a specific label). The transparent scoring prevents this — every recommendation includes point-by-point reasons.
- If connected to a real streaming service, biased scoring weights could create filter bubbles. The confidence scoring helps users recognize when results may not match their intent.

**What surprised me during testing**:
- The "Gym Hero" effect persisted from Module 3 — songs with extreme numerical values (high energy + high valence + high danceability) accumulate baseline points and appear across many profiles. This is a structural bias in any additive scoring system.
- LLM rate limiting gracefully degrades rather than crashing — the system falls back to retrieval-only scoring, which still produces reasonable (if lower-confidence) results.

**AI collaboration**:
- **Helpful**: AI suggested using an inverted index for retrieval instead of scanning all songs for every query, which was a cleaner approach than my initial idea of regex matching.
- **Flawed**: AI initially suggested using cosine similarity between embedding vectors for the 20-song catalog, which was massive overkill. Simple keyword matching achieved the same retrieval accuracy with zero dependencies and instant execution.

---

## TF Reflection

This project made it clear to me that the difference between something that works and something you can rely on comes down to how you handle failure, not how many features you have. The Module 3 recommender worked fine when everything was hardcoded. But once I added natural language input through the LLM, a new class of problems showed up. Things like rate limits, unclear parsing, and mismatched vocabulary. The agent pipeline is not there to improve recommendations directly. It is there to surface failures, explain them, and recover from them. Each step can break on its own, log what happened, and fall back without taking down the whole system.

The biggest takeaway for me was understanding RAG as a constraint rather than a capability. Passing retrieved song data into the LLM does not make it smarter. It makes it grounded. Without that constraint, the model can easily make up something like “Midnight Vibes by DJ Shadow” and say it with confidence. With RAG, it is limited to actual songs in the catalog like Library Rain or Midnight Coding. That step is less about helping the model and more about controlling what it is allowed to say.

Building the evaluation harness also shifted how I think about testing. Unit tests check if the code does what it is supposed to do. The evaluation harness checks how the system behaves in practice. Those are not the same thing. All 16 unit tests pass, but the evaluation showed that 5 out of 8 standard queries drop to low confidence when the LLM hits rate limits. So the implementation is technically correct, but the system becomes unreliable under real conditions. That gap is what matters in production.

AI tools were helpful for the repetitive parts, like setting up retry logic, organizing logging, and drafting the structure of the evaluation harness. But the core decisions still came down to me. Choosing keyword-based retrieval over embeddings, setting the confidence threshold at 40 percent, and deciding on a 6 step agent pipeline instead of something simpler all required thinking through tradeoffs. The AI can help build, but it does not replace the role of deciding how the system should behave.

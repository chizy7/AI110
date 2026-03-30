# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

This system suggests 3 to 5 songs from a small catalog of 20 tracks based on a user's preferred genre, mood, energy level, and acoustic preference. It is designed for classroom exploration and learning about how recommender systems work. It is not intended for real users or production deployment.

The system assumes a single user with a fixed taste profile. It does not learn or adapt over time.

---

## 3. How the Model Works

Imagine you walk into a record store and tell the clerk: "I like pop music, happy vibes, and high energy." The clerk would mentally go through every album on the shelf, give each one a score based on how well it matches what you said, and hand you the top 5.

That is exactly what VibeFinder does:

1. It reads your preferences: favorite genre, favorite mood, target energy level, and whether you like acoustic music.
2. For every song in the catalog, it checks: Does the genre match? Does the mood match? How close is this song's energy to what you want?
3. Each match earns points — genre match is worth the most (3 points), mood match is next (2 points), and energy closeness can earn up to 1.5 points. Small bonuses come from valence, danceability, and acoustic qualities.
4. It sorts all songs from highest to lowest score and shows you the top results, along with the reasons each song scored well.

---

## 4. Data

- **Catalog size**: 20 songs in `data/songs.csv`
- **Original starter**: 10 songs (pop, lofi, rock, ambient, jazz, synthwave, indie pop)
- **Added**: 10 songs covering r&b, hip-hop, classical, latin, country, metal, electronic, reggae
- **Genres represented**: 12 distinct genres
- **Moods represented**: 12 distinct moods (happy, chill, intense, relaxed, focused, moody, romantic, hype, peaceful, nostalgic, aggressive, euphoric, melancholy, dark)
- **Missing from the dataset**: K-pop, Afrobeats, folk, punk, and many other global genres. The catalog skews toward English-language Western music. Lyrics and language are not represented at all.

---

## 5. Strengths

- **Clear differentiation**: The system produces visibly different top-5 lists for different user types. The "Chill Lofi Listener" gets Library Rain and Midnight Coding, while the "Intense Rock Lover" gets Storm Runner — no overlap in the top results.
- **Transparency**: Every recommendation comes with a plain-English explanation showing exactly which factors contributed and how many points each earned. There is no black box.
- **Intuitive results for core profiles**: For the "Energetic Pop Fan," Sunrise City (pop, happy, energy 0.82) ranks first with 7.29 points — this matches what a human would pick. Gym Hero ranks second, which also makes sense since it is pop but intense rather than happy.
- **Acoustic preference works well**: The "Mellow Jazz Explorer" gets acoustic-heavy songs boosted into their list (Coffee Shop Stories, Monsoon Jazz), while non-acoustic profiles correctly ignore this signal.

---

## 6. Limitations and Bias

**Genre over-prioritization**: Genre match is worth 3.0 points — the single largest factor. This means a pop song with the wrong mood and wrong energy can still outscore a non-pop song that perfectly matches the user's mood and energy. In the "Sad but High-Energy" edge case, the user wants melancholy mood at 0.95 energy. The system recommends Gym Hero (pop, intense, 0.93 energy) at #1 because the genre match (+3.0) overpowers everything. Monsoon Jazz — which actually matches the melancholy mood — ranks #3 because it lacks the genre bonus and has low energy (0.44). The system prioritizes genre identity over emotional fit.

**No graceful fallback for unknown genres**: When tested with "reggaeton" (a genre not in the catalog), the system cannot match any song's genre, so it falls back entirely on mood and energy. The results are reasonable but the user gets no genre-relevant recommendations at all. A real system would use genre similarity (reggaeton is close to latin) rather than exact string matching.

**Binary categorical matching creates blind spots**: "Indie pop" and "pop" are treated as completely different genres (0 points for a mismatch). A user who likes pop would intuitively enjoy indie pop songs like Rooftop Lights, but the system only recommends it when the mood happens to match. This is a fundamental limitation of exact-match scoring.

**Acoustic + intense is contradictory but undetected**: The "Wants Everything Acoustic + Intense" profile asks for metal (aggressive, 0.95 energy) but also likes acoustic. Iron Lung correctly ranks #1 for genre+mood+energy, but the acoustic bonus (+1.0) goes to Backroad Dust (country, nostalgic, 0.50 energy) at #2, pushing it above songs that are much closer in energy. The system does not recognize that "acoustic metal" is rare and does not warn the user about conflicting preferences.

**Small catalog bias**: With only 1-2 songs per genre, a genre match almost guarantees a specific song. Rock fans will always get Storm Runner because it is the only rock song. This makes the system deterministic in a way that would feel repetitive in practice.

---

## 7. Evaluation

### Profiles Tested

Seven user profiles were tested — four core profiles and three adversarial edge cases:

| Profile | Top Result | Score | Intuition Check |
|---------|-----------|-------|-----------------|
| Energetic Pop Fan | Sunrise City | 7.29 | Correct — pop, happy, high energy |
| Chill Lofi Listener | Library Rain | 8.09 | Correct — lofi, chill, low energy, acoustic |
| Intense Rock Lover | Storm Runner | 7.05 | Correct — only rock song, perfect match |
| Mellow Jazz Explorer | Coffee Shop Stories | 8.08 | Correct — jazz, relaxed, acoustic |
| EDGE: Sad but High-Energy | Gym Hero | 5.30 | Surprising — user wants melancholy but gets intense pop |
| EDGE: Genre Doesn't Exist | Neon Cumbia | 4.25 | Reasonable fallback — mood+energy carry the score |
| EDGE: Acoustic + Intense | Iron Lung | 6.85 | Correct #1, but acoustic bonus distorts #2-5 |

### Weight Experiment

We ran an experiment where genre weight was halved (3.0 to 1.5) and energy weight was doubled (1.5 to 3.0):

- **Pop Fan**: Neon Cumbia jumped from #3 to #2 (energy closeness now worth more than genre). Gym Hero dropped from #2 to #4.
- **Rock Lover**: Gym Hero (pop/intense) climbed from #2 to #2 with a much higher score (5.74 vs 4.28) because its energy proximity was amplified. Non-genre songs became more competitive.
- **Reggaeton edge case**: Rooftop Lights overtook Neon Cumbia for #1 because energy proximity (0.76 vs 0.80 = small gap) was now worth more points.
- **Overall finding**: Doubling energy made results more "energy-homogeneous" — songs clustered by energy level regardless of genre. This felt less natural. The original weights (genre=3.0) better match how humans think about music: genre first, then refine by mood and energy.

### What Surprised Us

"Gym Hero" keeps appearing in multiple profiles' top 5 — it shows up for the Pop Fan, the Rock Lover, the Sad-but-High-Energy user, and the Acoustic+Intense user. This is because Gym Hero has high energy (0.93), high valence (0.77), and high danceability (0.88), giving it strong baseline scores even without genre or mood matches. In a real system, this would be a popularity bias problem — some songs "game" the algorithm by having extreme numerical values.

---

## 8. Future Work

- **Genre similarity**: Instead of exact string matching, use a genre distance map (e.g., indie pop is 0.8 similar to pop, 0.3 similar to rock) so near-misses still earn partial credit.
- **Negative signals**: Add skip history or disliked genres so the system can penalize, not just reward. Currently every song gets at least ~1.5 points from valence+danceability+energy even if the user would hate it.
- **Diversity injection**: After scoring, ensure the top-k results include at least 2 different genres to prevent the filter bubble effect.
- **Multi-preference profiles**: Let users specify multiple genres or moods (e.g., "I like both jazz and lofi") instead of forcing a single favorite.
- **Conflict detection**: Warn users when their preferences are contradictory (e.g., acoustic + metal) and explain that few songs will satisfy both.

---

## 9. TF Personal Reflection

### Biggest Learning Moment

The moment that changed how I think about this project was running the "Sad but High-Energy" edge case. The user asked for melancholy pop at 0.95 energy, and the system confidently returned Gym Hero — an intense, upbeat workout anthem. The math was correct: genre match (+3.0) plus energy closeness (+1.47) gave it a high score. But the recommendation was emotionally wrong. That gap between "mathematically correct" and "humanly right" is the core tension in every recommender system. It made me realize that the weights we choose are not neutral math — they are value judgments about what matters in music, and those judgments have real consequences for what people discover (or never discover).

### How AI Tools Helped — and Where I Double-Checked

AI tools were most useful for scaffolding: generating the initial CSV expansion with diverse genres, suggesting the proximity formula for energy scoring, and formatting the Mermaid diagram. These are tasks where speed matters more than judgment. But I had to double-check the AI's work in two key areas. First, when generating new songs for the CSV, I verified that the numerical values were realistic (e.g., a classical piece should have high acousticness and low energy, not random values). Second, when the AI suggested scoring logic, I manually traced through the math with a specific song to confirm the formula rewarded closeness rather than raw magnitude. The AI is a fast first-draft writer, but the human still needs to validate whether the output makes domain sense.

### Why Simple Algorithms Feel Like Real Recommendations

The most surprising thing was how little math it takes to produce results that "feel" like real recommendations. The entire scoring function is about 15 lines of code — just add points for matches and proximity. Yet when I ran it for the "Energetic Pop Fan" and saw Sunrise City at #1, it genuinely felt like what Spotify would suggest. The reason is that content-based filtering works well when the user's preferences are clear and the catalog is small enough. The illusion breaks when preferences conflict (sad + high-energy), when genres are missing (reggaeton), or when the catalog is too small to offer variety. Real platforms hide these cracks with massive datasets and hybrid algorithms, but the fundamental logic is not that different from what we built here.

### What I Would Try Next

If I extended this project, the first thing I would add is **genre similarity scoring** — a lookup table where "indie pop" is 0.8 similar to "pop" and 0.3 similar to "rock," so near-misses earn partial credit instead of zero. The second addition would be **negative preferences** — letting users say "I don't like country" so the system can subtract points, not just add them. Third, I would introduce **diversity enforcement**: after scoring, ensure the top 5 includes at least 2 different genres to prevent the filter bubble where a pop fan only ever hears pop. These three changes would address the biggest limitations we found during testing without fundamentally changing the architecture.

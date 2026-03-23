# Model Card: Mood Machine

This model card documents **two** mood classifiers built for the Mood Machine project:

1. A **rule-based model** implemented in `mood_analyzer.py`
2. A **machine learning model** implemented in `ml_experiments.py` using scikit-learn

Both were developed and compared during this project.

## 1. Model Overview

**Model type:**
Both a hand-coded rule-based classifier and a logistic regression ML classifier were built and compared on the same dataset.

**Intended purpose:**
Classify short social-media-style text messages (1–2 sentences) into one of four mood labels: `positive`, `negative`, `neutral`, or `mixed`.

**How it works (brief):**

- **Rule-based:** Text is tokenized and cleaned (punctuation removed, emojis extracted, repeated characters normalized). Each token is checked against positive/negative word lists, slang dictionaries, and emoji sentiment maps. Matches increase or decrease a numeric score. A negation detector flips the polarity when words like "not" or "never" precede a sentiment word. The final score and signal pattern determine the label.
- **ML:** Text is converted to bag-of-words vectors using `CountVectorizer`, then a `LogisticRegression` model is trained on those vectors and the human-assigned labels. It learns statistical associations between words and labels rather than following hand-written rules.

## 2. Data

**Dataset description:**
`SAMPLE_POSTS` contains **19 short posts** with matching labels in `TRUE_LABELS`. The dataset started with 6 posts provided in the starter code and was expanded in two rounds:
- Round 1 (+8 posts): Added slang ("lowkey", "no cap", "ngl", "mid"), emojis (💀, 🔥, 😭, 🎉, 😩, 😌), sarcasm, and mixed-emotion posts.
- Round 2 (+5 posts): Added understated positivity ("can't complain"), implicit negativity ("not even mad just disappointed"), ironic self-awareness ("pain but make it aesthetic"), and humor-masking-pain posts.

**Labeling process:**
Labels were assigned by the developer based on the *intended human meaning* of each post, not just the literal words. Several posts were deliberately ambiguous:
- "just got the internship offer omggg 😭🎉" — labeled `positive` even though 😭 typically signals sadness, because here it represents happy tears.
- "ngl today was mid at best" — labeled `negative` even though "at best" contains the word "best", because the phrase as a whole means "mediocre at most."
- "pain but make it aesthetic 🥲" — labeled `mixed` because it blends real sadness with ironic self-awareness.

**Important characteristics of the dataset:**
- Includes Gen-Z slang ("lowkey", "no cap", "mid", "bruh", "ngl", "rn")
- Contains emoji-heavy posts where emojis carry the primary sentiment
- Includes sarcasm ("I absolutely love sitting in traffic for two hours")
- Contains posts with mixed or contradictory emotions
- All posts are short (1–2 sentences), informal, English-only

**Possible issues with the dataset:**
- **Very small** — 19 examples is far too few for any model to generalize reliably.
- **Label imbalance** — 6 negative, 5 positive, 5 mixed, 3 neutral. "Neutral" is underrepresented.
- **Single labeler** — all labels reflect one person's interpretation. No inter-annotator agreement was measured.
- **Narrow demographic** — the slang, emojis, and cultural references skew toward young, English-speaking, internet-native users.

## 3. How the Rule-Based Model Works

**Preprocessing (`preprocess`):**
1. Lowercase and strip whitespace
2. Split on whitespace into raw tokens
3. Extract emoji characters as separate tokens (so "omggg😭" becomes ["omgg", "😭"])
4. Strip punctuation from text tokens
5. Normalize repeated characters (3+ of the same character → 2, e.g., "soooo" → "soo")

**Scoring rules (`score_text`):**
- Each token is checked against four sources: `POSITIVE_WORDS` (19 words), `NEGATIVE_WORDS` (19 words), `POSITIVE_SLANG` (9 terms), `NEGATIVE_SLANG` (5 terms), `POSITIVE_EMOJIS` (9), and `NEGATIVE_EMOJIS` (7).
- Positive match → score +1. Negative match → score −1.
- **Negation handling:** If the token immediately before a sentiment word is a negator (`not`, `no`, `never`, `don't`, `doesn't`, `isn't`, `wasn't`, `aren't`), the polarity is flipped. Example: "not happy" → −1 instead of +1.
- Emoji signals are scored the same as keywords (+1 or −1).

**Label mapping (`predict_label`):**
- If *both* positive and negative signals were detected → `mixed`
- Score > 0 → `positive`
- Score < 0 → `negative`
- Score == 0 → `neutral`

**Strengths of this approach:**
- Fully transparent — every prediction can be traced to specific tokens and scores
- Handles clear-cut cases well: "I love this class" → positive (score +1, "love" detected)
- Negation works for simple cases: "I am not happy about this" → negative (score −1, "not happy" detected)
- Slang and emojis provide signal where standard keywords fail: "this song is absolute fire 🔥" → positive (score +2, "fire" + 🔥)

**Weaknesses of this approach:**
- Cannot detect **sarcasm**: "I absolutely love sitting in traffic" → predicted `positive` (true: `negative`). The model takes "love" at face value.
- **Context-dependent emojis** are fixed-polarity: 😭 is always negative, so "just got the internship offer 😭🎉" → predicted `mixed` (true: `positive`). The model can't tell happy tears from sad tears.
- **Idioms are invisible**: "at best" contains "best" (+1), so "ngl today was mid at best" → predicted `mixed` (true: `negative`).
- **Understated language** gets no score: "can't complain life is decent rn" → predicted `neutral` (true: `positive`). Neither "decent" nor "can't complain" are in any word list.
- **Negation scope** is limited to one token: "I'm not even mad" — "not" is followed by "even", not "mad", so the negation is wasted.

## 4. How the ML Model Works

**Features used:**
Bag-of-words representation using `CountVectorizer` — each post is converted into a vector of word counts.

**Training data:**
The model trained on all 19 posts in `SAMPLE_POSTS` with labels from `TRUE_LABELS`.

**Training behavior:**
The model achieved **100% accuracy on its training data** across all 19 examples. When the dataset was expanded from 14 → 19 posts, accuracy remained at 100%. This is expected — with so few examples and many features, logistic regression can perfectly memorize the training set.

**Strengths:**
- Learns patterns automatically without hand-coded rules
- Correctly classifies sarcasm, context-dependent emojis, and understated language *on training data*
- Adapts when new labeled data is added — no manual rule updates needed

**Weaknesses:**
- **Overfitting** — 100% training accuracy on 19 examples does not mean the model generalizes. It has memorized the answers.
- **No real test set** — the model is evaluated on the same data it trained on, which inflates accuracy.
- **Black box** — unlike the rule-based model, you can't easily ask "why did you predict positive?" The logistic regression coefficients exist but are harder to interpret than a score breakdown.
- **Data-hungry** — with only 19 examples, any single mislabeled post could significantly shift the model's behavior.

## 5. Evaluation

**How the models were evaluated:**
Both models were evaluated on the 19 labeled posts in `dataset.py`. The rule-based model was also tested on 12 additional "breaker" sentences designed to probe specific failure modes.

**Accuracy:**
| Model | Accuracy | Correct/Total |
|-------|----------|---------------|
| Rule-based | 63% | 12/19 |
| ML (logistic regression) | 100% | 19/19 (training data) |

**Examples of correct predictions (rule-based):**

1. `"I am not happy about this"` → predicted `negative`, true `negative`
   - Why: Negation handler detects "not" before "happy" and flips polarity to −1. Score = −1 → negative. This demonstrates the negation enhancement working correctly.

2. `"vibes are immaculate today honestly chill day 😌"` → predicted `positive`, true `positive`
   - Why: Three positive signals fire — "immaculate" (slang, +1), "chill" (keyword, +1), 😌 (emoji, +1). Score = +3 → positive. This shows slang + emoji + keyword working together.

3. `"lmaooo this group project is a disaster 💀😂"` → predicted `mixed`, true `mixed`
   - Why: 💀 scores −1 (negative emoji) and 😂 scores +1 (positive emoji). Both signals present → mixed. The model correctly captures the laughing-at-misery tone.

**Examples of incorrect predictions (rule-based):**

1. `"I absolutely love sitting in traffic for two hours"` → predicted `positive`, true `negative`
   - Why: "love" scores +1. The model has no concept of sarcasm — it takes the positive keyword literally. No negative signals fire because "traffic" and "sitting" aren't in any word list. Score = +1 → positive.

2. `"I'm not even mad just disappointed"` → predicted `neutral`, true `negative`
   - Why: Neither "mad" nor "disappointed" are in the negative word list. The negator "not" precedes "even" (not a sentiment word), so it's wasted. The model sees zero signal words and returns neutral. Score = 0 → neutral.

3. `"just got the internship offer omggg 😭🎉"` → predicted `mixed`, true `positive`
   - Why: 😭 is hardcoded as negative (−1) and 🎉 as positive (+1). Both signals present → mixed. But in context, 😭 means overwhelmed joy, not sadness. The model can't distinguish emoji intent from emoji face value.

**How failures differ between models:**
The ML model gets all 19 training examples correct, including the sarcasm and emoji cases the rule-based model misses. However, this is because it memorized the training data, not because it "understands" sarcasm. If given a new sarcastic sentence it hasn't seen, it would likely fail too.

## 6. Limitations

- **Tiny dataset** — 19 examples is insufficient for meaningful generalization. Both models are effectively toys.
- **No test set** — the ML model's 100% accuracy is on training data. Real evaluation requires held-out data the model has never seen.
- **Sarcasm is undetectable** by the rule-based model. This is a fundamental limitation of keyword matching — sarcasm requires understanding that the speaker's intent contradicts their literal words.
- **Fixed emoji polarity** — emojis like 😭 and 💀 can mean different things in different contexts (happy tears vs. sadness, humor vs. death). The rule-based model assigns them a single fixed sentiment.
- **Negation is shallow** — only checks the immediately preceding token. Phrases like "I could not be more disappointed" or "not even mad" have gaps between the negator and the sentiment word.
- **English-only, informal register** — the model only handles short, informal English posts. It has no support for other languages, formal writing, or longer text.
- **Single-label limitation** — each post gets exactly one label, but real posts often express multiple emotions simultaneously.

## 7. Ethical Considerations

- **Misclassifying distress:** If a user writes "I'm fine 🙂" (which often signals distress), the model returns `neutral`. In a mental health context, missing negative sentiment could mean failing to flag someone who needs help.
- **Cultural and demographic bias:** The word lists and slang dictionaries reflect a specific demographic — young, English-speaking, internet-native users. The model would likely misinterpret:
  - African American Vernacular English (AAVE) expressions
  - Regional slang from outside the US
  - Non-English text or code-switching
  - Formal or professional communication styles
- **Privacy:** Mood detection on personal messages raises consent and surveillance concerns. Even a toy model like this normalizes the idea of automated emotional analysis of private communication.
- **Labeling subjectivity:** All labels were assigned by a single person. Different annotators from different backgrounds would likely disagree on posts like "this is fine" (genuine vs. sarcastic) or "pain but make it aesthetic" (funny vs. concerning). A model trained on one person's interpretation encodes that person's biases.
- **False confidence:** The ML model's 100% accuracy could mislead someone into thinking the system is reliable. Without a proper test set, this number is meaningless as a measure of real-world performance.

## 8. Ideas for Improvement

- **Add more labeled data** — at least 100–200 examples across diverse language styles, with multiple annotators per post
- **Create a real test set** — split data into training and evaluation sets so ML accuracy reflects generalization, not memorization
- **Use TF-IDF instead of CountVectorizer** — would down-weight common words like "the" and "is" that add noise
- **Add phrase-level rules** — detect multi-word expressions like "not even", "at best", "can't complain" as units rather than individual tokens
- **Context-aware emoji handling** — use surrounding words to disambiguate emojis (😭 near "offer" or "got" likely means joy)
- **Sarcasm detection heuristics** — flag sentences where strong positive words co-occur with typically negative contexts ("love" + "traffic", "great" + "Monday")
- **Use a pretrained language model** — a transformer like BERT or a small LLM would capture context, sarcasm, and idioms far better than either approach here
- **Inter-annotator agreement** — have multiple people label the same posts and measure agreement to identify genuinely ambiguous cases

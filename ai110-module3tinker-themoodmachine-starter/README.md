# The Mood Machine

The Mood Machine is a simple text classifier that begins with a rule based approach and can optionally be extended with a small machine learning model. It tries to guess whether a short piece of text sounds **positive**, **negative**, **neutral**, or even **mixed** based on patterns in your data.

This lab gives you hands on experience with how basic systems work, where they break, and how different modeling choices affect fairness and accuracy. You will edit code, add data, run experiments, and write a short model card reflection.

---

## Repo Structure

```plaintext
├── dataset.py         # Starter word lists and example posts (you will expand these)
├── mood_analyzer.py   # Rule based classifier with TODOs to improve
├── main.py            # Runs the rule based model and interactive demo
├── ml_experiments.py  # (New) A tiny ML classifier using scikit-learn
├── model_card.md      # Template to fill out after experimenting
└── requirements.txt   # Dependencies for optional ML exploration
```

---

## Getting Started

1. Open this folder in VS Code.
2. Make sure your Python environment is active.
3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the rule-based starter:

    ```bash
    python main.py
    ```

If pieces of the analyzer are not implemented yet, you will see helpful errors that guide you to the TODOs.

To try the ML model later, run:

```bash
python ml_experiments.py
```

---

## What You Will Do

During this lab you will:

- Implement the missing parts of the rule based `MoodAnalyzer`.
- Add new positive and negative words.
- Expand the dataset with more posts, including slang, emojis, sarcasm, or mixed emotions.
- Observe unusual or incorrect predictions and think about why they happen.
- Train a tiny machine learning model and compare its behavior to your rule based system.
- Complete the model card with your findings about data, behavior, limitations, and improvements.
- The goal is to help you reason about how models behave, how data shapes them, and why even small design choices matter.

---

## Tips

- Start with preprocessing before updating scoring rules.
- When debugging, print tokens, scores, or intermediate choices.
- Ask an AI assistant to help create edge case posts or unusual wording.
- Try examples that mislead or confuse your model. Failure cases teach you the most.

---

## TF Summary

The core idea in this module is helping students see how rule-based and ML-based text classifiers actually make decisions, and more importantly, why neither of them is magic. Where students tend to get stuck is that gap between how a human reads a sentence and how a model processes it. Things like sarcasm, subtle tone, or even emojis completely break that illusion because the model is really just looking at patterns, not intent.

AI (Copilot) was helpful in some very real ways. It made it easier to come up with realistic, slang-heavy examples, and it did a good job walking through how tokenization and scoring flow through the system. It also helped surface why certain predictions were failing. But it also had moments where it sounded very confident while suggesting fixes that actually made things worse, especially with edge cases. So every suggestion had to be grounded in testing, not just accepted at face value.

If I were helping a student who is stuck on sarcasm, I would slow them down and have them print out the tokens and the score for that sentence. Then I would ask: which word is actually driving this prediction, and does the model have any way to understand that the speaker does not mean it literally? That usually clicks. It shifts them from thinking the model is “wrong” to understanding the limitation of how it works.

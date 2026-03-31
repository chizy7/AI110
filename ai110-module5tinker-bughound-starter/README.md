# 🐶 BugHound

BugHound is a small, agent-style debugging tool. It analyzes a Python code snippet, proposes a fix, and runs basic reliability checks before deciding whether the fix is safe to apply automatically.

---

## What BugHound Does

Given a short Python snippet, BugHound:

1. **Analyzes** the code for potential issues  
   - Uses heuristics in offline mode  
   - Uses Gemini when API access is enabled  

2. **Proposes a fix**  
   - Either heuristic-based or LLM-generated  
   - Attempts minimal, behavior-preserving changes  

3. **Assesses risk**  
   - Scores the fix  
   - Flags high-risk changes  
   - Decides whether the fix should be auto-applied or reviewed by a human  

4. **Shows its work**  
   - Displays detected issues  
   - Shows a diff between original and fixed code  
   - Logs each agent step

---

## Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# or
.venv\Scripts\activate      # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running in Offline (Heuristic) Mode

No API key required.

```bash
streamlit run bughound_app.py
```

In the sidebar, select:

* **Model mode:** Heuristic only (no API)

This mode uses simple pattern-based rules and is useful for testing the workflow without network access.

---

## Running with Gemini

### 1. Set up your API key

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```text
GEMINI_API_KEY=your_real_key_here
```

### 2. Run the app

```bash
streamlit run bughound_app.py
```

In the sidebar, select:

* **Model mode:** Gemini (requires API key)
* Choose a Gemini model and temperature

BugHound will now use Gemini for analysis and fix generation, while still applying local reliability checks.

---

## Running Tests

Tests focus on **reliability logic** and **agent behavior**, not the UI.

```bash
pytest
```

You should see tests covering:

* Risk scoring and guardrails
* Heuristic fallbacks when LLM output is invalid
* End-to-end agent workflow shape
* False positive prevention (print inside strings)
* New import detection in risk assessment
* High-severity auto-fix blocking

---

## TF Reflection

[**Full Model Card**](model_card.md)

The biggest thing this project showed me is that building the AI part is actually the easy part. The harder part is figuring out what happens when the AI gets things wrong. BugHound’s 5 step agent loop looks simple when you draw it out, but every step has its own failure modes. The LLM might return invalid JSON, ignore instructions and wrap code in markdown fences, or hit rate limits in the middle of the workflow. Each of those needs a fallback, and every fallback needs to be tested. At that point, the system is less about intelligence and more about handling failure cleanly.

The moment that really made this click for me was the false positive with `print()` inside a string. The check was just `"print(" in code`. It looked fine, passed the tests, and worked on all the sample inputs. But a simple edge case broke everything. The fixer ended up modifying `print(` inside a string and corrupted the output without any warning. The risk assessor did not catch it because the structure still looked valid. That showed me how one small mistake at the top of the pipeline can quietly affect everything downstream. In an agent system, errors do not stay isolated, they propagate.

Working on the risk assessor changed how I think about automation decisions. The original rule was straightforward. If the score is 75 or higher, apply the fix. But then I realized a high severity issue like a bare except could still pass that threshold if the fix looked clean. That means the system could automatically change control flow or error handling, which is exactly where subtle bugs hide. Adding a rule to always block auto fix for high severity issues was a small change, but it represents something bigger. Just because a fix looks correct does not mean it is safe to apply automatically.

AI tools helped with the repetitive parts like setting up test cases, suggesting regex for matching patterns, and outlining the model card. But the important decisions were not something the AI could make. Figuring out where to put guardrails, deciding what severity should block auto fix, and choosing which failure modes to prioritize all required stepping through the system and understanding how everything connects. The AI can help write pieces of the system, but it does not decide how the system should behave.


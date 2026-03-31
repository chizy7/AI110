# BugHound Mini Model Card (Reflection)

---

## 1) What is this system?

**Name:** BugHound

**Purpose:** BugHound is an agentic code analysis tool that scans Python code for reliability and quality issues, proposes minimal fixes, and evaluates whether those fixes are safe enough to apply automatically or require human review. It operates as a 5-step reasoning pipeline rather than a single-shot tool, making each decision observable and auditable.

**Intended users:** Students learning about agentic AI workflows, reliability engineering, and human-in-the-loop decision-making. Not intended for production use on real codebases.

---

## 2) How does it work?

BugHound runs a 5-step agentic loop for every code snippet it receives:

1. **PLAN**: The agent logs that it is beginning a scan-and-fix workflow. This step is lightweight — it sets up the trace log and establishes intent.

2. **ANALYZE**: The agent decides how to detect issues. If a Gemini API key is configured and the client is available, it sends the code to the LLM with a structured prompt that demands a JSON array of issues. If the LLM is unavailable, returns non-JSON, or throws an error, the agent falls back to heuristic analysis — three regex-based pattern checks for bare `except:` blocks, `print()` statements at the statement level, and `TODO` comments.

3. **ACT**: The agent proposes a fix. Again, it tries the LLM first (with a prompt requesting minimal, behavior-preserving rewrites), then falls back to heuristic fixes (replacing `except:` with `except Exception as e:`, replacing `print()` with `logging.info()`). If no issues were found, it returns the original code unchanged.

4. **TEST**: The agent passes the original code, fixed code, and detected issues to the risk assessor. This module scores the fix 0-100 based on issue severity, structural changes (code length, removed returns, modified exception handling, new imports), and assigns a risk level (low/medium/high).

5. **REFLECT**: The agent decides whether to recommend auto-fix. Auto-fix is only allowed when the risk level is "low" AND no high-severity issues are present. Otherwise it recommends human review.

**Heuristic mode** handles steps 2 and 3 with regex patterns and string replacement. **Gemini mode** uses the LLM for both, with the detailed prompts from the `prompts/` folder. Steps 1, 4, and 5 always run the same logic regardless of mode.

---

## 3) Inputs and outputs

**Inputs tested:**

| Input | Description |
|-------|-------------|
| `sample_code/cleanish.py` | Clean function using logging correctly, no issues |
| `sample_code/print_spam.py` | Multiple print() statements, no error handling |
| `sample_code/flaky_try_except.py` | Bare `except:` block with resource leak |
| `sample_code/mixed_issues.py` | All three issue types: print, bare except, TODO |
| Empty string | Edge case — no code at all |
| Comments-only file | Edge case — no executable code |
| `print()` inside string literal | Edge case — tests false positive detection |
| `TODO` in variable name | Edge case — tests false positive detection |

**Outputs:**

- **Issue types detected**: Code Quality (print statements), Reliability (bare except), Maintainability (TODO comments)
- **Fixes proposed**: `except:` replaced with `except Exception as e:`, `print()` replaced with `logging.info()` (with `import logging` added), TODO comments left unchanged (no automated fix for incomplete logic)
- **Risk reports**:
  - `cleanish.py`: 100/100, low risk, auto-fix approved (nothing changed)
  - `print_spam.py`: 85/100, low risk, auto-fix approved (only low-severity issue, import flagged)
  - `flaky_try_except.py`: 55/100, medium risk, auto-fix blocked (high severity)
  - `mixed_issues.py`: 20/100, high risk, auto-fix blocked (stacked penalties)
  - Empty string: 0/100, high risk (no fix produced)

---

## 4) Reliability and safety rules

### Rule 1: Return statement removal check

```python
if "return" in original_code and "return" not in fixed_code:
    score -= 30
```

- **What it checks**: Whether the fix removed all return statements from code that previously had them.
- **Why it matters**: Removing a return statement silently changes function behavior from returning a value to returning `None`. Callers relying on the return value would break without any error, making this one of the hardest bugs to diagnose.
- **False positive**: If the fix legitimately refactors a function from returning a value to raising an exception (a valid pattern), this rule penalizes it. For example, replacing `return 0` in an error path with `raise ValueError("...")` would trigger the penalty even though the fix is an improvement.
- **False negative**: The rule checks for complete removal only. If the fix changes `return result` to `return None` or `return 0`, the rule does not detect it because "return" is still present. The value changed, but the rule only checks for the keyword's existence.

### Rule 2: New imports detection (added during this activity)

```python
new_imports = fixed_imports - original_imports
if new_imports:
    score -= 10
```

- **What it checks**: Whether the fix introduces import statements that were not in the original code.
- **Why it matters**: New imports add dependencies. In the heuristic fixer, `import logging` is always safe. But an LLM fixer might add `import os`, `import subprocess`, or `import sys` — any of which could introduce security risks or break in environments where those modules are unavailable or restricted.
- **False positive**: When the heuristic fixer replaces `print()` with `logging.info()`, it must add `import logging`. This is a safe, expected change, but the rule still deducts 10 points for it. The deduction is small enough that it does not block auto-fix for low-severity cases (85/100 still qualifies as "low" risk).
- **False negative**: The rule only checks for top-level `import` and `from` statements. If the LLM adds an inline import inside a function (`def f(): import os`), the rule misses it because it only scans lines starting with import keywords.

---

## 5) Observed failure modes

### Failure 1: False positive — `print()` inside a string literal

**Input:**
```python
def explain():
    msg = "use print() for debug"
    return msg
```

**What happened (before fix):** The heuristic analyzer used `"print(" in code` which matched the substring inside the string literal. The agent flagged a Code Quality issue and the fixer replaced `print(` with `logging.info(` inside the string, corrupting it to `"use logging.info() for debug"`. The code's behavior changed — the return value was now different.

**What should have happened:** No issues should be detected because there are no actual `print()` function calls. The code should be returned unchanged.

**How it was fixed:** Added `_has_print_statement()` helper that checks for `print(` only at the start of a line (after whitespace) using a regex pattern. Also updated `_heuristic_fix()` to use `re.sub` with `re.MULTILINE` and `^\s*print\(` so only statement-level print calls are replaced.

### Failure 2: MockClient stub response triggers cascading risk penalties

**Input:** `sample_code/flaky_try_except.py` (bare except block)

**What happened:** In MockClient mode, the LLM fixer returns `"# MockClient: no rewrite available in offline mode."` — a one-line comment. The risk assessor then applies multiple penalties: "Fixed code is much shorter than original" (-20), "Return statements may have been removed" (-30), and "High severity issue detected" (-40). The score drops to 5/100, which looks like a dangerous fix when actually no fix was attempted at all.

**What should have happened:** The system should recognize that MockClient's response is not a real fix and fall back to the heuristic fixer, which produces a proper rewrite. The issue is that MockClient returns a non-empty string (a comment), so the agent's check for empty output (`if not cleaned`) does not trigger the fallback.

**Impact:** In pure offline mode (client=None), the heuristic fixer runs correctly and scores 55/100. With MockClient, the same code scores 5/100 — a 50-point difference for the same input, purely because of how the stub response interacts with the risk assessor.

---

## 6) Heuristic vs Gemini comparison

**Detection differences:**

- **Heuristics** consistently detect three patterns: bare `except:`, `print()` statements, and `TODO` comments. They are fast, deterministic, and never make API calls. After our fix, they correctly avoid false positives from `print()` inside strings.
- **Gemini** can theoretically detect a wider range of issues — unused variables, logic errors, missing type hints, potential race conditions — because it understands code semantics, not just patterns. However, during testing, Gemini was frequently rate-limited (free tier: 5 requests/minute), causing fallback to heuristics in most cases.

**Fix quality differences:**

- **Heuristic fixes** are mechanical: regex replacements for `except:` and `print()`. They preserve code structure but are limited to the three known patterns. They cannot fix logic errors or restructure code.
- **Gemini fixes** (when available) can perform more nuanced rewrites, such as adding proper error logging inside except blocks, restructuring function signatures, or adding docstrings. However, the LLM sometimes wraps its response in markdown code fences despite the prompt saying not to, requiring the `_strip_code_fences()` cleanup.

**Risk scorer alignment:**

The risk scorer consistently agreed with intuition for heuristic fixes — low-severity print replacement scored well (85/100), high-severity bare-except fixes scored lower (55/100), and stacked issues drove scores down appropriately (20/100). The scorer was less reliable for LLM fixes because the LLM's structural changes (adding imports, reorganizing code) triggered penalties that the heuristic fixer avoids.

---

## 7) Human-in-the-loop decision

**Scenario:** The agent detects a bare `except:` block and the LLM proposes a fix that changes the exception type to a specific one like `except FileNotFoundError as e:`. This is a more precise fix than the heuristic's generic `except Exception as e:`, but it changes the code's behavior — the original caught ALL exceptions, and the new version only catches one type. Other exceptions (PermissionError, IOError) would now propagate up instead of being silently caught.

**Trigger:** The risk assessor should detect when the fix narrows exception handling scope — specifically when `except:` or `except Exception` is replaced with a more specific exception type. This changes which errors are caught and is a semantic behavior change.

**Where to implement:** In `reliability/risk_assessor.py`, add a check that compares except clauses between original and fixed code. If the fix replaces a broad except with a narrow one, deduct points and add a reason like "Exception handling scope was narrowed. Verify that uncaught exceptions are handled upstream."

**Message to show:** "This fix changes which exceptions are caught. The original code caught all errors; the proposed fix only catches specific ones. Other errors will now crash instead of being silently handled. Review the fix to confirm this is the intended behavior."

---

## 8) Improvement idea

**Proposal: Add a structural diff limit to the risk assessor.**

Currently, the risk assessor checks if the fixed code is much shorter than the original (< 50% of lines), but it does not check how many lines were changed. An LLM could rewrite 80% of a 20-line function while keeping the same line count, passing the length check despite making extensive changes.

**Implementation:** Count the number of lines that differ between original and fixed code using a simple line-by-line comparison. If more than 50% of lines changed, deduct 15 points and add a reason: "Fix modifies more than half of the original code. Consider whether a smaller change would address the issue."

```python
import difflib
changed = sum(1 for tag, _, _, _, _ in difflib.SequenceMatcher(
    None, original_lines, fixed_lines).get_opcodes() if tag != 'equal')
if changed / max(len(original_lines), 1) > 0.5:
    score -= 15
    reasons.append("Fix modifies more than half of the original code.")
```

This is low-complexity (5 lines using stdlib `difflib`), requires no new dependencies, and directly addresses the over-editing failure mode. It would catch LLM fixes that rewrite entire functions when only one line needed to change, pushing the agent toward human review for large-scale modifications.

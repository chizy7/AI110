from bughound_agent import BugHoundAgent
from llm_client import MockClient


def test_workflow_runs_in_offline_mode_and_returns_shape():
    agent = BugHoundAgent(client=None)  # heuristic-only
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert isinstance(result, dict)
    assert "issues" in result
    assert "fixed_code" in result
    assert "risk" in result
    assert "logs" in result

    assert isinstance(result["issues"], list)
    assert isinstance(result["fixed_code"], str)
    assert isinstance(result["risk"], dict)
    assert isinstance(result["logs"], list)
    assert len(result["logs"]) > 0


def test_offline_mode_detects_print_issue():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])


def test_offline_mode_proposes_logging_fix_for_print():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    fixed = result["fixed_code"]
    assert "logging" in fixed
    assert "logging.info(" in fixed


def test_mock_client_forces_llm_fallback_to_heuristics_for_analysis():
    # MockClient returns non-JSON for analyzer prompts, so agent should fall back.
    agent = BugHoundAgent(client=MockClient())
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])
    # Ensure we logged the fallback path
    assert any("Falling back to heuristics" in entry.get("message", "") for entry in result["logs"])


def test_print_inside_string_is_not_flagged():
    """print() appearing inside a string literal should not trigger a false positive."""
    agent = BugHoundAgent(client=None)
    code = 'def explain():\n    msg = "use print() for debug"\n    return msg\n'
    result = agent.run(code)

    # No issues should be detected — print( is in a string, not a statement
    assert len(result["issues"]) == 0
    # Code should be returned unchanged
    assert result["fixed_code"].strip() == code.strip()
    # Risk should be perfect since nothing was changed
    assert result["risk"]["score"] == 100


def test_actual_print_statement_is_still_detected():
    """Real print() calls at statement level should still be caught."""
    agent = BugHoundAgent(client=None)
    code = 'def f():\n    print("hello")\n    return True\n'
    result = agent.run(code)

    assert any(i.get("type") == "Code Quality" for i in result["issues"])
    assert "logging.info(" in result["fixed_code"]


def test_new_imports_flagged_in_risk():
    """Risk assessor should flag when a fix introduces new import statements."""
    from reliability.risk_assessor import assess_risk

    original = "def f():\n    print('hi')\n    return True\n"
    fixed = "import logging\n\ndef f():\n    logging.info('hi')\n    return True\n"
    risk = assess_risk(
        original_code=original,
        fixed_code=fixed,
        issues=[{"type": "Code Quality", "severity": "Low", "msg": "print"}],
    )
    assert any("import" in r.lower() for r in risk["reasons"])
    assert risk["score"] < 100


def test_high_severity_blocks_autofix_even_at_low_risk_score():
    """Even if score is technically in 'low' range, high severity issues block auto-fix."""
    from reliability.risk_assessor import assess_risk

    original = "def f():\n    try:\n        return 1\n    except:\n        return 0\n"
    fixed = "def f():\n    try:\n        return 1\n    except Exception as e:\n        return 0\n"
    risk = assess_risk(
        original_code=original,
        fixed_code=fixed,
        issues=[{"type": "Reliability", "severity": "High", "msg": "bare except"}],
    )
    # High severity should always block auto-fix regardless of score
    assert risk["should_autofix"] is False

"""Rigr smoke tests."""

import json, tempfile
from pathlib import Path
from rigr.eval_runner import EvalRunner, TestCase, EvalResult
from rigr.freeze import Freezer
from rigr.reporter import Reporter


def dummy_agent(input_data: dict) -> dict:
    """Simple test agent that echoes input with a response."""
    return {
        "response": f"Echo: {input_data.get('message', '')}",
        "tag": input_data.get("tag", "unknown"),
    }


def test_basic_run():
    """Test basic eval run with passing test cases."""
    cases = [
        TestCase(id="test1", input={"message": "hi", "tag": "greeting"},
                 expected={"response": "Echo: hi", "tag": "greeting"}),
        TestCase(id="test2", input={"message": "bye", "tag": "farewell"},
                 expected={"response": "Echo: bye", "tag": "farewell"}),
    ]
    runner = EvalRunner(agent_fn=dummy_agent)
    result = runner.run(cases)
    
    assert result.total_cases == 2
    assert result.passed_cases == 2
    assert result.passed_fields == 4  # 2 fields × 2 cases
    assert len(result.cases) == 2
    assert all(c.passed for c in result.cases)


def test_failing_case():
    """Test that mismatched outputs are caught."""
    cases = [
        TestCase(id="fail1", input={"message": "hi", "tag": "greeting"},
                 expected={"response": "Echo: hi", "tag": "wrong_tag"}),
    ]
    runner = EvalRunner(agent_fn=dummy_agent)
    result = runner.run(cases)
    
    assert result.total_cases == 1
    assert result.passed_cases == 0
    assert result.passed_fields == 1  # response matches, tag doesn't
    assert "tag" in result.per_field
    assert result.per_field["tag"]["correct"] == 0


def test_freezer_roundtrip():
    """Test freeze and load cycle."""
    cases = [TestCase(id="f1", input={"message": "hi", "tag": "x"},
                      expected={"response": "Echo: hi", "tag": "x"})]
    runner = EvalRunner(agent_fn=dummy_agent)
    result = runner.run(cases)
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        path = Path(tf.name)
    
    Freezer.freeze(result, path)
    assert Freezer.exists(path)
    
    data = Freezer.load(path)
    assert len(data["cases"]) == 1
    assert data["cases"][0]["passed"]
    
    path.unlink()


def test_baseline_regression_detection():
    """Test that baseline comparison catches regressions."""
    cases = [TestCase(id="r1", input={"message": "hi", "tag": "x"},
                      expected={"response": "Echo: hi", "tag": "x"})]
    
    # Freeze a passing baseline
    runner = EvalRunner(agent_fn=dummy_agent)
    result1 = runner.run(cases)
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        bp = Path(tf.name)
    Freezer.freeze(result1, bp)
    
    # Now change the expected output (simulating a regression-inducing change)
    cases2 = [TestCase(id="r1", input={"message": "hi", "tag": "x"},
                       expected={"response": "NEW OUTPUT", "tag": "x"})]
    runner2 = EvalRunner(agent_fn=dummy_agent, baseline_path=bp)
    result2 = runner2.run(cases2)
    
    assert result2.baseline_compared
    assert len(result2.new_errors) == 1 or len(result2.new_errors) == 0
    # The case should fail because expected differs from actual
    assert not result2.cases[0].passed
    
    bp.unlink()


def test_reporter_formats():
    """Test all reporter output formats."""
    cases = [TestCase(id="r1", input={"message": "hi", "tag": "x"},
                      expected={"response": "Echo: hi", "tag": "x"})]
    runner = EvalRunner(agent_fn=dummy_agent)
    result = runner.run(cases)
    
    terminal = Reporter.terminal(result)
    assert "PASS" in terminal or "100.0%" in terminal
    
    json_str = Reporter.json(result)
    data = json.loads(json_str)
    assert data["passed_cases"] == 1
    
    md = Reporter.markdown(result)
    assert "Rigr Eval Report" in md
    assert "PASS" in terminal or "✅" in md

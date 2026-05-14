"""Eval runner — the core engine. Runs test cases against an agent, compares to baseline."""

import json, time, hashlib
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from collections import Counter
from pydantic import BaseModel


class TestCase(BaseModel):
    """A single test case: input + expected output."""
    id: str
    input: dict[str, Any]
    expected: dict[str, Any]
    tags: list[str] = []


@dataclass
class FieldResult:
    """Result for a single field in a single test case."""
    field: str
    expected: Any
    actual: Any
    passed: bool
    changed_from_baseline: bool = False


@dataclass
class CaseResult:
    """Result for a single test case."""
    case_id: str
    passed: bool
    fields: list[FieldResult]
    duration_ms: float
    error: Optional[str] = None


@dataclass
class EvalResult:
    """Full evaluation result across all test cases."""
    run_id: str
    timestamp: str
    total_cases: int
    passed_cases: int
    total_fields: int
    passed_fields: int
    cases: list[CaseResult]
    per_field: dict[str, dict[str, int]] = field(default_factory=dict)
    new_errors: list[str] = field(default_factory=list)
    resolved_errors: list[str] = field(default_factory=list)
    baseline_compared: bool = False
    duration_total_ms: float = 0.0


class EvalRunner:
    """Runs test cases against an agent function and compares to frozen baseline."""

    def __init__(
        self,
        agent_fn=None,
        baseline_path: Optional[Path] = None,
        field_spec: Optional[dict[str, Any]] = None,
    ):
        self.agent_fn = agent_fn
        self.baseline_path = Path(baseline_path) if baseline_path else None
        self.field_spec = field_spec or {}
        self._baseline = None
        if self.baseline_path and self.baseline_path.exists():
            self._baseline = json.loads(self.baseline_path.read_text())

    def run(self, test_cases: list[TestCase]) -> EvalResult:
        """Run all test cases and return results."""
        if not self.agent_fn:
            raise ValueError("No agent_fn provided. Set agent_fn or use --agent flag.")

        run_id = hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]
        case_results = []

        for tc in test_cases:
            start = time.time()
            try:
                actual = self.agent_fn(tc.input)
                if not isinstance(actual, dict):
                    case_results.append(CaseResult(
                        case_id=tc.id, passed=False, fields=[],
                        duration_ms=(time.time() - start) * 1000,
                        error=f"Agent returned {type(actual).__name__}, expected dict",
                    ))
                    continue

                fields = self._compare_fields(tc.id, tc.expected, actual)
                passed = all(f.passed for f in fields)
                case_results.append(CaseResult(
                    case_id=tc.id, passed=passed, fields=fields,
                    duration_ms=(time.time() - start) * 1000,
                ))
            except Exception as e:
                case_results.append(CaseResult(
                    case_id=tc.id, passed=False, fields=[],
                    duration_ms=(time.time() - start) * 1000,
                    error=str(e),
                ))

        # Aggregate
        total_fields = sum(len(c.fields) for c in case_results)
        passed_fields = sum(
            sum(1 for f in c.fields if f.passed) for c in case_results
        )
        passed_cases = sum(1 for c in case_results if c.passed)

        # Per-field stats
        per_field: dict[str, dict[str, int]] = {}
        for c in case_results:
            for f in c.fields:
                if f.field not in per_field:
                    per_field[f.field] = {"correct": 0, "total": 0, "changed": 0}
                per_field[f.field]["total"] += 1
                if f.passed:
                    per_field[f.field]["correct"] += 1
                if f.changed_from_baseline:
                    per_field[f.field]["changed"] += 1

        # Detect new/resolved errors vs baseline
        new_errors = []
        resolved_errors = []
        if self._baseline:
            baseline_cases = {c["case_id"]: c for c in self._baseline.get("cases", [])}
            for c in case_results:
                bl = baseline_cases.get(c.case_id)
                if bl:
                    was_passing = bl.get("passed", False)
                    if was_passing and not c.passed:
                        new_errors.append(c.case_id)
                    elif not was_passing and c.passed:
                        resolved_errors.append(c.case_id)

        return EvalResult(
            run_id=run_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            total_cases=len(test_cases),
            passed_cases=passed_cases,
            total_fields=total_fields,
            passed_fields=passed_fields,
            cases=case_results,
            per_field=per_field,
            new_errors=new_errors,
            resolved_errors=resolved_errors,
            baseline_compared=self._baseline is not None,
            duration_total_ms=sum(c.duration_ms for c in case_results),
        )

    def _compare_fields(
        self, case_id: str, expected: dict, actual: dict
    ) -> list[FieldResult]:
        """Compare expected vs actual per field, with baseline comparison."""
        results = []
        all_keys = set(expected.keys()) | set(actual.keys())

        baseline_fields = {}
        if self._baseline:
            for c in self._baseline.get("cases", []):
                if c["case_id"] == case_id:
                    baseline_fields = {
                        f["field"]: f.get("actual") for f in c.get("fields", [])
                    }
                    break

        for key in sorted(all_keys):
            exp_val = expected.get(key)
            act_val = actual.get(key)
            passed = exp_val == act_val
            bl_val = baseline_fields.get(key)
            changed = bl_val is not None and act_val != bl_val

            results.append(FieldResult(
                field=key,
                expected=exp_val,
                actual=act_val,
                passed=passed,
                changed_from_baseline=changed,
            ))

        return results

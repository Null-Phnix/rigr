"""Freezer — locks current eval results as the baseline for regression detection."""

import json
from pathlib import Path
from dataclasses import asdict
from .eval_runner import EvalResult


class Freezer:
    """Stores and loads frozen baseline snapshots for comparison."""

    DEFAULT_PATH = Path("rigr_baseline.json")

    @staticmethod
    def freeze(result: EvalResult, path: Path = DEFAULT_PATH) -> Path:
        """Save current eval result as the frozen baseline."""
        data = {
            "run_id": result.run_id,
            "timestamp": result.timestamp,
            "cases": [
                {
                    "case_id": c.case_id,
                    "passed": c.passed,
                    "fields": [asdict(f) for f in c.fields],
                }
                for c in result.cases
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return path

    @staticmethod
    def exists(path: Path = DEFAULT_PATH) -> bool:
        return path.exists()

    @staticmethod
    def load(path: Path = DEFAULT_PATH) -> dict:
        return json.loads(path.read_text()) if path.exists() else {}

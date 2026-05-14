"""
Rigr — Agent evaluation framework.
Define expectations. Catch regressions. Prove your agent isn't getting worse.
"""

from .eval_runner import EvalRunner, EvalResult, TestCase
from .reporter import Reporter
from .freeze import Freezer

__version__ = "0.1.0"

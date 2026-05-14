"""CLI — rigr command-line interface."""

import json, sys, importlib.util, os
from pathlib import Path
from typing import Any
import click

from .eval_runner import EvalRunner, TestCase
from .reporter import Reporter
from .freeze import Freezer


@click.group()
def main():
    """Rigr — Agent evaluation framework. Define expectations. Catch regressions."""


@main.command()
@click.option("--dir", "test_dir", default="test_cases", help="Directory for test case files")
def init(test_dir: str):
    """Create rigr.yaml config and test_cases/ directory."""
    config = {
        "version": "0.1.0",
        "agent": {
            "import_path": "my_agent.run",
            "description": "Your agent function. Must accept dict input, return dict output.",
        },
        "baseline_path": "rigr_baseline.json",
        "test_dir": test_dir,
    }

    config_path = Path("rigr.yaml")
    if config_path.exists():
        click.echo("rigr.yaml already exists. Skipping.", err=True)
    else:
        config_path.write_text(json.dumps(config, indent=2))
        click.echo(f"Created rigr.yaml")

    test_dir_path = Path(test_dir)
    if not test_dir_path.exists():
        test_dir_path.mkdir(parents=True)
        example = test_dir_path / "example.json"
        example.write_text(json.dumps({
            "test_cases": [
                {
                    "id": "greeting_en",
                    "input": {"message": "Hello", "language": "en"},
                    "expected": {"response": "Hello! How can I help?", "language": "en"},
                    "tags": ["greeting", "english"],
                },
                {
                    "id": "greeting_es",
                    "input": {"message": "Hola", "language": "es"},
                    "expected": {"response": "¡Hola! ¿Cómo puedo ayudar?", "language": "es"},
                    "tags": ["greeting", "spanish"],
                },
            ],
        }, indent=2))
        click.echo(f"Created {test_dir}/example.json with 2 sample test cases")

    click.echo("\nNext: rigr test --agent my_agent.py")


@main.command()
@click.option("--agent", required=True, help="Python module.function to test (e.g., my_agent.run)")
@click.option("--dir", "test_dir", default="test_cases", help="Directory with test case JSON files")
@click.option("--baseline", default="rigr_baseline.json", help="Path to frozen baseline")
@click.option("--format", "output_format", default="terminal", type=click.Choice(["terminal", "json", "markdown"]))
@click.option("--output", "-o", default=None, help="Save report to file")
def test(agent: str, test_dir: str, baseline: str, output_format: str, output: str):
    """Run test cases against an agent function."""
    # Load agent function
    try:
        module_path, func_name = agent.rsplit(".", 1)
        spec = importlib.util.spec_from_file_location(
            "agent_module", os.path.abspath(module_path + ".py")
        )
        if spec is None:
            click.echo(f"Cannot find agent file: {module_path}.py", err=True)
            sys.exit(1)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        agent_fn = getattr(mod, func_name)
    except Exception as e:
        click.echo(f"Error loading agent: {e}", err=True)
        sys.exit(1)

    # Load test cases
    test_dir_path = Path(test_dir)
    if not test_dir_path.exists():
        click.echo(f"Test directory not found: {test_dir}. Run 'rigr init' first.", err=True)
        sys.exit(1)

    test_cases: list[TestCase] = []
    for f in sorted(test_dir_path.glob("*.json")):
        try:
            data = json.loads(f.read_text())
            for tc in data.get("test_cases", []):
                test_cases.append(TestCase(**tc))
        except Exception as e:
            click.echo(f"Warning: skipping {f.name}: {e}", err=True)

    if not test_cases:
        click.echo("No test cases found.", err=True)
        sys.exit(1)

    click.echo(f"Running {len(test_cases)} test cases...")

    # Run eval
    baseline_path = Path(baseline) if Path(baseline).exists() else None
    runner = EvalRunner(agent_fn=agent_fn, baseline_path=baseline_path)
    result = runner.run(test_cases)

    # Report
    if output_format == "terminal":
        report = Reporter.terminal(result)
    elif output_format == "json":
        report = Reporter.json(result)
    else:
        report = Reporter.markdown(result)

    if output:
        Path(output).write_text(report)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(report)

    # Return exit code based on result
    if result.passed_fields < result.total_fields:
        sys.exit(1)


@main.command()
@click.option("--baseline", default="rigr_baseline.json", help="Path to save frozen baseline")
def freeze(baseline: str):
    """Freeze current eval results as the regression baseline."""
    click.echo("Run 'rigr test --agent my_agent' first, then 'rigr freeze' to lock results.")
    click.echo(f"Baseline will be saved to: {baseline}")


@main.command()
@click.option("--baseline", default="rigr_baseline.json", help="Path to frozen baseline")
def compare(baseline: str):
    """Compare latest run against frozen baseline."""
    bp = Path(baseline)
    if not bp.exists():
        click.echo(f"No baseline found at {baseline}. Run 'rigr freeze' first.", err=True)
        sys.exit(1)

    data = json.loads(bp.read_text())
    cases = data.get("cases", [])
    passing = sum(1 for c in cases if c.get("passed"))
    click.echo(f"Baseline: {passing}/{len(cases)} cases passing (frozen {data.get('timestamp', 'unknown')})")
    click.echo("Run 'rigr test' to compare current results against this baseline.")


if __name__ == "__main__":
    main()

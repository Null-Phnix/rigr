"""Reporter — generates human-readable eval reports from EvalResult."""

from datetime import datetime
from .eval_runner import EvalResult


class Reporter:
    """Generates terminal and file-based reports."""

    @staticmethod
    def terminal(result: EvalResult) -> str:
        """Colorful terminal report using Rich."""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console(width=100)
        out: list[str] = []

        # Header
        pct = result.passed_fields / max(result.total_fields, 1) * 100
        status = "[green]PASS" if result.passed_fields == result.total_fields else "[red]FAIL"
        out.append(f"\n═══ Rigr Eval Report ({result.run_id}) ═══")
        out.append(f"  {result.passed_cases}/{result.total_cases} cases | {result.passed_fields}/{result.total_fields} fields | {pct:.1f}% {status}")

        if result.baseline_compared:
            out.append(f"  Baseline comparison: {len(result.new_errors)} new errors, {len(result.resolved_errors)} resolved")
            for eid in result.new_errors[:5]:
                out.append(f"    [red]✗ NEW ERROR: {eid}")
            for eid in result.resolved_errors[:5]:
                out.append(f"    [green]✓ RESOLVED: {eid}")
        out.append("")

        # Per-field table
        table = Table(title="Per-Field Breakdown")
        table.add_column("Field", style="cyan")
        table.add_column("Correct", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("%", justify="right")
        table.add_column("Changed", justify="right")

        for field, stats in sorted(result.per_field.items()):
            p = stats["correct"] / max(stats["total"], 1) * 100
            changed = stats.get("changed", 0)
            style = "green" if p == 100 else ("yellow" if p >= 80 else "red")
            table.add_row(
                field,
                str(stats["correct"]),
                str(stats["total"]),
                f"[{style}]{p:.0f}%[/]",
                str(changed) if changed else "-",
            )

        out.append(str(table))

        # Case details
        out.append("\nCase Details:")
        for c in result.cases:
            if c.passed:
                continue  # Skip passing cases in terminal for brevity
            out.append(f"  [{c.case_id}] {'PASS' if c.passed else 'FAIL'} ({c.duration_ms:.0f}ms)")
            if c.error:
                out.append(f"    Error: {c.error}")
            for f in c.fields:
                if not f.passed:
                    marker = "[yellow]Δ" if f.changed_from_baseline else "[red]✗"
                    out.append(f"    {marker} {f.field}: expected={f.expected}, actual={f.actual}")

        out.append(f"\n  Total: {result.duration_total_ms:.0f}ms")

        return "\n".join(out)

    @staticmethod
    def json(result: EvalResult) -> str:
        """Machine-readable JSON report."""
        import json
        from dataclasses import asdict

        return json.dumps(asdict(result), indent=2, default=str)

    @staticmethod
    def markdown(result: EvalResult) -> str:
        """Markdown report for PRs and compliance documentation."""
        lines = [
            f"# Rigr Eval Report",
            f"",
            f"**Run:** `{result.run_id}` | **Date:** {result.timestamp}",
            f"",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Cases | {result.passed_cases}/{result.total_cases} |",
            f"| Fields | {result.passed_fields}/{result.total_fields} ({result.passed_fields/max(result.total_fields,1)*100:.1f}%) |",
            f"| Duration | {result.duration_total_ms:.0f}ms |",
        ]

        if result.baseline_compared:
            lines.extend([
                f"",
                f"## Baseline Comparison",
                f"| New Errors | Resolved |",
                f"|---|---|",
                f"| {len(result.new_errors)} | {len(result.resolved_errors)} |",
            ])
            if result.new_errors:
                lines.append("")
                lines.append("### New Errors")
                for eid in result.new_errors:
                    lines.append(f"- `{eid}`")

        lines.extend([
            f"",
            f"## Per-Field Accuracy",
            f"| Field | Correct | Total | % | Changed |",
            f"|---|---|---|---|---|",
        ])
        for field, stats in sorted(result.per_field.items()):
            pct = stats["correct"] / max(stats["total"], 1) * 100
            changed = stats.get("changed", 0)
            lines.append(f"| {field} | {stats['correct']} | {stats['total']} | {pct:.0f}% | {changed or '-'} |")

        lines.extend([
            f"",
            f"## Case Details",
        ])
        for c in result.cases:
            status = "✅" if c.passed else "❌"
            lines.append(f"- {status} **{c.case_id}** ({c.duration_ms:.0f}ms)")
            if c.error:
                lines.append(f"  - Error: `{c.error}`")
            for f in c.fields:
                if not f.passed:
                    lines.append(f"  - `{f.field}`: expected `{f.expected}`, got `{f.actual}`")

        return "\n".join(lines)

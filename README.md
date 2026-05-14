# Rigr

**Agent evaluation for teams that can't afford to be wrong.**

Open-source core. Enterprise platform. Prove your AI agents are safe, consistent, and not quietly degrading — before your customers or your compliance team find out.

```bash
pip install rigr
rigr init && rigr test
```

## Who this is for

You have AI agents in production. Every model update, prompt change, or retrieval tweak risks breaking them. Your compliance team wants evidence they're safe. Your CTO wants to know if v2 is actually better than v1. You need more than "looks good to me."

## What it does

1. **Define expectations** — Structured schema for what your agent must output
2. **Write test cases** — Inputs with expected outputs. Version-controlled, reviewable
3. **Freeze baselines** — Lock known-good results. Every run compares against them
4. **Catch regressions** — New errors flagged before deployment. Resolved errors tracked
5. **Generate audit reports** — Per-field accuracy, changelog, compliance-ready evidence

## Enterprise

For teams deploying agents in regulated environments. SSO, audit logs, SOC 2, on-prem deployment, priority support. [Book a call](mailto:Contact@phnix.dev).

## Quickstart

```bash
pip install rigr
rigr init                     # Creates rigr.yaml + test_cases/
rigr test --agent my_agent   # Runs tests against your agent
rigr freeze                   # Locks current results as baseline
rigr compare                  # Shows regressions vs baseline
```

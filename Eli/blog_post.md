# We spent months measuring whether our AI was getting better or worse. Most teams don't.

I have been building AI agents for a while now. Not the kind that answer trivia questions. The kind that actually do work. Trade crypto. Scrape documentation. Extract structured data from ancient texts.

Here is the thing nobody tells you about agents. They break. Silently. You change the prompt by three words. You swap the model. You tweak the retrieval pipeline. And suddenly your agent that was nailing refund calculations last week is now confidently wrong about everything. And you have no way to know until a customer tells you.

Most teams handle this by looking at outputs and going "yeah that looks right." That is not testing. That is vibes.

So we built something different. A protocol for agent evaluation that actually catches regressions before they hit production. We called it Rigr.

## What we learned from our own agent

We have this model called Ymir. It predicts political state transitions from historical texts. Like, here is what the government looked like before a coup, here is what it looked like after. Very niche. Very structured.

The problem was we kept making changes. New training data. Tweaked loss functions. Different hyperparameters. And sometimes the model got worse on specific fields but we would not notice because the overall score looked fine.

So we built a protocol. Frozen baselines. Every time we run the model, we compare against a known good snapshot. If a field that was passing before suddenly fails, we catch it immediately. Not next week when we happen to re-read the outputs.

We also built audit packs. Extra test cases that the model never saw during development. Turns out our best model that scored 85 percent on validation dropped to 52 percent on the audit. The validation score was lying to us. The protocol caught it.

Most teams would have shipped the 85 percent and called it a win.

## What Rigr actually does

It is dead simple. You write test cases. Input and expected output. Rigr runs them against your agent and tells you what passed and what failed. You freeze a baseline. From that point on, every run compares against it. New failures get flagged. Old failures that got fixed get marked resolved.

That is it. No SDK integration in your agent. No cloud dependency. No dashboard you have to learn. Just a CLI tool that tells you whether your agent got better or worse since last time.

```bash
pip install rigr
rigr init
rigr test --agent my_agent.py
```

## Why I am open sourcing it

The agent infrastructure space is weird right now. There are like fifty companies building agent frameworks. Memory layers. Orchestration tools. Vector databases. Everyone is building the thing that helps you build agents.

Nobody is building the thing that helps you know if your agent actually works.

DeepEval and Evidently are solid tools but they evaluate LLM outputs. They tell you if the chatbot sounds natural. They do not tell you if your support agent still calculates refunds correctly after a model swap. That is a different problem.

So here is Rigr. Apache 2.0. Use it. Break it. Tell me what sucks. If you are deploying agents in production and your compliance team is asking how you know they are safe, this is for you.

[GitHub](https://github.com/Null-Phnix/rigr)

[Enterprise](mailto:Contact@phnix.dev) — for teams that need SSO, audit logs, SOC 2.

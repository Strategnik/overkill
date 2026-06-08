# Building this into your own agent

The config in this repo is the best you can do **inside Claude Code** — but it's a
workaround, not the ideal. This doc explains the ideal: how you'd solve model routing if
you owned the agent loop, and why it's a fundamentally better design.

See [`sdk/escalating_agent.py`](sdk/escalating_agent.py) for a runnable reference sketch
of the pattern argued for here.

## Why config is the ceiling in Claude Code

Everything in this repo exists to work around one fact: in Claude Code, **the model is a
session property, and only a model or a human can change it.** You can't intercept a turn
and swap the brain. So the only lever is to define model-pinned subagents and write a
rubric the router-model *probably* follows. That's *soft* enforcement — a model reading
instructions and choosing to comply. It works, but you can't measure it, can't prove it,
and can't tune it.

## When you own the loop, the model is just a parameter

In the [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk) (or the raw Messages
API), `model` is a field on every request. Routing stops being orchestration and becomes
a function you call before each turn. That single change removes the three ugliest parts
of the Claude Code version:

- **No subagent spawn** — no fresh context, no cache carryover lost.
- **No lost interactivity** — you stay in one conversation; a different model just answers
  a given turn.
- **Hard enforcement** — code decides, deterministically, and logs the decision.

## The router spectrum (cheapest → smartest)

Every option here guesses difficulty *before* doing the work:

| Approach | How | Tradeoff |
|----------|-----|----------|
| **Heuristic** | Pure function on cheap signals — prompt length, file count, diff size, command-vs-question | Free, instant; brittle on the ambiguous middle |
| **Embedding** | Pre-embed labeled exemplars per tier, route by nearest centroid (e.g. Aurelio's `semantic-router`) | Sub-ms, no LLM call; drifts if your task mix shifts |
| **LLM-as-router** | A tiny Haiku call emitting `{tier, confidence}` | Accurate on ambiguity; costs a round-trip |
| **Cascade** | Heuristic first; only the *ambiguous* band pays for the LLM classifier | Best blend — how production routers (RouteLLM et al.) actually work |

## The elegant pattern: reactive escalation, gated by a verifier

The better idea is to stop predicting difficulty and start **measuring** it:

1. Attempt the task on the cheap model.
2. **Verify** the output — run the tests, typecheck, a cheap critic, a confidence check.
3. **Escalate only on failure**, replaying the same (cached) context to the stronger model.

This routes on *demonstrated* difficulty — you pay for Opus only when Sonnet **actually**
failed, not when the task merely *looked* hard. For a workload that's mostly easy, the
expected cost is low and the accuracy is high. With prompt caching, the escalated call
reuses the cheap attempt's context for a fraction of the cost, and the whole thing is
invisible: same thread, a smarter model quietly takes over the hard turn.

**The verifier is the crux.** This pattern only wins if checking is cheaper than the
expensive model:

- **Code tasks — the killer case.** The verifier is objective and nearly free: run the
  tests, the typechecker, the linter. If they're green, the cheap model was enough.
- **Open-ended reasoning — harder.** Use a cheap critic model or self-consistency, biased
  toward escalation ("unsure" counts as "fail"). When you genuinely can't verify cheaply,
  fall back to a predictive cascade from the table above.

You can also combine them: a confident *heuristic* result skips the cascade (start a
known-hard task on Opus directly, skip the wasted cheap attempt), while everything else
goes through attempt-verify-escalate. The sketch does exactly this.

## The real prize: a measurement loop

The thing config can never give you: log every
`(task, tier chosen, did it clear the bar)` and tune your thresholds from data. Routing
stops being a vibe a model is loosely honoring and becomes a **policy you can prove and
improve.** That feedback loop — not any particular classifier — is what makes an
agent-native router worth building.

## When to use which

- **Inside Claude Code →** config (this repo). Don't fight the harness.
- **Your own agent, cheap verifier available →** reactive escalation + verifier. The
  elegant default.
- **Your own agent, no cheap verifier →** predictive cascade (heuristic + embedding or
  LLM classifier).
- **Routing at real scale →** consider a *learned* router (RouteLLM-style: train a small
  model to predict whether the cheap answer will suffice). Most accurate, most to
  maintain — overkill unless volume justifies it.

## So what

If you ever lift this idea out of Claude Code and into your own agent, **don't port the
config.** Implement routing as code, make it reactive-escalation-with-a-verifier rather
than upfront classification, and instrument the decisions. The config version optimizes
spend; the agent-native version optimizes spend *and* tells you whether it's working.

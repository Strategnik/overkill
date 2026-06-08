"""
overkill — agent-native reference sketch
=========================================

The config in this repo is the best you can do *inside Claude Code*, where the
model is a session property only a model or human can change. When you own the
agent loop, `model` is a per-call parameter and routing becomes code.

This sketch implements the pattern AGENT.md argues for: **reactive escalation
gated by a cheap verifier** — attempt on the cheap model, check whether it
actually worked, and only pay for the expensive model when it demonstrably
didn't. Routing on *measured* difficulty, not *predicted* difficulty. A
confident heuristic can still short-circuit the obvious cases.

This is illustrative, not a package. Wire `verify` to your real check (tests,
typecheck, a critic) and adapt `run_attempt` to your real loop.

    pip install anthropic
    export ANTHROPIC_API_KEY=...
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from anthropic import Anthropic

client = Anthropic()

# --- Tiers: the same pins as the Claude Code version (see MODELS.md) ---------
QUICK = "claude-haiku-4-5-20251001"   # mechanical, self-verifying work
DEFAULT = "claude-sonnet-4-6"         # everyday work + the first real attempt
DEEP = "claude-opus-4-8"              # sealed hard reasoning

# Escalation ladder, cheapest first. A task starts somewhere on this ladder
# and climbs only when the verifier says the current tier didn't clear the bar.
LADDER = [QUICK, DEFAULT, DEEP]


@dataclass
class Attempt:
    task: str
    model: str
    output: str
    ok: bool
    elapsed: float


# The measurement loop: every routing decision + outcome lands here. Tune your
# heuristics and thresholds from this — it's the thing config can never give you.
ROUTING_LOG: list[Attempt] = []


# --- 1. Fast path: deterministic heuristics for the *obvious* cases ----------
# Free and instant. Routes only when confident; returns None for the ambiguous
# middle, which starts at DEFAULT and lets the verifier decide.
def heuristic_tier(task: str, *, file_count: int = 0, diff_lines: int = 0) -> Optional[str]:
    t = task.lower()

    trivial = any(k in t for k in ("rename", "typo", "headline", "reword", "format", "bump version"))
    if trivial and file_count <= 1 and diff_lines < 10:
        return QUICK

    hard = any(k in t for k in ("optimize", "architecture", "race condition", "concurrency", "refactor", "complexity"))
    if hard or file_count > 20:
        return DEEP  # confidently hard: skip the wasted cheap attempt

    return None  # ambiguous -> measure instead of guess


# --- 2. The verifier: the crux. Must be cheaper than the expensive model, ----
#     or the whole approach collapses back into predictive guessing.
def verify_with_tests(run_tests: Callable[[], bool]) -> bool:
    """Code tasks: objective and nearly free. Green tests == cheap tier sufficed."""
    return run_tests()


def verify_with_critic(task: str, output: str) -> bool:
    """No objective check? A cheap Haiku critic, biased toward escalation:
    'unsure' counts as 'fail', so borderline answers climb the ladder."""
    msg = client.messages.create(
        model=QUICK,
        max_tokens=8,
        messages=[{
            "role": "user",
            "content": (
                f"TASK:\n{task}\n\nANSWER:\n{output}\n\n"
                "Did the answer fully and correctly solve the task? "
                "Reply with exactly PASS or FAIL. If unsure, reply FAIL."
            ),
        }],
    )
    return msg.content[0].text.strip().upper().startswith("PASS")


# --- 3. A single attempt at a given tier -------------------------------------
def run_attempt(task: str, model: str, history: list[dict]) -> Attempt:
    start = time.perf_counter()
    msg = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=history + [{"role": "user", "content": task}],
        # Prompt caching matters here: mark the stable context prefix with
        # cache_control so an escalated call reuses the cheap attempt's context
        # for a fraction of the cost. Omitted for brevity — see the caching docs.
    )
    output = "".join(b.text for b in msg.content if b.type == "text")
    return Attempt(task, model, output, ok=False, elapsed=time.perf_counter() - start)


# --- 4. The loop: attempt -> verify -> escalate ------------------------------
def solve(
    task: str,
    *,
    verify: Callable[[str], bool],
    history: Optional[list[dict]] = None,
    file_count: int = 0,
    diff_lines: int = 0,
) -> str:
    history = history or []

    # Where do we start on the ladder? A confident heuristic picks the floor;
    # ambiguous tasks start mid (DEFAULT) and can climb to DEEP.
    forced = heuristic_tier(task, file_count=file_count, diff_lines=diff_lines)
    start = LADDER.index(forced) if forced else LADDER.index(DEFAULT)

    attempt = None
    for model in LADDER[start:]:
        attempt = run_attempt(task, model, history)
        attempt.ok = verify(attempt.output)
        ROUTING_LOG.append(attempt)
        if attempt.ok:
            return attempt.output  # cheap tier cleared the bar — stop here

    # Ladder exhausted: the strongest model is our best effort.
    return attempt.output


# --- 5. Usage ----------------------------------------------------------------
if __name__ == "__main__":
    # Code task: objective, free verification. Starts on Sonnet (ambiguous),
    # escalates to Opus only if the tests don't pass.
    result = solve(
        "Rewrite this function to run in O(n) instead of O(n^2): <code>",
        verify=lambda _out: verify_with_tests(run_tests=lambda: True),  # plug in your runner
        file_count=1,
    )
    print(result)

    for a in ROUTING_LOG:
        print(f"  {a.model:<32} ok={a.ok} {a.elapsed:.2f}s")

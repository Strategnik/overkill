## Model routing

This setup runs a **three-tier model strategy**. The session default is **Sonnet**,
which acts as both the *router* and the everyday worker. Two subagents are available
for the tails:

- **`quick`** (Haiku) — the cheap, fast tier.
- **`deep-work`** (Opus) — the heavy-reasoning tier.

Your job on every task: **do the work yourself on Sonnet by default, and reach for a
tail only when the task clearly belongs there.**

The governing principle is **asymmetric error cost** — under-powering a hard task is far
more expensive than over-powering a trivial one. A subtly-wrong hard answer (a
plausible-but-broken optimization) can cost hours before it's caught; a wrong trivial
answer (a bad headline) is cheap and instantly visible. So when in doubt, round *up*.

### Delegate down to `quick` (Haiku)
Mechanical work where a mistake is immediately visible and self-correcting:
- copy / headline / microcopy changes
- single-line or single-file edits with no logic
- renames, formatting, import sorting
- simple, well-documented API calls
- file lookups, "where is X", reading a value

If it's trivial and self-verifying, hand it to `quick`.

### Delegate up to `deep-work` (Opus) — *reactively*
Do **not** try to predict difficulty perfectly up front. Difficulty is usually only
knowable once you're in the work. Start on Sonnet, and **escalate the moment the task
reveals itself as hard.** Escalate when you notice any of:
- algorithm or performance optimization where correctness is non-obvious
- architecture / system-design decisions with downstream consequences
- large-codebase analysis spanning many files or subsystems
- gnarly refactors that touch invariants
- subtle bugs where the wrong fix looks right
- **your own uncertainty** — if you're guessing, hedging, or about to ship something you
  can't verify, that *is* the escalation signal. Don't push through.

The trigger is **discovered difficulty and low confidence, not a keyword.** A task that
looked trivial but hides a hard problem goes up; a task with scary words that's actually
mechanical does not.

### When NOT to delegate up — recommend a session switch instead
Subagents run to completion in isolation — you can't steer them mid-stream. So
`deep-work` is right for **sealed, well-scoped** hard tasks ("optimize this function,
return the diff"). For **collaborative, exploratory** hard work — thinking through an
architecture or algorithm with the user turn by turn — do **not** delegate blind. Tell
the user to switch the session to Opus (`/model opus`) so they keep interactivity.
Delegating exploratory work to a subagent trades away the steering the user needs.

### Summary
- Default: **Sonnet** (router + worker)
- Trivial, self-verifying → **`quick`**
- Hard + sealed, or you've lost confidence → **`deep-work`**
- Hard + exploratory → recommend **`/model opus`** for the session
- When unsure between tiers, under-powering costs more than over-powering — **round up.**

# claude-model-router

A **three-tier model strategy** for [Claude Code](https://claude.com/claude-code): run a
cheap, capable model by default and let it route work up or down by difficulty — so you
spend Opus dollars on the algorithm, not the headline.

Set once in `~/.claude/`, inherited by every project, overridable per repo.

---

## The idea

Claude Code fixes one model per session — it can't downgrade itself mid-task. The only
real mechanism for "use the right model for the job" is a **router that delegates to
model-pinned subagents.** This repo is that router, expressed as config:

| Tier | Model | For |
|------|-------|-----|
| **Default / router** | Sonnet | Everyday work, *and* deciding what to delegate |
| **`quick`** | Haiku | Mechanical, self-verifying tasks (copy, renames, lookups) |
| **`deep-work`** | Opus | Hard reasoning — optimization, architecture, subtle bugs |

The Sonnet session classifies each task *inline* as it reads it — no separate classifier
call, no latency tax — and hands the tails off to the right subagent.

## Why these three (and not four)

Two design decisions worth stealing:

**1. Optimize for error cost, not token price.** The dominant cost in this system isn't
per-token rates — it's a *subtly-wrong answer you have to catch and redo.* That cost is
asymmetric: a wrong headline is cheap and instantly visible; a plausible-but-broken
optimization can cost hours. So the policy is: push trivial work to the cheapest model
aggressively (errors are cheap there), pay for the best model on hard work (errors are
expensive there), and **when unsure, round up.**

**2. Three tiers, not four.** It's tempting to add a fourth tier (e.g. Opus 4.6 vs 4.8).
Don't. The boundary between two same-class models is the *hardest* for the router to
judge and saves the *least* money — the worst margin to maintain. The valuable cliffs are
trivial↔standard (~3×) and standard↔hard (~5×). Tier those; ignore the rest.

**3. Escalate reactively, not predictively.** Difficulty is usually only knowable once
you're in the work. So the rubric tells Sonnet to *start* the task and escalate to
`deep-work` the moment it discovers the problem is hard — or the moment its own
confidence drops — rather than trying to forecast difficulty at t=0. The breakpoint
becomes measured, not guessed.

## The one honest limitation

Subagents run to completion in isolation — you can't steer them mid-stream. So
`deep-work` is great for **sealed, well-scoped** hard tasks ("optimize this function,
return the diff") and worse for **collaborative, exploratory** ones ("let's rethink this
architecture together"). For the latter, the rubric tells Sonnet to recommend you switch
the *session* to Opus (`/model opus`) instead of delegating blind. Reactive escalation
handles sealed hard tasks; it can't make a subagent feel interactive.

## Install

```bash
git clone https://github.com/<you>/claude-model-router.git
cd claude-model-router
./install.sh
```

The installer:
- copies `deep-work` and `quick` into `~/.claude/agents/`
- sets `"model": "sonnet"` as your default (only if you haven't already chosen one)
- appends the routing rubric to `~/.claude/CLAUDE.md` (idempotent, marker-guarded, backs up first)

Then start a new session. Honors `$CLAUDE_CONFIG_DIR` if you keep config elsewhere.

### Manual install

If you'd rather not run the script:
1. Copy `agents/*.md` → `~/.claude/agents/`
2. Add `"model": "sonnet"` to `~/.claude/settings.json`
3. Paste the contents of `CLAUDE.routing.md` into `~/.claude/CLAUDE.md`

## Customize

- **Swap models** by editing the `model:` frontmatter in `agents/deep-work.md` /
  `agents/quick.md`. Pin full model IDs (e.g. `claude-opus-4-8`) rather than the `opus`
  alias to avoid subagent model-inheritance surprises.
- **Change the default floor** by editing `settings.json` — e.g. main-on-Opus with
  downward delegation if you'd rather have a smarter router and accept a higher base cost.
- **Tune the routing rules** by editing the rubric between the
  `<!-- BEGIN/END claude-model-router -->` markers in your `CLAUDE.md`.
- **Override per project** by dropping a `.claude/settings.json` in any repo — it beats
  the user-level default.

## License

MIT

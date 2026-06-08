# Models

This router pins **specific, tested model versions** rather than floating aliases
(`opus` / `sonnet` / `haiku`). That's deliberate: the entire premise of this project is
choosing models on purpose, so a new release should never silently take over a tier.
Every upgrade is a conscious decision, logged below.

## Current pins

| Tier | Model ID | Pinned | Role |
|------|----------|--------|------|
| Default / router | `claude-sonnet-4-6` | 2026-06-08 | Reads + classifies every task; handles mid-tier work |
| `quick` | `claude-haiku-4-5-20251001` | 2026-06-08 | Mechanical, self-verifying work — at volume |
| `deep-work` | `claude-opus-4-8` | 2026-06-08 | Sealed hard reasoning |

## Upgrade ritual — run this when a new model ships

When Anthropic releases a new model (Opus 4.9, Opus 5, a new Sonnet/Haiku, …), **do not
auto-bump.** Newer is not automatically better *for a given tier's job*. Run this:

1. **Read what Anthropic says it's good at.** Pull the announcement and model card —
   stated strengths, intended use, benchmark deltas, pricing, latency. Capture the actual
   claims; don't infer them.
2. **Map strengths to tiers.** Decide where (if anywhere) the new model actually helps:
   - Stronger *reasoning* → candidate to replace `deep-work` (the Opus tier).
   - Cheaper/faster but still *capable* → candidate for the router/default, or to shift a
     tier boundary.
   - Better *cheap/fast* model → candidate for `quick`.
3. **Decide the shape, not just the version.** Three honest outcomes:
   - **Upgrade in place** — swap the pin in the relevant `agents/*.md` or `settings.json`.
   - **Fork a new path** — if the model changes the economics enough to warrant a
     different *structure* (collapses two tiers into one, or finally makes a fourth tier
     pay for itself), branch and try it rather than mutating the main line.
   - **Hold** — if the gain doesn't clear the switching + re-testing cost, stay put.
4. **Test before committing.** Run a few representative tasks per affected tier — a real
   optimization for `deep-work`, a batch of edits for `quick` — and confirm the new model
   clears the bar at its price and latency, not just on paper.
5. **Re-check whether the scaffolding still earns its place.** A better model can make a
   tier — or the routing itself — unnecessary. If a stronger default means you stop
   reaching for `deep-work`, that's signal, not failure.
6. **Log it.** Add a dated entry below, bump the pin(s), and note *why*.

## Decision log

### 2026-06-08 — Initial pins
- `deep-work` → `claude-opus-4-8` · `quick` → `claude-haiku-4-5-20251001` ·
  default → `claude-sonnet-4-6`.
- Chose explicit version pins over aliases so future models (4.9 / 5) are evaluated on
  their stated strengths before adoption rather than inherited silently. Holding Opus at
  4.8 until a successor is read and tested per the ritual above.

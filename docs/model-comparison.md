# Model Comparison

Per assignment Section 4F, this assistant uses two models, in two
different roles — not as a side-by-side popularity contest, but reflecting
a deliberate cost/quality tradeoff: a cheap, fast model for routing, and a
free-tier capable model for actual conversational responses.

## Setup

| Role | Model | Provider | Why this role |
|---|---|---|---|
| Triage classification | `deepseek-chat` | DeepSeek (direct API key) | Single-word classification output, called on most incoming messages — needs to be fast and cheap, not high-reasoning |
| Main conversational responses | `nvidia/nemotron-3-ultra-550b-a55b:free` | OpenRouter | Free tier, large model, used for all actual drafting/answering/tool-calling |

An earlier configuration used `deepseek-v4-pro` (DeepSeek's full
reasoning model) for both roles. This was changed after observing real
token cost during development — full diagnostic conversations with a
large reasoning model, repeated many times while debugging, consumed
meaningfully more than the same conversations would with a lighter model.
Switching the main conversational role to the free OpenRouter model after
development was complete was a deliberate cost-control decision, not a
quality compromise for this assistant's actual day-to-day use (status
checks, quiz drafts, deadline logging) — none of which requires
frontier-level reasoning depth.

## Comparison table

| Model | Setup | Speed | Response Quality | Tool Use Accuracy | Cost | Notes |
|---|---|---|---|---|---|---|
| `deepseek-chat` | API key | Fast | N/A (single-word output only) | N/A (not given tools) | Low-cost | Used exclusively for classification; never sees user-facing output |
| `deepseek-v4-pro` | API key | Medium for long reasoning chains | High — correctly used registered tools once instructions were tightened (see reflection) | Good, after fixing two real bugs (vague instructions led to improvisation) | Paid, usage-based | Strong reasoning, but cost adds up quickly across an iterative debugging session |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | OpenRouter (one key) | Extremely slow, almost useless | Used successfully as the live default after switch-over; no comparison failures observed in normal use | Not formally tested against identical prompts | Free tier (rate-limited) | Large parameter count for a free-tier model; adopted for cost control after observing DeepSeek's usage-based cost during iterative development |

## Honest status

The DeepSeek row reflects real, observed behavior across a full day of
development and live testing (see `docs/reflection.md` for the specific
incidents referenced above) — including genuine tool calls, real
deadline lookups, and real quiz generation, all on `deepseek-v4-pro`.

The Nemotron model was connected, configured, and set as the live
default for day-to-day use, but a formal side-by-side test on identical
prompts was not run within this submission's time window — a deliberate
scoping decision given everything else completed (a working install,
three agents, six tools across two real external APIs, three skills,
and a fully functional email channel). The comparison table above
reflects the deliberate cost/role split actually deployed: DeepSeek for
classification, a free-tier OpenRouter model for the live default. A
formal head-to-head on identical prompts is the natural next step,
noted under "What would be improved next."

## Failure cases observed (both models)

These were not model-specific — they were architecture bugs that any
model would have hit, and are documented in full in
`docs/reflection.md`:

- Both models, when given vague instructions ("use memory_store.py via
  execute_code"), independently chose to create files in unintended
  locations rather than following the intended path exactly. This was
  fixed by removing the choice entirely (registered tools instead of
  code-execution instructions), not by prompting harder.
- Both models, when a tool's results seemed weak, reached for unscoped
  alternatives (browser automation, RSS scraping) rather than reporting
  the limitation. This is arguably *good* general-purpose judgment, but
  undesirable for an assistant whose tool outputs need to stay
  attributable for review purposes — fixed with an explicit
  instruction naming the exact behavior to avoid.

# Architecture & Design Rationale

## Why a Plugin, not a Profile

Hermes offers two ways to run multiple "agents": **Profiles** (separate
home directories, separate processes, separate gateway tokens) or a
**Plugin** with internal routing logic on top of one shared agent.

Profiles were considered and rejected for this use case, for two reasons:

1. **One communication channel, one number/account.** Profiles require
   each agent to run its own gateway with its own bot token — for email,
   that would mean three separate email accounts being polled
   independently, with no shared awareness between them. The user has one
   email identity for this assistant; three competing inboxes would be
   worse, not better.

2. **Cross-referencing is a stated requirement, not an edge case.** The
   user explicitly wants future agents (Career, Venture) to be able to
   *reference* facts from Research/Teaching (e.g., citing a published
   paper in a cover letter) without being able to *edit* or fully *read*
   Research's private working notes. Profiles store memory per-profile by
   design — building cross-profile read access would mean building
   exactly the permission system described below anyway, on top of
   Profiles' added process/token overhead. The Plugin approach gets this
   for free with one shared, scoped data store.

Profiles remain the right tool for a genuinely separate, unrelated agent
(e.g., a coding assistant with no relationship to Faculty Co-Pilot) — not
for this internally-related, internally-cross-referencing set of roles.

## Routing: per-turn context injection, not separate sessions

The Triage Router uses Hermes's `pre_llm_call` hook, which fires once per
turn and can inject text into that turn's user message — ephemeral,
never persisted to session history, and the system prompt (SOUL.md) stays
untouched so prompt caching isn't broken.

This was chosen over forcing a hard session-key switch per agent because:

- It's lighter weight for a single email/chat thread used continuously
  for one ongoing relationship with the assistant
- It still achieves the actual requirement (no agent's instructions leak
  into another's response) because injection is per-turn, not persistent
- **Sticky routing** (skip re-classification for up to 3 consecutive
  messages on the same topic) keeps classification cost low, with an
  explicit re-classification trigger if the message strongly matches a
  *different* agent's domain — this was a real bug caught during testing
  (see `docs/reflection.md`) where sticky routing initially let an
  obvious topic switch slip through unrouted.

## Memory: write scopes vs. read scopes

`agent_registry.py` defines, per agent:

- `write_scopes` — record types this agent may create or edit
- `read_scopes` — record types this agent may query but never edit

`memory_store.py` enforces this in code, not just by convention:
- `write()` checks the calling agent is the scope's designated writer
- `read()` returns a **field-filtered public view** — private fields
  (e.g. a paper's `captured_ideas`, `methodology_notes`) are never
  included, even for an agent with legitimate read access to that scope
- `read_full()` (private fields included) is only callable by the
  scope's own writer — a read-only agent cannot call it even though it
  has `read_scopes` for that type

This is what lets Career Agent (phase 2, currently inactive) eventually
cite "published a Q1 journal paper on X" in a cover letter, while never
seeing Research Agent's half-formed ideas or deadline stress notes.

## Tools, not `execute_code`

An earlier version of this plugin instructed the model to call
`memory_store.py` directly via `execute_code`/`terminal`. This failed in
practice: the model would intermittently improvise an alternate storage
file in an unrelated location (observed: a stray `memory_store.json`
created on the Desktop) rather than reliably using the intended path.

The fix was architectural, not a stronger prompt: `memory_store.py`'s
functions are now wrapped as **registered tools**
(`faculty_read_paper`, `faculty_write_paper`, etc.) via
`ctx.register_tool()`. The model never sees a file path — it sees a
named tool with a fixed implementation. There is no path left for it to
improvise an alternative, because the alternative (knowing where the
file lives) was the thing removed.

The same lesson was applied to news search after the model was observed
supplementing `faculty_news_search`'s results with unscoped browser
automation and RSS scraping when it judged the tool's results "thin" —
the fix was an explicit instruction naming this exact failure mode and
prohibiting it, added once the pattern was directly observed twice.

## Extensibility: Career and Venture agents

Two more agents are registered in `agent_registry.py` with
`active=False`. This means:

- They appear in the registry, with their scopes and classifier
  descriptions already defined
- The Triage Router's classifier prompt excludes them (filtered via
  `_active_agents()`), so they cannot be accidentally routed to before
  they're actually built
- Turning one on requires: writing its instructions block in
  `agent_instructions.py`, writing its tool handlers (if it needs new
  data types), and flipping `active=True` — no changes to the router,
  memory store enforcement, or hook registration

# Reflection

## What worked well

- **The Triage Router + shared memory store architecture held up.**
  Once built correctly, routing between Research/Teaching/Planning agents
  worked reliably, including correctly re-classifying mid-conversation
  topic switches (after a bug fix — see below).
- **Permission boundaries were genuinely enforced, not just assumed.**
  Sandbox tests proved Planning Agent's read-only access and Career/
  Venture's future read-only cross-referencing design hold even under
  direct attempts to violate them (`PermissionError` raised correctly in
  every tested case).
- **Switching from `execute_code` instructions to real registered tools
  was the single highest-value architectural change.** It eliminated an
  entire category of bugs (the model creating unscoped files in
  unintended locations) by removing the model's ability to choose an
  alternate path, rather than asking it not to.
- **Email as a communication channel works**, end-to-end, including a
  genuine round trip: email in → router → agent → tool → reply → SMTP →
  back to the inbox, with real data persisted between separate messages.

## What failed (and was fixed)

1. **Relative vs. absolute imports across two loading contexts.**
   `memory_store.py` needed to work both when loaded as part of the
   Hermes plugin package (relative imports) and when an agent might run
   it standalone via `execute_code` (absolute imports, no parent
   package). The fix was a try/except import fallback — but the deeper
   lesson was that our own test suite, using flat `sys.path` imports,
   would never have caught the original bug. Tests were rewritten to
   simulate real package-style loading via `importlib`, which did catch
   it.

2. **Sticky routing could blindly override an obvious topic switch.**
   The cost-saving "skip re-classification for 3 messages" logic
   initially had no mechanism to detect that message 2 in a sticky
   window was actually about a different agent's domain. Caught by a
   unit test specifically designed to simulate a Research → Teaching
   switch mid-conversation; fixed by adding a lightweight keyword-overlap
   check that forces re-classification on a strong domain-word match,
   tuned twice — first to add the check, then again to exclude incidental
   stopwords ("status", "what's") that were causing false positives.

3. **A model improvising an unscoped data file instead of using the
   intended module.** When instructed to "run `memory_store.py` via
   execute_code," the model — more than once, across multiple sessions —
   created its own `memory_store.json` in an unrelated folder (the
   Desktop) instead. Prompt-level warnings ("do not create a file
   elsewhere") were not reliable; the model repeated the behavior even
   after being told not to. The actual fix was architectural: removing
   the model's visibility into any file path at all, replacing
   file-access instructions with named, registered tools.

4. **A guessed internal API that didn't exist.** An early version of the
   router called a placeholder `ctx.dispatch_tool("llm_complete", ...)`
   for cheap classification — invented rather than confirmed. This caused
   silent failures (classification always fell back to "none"). The
   actual API (`agent.auxiliary_client.call_llm`, with a
   `register_auxiliary_task` registration step) was found by asking the
   live system directly rather than continuing to guess.

5. **Two genuinely different "the plugin isn't working" causes, easy to
   conflate.** Across one extended session, the plugin failed to load
   (missing `agent_registry.py`) for a real, multi-hour stretch — every
   test run during that window was silently testing a dead plugin that
   had fallen back to default behavior. Distinguishing "the plugin
   crashed" from "the plugin works but skills aren't discoverable from
   the tool I'm using to check" required reading actual log timestamps
   rather than trusting a single chat response.

6. **Windows Smart App Control blocking the CLI, unrelated to the
   actual application.** A `hermes plugins list` command was blocked by
   a Windows security policy that evaluates the terminal-invoked binary
   separately from the already-trusted Desktop app process. This had
   nothing to do with our plugin code, but looked at first like a
   regression. Resolved by switching verification entirely to
   chat-based checks, which were unaffected.

## Which model performed best

See `docs/model-comparison.md`. The honest answer: for this assistant's
actual workload (status checks, short drafts, tool calls), the free-tier 
model doesn't perform adequately, and the cost difference against a paid
reasoning model is the more decisive factor than raw capability for this
particular use case. Still, deepseek was more useable. 

## How the assistant improved the workflow

Even mid-development, **real, usable changes were made through it**: a
deadline was set and correctly retrieved in a later, separate message; a
literature finding was logged against the correct paper from natural
language alone. This is qualitatively different from a demo — it's the
actual record the user will keep building on, with real data already in
it before the assignment was finished.

## What would be improved next

- **Run a formal head-to-head model comparison** on identical prompts
  across DeepSeek and the free OpenRouter model — deferred during this
  submission in favor of completing the core system (agents, tools,
  skills, and a working email channel), but the most direct way to
  fill in the one remaining placeholder in `docs/model-comparison.md`.
- **Finish wiring the weekly-digest skill to a scheduled cron job**, so
  status overviews arrive proactively rather than only on request —
  this was designed for from the start (Planning Agent's role is
  explicitly "overview, not work") but not yet automated.
- **Build out Career and Venture agents**, which the architecture was
  explicitly designed to support without rework — the registry, the
  read/write scope split, and the router's `active` flag are all already
  in place for this.
- **Tighten the news-search and lit-search instructions further** if the
  model is observed reaching for unscoped tools again in new
  circumstances — this was fixed reactively twice already, and a more
  general "use only registered tools for X category of task" instruction
  pattern may be worth applying preemptively to future tools, rather
  than waiting to observe each individual failure mode.
- **Smooth out the email channel's occasional multi-message replies**,
  observed once during testing — likely an IMAP poll-timing or
  message-chunking issue rather than a routing bug, not yet root-caused.

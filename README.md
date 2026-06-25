# Faculty Co-Pilot

A personal AI assistant built on **Hermes Agent**, designed for an academic
juggling research, teaching, and a household with no spare time. Reachable
by email, it routes incoming messages to one of three specialized agents —
Research, Teaching, or Planning — each backed by real registered tools and
skills, sharing one permission-scoped memory core.

Built for the Agentic AI Bootcamp (atomcamp) — Assignment: *Build Your Own
Local Personal AI Assistant Using OpenClaw or Hermes Agent*.

---

## What it does

- **Research Agent** — tracks working papers (status, deadlines,
  collaborators), logs literature summaries, searches arXiv
- **Teaching Agent** — manages course records (Business Analytics,
  Decision Analysis), generates quiz questions, searches course-relevant
  news
- **Planning Agent** — read-only weekly/status overview across both
  domains, never drafts content itself

A lightweight **Triage Router** classifies each incoming message and
injects the right agent's instructions for that turn only — no agent ever
sees another agent's private notes, enforced at the data layer, not just
by prompting.

---

## Architecture

```
Email (IMAP/SMTP)
      ↓
Triage Router (pre_llm_call hook, cheap-model classification + sticky routing)
      ↓
   ┌──────────────┬──────────────┬──────────────┐
   │ Research     │ Teaching     │ Planning     │
   │ Agent        │ Agent        │ Agent        │
   └──────┬───────┴──────┬───────┴──────┬───────┘
          ↓              ↓              ↓
   faculty_read/write_paper      faculty_read/write_course
          │              │              │
          └──────────────┴──────────────┘
                         ↓
              memory_store.json
        (write/read scopes enforced per agent)
```

See [`docs/architecture.md`](docs/architecture.md) for the full design
rationale, including why a Hermes **plugin** was chosen over **Profiles**
for this use case.

---

## Installation

1. Install [Hermes Agent](https://hermes-agent.nousresearch.com/) (Desktop
   app or CLI)
2. Copy the `faculty-router/` folder into your Hermes plugins directory:
   ```
   <HERMES_HOME>/plugins/faculty-router/
   ```
   (On Windows: `%LOCALAPPDATA%\hermes\plugins\faculty-router\`)
3. Copy `.env.example` to `.env` in your Hermes home directory and fill in
   your own keys (see below)
4. Enable the plugin:
   ```
   hermes plugins enable faculty-router
   hermes plugins enable email-platform
   ```
5. Restart Hermes fully (not just a new session — plugin code only loads
   at process start)

### Required environment variables

See `.env.example` for the full template. At minimum, you need:

```
DEEPSEEK_API_KEY=...           # or any provider Hermes supports
OPENROUTER_API_KEY=...         # for the free-tier comparison model

EMAIL_ADDRESS=your-bot@gmail.com
EMAIL_PASSWORD=your-16-char-app-password   # NOT your real Gmail password
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_ALLOWED_USERS=your-bot@gmail.com,your-real-email@gmail.com

NEWS_API_KEY=...               # free tier at newsapi.org
```

**Gmail setup note:** enable 2-Step Verification, then generate an App
Password at myaccount.google.com/apppasswords — this is what goes in
`EMAIL_PASSWORD`, never your actual account password. Use a **dedicated**
email address for the bot, not your personal one.

### Running it

```
hermes gateway run
```

This starts the email gateway in the foreground. For always-on use:
```
hermes gateway install
```
installs it as a background service that starts on login.

---

## Agents

| Agent | Responsibility | Write access | Read access |
|---|---|---|---|
| **Research** | Papers, lit review, deadlines, methodology | `paper` | — |
| **Teaching** | Courses, lectures, quizzes, case studies | `course` | — |
| **Planning** | Cross-domain status overview | none | `paper`, `course` (public fields only) |

Two more agents — **Career** and **Venture** — are registered in
`agent_registry.py` but deliberately inactive (`active=False`). Adding
them later means adding one registry entry and a prompt file; no changes
to the router, memory store, or tool registration are needed. They will
have **read-only** access to papers/courses (for CV-building, etc.) but
cannot write to or fully read Research/Teaching's private notes — see
`docs/architecture.md` for the cross-referencing design.

---

## Skills

| Skill | Category | What it does |
|---|---|---|
| `lit-summarizer` | research | Extracts findings from a shared paper, logs them against the right paper record |
| `quiz-generator` | teaching | Writes level-appropriate quiz questions, saves them to a course's quiz bank |
| `weekly-digest` | planning | Read-only status overview across all papers and courses, prioritized by urgency |

Full skill definitions: `plugins/faculty-router/skills/<category>/<name>/SKILL.md`

---

## Tools

| Tool | Type | Purpose |
|---|---|---|
| `faculty_read_paper` / `faculty_write_paper` | Internal (local file) | Paper record CRUD |
| `faculty_read_course` / `faculty_write_course` | Internal (local file) | Course record CRUD |
| `faculty_status_digest` | Internal (local file) | Read-only combined overview |
| `faculty_news_search` | **External — NewsAPI.org** | Course-relevant news search |
| Gmail (IMAP/SMTP) | **External — communication channel** | Receive/send messages |
| `arxiv` (bundled Hermes skill) | **External — arXiv API** | Academic paper search |

Two external APIs satisfy the assignment's tool requirement: **NewsAPI.org**
and **Gmail (IMAP/SMTP)**. `arxiv` is used as a supporting tool for the
Research Agent's literature search needs.

---

## Example usage

> **Input (email):** "What's the deadline status on my Brand-Follower
> Congruence paper?"
>
> **Agent:** Research Agent (classified by Triage Router)
> **Tool used:** `faculty_read_paper`
> **Reply:** "Brand-Follower Congruence — status: draft, no deadline set.
> Collaborators: Ahmed. Want me to set one?"

> **Input (email):** "Find news about decision trees for my course"
>
> **Agent:** Teaching Agent
> **Tool used:** `faculty_news_search`
> **Reply:** 5 recent article titles/sources/URLs, with an honest note
> when relevance is weak rather than padding with unrelated results.

See `docs/demo-screenshots/` for real screenshots of these exchanges.

---

## Model comparison

See [`docs/model-comparison.md`](docs/model-comparison.md) for the full
write-up. Summary:

| Model | Provider | Role | Cost |
|---|---|---|---|
| `deepseek-chat` | DeepSeek | Triage classification (cheap, fast) | Free/low-cost tier |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | OpenRouter | Main conversational model | Free tier |

---

## What worked, what failed, what's next

See [`docs/reflection.md`](docs/reflection.md) for the full reflection,
including real bugs found and fixed during development — relative import
failures, a model improvising an unscoped data file, sticky-routing logic
errors, and a Windows Smart App Control block that turned out to be
unrelated to the actual application.

---

## Project structure

```
faculty-router/
├── plugin.yaml
├── __init__.py              # register() — hooks, tools, auxiliary task, skills
├── router.py                 # Triage Router: classify, sticky routing, override
├── agent_registry.py          # Single source of truth for all agents + permissions
├── agent_instructions.py      # Per-turn injected instructions per agent
├── memory_store.py            # Permission-enforced read/write to memory_store.json
├── schemas.py                 # Tool schemas (what the LLM sees)
├── tools.py                   # Tool handlers (what actually runs)
└── skills/
    ├── research/lit-summarizer/SKILL.md
    ├── teaching/quiz-generator/SKILL.md
    └── planning/weekly-digest/SKILL.md
```

## Safety notes

- `.env` is gitignored; only `.env.example` (with placeholders) is committed
- Email access is restricted via `EMAIL_ALLOWED_USERS` — only the listed
  addresses can trigger the assistant
- A dedicated email account is used for the bot, separate from personal
  accounts
- No destructive actions (delete, irreversible sends) are performed without
  the user directly typing the request

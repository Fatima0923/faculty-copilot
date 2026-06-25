"""
Agent Registry — single source of truth for every agent in Faculty Co-Pilot.

WHY THIS EXISTS:
Adding a new agent (Career, Venture) later should mean adding ONE entry here —
nothing in router.py, memory_store.py, or the Hermes hook itself should need
to change. This file is the seam.

ISOLATION CONTRACT (read this before adding an agent):
- `session_key`   : Hermes session ID. NEVER shared between two agents.
- `system_prompt_file` : path to that agent's own prompt. NEVER inherits
                          another agent's prompt or appends to it.
- `write_scopes`  : record types this agent may CREATE or EDIT.
                    Enforced in memory_store.py — an agent not listed as a
                    writer for a scope cannot write to it, full stop.
- `read_scopes`   : record types this agent may QUERY but never edit.
                    This is the cross-referencing seam: e.g. Career Agent
                    reads "paper" facts to strengthen a cover letter, but
                    has no write_scope for "paper" — it cannot edit, log
                    ideas against, or otherwise mutate Research's data.
                    Cross-referencing is always an explicit, attributable
                    query — never automatic session/prompt inheritance.
- `classifier_description` : ONLY text the cheap routing classifier sees
                    for this agent. Keep it behavior-descriptive
                    ("papers, deadlines, lit review") not data-descriptive
                    (never paste real paper titles/content here — that
                    would leak Research Agent's data into the classifier
                    prompt, which is shared infrastructure all agents pass
                    through).
"""

from dataclasses import dataclass
from typing import Literal

MemoryScope = Literal[
    "paper", "course", "digest_read_only", "job_application", "venture_idea"
]


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    session_key: str
    system_prompt_file: str
    write_scopes: tuple[MemoryScope, ...]
    classifier_description: str
    read_scopes: tuple[MemoryScope, ...] = ()
    active: bool = True  # False = registered but not yet routed to (phase-2 stub)


# ---------------------------------------------------------------------------
# v1 agents — Research, Teaching, Planning (live)
# Phase-2 agents — Career, Venture (registered now, inactive until built)
# ---------------------------------------------------------------------------
AGENTS: dict[str, AgentDefinition] = {
    "research": AgentDefinition(
        name="research",
        session_key="agent.research",
        system_prompt_file="prompts/research_agent.md",
        write_scopes=("paper",),
        classifier_description=(
            "Academic papers, literature review, manuscript writing, "
            "research deadlines, methodology questions, paper reviews, "
            "logging a new idea or finding against a working paper."
        ),
    ),
    "teaching": AgentDefinition(
        name="teaching",
        session_key="agent.teaching",
        system_prompt_file="prompts/teaching_agent.md",
        write_scopes=("course",),
        classifier_description=(
            "Lecture prep, course outlines, quiz or exam questions, "
            "case studies, classroom activities, course-relevant news, "
            "anything about Business Analytics or Decision Analysis classes."
        ),
    ),
    "planning": AgentDefinition(
        name="planning",
        session_key="agent.planning",
        system_prompt_file="prompts/planning_agent.md",
        write_scopes=(),
        read_scopes=("paper", "course"),
        classifier_description=(
            "Status checks, 'what's due', weekly or daily summaries, "
            "deadline overviews spanning BOTH research and teaching — "
            "use this when the message is about overall workload, not "
            "about doing one specific piece of work."
        ),
    ),

    # -- Phase 2: registered now so router/memory_store logic is already
    #    exercised against them, but `active=False` keeps the Triage Router
    #    from ever routing a real message here until we actually build the
    #    prompt files and turn them on.
    "career": AgentDefinition(
        name="career",
        session_key="agent.career",
        system_prompt_file="prompts/career_agent.md",
        write_scopes=("job_application",),
        read_scopes=("paper", "course"),  # cross-reference for CVs/cover letters
        classifier_description=(
            "Job applications, CV tailoring, cover letters, Australia "
            "assistant professor roles, visa/immigration-linked career planning."
        ),
        active=False,
    ),
    "venture": AgentDefinition(
        name="venture",
        session_key="agent.venture",
        system_prompt_file="prompts/venture_agent.md",
        write_scopes=("venture_idea",),
        read_scopes=("paper",),  # e.g. published personality-prediction work -> brand-profiling pitch
        classifier_description=(
            "Side-hustle marketing AI business: brand kits, ad copy, "
            "AI influencer content ideas, client pitch material."
        ),
        active=False,
    ),
}

DEFAULT_FALLBACK_MESSAGE = (
    "I don't have an agent for that yet — right now I handle research, "
    "teaching, and planning. Want me to log this as a note for later, "
    "or did you mean one of those three?"
)

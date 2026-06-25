"""
Faculty Co-Pilot — Memory Core

Enforces the write_scopes / read_scopes contract from agent_registry.py in
actual code, not just naming convention. Every read/write call must pass
the requesting agent's key — the store checks permissions before touching
data, every time. There is no path that skips this check.

CROSS-REFERENCING DESIGN:
read() returns a PUBLIC VIEW of a record, not the raw record. For "paper"
records, this means Career/Venture Agents (read-only) get back title,
status, and published findings — but NEVER captured_ideas[] or
methodology_notes[], which stay visible only to Research Agent (the writer).
This is enforced by field allow-listing per scope, not by trusting agents
to "be polite" about what they look at.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

try:
    # Loaded as part of the Hermes plugin package (normal case).
    from .agent_registry import AGENTS, MemoryScope
except ImportError:
    # Run standalone via execute_code/terminal — no parent package exists,
    # so fall back to a same-directory absolute import. This is the path
    # an agent takes when it runs `import memory_store` directly as a
    # script rather than through Hermes's plugin loader.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from agent_registry import AGENTS, MemoryScope

STORE_PATH = Path(__file__).parent / "memory_store.json"

# Fields visible to READ-ONLY consumers of each scope. Everything not
# listed here is writer-only and never leaves the store for a read() call.
PUBLIC_VIEW_FIELDS: dict[MemoryScope, tuple[str, ...]] = {
    "paper": ("title", "status", "next_deadline", "collaborators", "key_findings"),
    "course": ("course_name", "level", "topics_covered"),
}


class PermissionError(Exception):
    pass


@dataclass
class PaperRecord:
    title: str
    status: str  # idea | draft | review | submitted | published
    next_deadline: str | None
    collaborators: list[str] = field(default_factory=list)
    key_findings: str | None = None          # public-safe summary
    methodology_notes: list[str] = field(default_factory=list)  # writer-only
    lit_summaries: list[str] = field(default_factory=list)      # writer-only
    captured_ideas: list[str] = field(default_factory=list)     # writer-only
    last_updated: str = ""


@dataclass
class CourseRecord:
    course_name: str
    level: str
    topics_covered: list[str] = field(default_factory=list)
    next_lecture_date: str | None = None      # writer-only
    lecture_outlines: list[str] = field(default_factory=list)   # writer-only
    quiz_bank: list[str] = field(default_factory=list)          # writer-only
    case_studies: list[str] = field(default_factory=list)       # writer-only
    last_updated: str = ""


def _seed_data() -> dict:
    now = datetime.now().isoformat(timespec="minutes")
    papers = {
        "ai_influencers": PaperRecord(
            title="AI Influencers and Audience Behaviour",
            status="draft",
            next_deadline=None,
            collaborators=[],
            key_findings=None,
            last_updated=now,
        ),
        "brand_follower_congruence": PaperRecord(
            title="Brand-Follower Personality Congruence and Follower Engagement",
            status="draft",
            next_deadline=None,
            collaborators=["Ahmed"],
            key_findings=None,
            last_updated=now,
        ),
        "generative_ai_art": PaperRecord(
            title="Generative AI and Art: Impact on Purchase Behavior",
            status="idea",
            next_deadline=None,
            collaborators=[],
            key_findings=None,
            last_updated=now,
        ),
        "automation_advertising": PaperRecord(
            title="Automation in the Advertising Domain",
            status="idea",
            next_deadline=None,
            collaborators=[],
            key_findings="Methodology in progress",
            last_updated=now,
        ),
    }
    courses = {
        "business_analytics": CourseRecord(
            course_name="Business Analytics",
            level="Level 4",
            topics_covered=[],
            last_updated=now,
        ),
        "decision_analysis": CourseRecord(
            course_name="Decision Analysis",
            level="Level 7",
            topics_covered=[],
            last_updated=now,
        ),
    }
    return {
        "paper": {k: asdict(v) for k, v in papers.items()},
        "course": {k: asdict(v) for k, v in courses.items()},
    }


def _load() -> dict:
    if not STORE_PATH.exists():
        data = _seed_data()
        _save(data)
        return data
    return json.loads(STORE_PATH.read_text())


def _save(data: dict) -> None:
    STORE_PATH.write_text(json.dumps(data, indent=2))


def _require_scope(agent_key: str, scope: MemoryScope, mode: str) -> None:
    agent = AGENTS.get(agent_key)
    if agent is None:
        raise PermissionError(f"Unknown agent '{agent_key}'")
    allowed = agent.write_scopes if mode == "write" else (agent.write_scopes + agent.read_scopes)
    if scope not in allowed:
        raise PermissionError(
            f"Agent '{agent_key}' has no {mode} access to scope '{scope}'. "
            f"write_scopes={agent.write_scopes}, read_scopes={agent.read_scopes}"
        )


def write(agent_key: str, scope: MemoryScope, record_id: str, updates: dict) -> None:
    """Full read/write access — only for the scope's designated writer."""
    _require_scope(agent_key, scope, mode="write")
    data = _load()
    bucket = data.setdefault(scope, {})
    record = bucket.setdefault(record_id, {})
    record.update(updates)
    record["last_updated"] = datetime.now().isoformat(timespec="minutes")
    _save(data)


def read(agent_key: str, scope: MemoryScope, record_id: str | None = None) -> dict:
    """
    Returns the PUBLIC VIEW only — fields in PUBLIC_VIEW_FIELDS for that
    scope. Works for both the scope's writer (convenience) and read-only
    cross-referencing agents (the actual point of this function).
    Private writer-only fields (methodology_notes, captured_ideas, etc.)
    are never included here, regardless of who's asking.
    """
    _require_scope(agent_key, scope, mode="read")
    data = _load()
    bucket = data.get(scope, {})
    allowed_fields = PUBLIC_VIEW_FIELDS.get(scope, ())

    def _view(record: dict) -> dict:
        return {k: v for k, v in record.items() if k in allowed_fields}

    if record_id is not None:
        record = bucket.get(record_id)
        return _view(record) if record else {}
    return {rid: _view(rec) for rid, rec in bucket.items()}


def read_full(agent_key: str, scope: MemoryScope, record_id: str | None = None) -> dict:
    """
    Full record access including private fields — ONLY callable by that
    scope's designated writer (checked via mode='write', same as write()).
    Planning Agent, Career Agent, etc. cannot call this even for scopes
    they have read_scopes on.
    """
    _require_scope(agent_key, scope, mode="write")
    data = _load()
    bucket = data.get(scope, {})
    if record_id is not None:
        return bucket.get(record_id, {})
    return bucket

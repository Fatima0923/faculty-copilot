"""
Faculty Co-Pilot — Triage Router, adapted to Hermes's real pre_llm_call hook.

Real signature confirmed from Hermes docs (Build a Hermes Plugin):
    pre_llm_call(session_id, user_message, conversation_history,
                 is_first_turn, model, platform, **kwargs) -> dict | str | None

Return {"context": "..."} to inject per-turn instructions into the user
message. Returning None means no injection (message proceeds unmodified
or, here, with the fallback notice handled separately).

This file keeps the SAME classification/sticky/override logic we already
unit-tested in the standalone prototype — only the entry point and return
shape changed to match the real hook contract.
"""

import re

from .agent_registry import AGENTS, DEFAULT_FALLBACK_MESSAGE
from .agent_instructions import get_instructions

STICKY_WINDOW = 3
MANUAL_OVERRIDE_PATTERN = re.compile(r"^use:(\w+)\b", re.IGNORECASE)

_STOPWORDS = {
    "what's", "anything", "against", "spanning", "message", "specific",
    "overall", "overviews",
}

# Per-session sticky state. session_id is what Hermes gives the hook —
# already unique per WhatsApp DM user, per CLI session, etc. (see Sessions
# docs), so we don't need to build our own per-chat keying on top of it.
_sticky_state: dict[str, dict] = {}


def _active_agents() -> dict:
    return {k: a for k, a in AGENTS.items() if a.active}


def _check_manual_override(message_text: str) -> str | None:
    match = MANUAL_OVERRIDE_PATTERN.match(message_text.strip())
    if not match:
        return None
    requested = match.group(1).lower()
    return requested if requested in _active_agents() else None


def _check_sticky(session_id: str, message_text: str) -> str | None:
    state = _sticky_state.get(session_id)
    if not state or state["count"] >= STICKY_WINDOW:
        return None
    sticky_agent_key = state["agent_key"]
    lowered = message_text.lower()
    for key, agent in _active_agents().items():
        if key == sticky_agent_key:
            continue
        domain_words = {
            w.strip(".,'\"") for w in agent.classifier_description.lower().split()
            if len(w) > 5 and w.strip(".,'\"") not in _STOPWORDS
        }
        if sum(1 for w in domain_words if w in lowered) >= 2:
            return None
    return sticky_agent_key


def _update_sticky(session_id: str, agent_key: str) -> None:
    state = _sticky_state.get(session_id)
    if state and state["agent_key"] == agent_key:
        state["count"] += 1
    else:
        _sticky_state[session_id] = {"agent_key": agent_key, "count": 1}


def _build_classifier_prompt(message_text: str) -> str:
    options = "\n".join(
        f'- "{key}": {agent.classifier_description}'
        for key, agent in _active_agents().items()
    )
    return f"""You are a strict message classifier. Output EXACTLY ONE WORD and \
NOTHING ELSE — no punctuation, no explanation, no reasoning, no greeting.

Categories:
{options}
- none: doesn't clearly fit any category above

Message: {message_text!r}

Reply with exactly one of these words: {', '.join(_active_agents().keys())}, none
Your one-word answer:"""


def _classify_via_auxiliary(prompt: str) -> str:
    """
    Uses the real Hermes auxiliary-model API (agent.auxiliary_client.call_llm)
    against our registered "faculty_router_classify" task — NOT dispatch_tool,
    which is for invoking existing tools (terminal, file ops) with side
    effects. This is a plain LLM completion call, routed through whichever
    provider the user configured for this task (default: auto-resolution
    chain, same as any other auxiliary task).
    Falls back to "none" on any failure (fail-open to the graceful
    fallback message, never silently mis-route or crash the turn).
    """
    try:
        from agent.auxiliary_client import call_llm
        response = call_llm(
            task="faculty_router_classify",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        raw = response.choices[0].message.content.strip().lower()
        # Defensive cleanup: take only the first whitespace-separated token
        # and strip common punctuation, in case the model adds anything
        # beyond the single word we asked for.
        first_word = raw.split()[0] if raw.split() else raw
        return first_word.strip('.,!?"\'')
    except Exception:
        return "none"


def route_and_get_context(session_id: str, user_message: str) -> dict | None:
    """
    Core entry point called from the pre_llm_call hook. Returns a dict
    with a "context" key (Hermes's expected injection format) or None.
    """
    override = _check_manual_override(user_message)
    if override:
        _sticky_state[session_id] = {"agent_key": override, "count": 1}
        return {"context": get_instructions(override)}

    sticky_agent_key = _check_sticky(session_id, user_message)
    if sticky_agent_key:
        _update_sticky(session_id, sticky_agent_key)
        return {"context": get_instructions(sticky_agent_key)}

    prompt = _build_classifier_prompt(user_message)
    category = _classify_via_auxiliary(prompt)

    if category in _active_agents():
        _update_sticky(session_id, category)
        return {"context": get_instructions(category)}

    _sticky_state.pop(session_id, None)
    return {"context": DEFAULT_FALLBACK_MESSAGE}

"""Faculty Co-Pilot — plugin registration."""

import logging
from pathlib import Path

from . import router, schemas, tools

logger = logging.getLogger(__name__)


def _on_pre_llm_call(session_id, user_message, conversation_history,
                      is_first_turn, model, platform, **kwargs):
    """
    pre_llm_call hook — fires once per turn, before the tool-calling loop.
    Returning {"context": ...} injects per-agent instructions into THIS
    turn's user message only (ephemeral, never written to session history,
    system prompt stays untouched so prompt caching is preserved).
    """
    logger.warning(
        "faculty-router: pre_llm_call FIRED — session_id=%r, "
        "user_message=%r, platform=%r", session_id, user_message, platform
    )
    try:
        result = router.route_and_get_context(session_id, user_message)
        logger.warning("faculty-router: returning context=%r", result)
        return result
    except Exception:
        logger.exception("faculty-router: routing failed, passing through unmodified")
        return None  # fail open — never block the user's message


def register(ctx):
    ctx.register_hook("pre_llm_call", _on_pre_llm_call)

    # Real tools, not "run this code via execute_code" instructions.
    # The model calls these by name; it never sees a file path, so it
    # has no opportunity to improvise an alternate storage location.
    ctx.register_tool(name="faculty_read_paper", toolset="faculty-router",
                       schema=schemas.READ_PAPER, handler=tools.read_paper)
    ctx.register_tool(name="faculty_write_paper", toolset="faculty-router",
                       schema=schemas.WRITE_PAPER, handler=tools.write_paper)
    ctx.register_tool(name="faculty_read_course", toolset="faculty-router",
                       schema=schemas.READ_COURSE, handler=tools.read_course)
    ctx.register_tool(name="faculty_write_course", toolset="faculty-router",
                       schema=schemas.WRITE_COURSE, handler=tools.write_course)
    ctx.register_tool(name="faculty_status_digest", toolset="faculty-router",
                       schema=schemas.READ_STATUS_DIGEST, handler=tools.read_status_digest)
    ctx.register_tool(name="faculty_news_search", toolset="faculty-router",
                       schema=schemas.FACULTY_NEWS_SEARCH, handler=tools.news_search)

    # Register our own auxiliary task so classification routing gets its
    # own model/provider slot — shows up in `hermes model -> Configure
    # auxiliary models` alongside built-ins like compression/vision.
    ctx.register_auxiliary_task(
        key="faculty_router_classify",
        display_name="Faculty Co-Pilot: message routing",
        description=(
            "Classifies incoming messages into research/teaching/planning "
            "for per-turn instruction injection. Short, cheap, no tool use."
        ),
        defaults={"provider": "auto", "timeout": 8},
    )

    # Walk the real two-level <category>/<name>/SKILL.md structure that
    # matches Hermes's documented skill path convention (confirmed via
    # the hermes-agent skill earlier in this build). A flat one-level
    # walk would silently find nothing here — caught and fixed before
    # shipping, not left as a quiet no-op.
    skills_dir = Path(__file__).parent / "skills"
    registered_skills = []
    if skills_dir.exists():
        for category in sorted(skills_dir.iterdir()):
            if not category.is_dir():
                continue
            for skill_folder in sorted(category.iterdir()):
                skill_md = skill_folder / "SKILL.md"
                if skill_folder.is_dir() and skill_md.exists():
                    ctx.register_skill(skill_folder.name, skill_md)
                    registered_skills.append(f"{category.name}/{skill_folder.name}")

    logger.info(
        "faculty-router: registered pre_llm_call hook, 5 tools, "
        "auxiliary task, and %d skills: %s",
        len(registered_skills), registered_skills,
    )

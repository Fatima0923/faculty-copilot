"""
Tool handlers — the code that actually runs when the LLM calls each
faculty_* tool. These wrap memory_store.py directly; there is no path
for the model to improvise an alternate storage location, because the
model never sees a file path at all — it only sees named tools.

Handler contract (per Hermes plugin docs):
1. def handler(args: dict, **kwargs) -> str
2. Always return a JSON string, success and error alike
3. Never raise — catch everything
"""

import json

from . import memory_store as ms


def _agent_key_for(toolset: str) -> str:
    """
    All our tools are registered under toolsets matching our internal
    agent names, so the calling agent's permission key is implicit in
    which tool got called — research tools always pass agent_key=
    "research", etc. This means write_paper can NEVER be invoked with
    the wrong permission key, because there is only one key wired to
    each tool, hardcoded here rather than trusted from model input.
    """
    return toolset


def read_paper(args: dict, **kwargs) -> str:
    try:
        paper_id = args.get("paper_id")
        result = ms.read_full("research", "paper", paper_id) if paper_id else ms.read_full("research", "paper")
        return json.dumps({"papers": result})
    except ms.PermissionError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"})


def write_paper(args: dict, **kwargs) -> str:
    try:
        paper_id = args.get("paper_id")
        if not paper_id:
            return json.dumps({"error": "paper_id is required"})

        updates = {}
        if "status" in args:
            updates["status"] = args["status"]
        if "next_deadline" in args:
            updates["next_deadline"] = args["next_deadline"]

        existing = ms.read_full("research", "paper", paper_id)
        if not existing:
            return json.dumps({"error": f"No paper record '{paper_id}'"})

        if "add_collaborator" in args:
            collabs = list(existing.get("collaborators", []))
            if args["add_collaborator"] not in collabs:
                collabs.append(args["add_collaborator"])
            updates["collaborators"] = collabs
        if "add_captured_idea" in args:
            ideas = list(existing.get("captured_ideas", []))
            ideas.append(args["add_captured_idea"])
            updates["captured_ideas"] = ideas
        if "add_methodology_note" in args:
            notes = list(existing.get("methodology_notes", []))
            notes.append(args["add_methodology_note"])
            updates["methodology_notes"] = notes
        if "add_lit_summary" in args:
            summaries = list(existing.get("lit_summaries", []))
            summaries.append(args["add_lit_summary"])
            updates["lit_summaries"] = summaries

        if not updates:
            return json.dumps({"error": "No fields to update were provided"})

        ms.write("research", "paper", paper_id, updates)
        return json.dumps({"success": True, "paper": ms.read_full("research", "paper", paper_id)})
    except ms.PermissionError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"})


def read_course(args: dict, **kwargs) -> str:
    try:
        course_id = args.get("course_id")
        result = ms.read_full("teaching", "course", course_id) if course_id else ms.read_full("teaching", "course")
        return json.dumps({"courses": result})
    except ms.PermissionError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"})


def write_course(args: dict, **kwargs) -> str:
    try:
        course_id = args.get("course_id")
        if not course_id:
            return json.dumps({"error": "course_id is required"})

        existing = ms.read_full("teaching", "course", course_id)
        if not existing:
            return json.dumps({"error": f"No course record '{course_id}'"})

        updates = {}
        if "add_topic_covered" in args:
            topics = list(existing.get("topics_covered", []))
            topics.append(args["add_topic_covered"])
            updates["topics_covered"] = topics
        if "add_lecture_outline" in args:
            outlines = list(existing.get("lecture_outlines", []))
            outlines.append(args["add_lecture_outline"])
            updates["lecture_outlines"] = outlines
        if "add_quiz_item" in args:
            quiz = list(existing.get("quiz_bank", []))
            quiz.append(args["add_quiz_item"])
            updates["quiz_bank"] = quiz
        if "add_case_study" in args:
            cases = list(existing.get("case_studies", []))
            cases.append(args["add_case_study"])
            updates["case_studies"] = cases

        if not updates:
            return json.dumps({"error": "No fields to update were provided"})

        ms.write("teaching", "course", course_id, updates)
        return json.dumps({"success": True, "course": ms.read_full("teaching", "course", course_id)})
    except ms.PermissionError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"})


def read_status_digest(args: dict, **kwargs) -> str:
    """
    Always called with agent_key="planning" — read-only by construction,
    since planning has no write_scopes. A bug here cannot become a write
    because ms.write() is never called in this handler at all.
    """
    try:
        papers = ms.read("planning", "paper")
        courses = ms.read("planning", "course")
        return json.dumps({"papers": papers, "courses": courses})
    except ms.PermissionError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"})


def news_search(args: dict, **kwargs) -> str:
    """
    Real external tool call — NewsAPI.org. Requires NEWS_API_KEY in the
    Hermes .env file. Returns only titles/sources/URLs/published dates,
    never full article bodies, both to respect copyright and because the
    model should summarize in its own words rather than relay raw text.
    """
    import os
    import urllib.request
    import urllib.parse

    query = args.get("query", "").strip()
    if not query:
        return json.dumps({"error": "query is required"})

    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
        return json.dumps({
            "error": "NEWS_API_KEY not set in .env — this tool is not configured yet."
        })

    params = urllib.parse.urlencode({
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 5,
        "language": "en",
        "apiKey": api_key,
    })
    url = f"https://newsapi.org/v2/everything?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
    except Exception as e:
        return json.dumps({"error": f"News search failed: {e}"})

    if data.get("status") != "ok":
        return json.dumps({"error": data.get("message", "Unknown NewsAPI error")})

    articles = [
        {
            "title": a.get("title"),
            "source": (a.get("source") or {}).get("name"),
            "published_at": a.get("publishedAt"),
            "url": a.get("url"),
        }
        for a in data.get("articles", [])[:5]
    ]
    return json.dumps({"query": query, "articles": articles})

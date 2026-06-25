"""Tool schemas — what the LLM reads to decide when to call our tools."""

READ_PAPER = {
    "name": "faculty_read_paper",
    "description": (
        "Read one or all paper records from Faculty Co-Pilot's memory "
        "(deadlines, status, collaborators, captured ideas, methodology "
        "notes, lit summaries). Use this whenever the user asks about a "
        "research paper's status, deadline, or notes. Known paper ids: "
        "ai_influencers, brand_follower_congruence, generative_ai_art, "
        "automation_advertising. Omit paper_id to get all papers."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "Record id, e.g. 'brand_follower_congruence'. Omit for all papers.",
            },
        },
        "required": [],
    },
}

WRITE_PAPER = {
    "name": "faculty_write_paper",
    "description": (
        "Update or log new information against an existing paper record — "
        "deadline, status, collaborators, a captured idea, a methodology "
        "note, or a lit summary. Use this whenever the user asks you to "
        "log, set, or update something about one of their research papers. "
        "Only pass the fields that changed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "Record id, e.g. 'brand_follower_congruence'.",
            },
            "status": {
                "type": "string",
                "description": "One of: idea, draft, review, submitted, published.",
            },
            "next_deadline": {
                "type": "string",
                "description": "ISO date string, e.g. '2026-06-30'.",
            },
            "add_collaborator": {
                "type": "string",
                "description": "A collaborator name to add to the list.",
            },
            "add_captured_idea": {
                "type": "string",
                "description": "A new idea, finding, or note to append.",
            },
            "add_methodology_note": {
                "type": "string",
                "description": "A new methodology note to append.",
            },
            "add_lit_summary": {
                "type": "string",
                "description": "A new literature summary to append.",
            },
        },
        "required": ["paper_id"],
    },
}

READ_COURSE = {
    "name": "faculty_read_course",
    "description": (
        "Read one or all course records from Faculty Co-Pilot's memory "
        "(topics covered, lecture outlines, quiz bank, case studies). Use "
        "this whenever the user asks about a course's progress or content. "
        "Known course ids: business_analytics, decision_analysis. Omit "
        "course_id to get all courses."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "Record id, e.g. 'decision_analysis'. Omit for all courses.",
            },
        },
        "required": [],
    },
}

WRITE_COURSE = {
    "name": "faculty_write_course",
    "description": (
        "Update or log new content against an existing course record — "
        "a new lecture outline, quiz question, case study, or topic "
        "covered. Use this whenever the user asks you to save or log "
        "teaching content you've just created. Only pass the fields "
        "that changed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "Record id, e.g. 'decision_analysis'.",
            },
            "add_topic_covered": {
                "type": "string",
                "description": "A topic to add to topics_covered.",
            },
            "add_lecture_outline": {
                "type": "string",
                "description": "A new lecture outline to append.",
            },
            "add_quiz_item": {
                "type": "string",
                "description": "A new quiz question to append to the quiz bank.",
            },
            "add_case_study": {
                "type": "string",
                "description": "A new case study to append.",
            },
        },
        "required": ["course_id"],
    },
}

READ_STATUS_DIGEST = {
    "name": "faculty_status_digest",
    "description": (
        "Read a combined, READ-ONLY overview across ALL papers and "
        "courses — use this for 'what's due', 'what's my status', or "
        "weekly/daily overview requests that span both research and "
        "teaching. Returns public-view fields only (no private notes)."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

FACULTY_NEWS_SEARCH = {
    "name": "faculty_news_search",
    "description": (
        "Search recent news articles for a topic — use when the user "
        "asks for course-relevant news, industry trends, or current "
        "events tied to a teaching or research topic (e.g. 'AI in "
        "marketing news', 'recent business analytics trends'). External "
        "tool via NewsAPI.org. Returns up to 5 recent article "
        "titles/sources/URLs, not full article text."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keywords, e.g. 'business analytics trends'.",
            },
        },
        "required": ["query"],
    },
}

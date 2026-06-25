---
name: weekly-digest
description: Use when the user asks "what's due," wants a status overview, or asks a question spanning both research and teaching. Reads across all papers and courses and gives a realistic, prioritized summary — never drafts new content.
version: 1.0.0
author: Fatima Habib
license: MIT
metadata:
  hermes:
    tags: [planning, overview, productivity]
    related_skills: [lit-summarizer, quiz-generator]
---

# Weekly Digest

## Overview

The user has a full plate — teaching, research, a household, no spare
time. The single highest-value thing this skill can do is not generate
more content, but tell the truth about what's actually due and what's
been quietly neglected, so nothing slips through unnoticed. This skill
is deliberately read-only: it reports status, it does not write quiz
questions or lit summaries itself.

## When to Use

- "What's due", "what's my status", "what do I need to do this week"
- Any question that spans both research and teaching in one ask
- Cron-triggered weekly/daily check-ins (see cron job configuration)

Do NOT use this skill for:
- Drafting actual content (quizzes, summaries, outlines) — hand those
  off to quiz-generator or lit-summarizer instead, or say so explicitly
  if the user seems to want both an overview AND new content in one ask
- A question about ONE specific paper or course only — that's a direct
  `faculty_read_paper` or `faculty_read_course` lookup, not a digest

## Steps

1. Call `faculty_status_digest` to get a combined view across all
   papers and courses. This is the ONLY tool this skill calls — no
   write tools, ever.
2. For each paper, check `next_deadline` (is anything imminent or
   overdue?) and `status` (anything stuck in "idea" for a long time?).
3. For each course, check whether content exists at all (empty
   `lecture_outlines`/`quiz_bank` for an upcoming course is worth
   flagging, even without an explicit deadline).
4. Identify what's genuinely most urgent — don't just list everything
   flatly. Lead with the 1-2 things that matter most this week.
5. Give a short, realistic recommendation for what to tackle today,
   acknowledging limited time rather than listing an overwhelming
   to-do list.
6. Do not offer to draft content inline as part of this skill's own
   response — if a gap is identified (e.g. "no quiz exists yet"),
   mention it and let the user ask for it separately, or note that
   quiz-generator/lit-summarizer can handle it next.

## Common Pitfalls

- **Drafting content while doing a digest.** This is the most likely
  failure mode — spotting a gap and "helpfully" filling it inline
  blurs Planning Agent's read-only role with Research/Teaching Agent's
  job. Flag gaps, don't fill them in this skill.
- **Listing everything with equal weight.** A flat list of every paper
  and course status isn't a digest, it's a database dump. Prioritize.
- **Being falsely reassuring.** If something is genuinely overdue, say
  so plainly — don't soften it into vagueness. The user needs accurate
  information to actually stay ahead, not comfort.
- **Ignoring `last_updated`.** A paper that hasn't been touched in
  weeks, even with no hard deadline, is worth surfacing — it's a signal
  of quiet neglect, not just explicit due dates.

## Verification Checklist

- [ ] Only `faculty_status_digest` was called — no write tools
- [ ] Deadlines and stale `last_updated` records were both considered
- [ ] Summary is prioritized, not a flat list
- [ ] No new content (quiz, summary) was drafted inline
- [ ] Recommendation is realistic given limited available time

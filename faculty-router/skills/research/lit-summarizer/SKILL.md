---
name: lit-summarizer
description: Use when the user shares a paper, PDF, or article and asks for a summary, or asks to log a finding against one of their working papers. Extracts key findings and logs them against the right paper record.
version: 1.0.0
author: Fatima Habib
license: MIT
metadata:
  hermes:
    tags: [research, summarization, papers]
    related_skills: [weekly-digest]
---

# Literature Summarizer

## Overview

Academic reading is slow, and notes taken in the moment often get lost
across chat history, sticky notes, or half-remembered impressions weeks
later. This skill turns a shared paper or pasted abstract into a short,
usable summary, and — critically — logs it against the right working
paper record so it's still findable when the user comes back to write
that section of the manuscript.

This skill does not replace careful reading. It produces a fast,
structured first pass: what the paper found, how it's relevant, and
what's worth revisiting in full later.

## When to Use

- The user shares a PDF, pastes an abstract, or pastes a block of text
  from a paper and asks for a summary
- The user says something like "log this against my [paper name]" after
  sharing a finding, dataset, or idea
- The user asks "what does the literature say about X" in a way that
  implies summarizing a specific source, not a general web search

Do NOT use this skill for:
- General research questions with no specific source attached (just
  answer conversationally)
- Summarizing the user's OWN paper-in-progress (that's drafting, not
  literature review)

## Steps

1. Identify the source material in the user's message (pasted text,
   forwarded file content, or a described paper).
2. Extract 3-5 key findings in your own words — not direct quotes. Focus
   on results and claims, not methodology details (that's a separate
   concern — see Common Pitfalls).
3. Identify which of the user's known papers this is relevant to. If
   unclear, ask once rather than guessing — call `faculty_read_paper`
   (no paper_id, to list all four) if you need to check titles before
   asking.
4. Call `faculty_write_paper` with `paper_id` set and `add_lit_summary`
   containing your 3-5 point summary as a single, well-formatted string.
5. Confirm back to the user in 2-3 sentences: what you found, and which
   paper you logged it against.

## Common Pitfalls

- **Summarizing methodology instead of findings.** A user asking for a
  "summary" usually wants results and implications, not a step-by-step
  replay of the paper's methods section. If they want methodology
  specifically, they'll usually say so — ask if unsure.
- **Guessing which paper to log against.** The user has four active
  papers with different focuses (personality prediction, brand-follower
  congruence, generative AI in art, ad automation). A wrong guess means
  a lost note. When genuinely ambiguous, ask a single clarifying
  question rather than picking one.
- **Reproducing large verbatim excerpts.** Summaries should be in your
  own words. Quoting more than a short phrase risks copyright issues
  and is also less useful as a working note than a clear paraphrase.
- **Writing a summary so long it defeats the purpose.** Keep it to 3-5
  bullet-style points. If the user wants more depth, they'll ask a
  follow-up.

## Verification Checklist

- [ ] Summary is 3-5 points, in your own words, focused on findings
- [ ] Correct `paper_id` identified (asked if ambiguous, didn't guess)
- [ ] `faculty_write_paper` called with `add_lit_summary`
- [ ] User given a short confirmation naming which paper it was logged against

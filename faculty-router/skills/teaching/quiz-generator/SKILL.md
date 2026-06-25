---
name: quiz-generator
description: Use when the user asks for quiz questions, exam questions, or assessment items for Business Analytics or Decision Analysis. Writes level-appropriate questions and saves them to the course's quiz bank.
version: 1.0.0
author: Fatima Habib
license: MIT
metadata:
  hermes:
    tags: [teaching, assessment, quiz]
    related_skills: [weekly-digest]
---

# Quiz Generator

## Overview

Writing good assessment questions takes real thought — wrong answers
need to be plausible enough to test understanding, not just obviously
wrong. This skill produces quiz questions matched to the actual course
level (Business Analytics is Level 4, introductory; Decision Analysis
is Level 7, advanced), and saves them to that course's quiz bank so
they accumulate into a reusable bank rather than being regenerated from
scratch every time.

## When to Use

- The user asks for quiz, exam, or assessment questions on a topic
- The user asks for "a few questions" or "test questions" tied to
  Business Analytics or Decision Analysis
- The user asks to vary or extend an existing quiz topic

Do NOT use this skill for:
- General explanations of a concept (just answer directly)
- Case studies or classroom activities (those are a different, more
  open-ended teaching skill — not covered here)

## Steps

1. Identify the course (`business_analytics` or `decision_analysis`)
   and the topic. If the user doesn't specify a course but the topic
   clearly belongs to one (e.g. "decision trees" → Decision Analysis),
   infer it — don't make the user repeat information already implied.
2. Match question difficulty to the course level:
   - Level 4 (Business Analytics): foundational concepts, single-step
     reasoning, clear right/wrong answers.
   - Level 7 (Decision Analysis): multi-step reasoning, realistic
     business scenarios, may include short calculations.
3. Write a mix of question types unless the user asks for one
   specifically — multiple choice for concept checks, short calculation
   for quantitative topics. 3-5 questions is a good default unless
   asked for more.
4. For each question, include the correct answer and a one-line
   rationale — this matters for the user's own later reference, not
   just for students.
5. Call `faculty_write_course` with `course_id` and `add_quiz_item` for
   each question (call once per question, or pass a combined string if
   the tool only accepts one addition per call — check current schema).
6. Confirm back to the user with a short summary of what was added and
   to which course.

## Common Pitfalls

- **Mismatching difficulty to level.** A Level 7 question that's really
  a Level 4 recall question wastes the advanced students' time, and the
  reverse confuses introductory students. Re-check the level before
  finalizing.
- **Implausible wrong answers.** A multiple-choice question where three
  options are obviously silly isn't testing anything — wrong answers
  should reflect common misconceptions or near-miss reasoning.
- **Forgetting to save.** Generating good questions in chat without
  calling `faculty_write_course` means they're lost the moment the
  conversation moves on. Always save unless the user explicitly says
  "just show me, don't save yet."
- **Overloading one message with too many questions.** If the user
  wants a full exam (10+ questions), confirm scope first rather than
  generating an overwhelming wall of text.

## Verification Checklist

- [ ] Correct course identified (asked or correctly inferred)
- [ ] Difficulty matches the course level
- [ ] Each question has a correct answer and brief rationale
- [ ] `faculty_write_course` called to persist the questions
- [ ] User given a short confirmation of what was saved

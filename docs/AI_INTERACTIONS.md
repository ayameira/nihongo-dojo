# AI Interactions Reference

This document provides a detailed reference of all AI interactions in Nihongo Dojo for debugging and improvement.

---

## Table of Contents

1. [System Prompt](#1-system-prompt)
2. [Memory Injections](#2-memory-injections)
3. [Tool Definitions](#3-tool-definitions)
4. [Tool Loop Mechanism](#4-tool-loop-mechanism)
5. [Request/Response Logging](#5-requestresponse-logging)
6. [File Reference](#6-file-reference)

---

## 1. System Prompt

**File:** `backend/app/core/context_builder.py:8-47`

The system prompt is a template with dynamic injections. Here is the complete template:

```
Current Date: {today}

You are a Japanese language tutor for an intermediate learner studying through immersion.

## Core Principles
- Default to responding in Japanese
- Push the student to the edge of their ability (i+1 hypothesis)
- Only switch to English for explicit grammar explanations, then immediately provide Japanese examples
- Use vocabulary the student is currently learning when possible
- Be a warm, personable tutor who remembers and cares about the student as a person

## About This Student
{student_record_content}

## Current Study Focus (Recent Memory)
{class_notes_content}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually

## Tool Usage
- Use update_notes when you notice patterns in current learning worth remembering
- Use update_student_record when you learn something important about the student (goals, interests, background, preferences, or anything that helps you be a better tutor for them)

## Important: Keep Notes Updated
ALWAYS record new learnings in the class notes using update_notes. This includes:
- New grammar points introduced or practiced
- Expressions and phrases taught
- Vocabulary themes explored (e.g., "studied medical terms", "practiced food vocabulary")
- Patterns in mistakes or areas needing work
- Any significant teaching moments

Record the broader learning context and themes, not individual words.

When the class notes get too long or topics become stale, clean them up. Before removing anything, ask yourself: "Is this worth remembering long-term?" If yes, move it to the student record (e.g., "student has solid grasp of て-form", "struggles with keigo"). If it's no longer relevant, you can remove it.
```

### Injection Points

| Variable | Source | Description |
|----------|--------|-------------|
| `{today}` | `date.today().isoformat()` | Current date in ISO format (e.g., "2024-01-15") |
| `{student_record_content}` | `STUDENT_RECORD.md` file | Long-term memory about the student |
| `{class_notes_content}` | `CLASS_NOTES.md` file | Current learning focus and recent patterns |
| `{vocab_list_formatted}` | SQLite database | All vocabulary with status="Learning" |

### System Prompt Injection Logic

**File:** `backend/app/core/gemini_client.py:78-85`

```python
# Include system prompt only if no history (first message of session)
if system_prompt and not context.get("chat_history"):
    parts.append(f"[System Instructions]\n{system_prompt}\n[End System Instructions]\n\n")
```

**Important:** The system prompt is only injected on the **first message** of a chat session (when there's no history). On subsequent messages, the chat history carries the context forward.

---

## 2. Memory Injections

### 2.1 Student Record (Long-term Memory)

**Source File:** `STUDENT_RECORD.md` (configurable via `student_record_path`)

**Loaded at:** `backend/app/core/context_builder.py:59`

**Sections:**
- `## Goals` - Language learning goals and aspirations
- `## Background` - Why they're learning, their situation
- `## Interests` - Hobbies, topics they enjoy
- `## Preferences` - Learning style preferences
- `## Notes` - Other important information

**Default Template:**
```markdown
# Student Record

## Goals
<!-- The student's language learning goals and aspirations -->

## Background
<!-- Context about the student - why they're learning, their situation -->

## Interests
<!-- Hobbies, topics they enjoy discussing, favorite things -->

## Preferences
<!-- Learning style preferences, what works well for them -->

## Notes
<!-- Other important information about the student -->
```

### 2.2 Class Notes (Short-term Memory)

**Source File:** `CLASS_NOTES.md` (configurable via `class_notes_path`)

**Loaded at:** `backend/app/core/context_builder.py:62`

**Sections:**
- `## Current Focus` - Grammar points or themes currently being studied
- `## Recent Corrections` - Patterns of mistakes
- `## Recent Vocab` - Vocabulary themes recently taught

**Default Template:**
```markdown
# Japanese Study Notes

## Current Focus
<!-- What grammar points or vocabulary themes are we currently working on -->

## Recent Corrections
<!-- Patterns of mistakes the student makes -->

## Recent Vocab
<!-- Words recently taught in conversation -->
```

### 2.3 Vocabulary List

**Source:** SQLite database, `vocab_entries` table

**Query:** `backend/app/core/context_builder.py:93-119`

```python
stmt = (
    select(VocabEntry)
    .where(VocabEntry.status == "Learning")
    .order_by(VocabEntry.updated_at.desc())
)
```

**Filter:** Only entries with `status == "Learning"` (no limit)

**Format:** `backend/app/core/context_builder.py:122-134`
```
- 食べる (たべる): to eat [verb]
- 元気 (げんき): healthy, energetic [na-adj]
- すごい: amazing [i-adj]
```

### 2.4 Chat History

**Source:** SQLite database, `chat_history` table

**Query:** `backend/app/core/context_builder.py:137-164`

```python
stmt = (
    select(ChatMessage)
    .where(ChatMessage.session_id == session_id)
    .order_by(ChatMessage.created_at.desc())
    .limit(30)  # Last 30 messages
)
```

**Limit:** 30 messages per session

**Format:** Converted to Gemini format:
```python
{
    "role": "user" | "model",  # "assistant" becomes "model"
    "parts": [message_content]
}
```

**Injection:** Passed to `model.start_chat(history=chat_history)` at `gemini_client.py:74-76`

---

## 3. Tool Definitions

**File:** `backend/app/core/tools.py`

### 3.1 update_notes

**Definition:** Lines 7-30

**Purpose:** Update short-term memory (CLASS_NOTES.md)

**Description sent to model:**
> "Update a section of the student's study notes based on the conversation."

**Parameters:**

| Name | Type | Required | Values | Description |
|------|------|----------|--------|-------------|
| `section` | string | Yes | `current_focus`, `recent_corrections`, `recent_vocab` | Which section to update |
| `action` | string | Yes | `append`, `replace` | Whether to append to or replace content |
| `content` | string | Yes | (any) | Markdown content to add or replace |

**Execution:** `backend/app/core/tools.py:76-95`

Calls `NotesService.update_section()` which modifies `CLASS_NOTES.md`

### 3.2 update_student_record

**Definition:** Lines 32-55

**Purpose:** Update long-term memory (STUDENT_RECORD.md)

**Description sent to model:**
> "Update the student's long-term record with important information about them. Use this to remember things that help you be a better tutor: their goals, interests, background, learning preferences, personal details they share, or anything else worth remembering about them as a person."

**Parameters:**

| Name | Type | Required | Values | Description |
|------|------|----------|--------|-------------|
| `section` | string | Yes | `goals`, `background`, `interests`, `preferences`, `notes` | Which section to update |
| `action` | string | Yes | `append`, `replace` | Whether to append to or replace content |
| `content` | string | Yes | (any) | Markdown content to add or replace |

**Execution:** `backend/app/core/tools.py:98-117`

Calls `NotesService.update_student_record_section()` which modifies `STUDENT_RECORD.md`

### Tool Registration

**File:** `backend/app/core/tools.py:57`

```python
ALL_TOOLS = [UPDATE_NOTES_TOOL, UPDATE_STUDENT_RECORD_TOOL]
```

**Conversion to Gemini format:** `backend/app/core/gemini_client.py:25-45`

---

## 4. Tool Loop Mechanism

**File:** `backend/app/core/gemini_client.py:59-196`

The agent uses a **tool loop** that allows it to execute tools and then continue generating a response.

### Flow Diagram

```
User sends message
        │
        ▼
┌─────────────────────────────────────┐
│  Build message parts                │
│  (system prompt + user message)     │
│                                     │
│  File: gemini_client.py:81-97       │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  Send to Gemini                     │
│  chat.send_message(parts)           │
│                                     │
│  File: gemini_client.py:109-111     │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  Parse response                     │
│  - Extract function_calls           │
│  - Extract text_parts               │
│                                     │
│  File: gemini_client.py:126-131     │
└─────────────────────────────────────┘
        │
        ▼
    Has function calls?
       /          \
      YES          NO
       │            │
       ▼            ▼
┌──────────────┐  ┌──────────────────┐
│ Execute each │  │ Yield text parts │
│ tool call    │  │ and exit loop    │
│              │  │                  │
│ Lines 137-163│  │ Lines 170-176    │
└──────────────┘  └──────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Send function responses back       │
│  to Gemini                          │
│                                     │
│  parts = function_responses         │
│  continue  # loop again             │
│                                     │
│  File: gemini_client.py:165-168     │
└─────────────────────────────────────┘
       │
       └──────► (back to Send to Gemini)
```

### Safety Limit

**File:** `gemini_client.py:101`

```python
max_tool_iterations = 10  # Safety limit
```

The loop will exit after 10 iterations to prevent infinite loops.

### Events Yielded to Frontend

| Event Type | When | Data |
|------------|------|------|
| `tool_call` | Agent requests a tool | `{type, name, args}` |
| `tool_result` | Tool executed | `{type, name, result}` |
| `text` | Final response text | `{type, content}` |
| `usage` | After completion | `{type, input_tokens, output_tokens, cost_usd}` |
| `error` | On exception | `{type, content}` |

---

## 5. Request/Response Logging

**File:** `backend/app/services/request_logger.py`

Every AI interaction is logged to disk for debugging.

### Log Location

```
logs/ai_interactions/
└── {YYYY-MM-DD}/
    └── {session_id}/
        └── {HH-MM-SS-ffffff}.json
```

### Log Structure

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "session_id": "abc-123",
  "model": "gemini-2.0-flash",

  "request": {
    "user_message": "こんにちは！",
    "has_image": false,
    "image_data": null,
    "difficulty_feedback": null
  },

  "context": {
    "system_prompt": "Current Date: 2024-01-15\n\nYou are a Japanese...",
    "chat_history": [
      {"role": "user", "parts": ["Previous message"]},
      {"role": "model", "parts": ["Previous response"]}
    ],
    "chat_history_count": 30,
    "files": {
      "class_notes": "# Japanese Study Notes\n\n## Current Focus...",
      "student_record": "# Student Record\n\n## Goals..."
    },
    "vocabulary": {
      "items": [
        {"kanji": "食べる", "kana": "たべる", "meaning": "to eat", "pos": "verb"}
      ],
      "count": 42
    }
  },

  "response": {
    "content": "こんにちは！元気ですか？",
    "tool_calls": [
      {
        "type": "tool_call",
        "name": "update_notes",
        "args": {"section": "current_focus", "action": "append", "content": "..."}
      }
    ],
    "tool_calls_count": 1
  },

  "usage": {
    "input_tokens": 1234,
    "output_tokens": 56,
    "cost_usd": 0.00012
  },

  "error": null
}
```

### What to Check When Debugging

| Issue | Check in Log |
|-------|--------------|
| Agent not remembering context | `context.system_prompt` - is student record/class notes populated? |
| Agent not using vocabulary | `context.vocabulary.items` - are words present? |
| Agent not responding after tool use | `response.tool_calls` vs `response.content` |
| Wrong behavior | `context.system_prompt` - check instructions |
| Missing history | `context.chat_history_count` - should be up to 30 |

---

## 6. File Reference

### Core AI Files

| File | Purpose | Key Functions/Variables |
|------|---------|------------------------|
| `backend/app/core/context_builder.py` | Builds system prompt and context | `SYSTEM_PROMPT_TEMPLATE`, `build_context()` |
| `backend/app/core/gemini_client.py` | Gemini API client with tool loop | `GeminiClient`, `stream_chat()` |
| `backend/app/core/tools.py` | Tool definitions and execution | `ALL_TOOLS`, `execute_tool_call()` |
| `backend/app/api/chat.py` | HTTP endpoint, orchestration | `generate_stream()` |
| `backend/app/services/notes_service.py` | File-based notes management | `NotesService` |
| `backend/app/services/request_logger.py` | Interaction logging | `RequestLogger` |

### Memory Files

| File | Purpose | Updated By |
|------|---------|------------|
| `STUDENT_RECORD.md` | Long-term student info | `update_student_record` tool |
| `CLASS_NOTES.md` | Current learning focus | `update_notes` tool |

### Configuration

| Setting | File | Default |
|---------|------|---------|
| `class_notes_path` | `backend/app/config.py:15` | `./CLASS_NOTES.md` |
| `student_record_path` | `backend/app/config.py:16` | `./STUDENT_RECORD.md` |
| `ai_logs_path` | `backend/app/config.py:18` | `./logs/ai_interactions` |
| `gemini_model` | `backend/app/config.py:12` | `gemini-2.0-flash` |

---

## Quick Debugging Checklist

1. **Check the logs:** `logs/ai_interactions/{date}/{session}/`
2. **Verify system prompt:** Is it being injected? (only on first message)
3. **Check memory files:** Are `CLASS_NOTES.md` and `STUDENT_RECORD.md` being updated?
4. **Tool execution:** Are tools being called? Check `tool_calls` in logs
5. **Tool loop:** Is the agent responding after tool use? Check for `text` content after `tool_result`
6. **Token usage:** Are costs reasonable? Check `usage` in logs

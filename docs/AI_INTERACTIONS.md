# AI Interactions Reference

This document provides a detailed reference of all AI interactions in Nihongo Dojo for debugging and improvement.

---

## Table of Contents

1. [System Prompt](#1-system-prompt)
2. [Memory Injections](#2-memory-injections)
3. [Tool Definitions](#3-tool-definitions)
4. [Tool Loop Mechanism](#4-tool-loop-mechanism)
5. [Background Memory Compaction](#5-background-memory-compaction)
6. [Request/Response Logging](#6-requestresponse-logging)
7. [File Reference](#7-file-reference)

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

## Conversation Summary (This Session)
{session_summary}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually

## Tool Usage
Use update_student_record when you learn something important about the student (goals, interests, background, preferences, or anything that helps you be a better tutor for them)
```

### Injection Points

| Variable | Source | Description |
|----------|--------|-------------|
| `{today}` | `date.today().isoformat()` | Current date in ISO format (e.g., "2024-01-15") |
| `{student_record_content}` | `STUDENT_RECORD.md` file | Long-term memory about the student |
| `{session_summary}` | `chat_sessions.summary` column | Compacted summary of archived messages from this session |
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

### 2.2 Vocabulary List

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

### 2.3 Chat History

**Source:** SQLite database, `chat_history` table

**Query:** `backend/app/core/context_builder.py`

```python
stmt = (
    select(ChatMessage)
    .where(ChatMessage.session_id == session_id)
    .where(ChatMessage.is_archived == False)  # Exclude compacted messages
    .order_by(ChatMessage.created_at.desc())
    .limit(30)  # Last 30 non-archived messages
)
```

**Limit:** 30 non-archived messages per session

**Archived Messages:** When a session exceeds 30 messages, the oldest 10 are compacted into a summary and marked as `is_archived=True`. These archived messages are excluded from the chat history but their content is preserved in the session summary (see [Background Memory Compaction](#5-background-memory-compaction)).

**Format:** Converted to Gemini format:
```python
{
    "role": "user" | "model",  # "assistant" becomes "model"
    "parts": [message_content]
}
```

**Injection:** Passed to `model.start_chat(history=chat_history)` at `gemini_client.py:74-76`

### 2.4 Session Summary (Compacted History)

**Source:** SQLite database, `chat_sessions.summary` column

**Query:** `backend/app/core/context_builder.py`

```python
stmt = select(ChatSession.summary).where(ChatSession.id == session_id)
```

**Purpose:** When messages are compacted, a summary of the archived conversation is stored here. This allows the tutor to maintain context of the entire session even after older messages are removed from active history.

**Default:** `"(No previous conversation in this session)"` when no compaction has occurred yet.

---

## 3. Tool Definitions

**File:** `backend/app/core/tools.py`

### 3.1 update_student_record

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

**File:** `backend/app/core/tools.py`

```python
ALL_TOOLS = [UPDATE_STUDENT_RECORD_TOOL]
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

## 5. Background Memory Compaction

**File:** `backend/app/services/memory_service.py`

The memory compaction system automatically summarizes old messages to prevent context window overflow while preserving conversation continuity.

### Overview

When a chat session accumulates 30+ active (non-archived) messages, the system:
1. Selects the oldest 10 non-archived messages
2. Sends them to Gemini with a summarization prompt
3. Generates a session summary (stored in `chat_sessions.summary`)
4. Extracts any new student facts (appended to `STUDENT_RECORD.md`)
5. Marks the 10 messages as `is_archived=True`

### Trigger Mechanism

**File:** `backend/app/api/chat.py`

Compaction runs as a **FastAPI BackgroundTask** after each chat response:

```python
await session.commit()

# Schedule memory compaction check as background task (non-blocking)
background_tasks.add_task(run_compaction_if_needed, request.session_id)
```

This ensures compaction never blocks the user's chat experience.

### Compaction Prompt

**File:** `backend/app/services/memory_service.py`

The compaction AI receives a specialized prompt (different from the tutor prompt):

```
You are the Memory Manager for Nihongo Dojo.

I will provide you with:
1. A 'Current Conversation Summary' (may be empty if first compaction)
2. A 'Recent Chunk' of 10 messages

## Task 1: Recursive Summarization
Update the summary to include key events from the chunk. Be concise but specific.
Example: "User practiced Te-form verbs (tabete, nonde). Discussed travel to Tokyo."

## Task 2: Fact Extraction
Did the user reveal NEW permanent info (biography, goals, interests, dislikes)?
If yes, extract it. If no, return null.

## Output (JSON only)
{"new_summary": "...", "new_student_facts": "..." or null}
```

### Dual Output Channels

| Channel | Destination | Purpose |
|---------|-------------|---------|
| **Session Summary** | `chat_sessions.summary` column | Preserves conversation context within the session |
| **Student Facts** | `STUDENT_RECORD.md` (Notes section) | Extracts permanent info to long-term memory |

### Database Schema

**ChatMessage** (updated):
```python
is_archived = Column(Boolean, default=False, index=True)
```

**ChatSession** (updated):
```python
summary = Column(Text, nullable=True)
```

### Flow Diagram

```
User sends message #31
         │
         ▼
┌─────────────────────────┐
│ Chat response generated │
│ and committed to DB     │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ BackgroundTask starts   │
│ run_compaction_if_needed│
└─────────────────────────┘
         │
         ▼
    Active msgs >= 30?
       /          \
      NO           YES
       │            │
       ▼            ▼
   (exit)    ┌──────────────────┐
             │ Get oldest 10    │
             │ non-archived msgs│
             └──────────────────┘
                     │
                     ▼
             ┌──────────────────┐
             │ Call Gemini with │
             │ compaction prompt│
             └──────────────────┘
                     │
                     ▼
             ┌──────────────────┐
             │ Save summary to  │
             │ ChatSession      │
             └──────────────────┘
                     │
                     ▼
             ┌──────────────────┐
             │ If facts found,  │
             │ update STUDENT_  │
             │ RECORD.md        │
             └──────────────────┘
                     │
                     ▼
             ┌──────────────────┐
             │ Mark 10 msgs as  │
             │ is_archived=True │
             └──────────────────┘
```

### Error Handling

| Failure Point | Behavior |
|---------------|----------|
| Gemini API error | Log error, do NOT archive messages (retry on next trigger) |
| Database save error | Log error, rollback, do NOT archive |
| Notes service error | Log error, but still save summary (partial success) |

Messages are only marked as archived **after** the summary is successfully saved, ensuring no data loss.

### Key Functions

| Function | Purpose |
|----------|---------|
| `MemoryService.should_compact(session_id)` | Check if 30+ active messages |
| `MemoryService.run_compaction(session_id)` | Execute full compaction flow |
| `run_compaction_if_needed(session_id)` | Background task entry point |
| `GeminiClient.generate_json(prompt)` | Non-streaming JSON response for compaction |

---

## 6. Request/Response Logging

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
        "name": "update_student_record",
        "args": {"section": "notes", "action": "append", "content": "..."}
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
| Agent not remembering context | `context.system_prompt` - is student record populated? |
| Agent not using vocabulary | `context.vocabulary.items` - are words present? |
| Agent not responding after tool use | `response.tool_calls` vs `response.content` |
| Wrong behavior | `context.system_prompt` - check instructions |
| Missing history | `context.chat_history_count` - should be up to 30 |

---

## 7. File Reference

### Core AI Files

| File | Purpose | Key Functions/Variables |
|------|---------|------------------------|
| `backend/app/core/context_builder.py` | Builds system prompt and context | `SYSTEM_PROMPT_TEMPLATE`, `build_context()`, `get_session_summary()` |
| `backend/app/core/gemini_client.py` | Gemini API client with tool loop | `GeminiClient`, `stream_chat()`, `generate_json()` |
| `backend/app/core/tools.py` | Tool definitions and execution | `ALL_TOOLS`, `execute_tool_call()` |
| `backend/app/api/chat.py` | HTTP endpoint, orchestration | `generate_stream()`, BackgroundTasks integration |
| `backend/app/services/notes_service.py` | File-based notes management | `NotesService` |
| `backend/app/services/memory_service.py` | Background memory compaction | `MemoryService`, `run_compaction_if_needed()` |
| `backend/app/services/request_logger.py` | Interaction logging | `RequestLogger` |

### Memory Files

| File | Purpose | Updated By |
|------|---------|------------|
| `STUDENT_RECORD.md` | Long-term student info | `update_student_record` tool, memory compaction |

### Configuration

| Setting | File | Default |
|---------|------|---------|
| `student_record_path` | `backend/app/config.py` | `./STUDENT_RECORD.md` |
| `ai_logs_path` | `backend/app/config.py` | `./logs/ai_interactions` |
| `gemini_model` | `backend/app/config.py` | `gemini-2.0-flash` |

---

## Quick Debugging Checklist

1. **Check the logs:** `logs/ai_interactions/{date}/{session}/`
2. **Verify system prompt:** Is it being injected? (only on first message)
3. **Check memory file:** Is `STUDENT_RECORD.md` being updated?
4. **Tool execution:** Are tools being called? Check `tool_calls` in logs
5. **Tool loop:** Is the agent responding after tool use? Check for `text` content after `tool_result`
6. **Token usage:** Are costs reasonable? Check `usage` in logs
7. **Memory compaction:** Check database for archived messages and session summaries:
   ```sql
   -- Check archived message count
   SELECT is_archived, COUNT(*) FROM chat_history GROUP BY is_archived;

   -- Check session summary
   SELECT id, summary FROM chat_sessions WHERE id = 'your-session-id';
   ```
8. **Compaction not triggering?** Verify active message count >= 30:
   ```sql
   SELECT COUNT(*) FROM chat_history
   WHERE session_id = 'your-session-id' AND is_archived = FALSE;
   ```

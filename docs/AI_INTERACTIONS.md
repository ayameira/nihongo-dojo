# AI Interactions Reference

This document provides a detailed reference of all AI interactions in Nihongo Dojo for debugging and improvement.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [System Prompt](#2-system-prompt)
3. [Memory Injections](#3-memory-injections)
4. [Tool Definitions](#4-tool-definitions)
5. [Tool Loop Mechanism](#5-tool-loop-mechanism)
6. [Background Memory Compaction](#6-background-memory-compaction)
7. [Request/Response Logging](#7-requestresponse-logging)
8. [File Reference](#8-file-reference)

---

## 1. Architecture Overview

Nihongo Dojo is provider-neutral: `backend/app/core/llm_client.py` dispatches to Groq (the default), Gemini, OpenRouter, or any OpenAI-compatible endpoint. The Gemini path is described in detail below; the OpenAI-compatible path lives in `openai_compatible_client.py` and follows the same flow.

On top of whichever provider is configured, the app uses a **two-agent architecture**:

1. **Tutor Agent** - Synchronous, SSE streaming, focused purely on teaching (NO tools)
2. **Listener Agent** - Background task, extracts student facts from messages (uses tools)

This separation allows the Tutor to focus 100% on high-quality teaching while the Listener handles fact management in the background without blocking the user experience.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       NIHONGO DOJO - TWO-AGENT ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────────────┘

User Message ──► POST /api/chat/stream
                        │
                        ▼
              ┌─────────────────────────────────────────────────────────────────┐
              │                     CHAT ENDPOINT (chat.py)                      │
              └─────────────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼ (Background Task)
┌───────────────────────┐     ┌───────────────────────────────────────────────┐
│    TUTOR AGENT        │     │              LISTENER AGENT                    │
│  (Synchronous SSE)    │     │            (Background Task)                   │
├───────────────────────┤     ├───────────────────────────────────────────────┤
│                       │     │                                               │
│ Context:              │     │ Context (minimal):                            │
│ • Student facts       │     │ • Student facts (with IDs)                    │
│ • Session summary     │     │ • Tutor's response                            │
│ • Vocab (Learning)    │     │ • User's message                              │
│ • Chat history (30)   │     │                                               │
│                       │     │ Tool: manage_student_facts                    │
│ NO TOOLS              │     │ • add / edit / delete facts                   │
│ Pure teaching focus   │     │                                               │
│                       │     │ Non-streaming, logs results                   │
├───────────────────────┤     ├───────────────────────────────────────────────┤
│ Output Events:        │     │ Updates:                                      │
│ • text                │     │ • student_facts DB (source="listener")        │
│ • usage               │     │                                               │
│ • done                │     │ Facts ready for next conversation turn        │
└───────────────────────┘     └───────────────────────────────────────────────┘
        │
        ▼
   SSE Stream to Frontend
```

### Why Two Agents?

| Benefit | Description |
|---------|-------------|
| **Faster responses** | Tutor doesn't wait for tool execution |
| **Better teaching** | Tutor prompt is 100% focused on pedagogy, no tool instructions |
| **Lower latency** | User sees response immediately, facts updated in background |
| **Pronoun resolution** | Listener sees both tutor question and user answer to understand "it", "that", etc. |

---

## 2. System Prompts

The system uses **two separate prompts** for the Tutor and Listener agents.

**Files:** `backend/app/core/agents.py`

### 2.1 Tutor System Prompt

The Tutor prompt focuses purely on teaching with **NO tool instructions**:

```
Current Date: {today}

You are a Japanese language tutor.

## Core Principles
- Push the student to the edge of their ability (i+1 hypothesis)
- Use vocabulary the student is currently learning when possible
- Repetition is key for learning: use the same vocabulary and grammatical
  constructions that the user is currently learning or has been struggling with.
  However, always use it in new phrases and contexts.
- Be a warm, personable tutor who remembers and cares about the student as a person

## About This Student
{student_facts_formatted}

## Conversation Summary (This Session)
{session_summary}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually
```

**Note:** The Tutor prompt has NO tool usage section - all fact management is handled by the Listener.

### 2.2 Listener System Prompt

The Listener prompt is minimal and focused on fact extraction:

```
You are a silent observer for a Japanese tutoring application.
Your ONLY job is to extract and manage facts about the student based on their conversation.

## Current Student Facts (with IDs for reference)
{student_facts_formatted}

## Conversation Exchange
Tutor: {tutor_message}
Student: {user_message}

## Task
Analyze the student's message in context of the tutor's question. If needed:
- add: New permanent info about the student (goals, interests, background, preferences)
- edit: Update an existing fact if new information contradicts or refines it (provide fact_id)
- delete: Remove a fact that is no longer accurate (provide fact_id)

If NO fact changes are needed, do not call the tool.

## Important Rules
- Only extract PERMANENT facts about the student as a person
- Do NOT record transient conversation topics or grammar points (handled by compaction)
- Use the Tutor's question to understand pronouns like "it", "that", "this" in the response
```

**Key difference:** The Listener receives both the tutor's message AND the user's message to resolve pronouns (e.g., "Do you like natto?" + "No, I hate it" → "User hates natto").

### Injection Points

**Tutor Agent Variables:**

| Variable | Source | Description |
|----------|--------|-------------|
| `{today}` | `date.today().isoformat()` | Current date in ISO format |
| `{student_facts_formatted}` | `student_facts` table | Long-term memory: `- [1] fact...` |
| `{session_summary}` | `chat_sessions.summary` | Compacted summary from this session |
| `{vocab_list_formatted}` | SQLite database | All vocabulary with status="Learning" |

**Listener Agent Variables:**

| Variable | Source | Description |
|----------|--------|-------------|
| `{student_facts_formatted}` | `student_facts` table | Facts with IDs for edit/delete |
| `{tutor_message}` | Previous Tutor response | For pronoun resolution |
| `{user_message}` | Current user message | The message being analyzed |

### Context Building

**Files:** `backend/app/core/context_builder.py`

```python
# Tutor context - full teaching context
async def build_tutor_context(session_id, difficulty_feedback) -> Dict:
    # Returns: system_prompt, chat_history, _raw (for logging)

# Listener context - minimal for fact extraction
async def build_listener_context(user_message, tutor_message) -> Dict:
    # Returns: system_prompt, user_message
```

---

## 3. Memory Injections

### Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MEMORY MANAGEMENT                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────────────┐      Long-term memory about the student              │
│   │   StudentFact       │      (flat list of facts with IDs)                   │
│   │  (student_facts)    │                                                      │
│   ├─────────────────────┤                                                      │
│   │ id (PK)             │      Example in prompt:                              │
│   │ content             │      - [1] Learning Japanese for travel              │
│   │ source              │      - [2] Likes anime, especially Naruto            │
│   │ created_at          │      - [3] Works as a software engineer              │
│   │ updated_at          │                                                      │
│   └─────────────────────┘                                                      │
│                                                                                 │
│   ┌─────────────────────┐      ┌─────────────────────┐                         │
│   │    ChatSession      │      │    ChatMessage      │                         │
│   │  (chat_sessions)    │      │   (chat_history)    │                         │
│   ├─────────────────────┤      ├─────────────────────┤                         │
│   │ id (PK)             │◄────┐│ id (PK)             │                         │
│   │ name                │     ││ session_id (FK)  ───┘                         │
│   │ summary             │     ││ role (user/assistant)                         │
│   │ preview             │     ││ content             │                         │
│   │ message_count       │     ││ image_data (base64) │                         │
│   │ created_at          │     ││ is_archived         │                         │
│   │ updated_at          │     ││ token_count         │                         │
│   └─────────────────────┘     ││ created_at          │                         │
│                               │└─────────────────────┘                         │
│                               │                                                │
│   Context Window:             │   ┌─────────────────────┐                      │
│   • Last 30 non-archived msgs │   │    VocabEntry       │                      │
│   • System prompt on first msg│   │  (vocab_entries)    │                      │
│   • ALL Learning vocab        │   ├─────────────────────┤                      │
│   • Session summary           │   │ kanji, kana         │                      │
│   • ALL student facts         │   │ meaning, pos        │                      │
│                               │   │ status="Learning"   │                      │
│                               │   └─────────────────────┘                      │
│                               │   ALL Learning vocab in context                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Student Facts (Long-term Memory)

**Source:** SQLite database, `student_facts` table

**Loaded at:** `backend/app/core/context_builder.py:129-142`

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer (PK) | Unique identifier shown to AI as `[id]` |
| `content` | Text | The fact text |
| `source` | String | `tutor`, `compaction`, or `manual` |

**Format in prompt:**
```
- [1] Learning Japanese for travel to Tokyo
- [2] Likes anime, especially Naruto (favorite character: Kakashi)
- [3] Works as a software engineer
- [4] Prefers conversational practice over textbook exercises
```

The IDs in brackets allow the AI to reference specific facts when editing or deleting.

**See also:** [Student Facts Logic](./STUDENT_FACTS_LOGIC.md) for full details.

### 3.2 Vocabulary List

**Source:** SQLite database, `vocab_entries` table

**Query:** `backend/app/core/context_builder.py:85-111`

```python
stmt = (
    select(VocabEntry)
    .where(VocabEntry.status == "Learning")
    .order_by(VocabEntry.updated_at.desc())
)
```

**Filter:** Only entries with `status == "Learning"` (no limit)

**Format:** `backend/app/core/context_builder.py:114-126`
```
- 食べる (たべる): to eat [verb]
- 元気 (げんき): healthy, energetic [na-adj]
- すごい: amazing [i-adj]
```

### 3.3 Chat History

**Source:** SQLite database, `chat_history` table

**Query:** `backend/app/core/context_builder.py:144-172`

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

**Archived Messages:** When a session exceeds 30 messages, the oldest 10 are compacted into a summary and marked as `is_archived=True`. These archived messages are excluded from the chat history but their content is preserved in the session summary (see [Background Memory Compaction](#6-background-memory-compaction)).

**Format:** Converted to Gemini format:
```python
{
    "role": "user" | "model",  # "assistant" becomes "model"
    "parts": [message_content]
}
```

**Injection:** Passed to `model.start_chat(history=chat_history)` at `gemini_client.py:74-76`

### 3.4 Session Summary (Compacted History)

**Source:** SQLite database, `chat_sessions.summary` column

**Query:** `backend/app/core/context_builder.py:129-141`

```python
stmt = select(ChatSession.summary).where(ChatSession.id == session_id)
```

**Purpose:** When messages are compacted, a summary of the archived conversation is stored here. This allows the tutor to maintain context of the entire session even after older messages are removed from active history.

**Default:** `"(No previous conversation in this session)"` when no compaction has occurred yet.

---

## 4. Tool Definitions

**File:** `backend/app/core/tools.py`

### 4.1 manage_student_facts

**Definition:** Lines 7-29

**Purpose:** Manage long-term memory (student_facts table)

**Description sent to model:**
> "Manage long-term facts about the student. Use this to remember important information that helps you be a better tutor: their goals, interests, background, learning preferences, personal details, or progress observations. Facts are stored permanently across sessions."

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `action` | string | Yes | `add`, `edit`, or `delete` |
| `content` | string | For add/edit | The fact text (new or updated) |
| `fact_id` | integer | For edit/delete | The ID of the fact to modify |

**Example tool calls:**

```json
// Add a new fact
{"action": "add", "content": "Enjoys discussing travel experiences"}

// Edit existing fact
{"action": "edit", "fact_id": 2, "content": "Loves anime, especially Naruto and One Piece"}

// Delete a fact
{"action": "delete", "fact_id": 3}
```

**Execution:** `backend/app/core/tools.py:34-109`

Directly queries/modifies the `student_facts` SQLite table.

### Tool Registration

**File:** `backend/app/core/tools.py`

```python
ALL_TOOLS = [MANAGE_STUDENT_FACTS_TOOL]
```

**Conversion to Gemini format:** `backend/app/core/gemini_client.py:25-45`

**See also:** [Student Facts Logic](./STUDENT_FACTS_LOGIC.md) for full tool documentation.

---

## 5. Tool Loop Mechanism

**File:** `backend/app/core/gemini_client.py`

Tools are now **only used by the Listener agent** (background). The Tutor agent has no tools.

### Tutor Agent (No Tools)

The Tutor uses `stream_chat()` with `use_tools=False`:

```python
async for chunk in client.stream_chat(
    context, parts,
    tool_executor=None,
    use_tools=False,  # Tutor has no tools
):
    # Only yields: text, usage
```

**Events to Frontend:**

| Event Type | Data |
|------------|------|
| `text` | `{type, content}` |
| `usage` | `{type, input_tokens, output_tokens, cost_usd}` |
| `done` | `{type}` |

### Listener Agent (Tool Loop)

The Listener uses `generate_with_tools()` for non-streaming generation with tool loop:

```
Listener receives (user_message, tutor_message)
        │
        ▼
┌─────────────────────────────────────┐
│  Build Listener context             │
│  (facts, tutor msg, user msg)       │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  Send to Gemini                     │
│  chat.send_message(parts)           │
└─────────────────────────────────────┘
        │
        ▼
    Has function calls?
       /          \
      YES          NO
       │            │
       ▼            ▼
┌──────────────┐  ┌──────────────────┐
│ Execute each │  │ Return result    │
│ tool call    │  │ (no changes)     │
│ (add/edit/   │  │                  │
│  delete)     │  │                  │
└──────────────┘  └──────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Send function responses back       │
│  to Gemini                          │
│  continue loop...                   │
└─────────────────────────────────────┘
       │
       └──────► (max 10 iterations)
```

### Safety Limit

```python
max_iterations = 10  # Safety limit
```

### Listener Result (Logged, Not Sent to Frontend)

```python
{
    "status": "success",
    "tool_calls": [
        {"name": "manage_student_facts", "args": {...}, "result": "..."}
    ],
    "usage": {"input_tokens": N, "output_tokens": N, "cost_usd": 0.001}
}
```

---

## 6. Background Memory Compaction

**File:** `backend/app/services/memory_service.py`

The memory compaction system automatically summarizes old messages to prevent context window overflow while preserving conversation continuity.

### Overview

When a chat session accumulates 30+ active (non-archived) messages, the system:
1. Selects the oldest 10 non-archived messages
2. Sends them to Gemini with a summarization prompt
3. Generates a session summary (stored in `chat_sessions.summary`)
4. Extracts any new student facts (inserted into `student_facts` table with `source="compaction"`)
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

**File:** `backend/app/services/memory_service.py:31-62`

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
| **Student Facts** | `student_facts` table (`source="compaction"`) | Extracts permanent info to long-term memory |

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
             │ insert into      │
             │ student_facts DB │
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
| Facts insertion error | Log error, but still save summary (partial success) |

Messages are only marked as archived **after** the summary is successfully saved, ensuring no data loss.

### Key Functions

| Function | Purpose |
|----------|---------|
| `MemoryService.should_compact(session_id)` | Check if 30+ active messages |
| `MemoryService.run_compaction(session_id)` | Execute full compaction flow |
| `run_compaction_if_needed(session_id)` | Background task entry point |
| `GeminiClient.generate_json(prompt)` | Non-streaming JSON response for compaction |

---

## 7. Request/Response Logging

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
  "model": "gemini-3-flash-preview",

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
    "student_facts": [
      {"id": 1, "content": "Likes anime"},
      {"id": 2, "content": "Learning for travel"}
    ],
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
        "name": "manage_student_facts",
        "args": {"action": "add", "content": "Enjoys travel discussions"}
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
| Agent not remembering context | `context.student_facts` - are facts populated? |
| Agent not using vocabulary | `context.vocabulary.items` - are words present? |
| Agent not responding after tool use | `response.tool_calls` vs `response.content` |
| Wrong behavior | `context.system_prompt` - check instructions |
| Missing history | `context.chat_history_count` - should be up to 30 |

---

## 8. File Reference

### Core AI Files

| File | Purpose | Key Functions/Variables |
|------|---------|------------------------|
| `backend/app/core/agents.py` | Agent configurations and prompts | `TUTOR_SYSTEM_PROMPT_TEMPLATE`, `LISTENER_SYSTEM_PROMPT_TEMPLATE` |
| `backend/app/core/context_builder.py` | Builds context for each agent | `build_tutor_context()`, `build_listener_context()`, `fetch_student_facts()` |
| `backend/app/core/gemini_client.py` | Gemini API client | `stream_chat()` (Tutor), `generate_with_tools()` (Listener), `generate_json()` (compaction) |
| `backend/app/core/tools.py` | Tool definitions and execution | `ALL_TOOLS`, `execute_manage_student_facts()` |
| `backend/app/api/chat.py` | HTTP endpoint, orchestration | `generate_stream()`, triggers both Tutor and Listener |
| `backend/app/api/notes.py` | Student facts REST API | CRUD endpoints for facts |
| `backend/app/services/listener_service.py` | Background fact extraction | `ListenerService`, `run_listener()` |
| `backend/app/services/memory_service.py` | Background memory compaction | `MemoryService`, `run_compaction_if_needed()` |
| `backend/app/services/request_logger.py` | Interaction logging | `RequestLogger` |

### Database Tables

| Table | Purpose | Updated By |
|-------|---------|------------|
| `student_facts` | Long-term student info | `manage_student_facts` tool, memory compaction, REST API |

### Configuration

| Setting | File | Default |
|---------|------|---------|
| `ai_logs_path` | `backend/app/config.py` | `./logs/ai_interactions` |
| `gemini_model` | `backend/app/config.py` | `gemini-3-flash-preview` |

### Related Documentation

| Document | Description |
|----------|-------------|
| [Student Facts Logic](./STUDENT_FACTS_LOGIC.md) | Detailed documentation of the student facts system |

---

## Quick Debugging Checklist

1. **Check the logs:** `logs/ai_interactions/{date}/{session}/`
2. **Verify system prompt:** Is it being injected? (only on first message)
3. **Check student facts:** Are facts in the database?
   ```sql
   SELECT id, content, source FROM student_facts ORDER BY created_at;
   ```
4. **Tool execution:** Are tools being called? Check `tool_calls` in logs
5. **Tool loop:** Is the agent responding after tool use? Check for `text` content after `tool_result`
6. **Token usage:** Are costs reasonable? Check `usage` in logs
7. **Memory compaction:** Check database for archived messages and session summaries:
   ```sql
   -- Check archived message count
   SELECT is_archived, COUNT(*) FROM chat_history GROUP BY is_archived;

   -- Check session summary
   SELECT id, summary FROM chat_sessions WHERE id = 'your-session-id';

   -- Check facts from compaction
   SELECT * FROM student_facts WHERE source = 'compaction';
   ```
8. **Compaction not triggering?** Verify active message count >= 30:
   ```sql
   SELECT COUNT(*) FROM chat_history
   WHERE session_id = 'your-session-id' AND is_archived = FALSE;
   ```

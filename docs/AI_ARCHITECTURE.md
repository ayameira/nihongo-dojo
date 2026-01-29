# Nihongo Dojo - AI Architecture

This document describes the AI interaction architecture of the Nihongo Dojo Japanese language tutoring application.

## Overview

Nihongo Dojo uses Google's Gemini API (gemini-2.0-flash) to power an AI Japanese language tutor. The system maintains both short-term (conversation history, class notes) and long-term (student record, vocabulary) memory to provide personalized tutoring.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              NIHONGO DOJO - AI ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐                                              ┌───────────────┐
│     FRONTEND     │                                              │  GEMINI API   │
│  (React + Vite)  │                                              │ gemini-2.0-   │
│                  │                                              │    flash      │
└────────┬─────────┘                                              └───────▲───────┘
         │                                                                │
         │ POST /api/chat/stream                                          │
         │ {message, image_data, session_id}                              │
         ▼                                                                │
┌─────────────────────────────────────────────────────────────────────────┴───────┐
│                                  BACKEND (FastAPI)                              │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         CONTEXT BUILDER                                   │  │
│  │                    (context_builder.py)                                   │  │
│  │                                                                          │  │
│  │  ┌─────────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │ STUDENT_RECORD  │  │ CLASS_NOTES │  │   VOCAB     │  │   CHAT     │  │  │
│  │  │ (Long-term)     │  │ (Recent)    │  │ (Learning)  │  │  HISTORY   │  │  │
│  │  │                 │  │             │  │             │  │ (Last 30)  │  │  │
│  │  └────────┬────────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │  │
│  │           │                  │                │               │         │  │
│  │           ▼                  ▼                ▼               ▼         │  │
│  │   ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │   │                    SYSTEM PROMPT TEMPLATE                        │ │  │
│  │   │                                                                  │ │  │
│  │   │  "Current Date: {today}                                         │ │  │
│  │   │   You are a Japanese language tutor...                          │ │  │
│  │   │                                                                  │ │  │
│  │   │   ## About This Student                                         │ │  │
│  │   │   {student_record_content}  ◄── Long-term memory               │ │  │
│  │   │                                                                  │ │  │
│  │   │   ## Current Study Focus (Recent Memory)                        │ │  │
│  │   │   {class_notes_content}  ◄────── Current learning focus        │ │  │
│  │   │                                                                  │ │  │
│  │   │   ## Vocabulary Currently Being Learned                         │ │  │
│  │   │   {vocab_list_formatted}  ◄───── ALL Learning status vocab     │ │  │
│  │   │                                                                  │ │  │
│  │   │   [Tool usage instructions...]"                                 │ │  │
│  │   └──────────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         GEMINI CLIENT                                     │  │
│  │                     (gemini_client.py)                                    │  │
│  │                                                                          │  │
│  │   1. start_chat(history=chat_history)   ◄── Last 30 messages            │  │
│  │   2. send_message([system_prompt + user_msg + images], stream=True)     │  │
│  │   3. Process streaming response chunks                                   │  │
│  │                                                                          │  │
│  │   Output Events:                                                         │  │
│  │   ├── {"type": "text", "content": "..."}                                │  │
│  │   ├── {"type": "tool_call", "name": "...", "args": {...}}              │  │
│  │   └── {"type": "usage", "input_tokens": N, "output_tokens": N}          │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Memory Management

### Long-term Memory: STUDENT_RECORD.md

Stores persistent information about the student that helps the tutor build rapport:

| Section | Purpose |
|---------|---------|
| `goals` | Language learning goals and aspirations |
| `background` | Context about why they're learning, their situation |
| `interests` | Hobbies, topics they enjoy discussing |
| `preferences` | Learning style preferences |
| `notes` | Other important information |

**Updated via:** `update_student_record` tool

### Short-term Memory: CLASS_NOTES.md

Tracks current learning focus and recent patterns:

| Section | Purpose |
|---------|---------|
| `current_focus` | Grammar points or themes currently being studied |
| `recent_corrections` | Patterns of mistakes the student makes |
| `recent_vocab` | Words recently taught in conversation |

**Updated via:** `update_notes` tool

### Vocabulary: SQLite Database

All vocabulary with "Learning" status is included in context (no limit).

**Updated via:** `save_vocab` tool

### Chat History: SQLite Database

Last 30 messages per session are included in context.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MEMORY MANAGEMENT                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────────────┐      ┌─────────────────────┐                         │
│   │   STUDENT_RECORD    │      │    CLASS_NOTES      │                         │
│   │   (Long-term)       │      │   (Short-term)      │                         │
│   ├─────────────────────┤      ├─────────────────────┤                         │
│   │ ## Goals            │      │ ## Current Focus    │                         │
│   │ ## Background       │      │ ## Recent Corrections│                        │
│   │ ## Interests        │      │ ## Recent Vocab     │                         │
│   │ ## Preferences      │      └─────────────────────┘                         │
│   │ ## Notes            │                                                      │
│   └─────────────────────┘                                                      │
│                                                                                 │
│   ┌─────────────────────┐      ┌─────────────────────┐                         │
│   │    ChatSession      │      │    ChatMessage      │                         │
│   │  (chat_sessions)    │      │   (chat_history)    │                         │
│   ├─────────────────────┤      ├─────────────────────┤                         │
│   │ id (PK)             │◄────┐│ id (PK)             │                         │
│   │ name                │     ││ session_id (FK)  ───┘                         │
│   │ preview             │     ││ role (user/assistant)                         │
│   │ message_count       │     ││ content             │                         │
│   │ created_at          │     ││ image_data (base64) │                         │
│   │ updated_at          │     ││ token_count         │                         │
│   └─────────────────────┘     ││ created_at          │                         │
│                               │└─────────────────────┘                         │
│                               │                                                │
│   Context Window:             │   ┌─────────────────────┐                      │
│   • Last 30 messages loaded   │   │    VocabEntry       │                      │
│   • System prompt on first msg│   │  (vocab_entries)    │                      │
│   • ALL Learning vocab        │   ├─────────────────────┤                      │
│                               │   │ kanji, kana         │                      │
│                               │   │ meaning, pos        │                      │
│                               │   │ status="Learning"   │                      │
│                               │   └─────────────────────┘                      │
│                               │   ALL Learning vocab in context                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Tools Provided to AI

The AI has access to three tools for managing student data:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            AI TOOLS (tools.py)                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  1. save_vocab                                                          │   │
│  │     Purpose: Save vocabulary words taught/corrected                     │   │
│  │     Parameters:                                                         │   │
│  │     ├── kanji: string (optional - empty for kana-only)                 │   │
│  │     ├── kana: string (required - hiragana/katakana)                    │   │
│  │     ├── meaning: string (required - English)                           │   │
│  │     └── pos: enum [noun, verb, i-adj, na-adj, adverb,                  │   │
│  │                    particle, expression, other]                         │   │
│  │     Storage: SQLite → vocab_entries table (status="Learning")          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  2. update_notes                                                        │   │
│  │     Purpose: Update current learning focus (short-term memory)          │   │
│  │     Parameters:                                                         │   │
│  │     ├── section: enum [current_focus, recent_corrections,              │   │
│  │     │                  recent_vocab]                                    │   │
│  │     ├── action: enum [append, replace]                                 │   │
│  │     └── content: string (markdown)                                      │   │
│  │     Storage: CLASS_NOTES.md file                                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  3. update_student_record                                               │   │
│  │     Purpose: Store long-term info about the student                     │   │
│  │     Parameters:                                                         │   │
│  │     ├── section: enum [goals, background, interests,                   │   │
│  │     │                  preferences, notes]                              │   │
│  │     ├── action: enum [append, replace]                                 │   │
│  │     └── content: string (markdown)                                      │   │
│  │     Storage: STUDENT_RECORD.md file                                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## System Prompt Injection

The system prompt is constructed dynamically in `context_builder.py`:

```python
SYSTEM_PROMPT_TEMPLATE = """Current Date: {today}

You are a Japanese language tutor for an intermediate learner studying through immersion.

## Core Principles
- Default to responding in Japanese
- Push the student to the edge of their ability (i+1 hypothesis)
- Only switch to English for explicit grammar explanations
- Use vocabulary the student is currently learning when possible
- Be a warm, personable tutor who remembers and cares about the student

## About This Student
{student_record_content}        ◄── Injected from STUDENT_RECORD.md

## Current Study Focus (Recent Memory)
{class_notes_content}           ◄── Injected from CLASS_NOTES.md

## Vocabulary Currently Being Learned
{vocab_list_formatted}          ◄── Injected from DB (ALL Learning status)

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly
- If user says something is "too easy", increase complexity gradually

## Tool Usage
- Use save_vocab when you teach or correct a word (dictionary form)
- Use update_notes when you notice patterns in current learning
- Use update_student_record when you learn something important about the student
"""
```

## Complete Message Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MESSAGE FLOW                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

  User types message          [Optional: Attach image]
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  useChat.ts                                                                     │
│  POST → /api/chat/stream                                                        │
│  Body: {message, image_data (base64), session_id}                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  chat.py → build_context()                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │ 1. Load STUDENT_RECORD.md (long-term memory)                    │           │
│  │ 2. Load CLASS_NOTES.md (current focus)                          │           │
│  │ 3. Query ALL vocab with status='Learning'                       │           │
│  │ 4. Query chat_history (last 30 messages)                        │           │
│  │ 5. Inject into SYSTEM_PROMPT_TEMPLATE                          │           │
│  │ 6. Return {system_prompt, chat_history}                         │           │
│  └─────────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  gemini_client.py → stream_chat()                                               │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │ 1. model.start_chat(history=chat_history)  ◄── 30 messages     │           │
│  │ 2. Build parts: [system_instructions] + user_msg + images       │           │
│  │ 3. chat.send_message(parts, stream=True) ─────────────────────▶│ GEMINI    │
│  │ 4. Async iterate response chunks                                │ API       │
│  │ 5. Yield: text/tool_call/usage events                          │           │
│  └─────────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
         ┌──────────────────────────────┼──────────────────────────────┐
         │                              │                              │
         ▼                              ▼                              ▼
   ┌──────────┐                  ┌──────────────┐               ┌──────────┐
   │   TEXT   │                  │  TOOL_CALL   │               │  USAGE   │
   │  chunk   │                  │              │               │ metadata │
   └────┬─────┘                  └──────┬───────┘               └────┬─────┘
        │                               │                            │
        │                               ▼                            │
        │                  ┌────────────────────────┐                │
        │                  │ execute_tool_call()    │                │
        │                  │                        │                │
        │                  │ ├─ save_vocab          │                │
        │                  │ │  → SQLite DB         │                │
        │                  │ │                      │                │
        │                  │ ├─ update_notes        │                │
        │                  │ │  → CLASS_NOTES.md    │                │
        │                  │ │                      │                │
        │                  │ └─ update_student_     │                │
        │                  │    record              │                │
        │                  │    → STUDENT_RECORD.md │                │
        │                  └────────────────────────┘                │
        │                               │                            │
        ▼                               ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  SSE Response Stream                                                            │
│  data: {"type": "text", "content": "..."}                                      │
│  data: {"type": "tool_call", "name": "save_vocab", "args": {...}}             │
│  data: {"type": "tool_result", "result": "..."}                                │
│  data: {"type": "usage", "input_tokens": N, "output_tokens": N}                │
│  data: {"type": "done"}                                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PERSISTENCE (chat.py)                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │ 1. Get/Create ChatSession                                       │           │
│  │ 2. Save ChatMessage (role=user)                                 │           │
│  │ 3. Save ChatMessage (role=assistant)                            │           │
│  │ 4. Save TokenLog (input/output/cost)                            │           │
│  │ 5. Update ChatSession (message_count, updated_at)               │           │
│  └─────────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Frontend (streamReader.ts + useChat.ts)                                        │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │ • Parse SSE events                                               │           │
│  │ • Append text chunks to message                                  │           │
│  │ • Show tool execution indicators                                 │           │
│  │ • Update usage/cost display                                      │           │
│  │ • Render final message in UI                                     │           │
│  └─────────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/core/context_builder.py` | System prompt construction, history retrieval |
| `backend/app/core/gemini_client.py` | Gemini API integration, streaming |
| `backend/app/core/tools.py` | Tool definitions and execution |
| `backend/app/api/chat.py` | HTTP endpoint, orchestration |
| `backend/app/db/models.py` | Database schemas |
| `backend/app/services/notes_service.py` | File-based notes management |
| `backend/app/services/request_logger.py` | AI request/response logging to disk |
| `backend/app/config.py` | Configuration settings |
| `src/hooks/useChat.ts` | Frontend chat state management |
| `src/utils/streamReader.ts` | SSE stream parsing |
| `STUDENT_RECORD.md` | Long-term student information |
| `CLASS_NOTES.md` | Current learning focus |
| `logs/ai_interactions/` | AI interaction logs (auto-created) |

## Configuration

Key settings in `backend/app/config.py`:

```python
# Gemini API
gemini_api_key: str = ""
gemini_model: str = "gemini-2.0-flash"

# File Paths
class_notes_path: str = "./CLASS_NOTES.md"
student_record_path: str = "./STUDENT_RECORD.md"
ai_logs_path: str = "./logs/ai_interactions"

# Cost tracking
cost_limit_weekly: float = 10.0
gemini_input_cost_per_1m: float = 0.075
gemini_output_cost_per_1m: float = 0.30
```

## Request/Response Logging

Every AI interaction is logged to disk for debugging and analysis. The `RequestLogger` service (`backend/app/services/request_logger.py`) captures complete request/response data.

### Log Structure

```
logs/ai_interactions/
└── YYYY-MM-DD/
    └── {session_id}/
        └── HH-MM-SS-ffffff.json
```

### Log Contents

Each JSON log file contains:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "session_id": "abc-123",
  "model": "gemini-2.0-flash",
  "request": {
    "user_message": "こんにちは！",
    "has_image": true,
    "image_data": "base64...",
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
      {"name": "save_vocab", "args": {"kana": "げんき", "meaning": "healthy", "pos": "na-adj"}}
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

### What's Logged

| Category | Data |
|----------|------|
| **Request** | User message, image data (full base64), difficulty feedback |
| **Context** | Complete system prompt, all 30 history messages, CLASS_NOTES.md content, STUDENT_RECORD.md content, all Learning vocabulary |
| **Response** | Full AI response text, all tool calls with arguments |
| **Metadata** | Timestamp, session ID, model name, token usage, cost |
| **Errors** | Any errors that occurred during processing |

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         REQUEST/RESPONSE LOGGING                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Every AI interaction is logged to:                                             │
│  ./logs/ai_interactions/YYYY-MM-DD/{session_id}/HH-MM-SS-ffffff.json           │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         LOG CONTENTS                                     │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                         │   │
│  │  REQUEST                    CONTEXT                    RESPONSE         │   │
│  │  ├─ user_message           ├─ system_prompt           ├─ content       │   │
│  │  ├─ image_data (base64)    ├─ chat_history (30)       ├─ tool_calls    │   │
│  │  └─ difficulty_feedback    ├─ files                   └─ tool_count    │   │
│  │                            │  ├─ class_notes                           │   │
│  │  METADATA                  │  └─ student_record       USAGE            │   │
│  │  ├─ timestamp              ├─ vocabulary              ├─ input_tokens  │   │
│  │  ├─ session_id             │  ├─ items[]              ├─ output_tokens │   │
│  │  ├─ model                  │  └─ count                └─ cost_usd      │   │
│  │  └─ error                  └─ chat_history_count                       │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

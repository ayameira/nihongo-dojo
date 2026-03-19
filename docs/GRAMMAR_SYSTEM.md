# Grammar System Architecture

This document explains how grammar learning is implemented in Nihongo Dojo.

## Overview

The grammar system is a skill-tree-like feature for tracking Japanese grammar points. Unlike vocabulary (which uses SRS/Anki), grammar is designed for chat-based learning where the AI tutor incorporates grammar patterns into conversation.

**Key concepts:**
- 706 grammar points seeded from JLPT N5-N1 levels
- Three statuses: `New` → `Learning` → `Burned`
- "Learning" grammar is injected into the tutor's system prompt
- Users can add custom grammar points
- AI can manage grammar via tools
- Background assessment service evaluates progress (token-efficient)

---

## Data Model

### GrammarEntry Table

Location: `backend/app/db/models.py`

```python
class GrammarEntry(Base):
    __tablename__ = "grammar_entries"

    id = Column(Integer, primary_key=True)
    pattern = Column(String(200))       # Japanese pattern, e.g. "ている", "が 1"
    meaning = Column(Text)              # English meaning
    jlpt_level = Column(String(5))      # "N5", "N4", "N3", "N2", "N1", or NULL for custom
    status = Column(String(20))         # "New" | "Learning" | "Burned"
    source = Column(String(20))         # "jlpt" | "manual" | "tutor"
    notes = Column(Text)                # Optional usage notes
    times_seen = Column(Integer)        # Updated by assessor
    times_correct = Column(Integer)     # Updated by assessor
    last_assessed_at = Column(DateTime) # Prevents redundant assessment
    last_seen_at = Column(DateTime)     # When student last used it
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

**Status meanings:**
- `New`: Grammar point exists but student hasn't started learning it
- `Learning`: Student is actively studying this; included in tutor's prompt
- `Burned`: Student has mastered this; no longer shown to tutor

**Source meanings:**
- `jlpt`: Seeded from `jlpt_grammar_list.txt` on startup
- `manual`: User created via the UI
- `tutor`: AI created via the `manage_grammar` tool

---

## Seeding from JLPT List

Location: `backend/app/services/grammar_seeder.py`

On backend startup, if the `grammar_entries` table is empty, the system parses `jlpt_grammar_list.txt` (project root) and seeds 706 grammar points.

**Parsing logic:**
1. Detect level headers like "N5 LEVEL"
2. Parse lines with format: `pattern    meaning` (separated by 2+ spaces)
3. Preserve disambiguators like "が 1", "が 2" as part of the pattern
4. Stop at "STATISTICS" section

**Startup trigger:** `backend/app/main.py` calls `check_and_seed_grammar()` in the lifespan function.

---

## Backend API

Location: `backend/app/api/grammar.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/grammar` | GET | List grammar with filters (`status`, `jlpt_level`, `search`) and pagination |
| `/api/grammar/stats` | GET | Counts by status and by JLPT level |
| `/api/grammar/learning` | GET | All grammar with status="Learning" |
| `/api/grammar/{id}` | GET | Single grammar point |
| `/api/grammar` | POST | Create new grammar (source="manual") |
| `/api/grammar/{id}` | PUT | Update grammar fields |
| `/api/grammar/{id}/status` | PATCH | Quick status change: `{"status": "Learning"}` |
| `/api/grammar/{id}` | DELETE | Delete grammar point |
| `/api/grammar/seed` | POST | Re-seed from JLPT file (clears existing jlpt entries) |

**Stats response shape:**
```json
{
  "by_status": {"New": 700, "Learning": 5, "Burned": 1},
  "by_level": {
    "N5": {"total": 53, "New": 50, "Learning": 3, "Burned": 0},
    ...
  },
  "total": 706,
  "custom": 2
}
```

---

## Integration with Tutor System Prompt

### How "Learning" Grammar Reaches the Tutor

Location: `backend/app/core/context_builder.py`

When a user sends a chat message, `build_tutor_context()` is called:

```python
async def build_tutor_context(session_id, difficulty_feedback):
    # ... fetch student facts, session summary, vocab ...

    # Fetch ALL grammar with status="Learning"
    grammar_list = await fetch_learning_grammar()
    grammar_formatted = format_grammar_list(grammar_list)

    system_prompt = TUTOR_SYSTEM_PROMPT_TEMPLATE.format(
        # ...
        grammar_list_formatted=grammar_formatted or "(No grammar points loaded)",
    )
```

**Formatted output example:**
```
- [N5] ている (is/are/am doing)
- [N5] から 1 (because; since)
- [N4] たら (if; after; when)
```

### Tutor Prompt Instructions

Location: `backend/app/core/agents.py`

The tutor's system prompt includes:

```
## Core Principles
- Incorporate grammar patterns the student is currently learning into your examples and practice sentences

## Grammar Points Currently Being Learned
{grammar_list_formatted}
```

This tells the tutor which grammar to focus on and practice with the student.

---

## AI Tool for Grammar Management

Location: `backend/app/core/tools.py`

The `manage_grammar` tool allows the Listener agent to manage grammar:

```python
MANAGE_GRAMMAR_TOOL = {
    "name": "manage_grammar",
    "actions": ["add", "update_status", "add_notes"],
    "parameters": {
        "action": "add | update_status | add_notes",
        "pattern": "Japanese pattern (for add)",
        "meaning": "English meaning (for add)",
        "grammar_id": "ID for update_status/add_notes",
        "status": "New | Learning | Burned",
        "notes": "Study notes",
        "jlpt_level": "N5-N1 (optional)"
    }
}
```

**Use cases:**
- User says "add ている to my grammar list" → Listener calls `manage_grammar(action="add", pattern="ている", meaning="...")`
- User says "I've mastered から" → Listener calls `manage_grammar(action="update_status", grammar_id=X, status="Burned")`

### Why Listener, Not Tutor?

The Tutor agent has `use_tools=False` (teaching-focused, no interruptions). The Listener agent runs in the background after each message exchange and has tool access. This separation keeps the tutor's responses clean while still allowing grammar management.

**Flow:**
1. User sends message to Tutor
2. Tutor responds (streams to user)
3. Listener runs in background, analyzes conversation
4. If user requested grammar changes, Listener calls `manage_grammar` tool

The Listener's prompt includes the current learning grammar with IDs so it can reference them:
```
## Current Learning Grammar (with IDs for reference)
- [1] [N5] ている (is/are/am doing)
- [2] [N5] から 1 (because; since)
```

---

## Background Grammar Assessment Service

Location: `backend/app/services/grammar_assessor.py`

A token-efficient service that evaluates student grammar proficiency without processing all conversations.

### Design Principles

1. **Pre-filtering with SQL**: Instead of sending all messages to AI, use `LIKE` queries to find messages containing grammar patterns
2. **Cooldown**: Only re-assess each grammar point every 24 hours
3. **Threshold**: Require 3+ relevant messages before sending to AI
4. **Batching**: Process 5 grammar points per AI call to reduce overhead
5. **Capped**: Max 20 grammar points assessed per run

### Assessment Flow

```
1. Get "Learning" grammar not assessed in 24h (max 20)
2. For each grammar point:
   - SQL LIKE search for pattern in user messages (last 30 days)
   - If 3+ relevant messages found, add to assessment batch
3. Send batches of 5 to AI with prompt:
   - Grammar points to assess
   - Relevant message excerpts (truncated to 300 chars)
4. AI returns JSON with:
   - proficiency: beginner | developing | proficient | mastered
   - recommendation: keep_learning | promote_to_burned | demote_to_new
5. Apply status changes based on recommendations
6. Update last_assessed_at timestamps
```

### Trigger

Location: `backend/app/api/chat.py`

Assessment runs as a background task every 20 messages:
```python
if chat_session.message_count % 20 == 0:
    background_tasks.add_task(run_grammar_assessment)
```

---

## Frontend Components

### Grammar Page

Location: `src/components/GrammarPage.tsx`

Full-page view with:
- **Header**: Title, stats strip, status filter pills (All/New/Learning/Burned), search input, "Add Grammar" button
- **Level sections**: Collapsible sections for N5, N4, N3, N2, N1, Custom
- **Grammar items**: Status dot + pattern + meaning. Click dot to cycle status.
- **Add modal**: Form for custom grammar (pattern, meaning, optional level/notes)

**Status colors:**
- New: Blue (`bg-blue-500`)
- Learning: Yellow (`bg-yellow-500`)
- Burned: Green/Jade (`bg-jade`)

### Grammar Hook

Location: `src/hooks/useGrammar.ts`

```typescript
function useGrammar(): {
  grammar: GrammarEntry[];
  grammarByLevel: Record<string, GrammarEntry[]>;  // Grouped by JLPT level
  stats: GrammarStats | null;
  isLoading: boolean;
  statusFilter: string | null;
  searchQuery: string;
  setStatusFilter: (status: string | null) => void;
  setSearchQuery: (query: string) => void;
  updateStatus: (id: number, status: string) => Promise<boolean>;
  addGrammar: (data: {...}) => Promise<GrammarEntry | null>;
  deleteGrammar: (id: number) => Promise<boolean>;
  refreshGrammar: () => Promise<void>;
}
```

### Navigation

Location: `src/components/VocabSidebar.tsx`

Chat/Grammar toggle buttons at the top of the left sidebar. Controlled by `currentView` state in `App.tsx`.

---

## Current Limitations

1. **Tutor cannot proactively suggest grammar**: The tutor sees what's in "Learning" but doesn't know what "New" grammar is available. If the learning queue is empty, it just sees "(No grammar points loaded)".

2. **No dependency tracking**: Grammar points are independent. There's no "learn X before Y" relationship.

3. **Assessment is pattern-based**: The SQL LIKE search for grammar patterns is simple string matching. Complex patterns like "○○ても" may not match well.

4. **No spaced repetition**: Unlike vocabulary, grammar doesn't use SRS. The assessment service provides some progression but it's not as sophisticated.

---

## Potential Enhancements

1. **Add grammar stats to tutor prompt**: Include available grammar counts so tutor can suggest new points when queue is empty.

2. **Give tutor a search tool**: A `search_grammar` tool to query available grammar by level/pattern.

3. **Proactive suggestion service**: Background service that auto-promotes "New" grammar based on student's inferred level.

4. **Better pattern matching**: Use regex or linguistic analysis instead of simple LIKE queries.

5. **Grammar dependencies**: Define prerequisites so the system suggests grammar in a logical order.

---

## File Reference

| File | Purpose |
|------|---------|
| `backend/app/db/models.py` | GrammarEntry model definition |
| `backend/app/api/grammar.py` | REST API endpoints |
| `backend/app/services/grammar_seeder.py` | Parse and seed JLPT grammar |
| `backend/app/services/grammar_assessor.py` | Background assessment service |
| `backend/app/core/context_builder.py` | Inject learning grammar into prompts |
| `backend/app/core/agents.py` | Tutor/Listener prompt templates |
| `backend/app/core/tools.py` | manage_grammar tool definition |
| `backend/app/api/chat.py` | Assessment trigger (every 20 messages) |
| `backend/app/main.py` | Auto-seed on startup |
| `src/hooks/useGrammar.ts` | Frontend state management |
| `src/components/GrammarPage.tsx` | Grammar UI |
| `src/components/VocabSidebar.tsx` | Navigation buttons |
| `src/App.tsx` | View switching logic |
| `jlpt_grammar_list.txt` | Source data (616 stated, 706 parsed) |

# Nihongo Dojo - Refactor Task List

This document provides a detailed breakdown of all tasks required to refactor Nihongo Dojo from a Tauri desktop app to a browser-based application with a FastAPI backend.

For each phase, you should create a new file REFACTOR_PHASE_X.md and add the tasks for that phase there. Describe in detail what you have done and how to test it.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Phase 1: Project Restructure & Backend Setup](#2-phase-1-project-restructure--backend-setup)
3. [Phase 2: Database Migration (SQLite → PostgreSQL)](#3-phase-2-database-migration-sqlite--postgresql)
4. [Phase 3: LLM Integration (Gemini 3 Flash)](#4-phase-3-llm-integration-gemini-3-flash)
5. [Phase 4: Frontend Refactor](#5-phase-4-frontend-refactor)
6. [Phase 5: CLASS_NOTES.md System](#6-phase-5-class_notesmd-system)
7. [Phase 6: Vocabulary HUD & Sidebar](#7-phase-6-vocabulary-hud--sidebar)
8. [Phase 7: Cost & Token Telemetry](#8-phase-7-cost--token-telemetry)
9. [Phase 8: Polish & Production Readiness](#9-phase-8-polish--production-readiness)

---

## 1. Architecture Overview

### Current State
```
┌─────────────────────────────────────────┐
│            Tauri Desktop App            │
├─────────────────────────────────────────┤
│  Frontend: React + Vite + Tailwind      │
│  - Chat.tsx (310 lines)                 │
│  - Mock message handling                │
│  - Image attachments                    │
│  - Chat/Blackboard tabs                 │
├─────────────────────────────────────────┤
│  Backend: Rust (minimal)                │
│  - Only shell plugin loaded             │
│  - No command implementations           │
├─────────────────────────────────────────┤
│  Data: SQLite                           │
│  - anki_export.db (20,133 notes)        │
│  - Python export scripts                │
└─────────────────────────────────────────┘
```

### Target State
```
┌─────────────────────────────────────────┐
│           Browser (Chrome/Safari)        │
│  ├── Yomitan extension enabled          │
│  └── React SPA served by Vite           │
├─────────────────────────────────────────┤
│         FastAPI Backend (Python)         │
│  ├── /api/chat/stream (SSE)             │
│  ├── /api/vocab/*                       │
│  ├── /api/notes/*                       │
│  └── /api/telemetry/*                   │
├─────────────────────────────────────────┤
│          Gemini 3 Flash API              │
│  ├── Streaming responses                │
│  └── Tool use (save_vocab, update_notes)│
├─────────────────────────────────────────┤
│  Data Layer                              │
│  ├── PostgreSQL (vocab, chat, tokens)   │
│  ├── CLASS_NOTES.md (file system)       │
│  └── Anki import (configurable path)    │
└─────────────────────────────────────────┘
```

---

## 2. Phase 1: Project Restructure & Backend Setup

### 2.1 Remove Tauri Dependencies

**Files to delete:**
- [ ] `src-tauri/` directory (entire Rust backend)
- [ ] Remove `@tauri-apps/api` from package.json
- [ ] Remove `@tauri-apps/plugin-shell` from package.json
- [ ] Remove `@tauri-apps/cli` from devDependencies
- [ ] Remove `"tauri": "tauri"` script from package.json

**Files to update:**
- [ ] `vite.config.ts` - Remove Tauri-specific port (1420) configuration
- [ ] `index.html` - Ensure no Tauri-specific scripts

### 2.2 Create FastAPI Backend Structure

**Directory structure to create:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment configuration
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py             # POST /api/chat/stream
│   │   ├── vocab.py            # Vocabulary CRUD endpoints
│   │   ├── notes.py            # CLASS_NOTES.md endpoints
│   │   └── telemetry.py        # Token usage endpoints
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── gemini_client.py    # Gemini API wrapper
│   │   ├── context_builder.py  # Prompt orchestration
│   │   ├── tools.py            # Tool definitions for Gemini
│   │   └── streaming.py        # SSE response utilities
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── models.py           # ORM models
│   │   └── migrations/         # Alembic migrations
│   │
│   └── services/
│       ├── __init__.py
│       ├── vocab_service.py    # Vocabulary business logic
│       ├── notes_service.py    # CLASS_NOTES.md operations
│       ├── anki_importer.py    # Anki deck import logic
│       └── token_tracker.py    # Usage tracking
│
├── requirements.txt
├── pyproject.toml              # Poetry or pip configuration
├── .env.example                # Environment template
└── alembic.ini                 # Database migrations config
```

### 2.3 Backend Dependencies

**Create `backend/requirements.txt`:**
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0              # PostgreSQL async driver
alembic>=1.13.0              # Database migrations
pydantic>=2.5.0
pydantic-settings>=2.1.0
google-generativeai>=0.3.0   # Gemini SDK
sse-starlette>=1.8.0         # Server-Sent Events
aiofiles>=23.2.0             # Async file operations
python-multipart>=0.0.6      # File uploads
```

### 2.4 FastAPI Application Setup

**Task: Create `backend/app/main.py`**

Requirements:
- [ ] Initialize FastAPI app with CORS middleware (allow localhost:5173 for Vite)
- [ ] Mount API routers: `/api/chat`, `/api/vocab`, `/api/notes`, `/api/telemetry`
- [ ] Add startup event to verify database connection
- [ ] Add startup event to verify Gemini API key
- [ ] Add shutdown event to close database connections
- [ ] Configure logging

**Task: Create `backend/app/config.py`**

Environment variables to support:
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `GEMINI_API_KEY` - Google AI API key
- [ ] `CLASS_NOTES_PATH` - Path to CLASS_NOTES.md (default: `./CLASS_NOTES.md`)
- [ ] `ANKI_COLLECTION_PATH` - Path to Anki collection.anki2
- [ ] `COST_LIMIT_WEEKLY` - Weekly spending limit in dollars
- [ ] `GEMINI_INPUT_COST_PER_1M` - Cost per 1M input tokens
- [ ] `GEMINI_OUTPUT_COST_PER_1M` - Cost per 1M output tokens

### 2.5 Frontend Vite Configuration Update

**Task: Update `vite.config.ts`**

- [ ] Configure proxy to FastAPI backend (`/api` → `http://localhost:8000/api`)
- [ ] Change dev server port from 1420 to 5173 (Vite default)
- [ ] Ensure HMR works correctly

**Example configuration:**
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### 2.6 Update Package.json Scripts

**Task: Add development workflow scripts**

- [ ] Add `"dev:frontend": "vite"`
- [ ] Add `"dev:backend": "cd backend && uvicorn app.main:app --reload"`
- [ ] Add `"dev": "concurrently \"npm run dev:frontend\" \"npm run dev:backend\""`
- [ ] Add `concurrently` as devDependency

---

## 3. Phase 2: Database Migration (SQLite → PostgreSQL)

### 3.1 PostgreSQL Schema Design

**Task: Create `backend/app/db/models.py`**

**Table: `vocab_entries`**
```python
class VocabEntry(Base):
    __tablename__ = "vocab_entries"

    id: int                    # Primary key
    kanji: str                 # Kanji representation (nullable for kana-only words)
    kana: str                  # Kana reading (required)
    meaning: str               # English meaning
    pos: str                   # Part of speech (noun, verb, adj, etc.)
    status: str                # 'New' | 'Learning' | 'Mature'
    source: str                # 'anki' | 'tutor' | 'manual'
    anki_note_id: int          # Reference to original Anki note (nullable)
    interval_days: int         # Days until next review (from Anki)
    times_seen: int            # How many times shown in chat
    times_correct: int         # Times user demonstrated understanding
    last_seen_at: datetime     # Last time appeared in conversation
    created_at: datetime
    updated_at: datetime
```

**Table: `chat_history`**
```python
class ChatMessage(Base):
    __tablename__ = "chat_history"

    id: int                    # Primary key
    session_id: str            # Groups messages by session
    role: str                  # 'user' | 'assistant'
    content: str               # Message text
    image_data: str            # Base64 image (nullable)
    token_count: int           # Tokens used for this message
    created_at: datetime
```

**Table: `token_logs`**
```python
class TokenLog(Base):
    __tablename__ = "token_logs"

    id: int                    # Primary key
    session_id: str
    model: str                 # 'gemini-2.0-flash' etc.
    input_tokens: int
    output_tokens: int
    image_count: int           # Number of images in request
    cost_usd: float            # Calculated cost
    created_at: datetime
```

### 3.2 Migrate Anki Import Script

**Task: Update `export_anki_to_sqlite.py` → `backend/app/services/anki_importer.py`**

Changes required:
- [ ] Convert to async function using `asyncpg`
- [ ] Insert into PostgreSQL `vocab_entries` table instead of SQLite
- [ ] Set `source = 'anki'` for all imported entries
- [ ] Map Anki status → our status: `New`→`New`, `Learning`→`Learning`, `Young`/`Mature`→`Mature`
- [ ] Handle duplicate detection (same kanji+kana = update, don't duplicate)
- [ ] Add progress callback for UI updates
- [ ] Make Anki collection path configurable via environment variable

**Task: Create import API endpoint**

- [ ] `POST /api/vocab/import-anki` - Trigger Anki import
- [ ] `GET /api/vocab/import-status` - Get import progress
- [ ] Return count of imported/updated/skipped records

### 3.3 Database Migrations

**Task: Set up Alembic**

- [ ] Initialize Alembic in `backend/`
- [ ] Create initial migration with all three tables
- [ ] Create migration script in package.json: `"db:migrate": "cd backend && alembic upgrade head"`

---

## 4. Phase 3: LLM Integration (Gemini 3 Flash)

### 4.1 Gemini Client Wrapper

**Task: Create `backend/app/core/gemini_client.py`**

Requirements:
- [ ] Initialize Gemini client with API key from config
- [ ] Support streaming responses using `generate_content_stream()`
- [ ] Extract and return token usage metadata from responses
- [ ] Handle rate limits with exponential backoff
- [ ] Handle API errors gracefully with user-friendly messages

### 4.2 Tool Definitions

**Task: Create `backend/app/core/tools.py`**

Define function declarations for Gemini tool use:

**Tool: `save_vocab`**
```python
save_vocab_tool = {
    "name": "save_vocab",
    "description": "Save a vocabulary word that was taught or corrected in the conversation. Always use dictionary form.",
    "parameters": {
        "type": "object",
        "properties": {
            "kanji": {"type": "string", "description": "Kanji writing (empty string if kana-only)"},
            "kana": {"type": "string", "description": "Hiragana/katakana reading"},
            "meaning": {"type": "string", "description": "English meaning"},
            "pos": {"type": "string", "enum": ["noun", "verb", "i-adj", "na-adj", "adverb", "particle", "expression", "other"]}
        },
        "required": ["kana", "meaning", "pos"]
    }
}
```

**Tool: `update_notes`**
```python
update_notes_tool = {
    "name": "update_notes",
    "description": "Update a section of the student's study notes based on the conversation.",
    "parameters": {
        "type": "object",
        "properties": {
            "section": {"type": "string", "enum": ["current_focus", "recent_corrections", "recent_vocab"]},
            "action": {"type": "string", "enum": ["append", "replace"]},
            "content": {"type": "string", "description": "Markdown content to add or replace"}
        },
        "required": ["section", "action", "content"]
    }
}
```

**Tool: `adjust_difficulty`**
```python
adjust_difficulty_tool = {
    "name": "adjust_difficulty",
    "description": "Log when user indicates content is too hard or too easy.",
    "parameters": {
        "type": "object",
        "properties": {
            "direction": {"type": "string", "enum": ["easier", "harder"]},
            "reason": {"type": "string", "description": "Brief note about what was too hard/easy"}
        },
        "required": ["direction"]
    }
}
```

### 4.3 Context Builder / Prompt Orchestration

**Task: Create `backend/app/core/context_builder.py`**

This is the "Context Orchestrator" that runs before each Gemini call.

Functions:
- [ ] `load_class_notes()` - Read CLASS_NOTES.md content
- [ ] `fetch_learning_vocab(limit=50)` - Get recent 'Learning' status words from DB
- [ ] `get_chat_history(session_id, limit=15)` - Get last N turns of conversation
- [ ] `build_system_prompt()` - Combine all context into system prompt

**System Prompt Template:**
```markdown
You are a Japanese language tutor for an intermediate learner studying through immersion.

## Core Principles
- Default to responding in Japanese
- Push the student to the edge of their ability (i+1 hypothesis)
- Only switch to English for explicit grammar explanations, then immediately provide Japanese examples
- Use vocabulary the student is currently learning when possible

## Student's Current Study Notes
{class_notes_content}

## Vocabulary Currently Being Learned
{vocab_list_formatted}

## Instructions for Difficulty
- If user says something is "too hard", simplify slightly but don't overcompensate
- If user says something is "too easy", increase complexity gradually
- When teaching new words, use the save_vocab tool
- When noticing patterns in student mistakes, update the notes

## Tool Usage
- Use save_vocab when you teach or correct a word (always dictionary form)
- Use update_notes when you notice patterns worth remembering
```

### 4.4 Streaming Chat Endpoint

**Task: Create `backend/app/api/chat.py`**

**Endpoint: `POST /api/chat/stream`**

Request body:
```python
class ChatRequest(BaseModel):
    message: str
    image_data: Optional[str] = None  # Base64 encoded
    session_id: str
    difficulty_feedback: Optional[str] = None  # 'too_hard' | 'too_easy'
```

Implementation steps:
- [ ] Validate request
- [ ] Build context using `context_builder`
- [ ] If `difficulty_feedback` provided, inject adjustment instruction into prompt
- [ ] Call Gemini with streaming enabled
- [ ] Return `StreamingResponse` with `text/event-stream` content type
- [ ] Yield chunks as SSE events: `data: {"type": "text", "content": "..."}\n\n`
- [ ] Yield tool calls as events: `data: {"type": "tool_call", "name": "save_vocab", "args": {...}}\n\n`
- [ ] Execute tool calls and store results
- [ ] Yield final event: `data: {"type": "done", "usage": {...}}\n\n`
- [ ] Use `BackgroundTasks` to: save message to chat_history, log token usage

### 4.5 Tool Execution Handler

**Task: Create tool execution logic in `backend/app/core/tools.py`**

- [ ] `execute_save_vocab(args)` - Insert/update vocab_entries table
- [ ] `execute_update_notes(args)` - Modify CLASS_NOTES.md file
- [ ] `execute_adjust_difficulty(args)` - Log to notes or separate tracking

---

## 5. Phase 4: Frontend Refactor

### 5.1 Remove Tauri References

**Task: Update `src/App.tsx`**

- [ ] Remove all Tauri imports
- [ ] Replace mock `handleSendMessage` with fetch to `/api/chat/stream`
- [ ] Add session_id generation (use UUID)
- [ ] Add state for difficulty feedback pending

### 5.2 Implement Streaming Message Handler

**Task: Create `src/hooks/useChat.ts`**

Custom hook for chat state management:
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  image?: string;
  timestamp: Date;
  status: 'sending' | 'streaming' | 'complete' | 'error';
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  sendMessage: (content: string, image?: string) => Promise<void>;
  sendDifficultyFeedback: (direction: 'too_hard' | 'too_easy') => void;
  clearHistory: () => void;
}
```

Implementation:
- [ ] Manage messages array state
- [ ] Generate unique session_id on mount (persist in sessionStorage)
- [ ] `sendMessage`:
  - Add user message to array with status 'sending'
  - Add placeholder assistant message with status 'streaming'
  - Call `fetch('/api/chat/stream', {...})`
  - Read response as `ReadableStream`
  - Parse SSE events and append to assistant message content
  - Update status to 'complete' when done
- [ ] Handle tool call events (optional: show in UI)
- [ ] Handle errors gracefully

**Task: Create `src/utils/streamReader.ts`**

SSE stream parsing utility:
```typescript
async function* readSSEStream(response: Response): AsyncGenerator<SSEEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6));
      }
    }
  }
}
```

### 5.3 Update Chat Component for react-markdown

**Task: Update `src/components/Chat.tsx`**

- [ ] Install `react-markdown` and `remark-gfm`:
  ```bash
  npm install react-markdown remark-gfm
  ```

- [ ] Replace `<p className="whitespace-pre-wrap">` with:
  ```tsx
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      // Custom renderers for clean DOM (Yomitan compatibility)
      p: ({children}) => <p className="mb-2">{children}</p>,
      // Avoid nested divs, keep spans and p tags
    }}
  >
    {msg.content}
  </ReactMarkdown>
  ```

- [ ] Test with Yomitan extension to verify hover detection works

### 5.4 Add "Too Hard / Too Easy" Feedback

**Task: Add difficulty feedback buttons to assistant messages**

- [ ] Add subtle buttons below assistant messages:
  ```tsx
  <div className="flex gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
    <button onClick={() => sendFeedback('too_hard')} className="text-xs text-gray-400 hover:text-gray-600">
      Too Hard
    </button>
    <button onClick={() => sendFeedback('too_easy')} className="text-xs text-gray-400 hover:text-gray-600">
      Too Easy
    </button>
  </div>
  ```
- [ ] Make the container a `group` for hover effect
- [ ] Clicking should send feedback with next message (not immediately)
- [ ] Show visual indicator that feedback is pending

### 5.5 Implement Sticky Bottom Auto-Scroll

**Task: Update scroll behavior in Chat.tsx**

Current implementation uses simple `scrollIntoView`. Replace with:

- [ ] Track if user has scrolled up manually (is not at bottom)
- [ ] If user is at bottom, auto-scroll on new content
- [ ] If user has scrolled up, don't auto-scroll
- [ ] Show "New messages" indicator when at top with new content
- [ ] Clicking indicator or new user message snaps to bottom

```typescript
const [isAtBottom, setIsAtBottom] = useState(true);
const containerRef = useRef<HTMLDivElement>(null);

const handleScroll = () => {
  const container = containerRef.current;
  if (!container) return;
  const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50;
  setIsAtBottom(atBottom);
};

useEffect(() => {
  if (isAtBottom) {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }
}, [messages, isAtBottom]);
```

### 5.6 Update Loading States

**Task: Improve loading indicators**

Current states: `'idle' | 'checking_vocab' | 'typing'`

New states to support streaming:
- [ ] Add `'connecting'` state (before stream starts)
- [ ] Replace `'typing'` with `'streaming'` (while receiving chunks)
- [ ] Show partial content while streaming (not just dots)
- [ ] Animate text appearing (optional: typewriter effect)

---

## 6. Phase 5: CLASS_NOTES.md System

### 6.1 Create Notes File Structure

**Task: Create initial `CLASS_NOTES.md` template**

```markdown
# Japanese Study Notes

## Current Focus
<!-- What grammar points or vocabulary themes are we currently working on -->

## Recent Corrections
<!-- Patterns of mistakes the student makes -->

## Recent Vocab
<!-- Words recently taught in conversation -->
```

### 6.2 Notes Service Backend

**Task: Create `backend/app/services/notes_service.py`**

Functions:
- [ ] `read_notes() -> str` - Read entire file content
- [ ] `read_section(section: str) -> str` - Extract specific section content
- [ ] `update_section(section: str, content: str, action: 'append' | 'replace')` - Modify section
- [ ] `archive_old_notes()` - Move content to ARCHIVE.md when exceeding token limit
- [ ] `get_notes_token_count() -> int` - Count tokens in current notes

Implementation details:
- [ ] Use `aiofiles` for async file operations
- [ ] Parse markdown to find section headers
- [ ] Handle concurrent access (simple file locking)
- [ ] Validate section names

### 6.3 Notes API Endpoints

**Task: Create `backend/app/api/notes.py`**

- [ ] `GET /api/notes` - Get full CLASS_NOTES.md content
- [ ] `GET /api/notes/{section}` - Get specific section
- [ ] `PUT /api/notes/{section}` - Update section (manual edit)
- [ ] `POST /api/notes/archive` - Trigger archival

### 6.4 Notes Editor in Frontend

**Task: Refactor Blackboard tab into Notes Editor**

- [ ] Rename "Blackboard" to "Notes" or "Study Notes"
- [ ] Display CLASS_NOTES.md content (fetched from API)
- [ ] Add edit mode toggle
- [ ] In edit mode:
  - Show markdown textarea
  - Add Save/Cancel buttons
  - Warn if AI is currently generating (avoid race condition)
- [ ] In view mode:
  - Render markdown with `react-markdown`
  - Show last updated timestamp
- [ ] Add refresh button to reload from server

### 6.5 Context Bloat Prevention

**Task: Implement automatic archival**

- [ ] In `notes_service.py`, check token count before reading
- [ ] If exceeds 1000 tokens:
  - Move oldest content in each section to `ARCHIVE.md`
  - Keep headers and most recent entries
  - Log archival action
- [ ] Make threshold configurable via environment variable

---

## 7. Phase 6: Vocabulary HUD & Sidebar

### 7.1 Vocabulary API Endpoints

**Task: Create `backend/app/api/vocab.py`**

- [ ] `GET /api/vocab` - List all vocab entries (paginated)
  - Query params: `status`, `source`, `search`, `page`, `limit`
- [ ] `GET /api/vocab/{id}` - Get single entry
- [ ] `POST /api/vocab` - Create entry (manual add)
- [ ] `PUT /api/vocab/{id}` - Update entry
- [ ] `DELETE /api/vocab/{id}` - Delete entry
- [ ] `GET /api/vocab/learning` - Get all 'Learning' status entries
- [ ] `POST /api/vocab/{id}/seen` - Increment times_seen counter
- [ ] `POST /api/vocab/{id}/correct` - Increment times_correct counter

### 7.2 Vocabulary Sidebar Component

**Task: Create `src/components/VocabSidebar.tsx`**

Layout:
```
┌─────────────────────┐
│ Vocabulary      [+] │
├─────────────────────┤
│ 🔴 Learning (23)    │
│ ├─ 食べる (taberu)  │
│ ├─ 飲む (nomu)      │
│ └─ ...              │
│ 🟢 Mature (1,234)   │
│ └─ [collapsed]      │
│ 🔵 New (15,000)     │
│ └─ [collapsed]      │
└─────────────────────┘
```

Features:
- [ ] Collapsible sections by status
- [ ] Show count per status
- [ ] Scrollable list within each section
- [ ] Click word to see full details (modal or expandable)
- [ ] Search/filter input at top
- [ ] Manual add button opens form
- [ ] Real-time updates when AI saves new vocab (WebSocket or polling)

### 7.3 Recall Highlighting in Chat

**Task: Implement vocabulary highlighting**

- [ ] When rendering assistant messages, scan for vocab words
- [ ] Match against 'Learning' status words in database
- [ ] Wrap matched words in highlight span:
  ```tsx
  <span className="bg-yellow-100 border-b border-yellow-400 cursor-help"
        title={`${meaning} - ${times_seen} times seen`}>
    {word}
  </span>
  ```
- [ ] Clicking highlighted word updates `times_seen` counter
- [ ] Consider performance: cache learning vocab list, update periodically

### 7.4 Layout Refactor for Sidebar

**Task: Update `src/App.tsx` layout**

Current: Single column chat
New: Sidebar + Main content

```tsx
<div className="flex h-screen">
  <VocabSidebar className="w-64 border-r" />
  <main className="flex-1">
    <Chat ... />
  </main>
</div>
```

- [ ] Make sidebar collapsible on mobile
- [ ] Add toggle button to show/hide sidebar
- [ ] Persist sidebar state in localStorage

---

## 8. Phase 7: Cost & Token Telemetry

### 8.1 Token Tracking Middleware

**Task: Create `backend/app/services/token_tracker.py`**

- [ ] Extract usage metadata from Gemini responses:
  ```python
  usage = response.usage_metadata
  input_tokens = usage.prompt_token_count
  output_tokens = usage.candidates_token_count
  ```
- [ ] Calculate cost based on configurable pricing:
  ```python
  cost = (input_tokens * INPUT_COST_PER_1M / 1_000_000) +
         (output_tokens * OUTPUT_COST_PER_1M / 1_000_000)
  ```
- [ ] Save to `token_logs` table with timestamp
- [ ] Include image count in calculation (images have different pricing)

### 8.2 Telemetry API Endpoints

**Task: Create `backend/app/api/telemetry.py`**

- [ ] `GET /api/telemetry/usage` - Get usage summary
  - Query params: `period` ('day', 'week', 'month')
  - Returns: total tokens, total cost, breakdown by day
- [ ] `GET /api/telemetry/limit` - Get current spend vs limit
  - Returns: `{ spent: 2.50, limit: 10.00, remaining: 7.50, period: 'weekly' }`
- [ ] `PUT /api/telemetry/limit` - Update weekly limit

### 8.3 Cost Dashboard Component

**Task: Create `src/components/CostDashboard.tsx`**

Display:
```
┌────────────────────────────────────────┐
│ This Week: $2.50 / $10.00              │
│ ████████████░░░░░░░░░░░░░░░░░░ 25%     │
├────────────────────────────────────────┤
│ Today: 12,345 tokens ($0.45)           │
│ Average: 8,234 tokens/day              │
└────────────────────────────────────────┘
```

- [ ] Progress bar showing spent/limit ratio
- [ ] Color coding: green (<50%), yellow (50-80%), red (>80%)
- [ ] Warning banner when approaching limit
- [ ] Click to expand detailed breakdown
- [ ] Option to adjust limit

### 8.4 Integrate Cost Display

**Task: Add cost indicator to header**

- [ ] Show mini cost indicator in app header
- [ ] Click opens full dashboard modal
- [ ] Update after each message (show cost of last response)

---

## 9. Phase 8: Polish & Production Readiness

### 9.1 Error Handling

**Frontend:**
- [ ] Show user-friendly error messages when API fails
- [ ] Retry logic for transient failures
- [ ] Offline indicator when backend unreachable
- [ ] Handle rate limit errors from Gemini

**Backend:**
- [ ] Consistent error response format
- [ ] Logging for all errors
- [ ] Don't expose internal errors to frontend

### 9.2 Session Management

- [ ] Generate session_id on app load, store in sessionStorage
- [ ] Option to start new session (clears chat history)
- [ ] Session history browser (list past sessions)

### 9.3 Configuration UI

**Task: Create Settings page/modal**

- [ ] Anki collection path configuration
- [ ] Trigger Anki import
- [ ] Weekly cost limit adjustment
- [ ] CLASS_NOTES.md path (for advanced users)
- [ ] Reset/clear data options

### 9.4 Startup Script

**Task: Create one-click startup**

For macOS, create a script that:
- [ ] Starts PostgreSQL (if using local install)
- [ ] Runs database migrations
- [ ] Starts FastAPI backend
- [ ] Starts Vite dev server
- [ ] Opens browser to localhost:5173

### 9.5 Documentation Updates

- [ ] Update README.md with new setup instructions
- [ ] Document environment variables in `.env.example`
- [ ] Document API endpoints
- [ ] Add troubleshooting section

### 9.6 Security Hardening

- [ ] Add rate limiting to API endpoints
- [ ] Validate file paths to prevent directory traversal
- [ ] Sanitize user input before sending to Gemini
- [ ] Add CSP headers to Vite config
- [ ] Consider authentication for multi-user scenarios (future)

---

## Appendix A: Files to Keep vs Remove

### Keep (with modifications)
| File | Action |
|------|--------|
| `src/main.tsx` | Keep as-is |
| `src/App.tsx` | Major refactor |
| `src/components/Chat.tsx` | Major refactor |
| `src/index.css` | Keep as-is |
| `vite.config.ts` | Update for proxy |
| `package.json` | Remove Tauri deps, add new deps |
| `tsconfig.json` | Minor updates |
| `tailwind.config.js` | Keep as-is |
| `postcss.config.js` | Keep as-is |
| `index.html` | Minor cleanup |
| `export_anki_to_sqlite.py` | Move to backend, refactor |

### Remove Entirely
| File/Directory | Reason |
|----------------|--------|
| `src-tauri/` | Replaced by FastAPI |
| `anki_export.db` | Replaced by PostgreSQL |
| `collection.anki2` | Keep in user's Anki folder |
| `temp_collection.anki2` | Temporary file |

### New Files to Create
| File | Description |
|------|-------------|
| `backend/` | Entire FastAPI backend |
| `src/hooks/useChat.ts` | Chat state management |
| `src/utils/streamReader.ts` | SSE parsing |
| `src/components/VocabSidebar.tsx` | Vocabulary display |
| `src/components/CostDashboard.tsx` | Usage tracking |
| `CLASS_NOTES.md` | Student notes file |
| `.env` | Environment variables |

---

## Appendix B: Estimated Complexity by Phase

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Phase 1: Project Restructure | 15 | Medium |
| Phase 2: Database Migration | 12 | Medium |
| Phase 3: LLM Integration | 18 | High |
| Phase 4: Frontend Refactor | 20 | High |
| Phase 5: CLASS_NOTES.md | 12 | Medium |
| Phase 6: Vocab HUD | 14 | Medium |
| Phase 7: Cost Telemetry | 10 | Low |
| Phase 8: Polish | 15 | Medium |
| **Total** | **116** | - |

---

## Appendix C: Critical Dependencies Between Phases

```
Phase 1 (Project Setup)
    ↓
Phase 2 (Database) ────────────────┐
    ↓                              │
Phase 3 (LLM) ←────────────────────┤
    ↓                              │
Phase 4 (Frontend) ←───────────────┤
    ↓                              │
Phase 5 (Notes) ←──────────────────┘
    ↓
Phase 6 (Vocab HUD)
    ↓
Phase 7 (Telemetry)
    ↓
Phase 8 (Polish)
```

**Notes:**
- Phases 1-4 are sequential and blocking
- Phase 5 (Notes) can start after Phase 3 (needs tool execution)
- Phase 6 (Vocab) needs Phase 2 (database) and Phase 4 (frontend)
- Phase 7 can be done in parallel with Phases 5-6
- Phase 8 should be last

---

*Last updated: January 2026*
*Based on REFACTOR.md specifications*

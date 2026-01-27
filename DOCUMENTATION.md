# Nihongo Dojo - Technical Documentation

**Version:** 0.2.1
**Status:** Active Development

---

## Overview

Nihongo Dojo is a personalized Japanese language tutor web application. It provides an interactive chat-based interface for Japanese language practice powered by Google Gemini AI, with the ability to reference and leverage users' existing Anki flashcard study data (particularly WaniKani decks and Japanese language decks).

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | ^18.2.0 | UI framework |
| TypeScript | ^5.0.0 | Type-safe JavaScript |
| Vite | ^5.0.0 | Build tool and dev server |
| Tailwind CSS | ^3.4.3 | Utility-first CSS framework |
| react-markdown | ^9.0.0 | Markdown rendering |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115.* | Python async web framework |
| SQLAlchemy | 2.0.* | Async ORM |
| aiosqlite | 0.20.* | Async SQLite driver |
| Google Gemini | 2.0-flash | LLM for chat |
| Pydantic | 2.0.* | Data validation |

---

## Project Structure

```
nihongo-dojo/
├── src/                          # React/TypeScript frontend
│   ├── main.tsx                  # React entry point
│   ├── App.tsx                   # Main application layout
│   ├── index.css                 # Tailwind CSS styles
│   ├── components/
│   │   ├── Chat.tsx              # Chat interface
│   │   ├── VocabSidebar.tsx      # Vocabulary sidebar with Anki settings
│   │   ├── SessionList.tsx       # Chat session list component
│   │   └── CostDashboard.tsx     # Usage/cost tracking modal
│   ├── hooks/
│   │   ├── useChat.ts            # Chat state management hook
│   │   └── useSessions.ts        # Session management hook
│   └── utils/
│       └── streamReader.ts       # SSE stream parser
│
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── main.py               # FastAPI app with lifespan events
│   │   ├── config.py             # Pydantic settings
│   │   ├── api/
│   │   │   ├── chat.py           # Streaming chat endpoint
│   │   │   ├── vocab.py          # Vocabulary CRUD endpoints
│   │   │   ├── notes.py          # CLASS_NOTES.md management
│   │   │   ├── telemetry.py      # Token usage tracking
│   │   │   ├── sessions.py       # Chat session management
│   │   │   └── config.py         # Anki path configuration
│   │   ├── core/
│   │   │   ├── gemini_client.py  # Gemini API wrapper
│   │   │   ├── tools.py          # Tool definitions for Gemini
│   │   │   ├── context_builder.py # System prompt builder
│   │   │   └── streaming.py      # SSE streaming utilities
│   │   ├── db/
│   │   │   ├── database.py       # SQLAlchemy async setup
│   │   │   └── models.py         # Database models
│   │   └── services/
│   │       ├── anki_sync.py      # Anki collection export
│   │       ├── anki_importer.py  # Import Anki data to app DB
│   │       ├── notes_service.py  # Notes file management
│   │       ├── vocab_service.py  # Vocabulary queries
│   │       └── token_tracker.py  # Token usage logging
│   ├── requirements.txt          # Python dependencies
│   ├── config.json               # Runtime configuration (Anki path)
│   └── .env                      # Environment variables
│
├── Configuration Files
│   ├── package.json              # Node.js dependencies & scripts
│   ├── vite.config.ts            # Vite with API proxy
│   ├── tsconfig.json             # TypeScript configuration
│   ├── tailwind.config.js        # Tailwind CSS configuration
│   └── postcss.config.js         # PostCSS configuration
│
├── Data Files
│   ├── CLASS_NOTES.md            # Persistent study notes
│   └── anki_export.db            # Exported Anki data (auto-generated)
│
└── index.html                    # HTML entry point
```

---

## Architecture

### Request Flow

```
Browser (React)
    ↓ HTTP/SSE
Vite Dev Server (proxy /api → :8000)
    ↓
FastAPI Backend
    ├── Gemini API (streaming chat)
    ├── SQLite Database (vocab, messages, tokens)
    └── File System (CLASS_NOTES.md)
```

### Key Features

1. **Streaming Chat**: Server-Sent Events for real-time response streaming
2. **Tool Calling**: Gemini can save vocabulary, update notes, adjust difficulty
3. **Anki Integration**: Automatic sync from Anki collection on server start
4. **Cost Tracking**: Token usage and spending limits

---

## API Endpoints

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/stream` | Streaming chat with SSE |
| GET | `/api/chat/history/{session_id}` | Get chat history for a session |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List all chat sessions |
| POST | `/api/sessions` | Create a new session |
| GET | `/api/sessions/{id}` | Get session details |
| PUT | `/api/sessions/{id}` | Rename a session |
| DELETE | `/api/sessions/{id}` | Delete session and messages |

### Vocabulary
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vocab` | List vocabulary with filtering |
| GET | `/api/vocab/stats` | Get vocabulary counts by status |
| GET | `/api/vocab/learning` | Get learning vocabulary |
| POST | `/api/vocab/import-anki` | Import from Anki export |

### Notes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes` | Get CLASS_NOTES.md content |
| PUT | `/api/notes` | Update CLASS_NOTES.md |

### Configuration
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config/anki-path` | Get Anki collection path |
| PUT | `/api/config/anki-path` | Set Anki collection path |
| POST | `/api/config/sync-anki` | Trigger manual Anki sync |

### Telemetry
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/telemetry/limit` | Get spending info |
| GET | `/api/telemetry/usage` | Get detailed usage stats |

---

## Database Schema

### VocabEntry
```sql
CREATE TABLE vocab_entries (
    id INTEGER PRIMARY KEY,
    kanji TEXT,                    -- Kanji representation (nullable)
    kana TEXT NOT NULL,            -- Kana reading
    meaning TEXT,                  -- English meaning
    pos TEXT,                      -- Part of speech
    status TEXT DEFAULT 'New',     -- New, Learning, Mature, Suspended
    source TEXT DEFAULT 'manual',  -- manual, anki, chat
    anki_note_id INTEGER,          -- Link to Anki note
    interval_days INTEGER,         -- Anki interval
    times_seen INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    last_seen_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### ChatSession
```sql
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,           -- e.g., session_1706384400000_abc123
    name TEXT,                     -- User-editable display name
    preview TEXT,                  -- Auto-generated from first message
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### ChatMessage
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,      -- Links to chat_sessions
    role TEXT NOT NULL,            -- user, assistant
    content TEXT NOT NULL,
    image_data TEXT,               -- Base64 encoded image
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP
);
```

### TokenLog
```sql
CREATE TABLE token_logs (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP
);
```

---

## Anki Integration

### Automatic Sync on Startup

When the server starts, it automatically:
1. Reads the Anki collection path from `config.json`
2. Copies the Anki database to avoid lock conflicts
3. Exports vocabulary and kanji to `anki_export.db`
4. Imports into the app database, updating existing entries

### Supported Card Types
- **Vocabulary**: Words with kanji, reading, meaning
- **Kanji**: Individual kanji with readings and meanings

### Card Status Mapping
| Anki Status | App Status |
|-------------|------------|
| queue < 0 | Suspended |
| type = 0 or queue = 0 | New |
| type = 1 or 3 | Learning |
| type = 2, interval >= 21 | Mature |
| type = 2, interval < 21 | Learning |

### Configuring Anki Path

The Anki collection path can be configured via:
1. **UI**: Click the gear icon in the Vocabulary sidebar
2. **API**: `PUT /api/config/anki-path`
3. **File**: Edit `backend/config.json`

Default path: `~/Library/Application Support/Anki2/User 1/collection.anki2`

---

## Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Anki (optional, for vocabulary sync)

### Setup

```bash
# Install frontend dependencies
npm install

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

### Running

```bash
# Start both frontend and backend
npm run dev

# Or separately:
npm run dev:frontend  # Vite on :5173
npm run dev:backend   # FastAPI on :8000
```

### Environment Variables

```env
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
GEMINI_MODEL=gemini-2.0-flash
DATABASE_URL=sqlite+aiosqlite:///./nihongo_dojo.db
CLASS_NOTES_PATH=../CLASS_NOTES.md
COST_LIMIT_WEEKLY=10.0
```

---

## Gemini Tool Calling

The AI tutor has access to these tools:

### save_vocab
Saves new vocabulary to the database when teaching.
```json
{
  "kanji": "食べる",
  "kana": "たべる",
  "meaning": "to eat",
  "pos": "verb"
}
```

### update_notes
Updates CLASS_NOTES.md with study notes.
```json
{
  "content": "# Today's Lesson\n- Learned て-form..."
}
```

### adjust_difficulty
Responds to user difficulty feedback.
```json
{
  "direction": "easier"
}
```

---

## Frontend Components

### Chat.tsx
Main chat interface with:
- Message history with markdown rendering
- Image attachment support (paste or file)
- Streaming response display
- Difficulty feedback buttons
- Tab switching (Chat / Notes)
- Spending progress bar

### VocabSidebar.tsx
Vocabulary browser with:
- **Chat Sessions section** at the top
- Learning/Mature/New sections
- Search functionality
- Vocabulary detail modal
- Anki settings modal (path config + manual sync)

### SessionList.tsx
Chat session management:
- "New Chat" button to create new sessions
- List of past conversations
- Click to switch between sessions
- Inline rename (click pencil icon)
- Delete with confirmation modal
- Auto-generated names from first message

### useChat Hook
Manages chat state:
- Accepts `sessionId` parameter
- Loads history when session changes
- Message history
- SSE stream handling
- Loading states
- Difficulty feedback

### useSessions Hook
Manages session state:
- List of all sessions
- Current session ID (persisted in localStorage)
- Create/switch/rename/delete sessions
- Auto-creates session on first use

---

## File Summary

| Category | Files | Purpose |
|----------|-------|---------|
| Frontend Source | 6 files | React components and hooks |
| Backend Source | 15 files | FastAPI app and services |
| Config Files | 6 files | Build and runtime config |
| Data Files | 2 files | Notes and Anki export |

---

## Recent Changes (v0.2.1)

- **Multi-Chat Sessions**: ChatGPT-style session management
  - New "Conversations" section in sidebar
  - Create new chats with "New Chat" button
  - Switch between conversations
  - Rename sessions (auto-named from first message)
  - Delete sessions with confirmation
  - Session history persists across browser restarts
- Chat history now persists in database and reloads on page refresh
- Fixed message ordering issue when loading history

## Changes (v0.2.0)

- Migrated from Tauri desktop app to browser-based web app
- Added FastAPI backend with async SQLAlchemy
- Integrated Google Gemini for AI chat with streaming
- Implemented automatic Anki sync on server startup
- Added configurable Anki path via UI settings
- Added manual sync button in Vocabulary sidebar
- Vocabulary sidebar now shows all statuses (Learning, Mature, New)
- Added spending limit tracking and progress bar

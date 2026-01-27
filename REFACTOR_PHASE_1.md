# Refactor Phase 1: Project Restructure & Backend Setup

## Summary

This phase removes the Tauri desktop app dependencies and establishes a new FastAPI backend architecture. The application is now a browser-based SPA that communicates with a Python backend.

## Changes Made

### 1. Removed Tauri Dependencies

**package.json:**
- Removed `@tauri-apps/api`
- Removed `@tauri-apps/plugin-shell`
- Removed `@tauri-apps/cli`
- Removed `"tauri": "tauri"` script
- Added `concurrently` for parallel dev servers
- Added `react-markdown` and `remark-gfm` for markdown rendering
- Updated scripts for new dev workflow

### 2. Updated Vite Configuration

**vite.config.ts:**
- Changed port from 1420 to 5173 (Vite default)
- Added proxy configuration for `/api` -> `localhost:8000`
- Removed Tauri-specific settings

### 3. Created FastAPI Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment configuration
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
│   │   ├── database.py         # SQLAlchemy async setup
│   │   └── models.py           # ORM models
│   │
│   └── services/
│       ├── __init__.py
│       ├── vocab_service.py    # Vocabulary business logic
│       ├── notes_service.py    # CLASS_NOTES.md operations
│       ├── anki_importer.py    # Anki deck import logic
│       └── token_tracker.py    # Usage tracking
│
├── requirements.txt
└── .env.example
```

### 4. New Development Scripts

```bash
npm run dev           # Start both frontend and backend
npm run dev:frontend  # Start only Vite dev server
npm run dev:backend   # Start only FastAPI server
```

## How to Test

### Prerequisites

1. Python 3.10+ installed
2. Node.js 18+ installed
3. A Gemini API key

### Setup Steps

1. **Install Python dependencies:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your GEMINI_API_KEY
   ```

3. **Install npm dependencies:**
   ```bash
   npm install
   ```

4. **Start the development servers:**
   ```bash
   npm run dev
   ```

5. **Open in browser:**
   Navigate to http://localhost:5173

### Test Endpoints

With the backend running (http://localhost:8000):

- **Health check:** `GET /api/health`
- **Vocabulary stats:** `GET /api/vocab/stats`
- **Notes:** `GET /api/notes`
- **Usage:** `GET /api/telemetry/usage?period=week`

### Test Chat (requires Gemini API key)

Send a message in the chat interface. The response should stream in real-time.

## Files to Delete

The following files can be safely deleted after verifying the refactor works:

- `src-tauri/` directory (entire Rust backend)
- `anki_export.db` (replaced by PostgreSQL/SQLite in backend)
- `collection.anki2` (keep in user's Anki folder)
- `temp_collection.anki2` (temporary file)
- `backend/server.py` (old stdin/stdout based server)
- `backend/chat_history.db` (old SQLite database)

## Architecture Notes

### Database

The application now uses SQLAlchemy with async support. By default, it uses SQLite (`nihongo_dojo.db`), but can be configured for PostgreSQL via the `DATABASE_URL` environment variable.

**Tables:**
- `vocab_entries` - Vocabulary words with status tracking
- `chat_history` - Chat messages by session
- `token_logs` - API usage and cost tracking

### API Design

All API endpoints are under `/api/`:
- `/api/chat/stream` - SSE streaming chat endpoint
- `/api/vocab/*` - Vocabulary CRUD operations
- `/api/notes/*` - Study notes management
- `/api/telemetry/*` - Usage statistics

### Streaming

Chat uses Server-Sent Events (SSE) for real-time streaming. The frontend reads the stream and updates the UI progressively.

Event types:
- `text` - Text content chunk
- `tool_call` - AI tool invocation
- `tool_result` - Tool execution result
- `usage` - Token usage metadata
- `done` - Stream complete
- `error` - Error occurred

## Known Limitations

1. **No authentication** - The app is designed for single-user local use
2. **SQLite concurrency** - For heavy use, consider switching to PostgreSQL
3. **No persistent sessions** - Chat history is per-session (stored in sessionStorage)

## Next Steps

- Phase 2: Database migration and Anki import
- Phase 3: Gemini integration refinements
- Phase 4: Frontend polish and features

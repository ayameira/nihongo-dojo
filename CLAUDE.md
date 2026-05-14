# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nihongo Dojo is a Japanese language learning application with an AI tutor powered by Google Gemini. It combines a React/TypeScript frontend with a FastAPI/Python backend, featuring vocabulary management synced from Anki, conversational tutoring with memory, and text-to-speech via VOICEVOX.

## Development Commands

```bash
# Run both frontend and backend together
npm run dev

# Run frontend only (Vite on port 5173)
npm run dev:frontend

# Run backend only (FastAPI on port 8000)
npm run dev:backend

# Build frontend
npm run build

# Frontend tests (Vitest)
npm test                    # Watch mode
npm run test:run            # Single run
npm run test:coverage       # With coverage

# Backend tests (pytest) - run from backend/
cd backend
./venv/bin/pytest                           # All tests
./venv/bin/pytest tests/test_api_chat.py    # Single file
./venv/bin/pytest -k "test_name"            # By name
./venv/bin/pytest --cov=app                 # With coverage
```

## Architecture

### Frontend (React + TypeScript + Tailwind)

- `src/App.tsx` - Main layout with resizable sidebars, session management, TTS voice selection
- `src/components/Chat.tsx` - Core chat interface with SSE streaming, image upload, tool call display
- `src/hooks/useChat.ts` - Chat logic, SSE stream handling, message state
- `src/hooks/useSessions.ts` - Session CRUD operations
- `src/utils/streamReader.ts` - SSE stream parsing for chat responses

### Backend (FastAPI + SQLAlchemy + SQLite)

**API Routers** (`backend/app/api/`):
- `chat.py` - SSE streaming endpoint at `/api/chat/stream`, handles Gemini tool loop
- `sessions.py` - Session CRUD at `/api/sessions`
- `vocab.py` - Vocabulary management at `/api/vocab`
- `media.py` - TTS audio serving at `/api/media`

**Core AI Components** (`backend/app/core/`):
- `gemini_client.py` - Gemini API wrapper with streaming and tool execution loop
- `context_builder.py` - Builds system prompt from student record, session summary, and vocab list
- `tools.py` - Tool definitions (update_student_record) and execution

**Services** (`backend/app/services/`):
- `memory_service.py` - Background conversation compaction to manage context length
- `anki_sync.py`, `anki_importer.py` - Anki collection sync on startup
- `tts_service.py` - VOICEVOX text-to-speech integration
- `notes_service.py` - Student record file operations

**Database Models** (`backend/app/db/models.py`):
- `VocabEntry` - Vocabulary with Anki sync
- `ChatMessage` - Chat history with `is_archived` flag for compaction
- `ChatSession` - Session metadata with `summary` for compacted history
- `TokenLog` - Usage and cost tracking

### Data Flow

1. User message hits `/api/chat/stream`
2. `context_builder.py` assembles: system prompt + student record + session summary + vocab + chat history
3. `gemini_client.py` streams response, executing tools in a loop if needed
4. Messages and token usage saved to SQLite
5. Background task checks if memory compaction needed

## Configuration

Settings in `.env` (see `backend/app/config.py`):
- `GEMINI_API_KEY` - Required for chat
- `GEMINI_MODEL` - Model selection (default: gemini-3-flash-preview)
- `VOICEVOX_URL` - TTS server URL
- Model pricing auto-configured from registry in `config.py`

## Key Patterns

- Frontend proxies `/api/*` to backend via Vite config
- Chat uses SSE with event types: `text`, `tool_call`, `tool_result`, `usage`, `done`, `error`
- Student record is a markdown file updated via Gemini tool calls
- Anki vocabulary syncs on startup from local collection
- Session sidebar state persisted to localStorage

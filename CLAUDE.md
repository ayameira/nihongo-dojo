# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nihongo Dojo is a language learning application with an AI tutor. It combines a React/TypeScript frontend with a FastAPI/Python backend, featuring vocabulary synced from Anki, grammar tracking, conversational tutoring with long-term memory, and text-to-speech.

Japanese is the flagship language; English and French are also supported. Each language is a separate "room" with its own vocabulary, grammar, sessions, and student facts (see `language_profiles/`).

The tutor is provider-neutral: Groq, Gemini, OpenRouter, and any OpenAI-compatible endpoint.

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

- `src/App.tsx` - Main layout with resizable sidebars, session management, language/voice selection
- `src/components/Chat.tsx` - Core chat interface with SSE streaming, image upload, tool call display
- `src/hooks/useChat.ts` - Chat logic, SSE stream handling, message state
- `src/hooks/useSessions.ts` - Session CRUD operations
- `src/hooks/useLanguageProfiles.ts` - Active language room and available profiles
- `src/utils/streamReader.ts` - SSE stream parsing for chat responses

### Backend (FastAPI + SQLAlchemy + SQLite)

**API Routers** (`backend/app/api/`), all mounted under `/api`:
- `chat.py` - SSE streaming endpoint at `/api/chat/stream`, runs the tool loop
- `sessions.py` - Session CRUD
- `vocab.py` - Vocabulary management
- `grammar.py` - Grammar library and status tracking
- `notes.py` - Student facts CRUD (despite the name, this is not file-based)
- `anki.py` - Anki setup wizard: introspect a collection, map fields, import
- `media.py` - TTS audio serving
- `telemetry.py` - Token usage and cost
- `config.py` - Runtime configuration

**Core AI Components** (`backend/app/core/`):
- `llm_client.py` - Provider-neutral entry point; picks the client for the configured provider
- `openai_compatible_client.py` - Groq / OpenRouter / any OpenAI-compatible endpoint
- `gemini_client.py` - Gemini API wrapper with streaming and tool execution
- `context_builder.py` - Builds the system prompt from student facts, session summary, vocab, and grammar
- `tools.py` - Tool definitions (`manage_student_facts`, `manage_grammar`) and execution
- `language_profiles/` - Per-language config: prompts, level scheme (JLPT/CEFR), grammar seed file

**Services** (`backend/app/services/`):
- `memory_service.py` - Background conversation compaction to manage context length
- `listener_service.py` - Background agent that extracts student facts from conversations
- `grammar_assessor.py` - Background grammar assessment
- `grammar_seeder.py` - Seeds the grammar table from a profile's seed file on first run
- `anki_introspect.py` - Read-only inspection of Anki collections (decks, note types, fields, suggested mappings) for the setup wizard
- `anki_importer.py` - Config-driven import: `import_deck_config`/`sync_all_decks` import vocab per `AnkiDeckConfig` using its field mapping
- `anki_sync.py` - Legacy hardcoded WaniKani export (still backing the old `/api/config/sync-anki` endpoint)
- `tts_service.py` - VOICEVOX text-to-speech (Japanese)
- `kokoro_tts.py` - Kokoro-FastAPI text-to-speech (English/French)

**Database Models** (`backend/app/db/models.py`):
- `VocabEntry` - Vocabulary; `deck_config_id` links Anki-sourced entries to their `AnkiDeckConfig`
- `AnkiDeckConfig` - A configured Anki deck source: collection path, deck name, field mapping, optional note filter
- `GrammarEntry` - Grammar point with level, status, and assessment counters
- `StudentFact` - Long-term memory about the student (goals, preferences, weak spots)
- `ChatMessage` (table `chat_history`) - Chat history with `is_archived` flag for compaction
- `ChatSession` - Session metadata with `summary` for compacted history
- `TokenLog` - Usage and cost tracking

Every user-scoped model carries a `language_code`, so data stays inside its language room.

### Data Flow

1. User message hits `/api/chat/stream`
2. `context_builder.py` assembles: system prompt + student facts + session summary + vocab + grammar + chat history
3. `llm_client.py` streams the response, executing tools in a loop if needed
4. Messages and token usage saved to SQLite
5. Background tasks check whether to compact memory, extract facts, or assess grammar

## Configuration

Settings in `backend/.env` (see `backend/app/config.py` and `.env.example`):
- `LLM_PROVIDER` - `groq` (default), `gemini`, `openrouter`, or `openai_compatible`
- `LLM_API_KEY` / `LLM_MODEL` / `LLM_BASE_URL` - Provider-neutral configuration
- `GEMINI_API_KEY` / `GEMINI_MODEL` - Used when the provider is `gemini`
- `VOICEVOX_URL` - Japanese TTS server URL
- `KOKORO_URL` - English/French TTS server URL (Kokoro-FastAPI)
- Model pricing auto-configured from the registry in `config.py`

## Key Patterns

- Frontend proxies `/api/*` to backend via Vite config
- Chat uses SSE with event types: `text`, `tool_call`, `tool_result`, `usage`, `done`, `error`
- Student memory lives in the `student_facts` table, written by the `manage_student_facts` tool and by the background listener agent. It is not a markdown file.
- The SQLite database is **not** in version control. It is created on first launch, and grammar self-seeds from a profile's seed file (Japanese uses `jlpt_grammar_list.txt`). Never commit it: it holds real chat history.
- Anki vocabulary syncs on startup via `sync_all_decks` over all enabled `AnkiDeckConfig` rows; users add/map decks through the Anki setup wizard (`AnkiSetupWizard.tsx`, `/api/anki/*`)
- Session sidebar state persisted to localStorage

## Deeper Documentation

- `docs/GRAMMAR_SYSTEM.md` - Grammar seeding, assessment, and status transitions
- `docs/STUDENT_FACTS_LOGIC.md` - How facts are extracted, deduplicated, and injected
- `docs/AI_INTERACTIONS.md` - Prompt and tool-call reference

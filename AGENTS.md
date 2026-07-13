# AGENTS.md

Guidance for coding agents (Codex, and others that read `AGENTS.md`) working in this repository.

The architecture notes, development commands, and conventions live in **[CLAUDE.md](CLAUDE.md)**. That file is the single source of truth for this repo; please read it and follow it.

This file used to duplicate that content and drifted out of date, so it now points at the canonical copy instead. If you update project guidance, update `CLAUDE.md`.

## Quick reference

```bash
npm run dev          # Frontend (5173) + backend (8000)
npm run test:run     # Frontend tests
cd backend && ./venv/bin/pytest   # Backend tests
```

Never commit `backend/nihongo_dojo.db`. It is the live database and contains real chat history; it is gitignored and is created automatically on first launch.

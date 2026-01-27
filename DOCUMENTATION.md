# Nihongo Dojo - Technical Documentation

**Version:** 0.1.0
**Package ID:** com.nihongodojo.app
**Status:** Early Development

---

## Overview

Nihongo Dojo is a personalized Japanese language tutor desktop application built with Tauri. It provides an interactive chat-based interface for Japanese language practice with the ability to reference and leverage users' existing Anki flashcard study data (particularly Wanikani decks and Japanese language decks).

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | ^18.2.0 | UI framework |
| TypeScript | ^5.0.0 | Type-safe JavaScript |
| Vite | ^5.0.0 | Build tool and dev server |
| Tailwind CSS | ^3.4.3 | Utility-first CSS framework |
| PostCSS | ^8.4.38 | CSS processing |

### Backend/Desktop
| Technology | Version | Purpose |
|------------|---------|---------|
| Tauri | ^2.0.0 | Desktop app framework (Rust backend + web frontend) |
| Rust | Edition 2021 | Backend runtime |
| tauri-plugin-shell | ^2.0.0 | Shell command execution |
| Serde | ^1 | JSON serialization |

### Python Utilities
| Library | Purpose |
|---------|---------|
| sqlite3 | Anki database integration |

---

## Project Structure

```
nihongo-dojo/
├── src/                          # React/TypeScript frontend
│   ├── main.tsx                  # React entry point
│   ├── App.tsx                   # Main application component
│   ├── components/
│   │   └── Chat.tsx              # Chat UI component (core interface)
│   ├── index.css                 # Tailwind CSS directives
│   └── vite-env.d.ts             # TypeScript environment definitions
│
├── src-tauri/                    # Rust backend (Tauri)
│   ├── src/
│   │   ├── main.rs               # Rust entry point
│   │   └── lib.rs                # Tauri application setup
│   ├── Cargo.toml                # Rust dependencies
│   ├── tauri.conf.json           # Tauri configuration
│   ├── capabilities/
│   │   └── default.json          # Security capabilities
│   └── build.rs                  # Rust build script
│
├── Configuration Files
│   ├── package.json              # Node.js dependencies & scripts
│   ├── vite.config.ts            # Vite build configuration
│   ├── tsconfig.json             # TypeScript configuration
│   ├── tsconfig.node.json        # TypeScript config for Vite
│   ├── tailwind.config.js        # Tailwind CSS configuration
│   └── postcss.config.js         # PostCSS configuration
│
├── Python Utilities
│   ├── export_anki_to_sqlite.py  # Anki data export script
│   ├── explore_anki.py           # Anki database exploration tool
│   └── DB-README.md              # Database documentation
│
├── Data Files
│   ├── anki_export.db            # Exported Anki data (SQLite)
│   └── collection.anki2          # Original Anki collection
│
├── index.html                    # HTML entry point
└── package-lock.json             # NPM dependency lock
```

---

## Component Documentation

### Frontend Components

#### `src/main.tsx` - React Entry Point
- Mounts the React application to the DOM root element
- Initializes React 18 StrictMode for development checks
- Loads global CSS styles

#### `src/App.tsx` - Main Application Component
**Purpose:** Orchestrates message flow between UI and backend

**Responsibilities:**
- Manages `blackboardContent` state for study notes
- Handles `onSendMessage` callback for backend integration
- Currently uses mock implementation with simulated delays

**State:**
```typescript
blackboardContent: string  // Content for the study notes "blackboard" view
```

**Props passed to Chat:**
```typescript
{
  onSendMessage: (message: string, image?: string) => Promise<string>;
  blackboardContent: string;
}
```

#### `src/components/Chat.tsx` - Chat Interface Component
**Purpose:** The core UI interface for user-LLM interaction

**Features:**
- Message history display with distinct user/assistant styling
- Image attachment support (file upload and clipboard paste)
- Tab-based navigation (Chat / Blackboard views)
- Loading states with vocabulary check and typing indicators
- Auto-scroll to latest messages

**Props Interface:**
```typescript
interface ChatProps {
  onSendMessage?: (message: string, image?: string) => Promise<string>;
  blackboardContent?: string;
}
```

**UI Characteristics:**
- Blue chat bubbles for user messages
- White bubbles with borders for assistant messages
- Responsive layout (max 80% width, centered)
- Two-phase loading animation (vocabulary check → typing indicator)

### Backend Components

#### `src-tauri/src/lib.rs` - Tauri Application Setup
- Initializes the Tauri application builder
- Loads the shell plugin for subprocess execution
- Generates application context from configuration
- Ready for Tauri command implementations

#### `src-tauri/src/main.rs` - Rust Entry Point
- Entry point that calls `run()` from lib.rs
- Windows-specific: Prevents additional console window in release builds

---

## Anki Data Integration

### Purpose
Extracts Japanese language study data from Anki (specifically Wanikani and Japanese decks) into a SQLite database accessible to the LLM backend.

### Export Process (`export_anki_to_sqlite.py`)
1. Copies live Anki collection to temporary database (avoids file locks)
2. Queries target decks matching patterns: `japanese%` or `%Wanikani%`
3. Extracts card data with review statistics

### Database Schema (`anki_export.db`)
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anki_note_id INTEGER,           -- Original Anki note ID
    deck_name TEXT,                 -- Source deck name
    model_name TEXT,                -- Card template/model name
    fields JSON,                    -- Full card field data
    tags TEXT,                      -- Comma-separated tags
    interval INTEGER,               -- Days until next review
    reps INTEGER,                   -- Number of repetitions
    lapses INTEGER,                 -- Number of lapses/failures
    status TEXT,                    -- Card status (see below)
    characters TEXT                 -- Main character/word
);
```

### Card Status Values
| Status | Condition |
|--------|-----------|
| `Suspended` | queue < 0 |
| `New` | type = 0 or queue = 0 |
| `Learning` | type = 1 or type = 3 |
| `Mature` | type = 2 and interval >= 21 |
| `Young` | type = 2 and interval < 21 |

### Field Extraction Priority
The `characters` field is extracted by looking for (in order):
1. 'Characters', 'vocab', 'katakana', 'Word'
2. 'Front', 'Frente', 'Texto'
3. First field as fallback

---

## Configuration

### Tauri Configuration (`tauri.conf.json`)
```json
{
  "productName": "nihongo-dojo",
  "version": "0.1.0",
  "identifier": "com.nihongodojo.app",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devUrl": "http://localhost:1420",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [{
      "title": "Nihongo Dojo",
      "width": 800,
      "height": 600
    }]
  }
}
```

### TypeScript Configuration (`tsconfig.json`)
- Target: ES2020
- Strict mode enabled
- JSX: react-jsx (new transform)
- Module resolution: bundler

### Vite Configuration (`vite.config.ts`)
- React plugin with Fast Refresh
- Development server on port 1420 (Tauri standard)
- Excludes `src-tauri` directory from file watching

---

## Development Workflow

### NPM Scripts
```bash
npm run dev        # Start Vite dev server on :1420
npm run build      # TypeScript compilation + Vite production build
npm run preview    # Preview production build
npm run tauri      # Access Tauri CLI commands
```

### Tauri Development
```bash
# Development with hot reload
npm run tauri dev

# Production build (creates native app bundle)
npm run tauri build
```

### Build Outputs
| Type | Location |
|------|----------|
| Frontend | `dist/` |
| Rust backend | `src-tauri/target/{debug,release}` |
| App bundle | `src-tauri/target/release/bundle/` |

---

## Security Configuration

### Tauri Capabilities (`src-tauri/capabilities/default.json`)
- `core:default` - Basic Tauri permissions
- `shell:allow-open` - Permission to open URLs/files via shell

### Notes
- CSP (Content Security Policy) is currently set to `null` (permissive)
- Future hardening recommended for production

---

## Current Development Status

### Completed
- React UI with Chat interface
- Message and image attachment handling
- Tab-based navigation (Chat / Blackboard)
- Loading state animations
- Tailwind CSS styling
- Tauri framework setup
- TypeScript configuration
- Anki data export system
- SQLite database schema for study data

### In Progress / Placeholder
- Backend message processing (currently mocked)
- LLM integration
- Tauri command definitions
- Blackboard persistence
- Vocabulary checking against Anki data
- Image processing (OCR / vision API)

---

## Future Implementation Notes

From `App.tsx`:
> "In the future, this will communicate with the backend via Tauri commands or sidecar"

### Recommended Next Steps
1. Implement Tauri commands in Rust backend for message processing
2. Integrate LLM API (OpenAI, Claude, or local model)
3. Connect frontend Chat component to backend commands
4. Implement vocabulary checking using Anki export database
5. Persist blackboard/notes to database
6. Implement image processing for Japanese text recognition
7. Add error handling and retry logic
8. Implement proper CSP for security

---

## File Summary

| Category | Count | Purpose |
|----------|-------|---------|
| Frontend Source | 4 files | React/TS components and styling |
| Backend Source | 3 files | Tauri/Rust setup |
| Config Files | 8 files | Build, TypeScript, CSS, Tauri config |
| Data Files | 2 files | Anki collections and exports |
| Utilities | 2 Python scripts | Anki data processing |

---

## Dependencies

### Production Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "@tauri-apps/api": "^2.0.0",
  "@tauri-apps/plugin-shell": "^2.0.0"
}
```

### Development Dependencies
```json
{
  "@tauri-apps/cli": "^2.0.0",
  "@types/node": "^20",
  "@types/react": "^18.2.15",
  "@types/react-dom": "^18.2.7",
  "@vitejs/plugin-react": "^4.0.3",
  "autoprefixer": "^10.4.19",
  "postcss": "^8.4.38",
  "tailwindcss": "^3.4.3",
  "typescript": "^5.0.2",
  "vite": "^5.0.0"
}
```

### Rust Dependencies (Cargo.toml)
```toml
[dependencies]
tauri = "2.0.0"
tauri-plugin-shell = "2.0.0"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

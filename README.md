# 🏯 Nihongo Dojo

A personalized Japanese language tutor powered by pluggable LLM providers like Gemini and Groq. Practice conversational Japanese with an AI sensei that adapts to your level, tracks your vocabulary from Anki, and remembers what you're working on.

**[Try the live demo →](https://nihongo-dojo.vercel.app)**

---

## ✨ Features

- **AI-Powered Chat** — Streaming conversations with Gemini, Groq, or another OpenAI-compatible provider
- **Anki Integration** — Automatically syncs your Anki flashcard collection so the tutor knows what you've been studying
- **Vocabulary Tracking** — Browse Learning / Mature / New words in the sidebar
- **Student Profile** — The AI remembers your goals, interests, and common mistakes
- **Grammar Library** — Track JLPT grammar points from N5 to N1
- **Text-to-Speech** — Hear Japanese pronunciation via VOICEVOX (optional) or browser TTS
- **Cost Dashboard** — Monitor your API spending with built-in weekly limits
- **Multi-Session Chat** — Create, rename, and switch between conversation threads

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Node.js** | 18+ | [Download](https://nodejs.org/) |
| **Python** | 3.11+ | [Download](https://www.python.org/downloads/) |
| **LLM API Key** | — | Groq is the fastest free trial path; Gemini is also supported |
| **Anki** | — | Optional. [Download](https://apps.ankiweb.net/) |
| **VOICEVOX** | — | Optional. For high-quality Japanese TTS. [Download](https://voicevox.hiroshiba.jp/) |

### 1. Clone the repository

```bash
git clone https://github.com/ayameira/nihongo-dojo.git
cd nihongo-dojo
```

### 2. Install frontend dependencies

```bash
npm install
```

### 3. Set up the backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
# macOS / Linux:
source venv/bin/activate
# Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
# Windows (CMD):
# venv\Scripts\activate.bat

pip install -r requirements.txt
```

### 4. Configure your environment

```bash
# Still inside backend/
cp .env.example .env
```

Open `backend/.env` in your editor and choose an LLM provider.

For the quickest free cloud trial, use Groq:

```env
LLM_PROVIDER=groq
LLM_API_KEY=your_groq_key_here
LLM_MODEL=llama-3.1-8b-instant
```

`LLM_BASE_URL` can stay blank for Groq; the backend fills in `https://api.groq.com/openai/v1`.

For Gemini, keep the default provider and set your Gemini key:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

> 💡 **Groq key:** Go to [Groq API Keys](https://console.groq.com/keys), sign in, create a key, and paste it as `LLM_API_KEY`.
>
> **Gemini key:** Go to [Google AI Studio](https://aistudio.google.com/apikey), sign in with your Google account, and click "Create API Key".

You do not need to delete your Gemini settings when trying Groq. Switch back later by setting `LLM_PROVIDER=gemini`.

If you want both Gemini and Groq to appear as usable choices in the in-app model selector, keep `GEMINI_API_KEY` set and add:

```env
GROQ_API_KEY=your_groq_key_here
```

### 5. Configure Anki path (optional)

If you use Anki, the app will auto-sync your Japanese vocabulary on startup. The default path is for macOS:

| OS | Default Anki Path |
|----|-------------------|
| **macOS** | `~/Library/Application Support/Anki2/User 1/collection.anki2` |
| **Windows** | `%APPDATA%\Anki2\User 1\collection.anki2` |
| **Linux** | `~/.local/share/Anki2/User 1/collection.anki2` |

To change the path, edit `ANKI_COLLECTION_PATH` in `backend/.env`, or configure it from the UI (gear icon in the Vocabulary sidebar).

### 6. Run the app

From the project root:

```bash
npm run dev
```

This starts both the frontend (http://localhost:5173) and the backend (http://localhost:8000) concurrently.

> 📝 If you don't have VOICEVOX installed, don't worry — the app will automatically fall back to your browser's built-in text-to-speech.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Backend** | FastAPI, SQLAlchemy (async), aiosqlite |
| **AI** | Gemini and OpenAI-compatible providers such as Groq/OpenRouter |
| **Database** | SQLite |
| **TTS** | VOICEVOX / Web Speech API |

---

## 📁 Project Structure

```
nihongo-dojo/
├── src/                    # React frontend
│   ├── components/         # Chat, VocabSidebar, SessionList, etc.
│   ├── hooks/              # useChat, useSessions, useTTS, etc.
│   └── utils/              # SSE stream parser
├── backend/                # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST endpoints (chat, vocab, notes, etc.)
│   │   ├── core/           # LLM clients, tools, context builder
│   │   ├── db/             # SQLAlchemy models and database setup
│   │   └── services/       # Anki sync, TTS, token tracking
│   ├── requirements.txt
│   └── .env.example
├── CLASS_NOTES.md           # Persistent study notes (read/updated by AI)
└── DOCUMENTATION.md         # Detailed technical documentation
```

For in-depth architecture details, API reference, and database schema, see [DOCUMENTATION.md](DOCUMENTATION.md).

---

## 🛠️ Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start frontend + backend + VOICEVOX together |
| `npm run dev:frontend` | Start only the Vite dev server |
| `npm run dev:backend` | Start only the FastAPI server |
| `npm run build` | Build the frontend for production |
| `npm run test` | Run frontend tests |

---

## 📄 License

This project is for personal and educational use.

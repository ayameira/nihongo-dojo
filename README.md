# Nihongo Dojo

Nihongo Dojo is a local Japanese practice app with an AI tutor, long-term learner memory, Anki vocabulary sync, JLPT grammar tracking, text-to-speech, and cost tracking.

It is built for people who want something more personal than a generic chatbot: the tutor can see what vocabulary and grammar you are studying, remember facts about your goals and preferences, and adapt future practice around that context.

[Try the live demo](https://nihongo-dojo-ten.vercel.app/)

## Should I Try It?

You might like Nihongo Dojo if:

- You already study Japanese with Anki and want your chat practice to use words you are actually learning.
- You want a tutor that can remember your goals, weak spots, interests, and preferred difficulty.
- You want quick Japanese conversation practice without building your own prompt every time.
- You care about seeing approximate API cost before it surprises you.

It is still a developer-run local app, not a polished commercial product. If you are comfortable following copy/paste setup steps, you should be fine. If you have never installed Node or Python before, the steps below are written to be as gentle as possible.

## What It Does

- Streaming AI chat for Japanese practice.
- Groq, Gemini, OpenRouter, and other OpenAI-compatible provider support.
- In-app model selector when multiple providers are configured.
- Student profile memory for goals, interests, preferences, and recurring mistakes.
- Anki deck setup wizard with deck selection and field mapping.
- Vocabulary sidebar with New, Learning, and Mature words.
- JLPT grammar library from N5 to N1, plus custom grammar points.
- Image upload for asking about screenshots, textbook pages, handwriting, or signs.
- Per-message audio playback with optional VOICEVOX voices.
- Multi-session chat history with automatic conversation summaries.
- Token and estimated cost dashboard with a weekly budget indicator.
- Light, dark, and system theme modes.

## The Fastest Setup: Groq

I personally like to use Gemini models (3.0 Pro and 3.0 Flash, depending on what I want to talk about), but if you don't have your own Gemini API key, Groq is the lowest-friction way to try the app. 

If you have a Google account, creating a Groq API key is usually a very quick web sign-in flow, and you face minimal setup without a credit card just to see whether the project is useful to you.

Groq limits, pricing, and account requirements can change, so check your Groq dashboard before heavy use. The default model in this repo is `llama-3.1-8b-instant`, which is fast and inexpensive for practice chat.

## Requirements

You need these:

| Requirement | Recommended | Why |
| --- | --- | --- |
| Node.js | 18 or newer | Runs the React frontend |
| Python | 3.11 or newer | Runs the FastAPI backend |
| One API key | Groq or Gemini | Powers the tutor |

Optional:

| Optional tool | What it adds |
| --- | --- |
| Anki | Lets the tutor use your real study vocabulary |
| VOICEVOX | Higher-quality Japanese voices |

## Install

### 1. Download the project

If you use Git:

```bash
git clone https://github.com/ayameira/nihongo-dojo.git
cd nihongo-dojo
```

If you do not use Git, download the project ZIP from GitHub, unzip it, and open a terminal in the `nihongo-dojo` folder.

### 2. Install the frontend

From the project root:

```bash
npm install
```

### 3. Install the backend

From the project root:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

macOS or Linux:

```bash
source venv/bin/activate
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Then install Python dependencies:

```bash
pip install -r requirements.txt
```

Go back to the project root:

```bash
cd ..
```

## Configure an API Key

### Option A: Groq, recommended for first try

1. Open [Groq API Keys](https://console.groq.com/keys).
2. Sign in. Google sign-in is the fastest path for many people.
3. Click `Create API Key`.
4. Copy the key.
5. In this project, copy the example environment file.

macOS or Linux:

```bash
cd backend
cp .env.example .env
cd ..
```

Windows PowerShell:

```powershell
cd backend
Copy-Item .env.example .env
cd ..
```

6. Open `backend/.env` in any text editor.
7. Set these values:

```env
LLM_PROVIDER=groq
LLM_API_KEY=paste_your_groq_key_here
LLM_MODEL=llama-3.1-8b-instant
LLM_BASE_URL=
```

You can leave `GEMINI_API_KEY` blank when using Groq.

### Option B: Gemini

Gemini also works. Google AI Studio has a free tier for getting started, while paid tiers are available for higher limits and production use.

1. Open [Google AI Studio API Keys](https://aistudio.google.com/apikey).
2. Create or choose an API key.
3. Copy `backend/.env.example` to `backend/.env` if you have not already.

macOS or Linux:

```bash
cd backend
cp .env.example .env
cd ..
```

Windows PowerShell:

```powershell
cd backend
Copy-Item .env.example .env
cd ..
```

4. Open `backend/.env` and set:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=paste_your_gemini_key_here
GEMINI_MODEL=gemini-3-flash-preview
```

## Run the App

From the project root:

```bash
npm run dev
```

This starts:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

Open `http://localhost:5173` in your browser.

The first time you chat, choose a configured model in the model selector if needed. If a model says `key needed`, the app can see that provider but does not have an API key for it yet.

## Optional: Connect Anki

You do not need Anki to use the chat tutor, but Anki is the feature that makes the app feel most useful to me. Seeing the vocabulary in different contexts improves memorization and recall, as well as boost confidence when I can understand and build real sentences.

1. Start Nihongo Dojo.
2. Open the Vocabulary sidebar.
3. Click the settings button.
4. Use the setup wizard to find your `collection.anki2` file.
5. Select one or more decks.
6. Confirm the field mapping for word, reading, meaning, and optional part of speech.
7. Sync.

Common Anki collection paths:

| OS | Typical path |
| --- | --- |
| macOS | `~/Library/Application Support/Anki2/User 1/collection.anki2` |
| Windows | `%APPDATA%\Anki2\User 1\collection.anki2` |
| Linux | `~/.local/share/Anki2/User 1/collection.anki2` |

Nihongo Dojo reads a temporary copy of your Anki collection. Your Anki deck is not modified.

## Optional: VOICEVOX

Text-to-speech has been a game changer in my own Japanese learning. Japanese study is usually the last thing I do in the day, and sometimes figuring out the readings is just too much for me, but I can still manage another half hour of practice if I can listen to the messages instead of reading.

The app works without VOICEVOX, but I highly recommend it. If VOICEVOX is not running, audio playback falls back to browser speech features where available.

To use VOICEVOX:

1. Install [VOICEVOX](https://voicevox.hiroshiba.jp/).
2. Start VOICEVOX before or after starting Nihongo Dojo.
3. Keep the default VOICEVOX server URL: `http://127.0.0.1:50021`.

On macOS, you can start the app and ask macOS to open VOICEVOX at the same time:

```bash
npm run dev:with-voicevox
```

On Windows or Linux, start VOICEVOX manually and use:

```bash
npm run dev
```

## Everyday Use

After setup, the normal flow is:

1. Run `npm run dev`.
2. Open `http://localhost:5173`.
3. Pick a model if you configured more than one provider.
4. Chat in Japanese, English, or a mix.
5. Use `Too Hard` or `Too Easy` after a tutor response to steer the next reply.
6. Open the Profile tab to review or edit what the tutor remembers.
7. Use the Grammar view to mark grammar as New, Learning, or Burned.
8. Check the Dashboard sidebar if you want to monitor usage cost.

## Configuration Reference

All backend settings live in `backend/.env`.

| Setting | Example | Notes |
| --- | --- | --- |
| `LLM_PROVIDER` | `groq` | Use `groq`, `gemini`, `openrouter`, or `openai_compatible` |
| `LLM_API_KEY` | `gsk_...` | Provider-neutral key, especially useful for Groq |
| `LLM_MODEL` | `llama-3.1-8b-instant` | Active model for non-Gemini providers |
| `LLM_BASE_URL` | blank | Leave blank for built-in Groq/OpenRouter defaults |
| `GROQ_API_KEY` | `gsk_...` | Optional, lets the in-app selector use Groq even if another provider is default |
| `GEMINI_API_KEY` | `...` | Gemini key |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | Gemini model |
| `OPENROUTER_API_KEY` | `sk-or-...` | Optional OpenRouter key |
| `DATABASE_URL` | `sqlite+aiosqlite:///./nihongo_dojo.db` | Local SQLite database by default |
| `ANKI_COLLECTION_PATH` | `~/Library/.../collection.anki2` | Optional legacy/direct Anki sync path |
| `AI_LOGS_PATH` | `./logs/ai_interactions` | Local request logs for debugging |
| `VOICEVOX_URL` | `http://127.0.0.1:50021` | Optional TTS server |
| `TTS_CACHE_DIR` | `./audio_cache` | Local generated audio cache |
| `DEFAULT_SPEAKER_ID` | `2` | Default VOICEVOX speaker/style ID |
| `COST_LIMIT_WEEKLY` | `10.0` | Weekly budget indicator in USD |

If you change `.env`, restart the backend.

## Commands

| Command | What it does |
| --- | --- |
| `npm run dev` | Starts frontend and backend |
| `npm run dev:with-voicevox` | Starts frontend, backend, and opens VOICEVOX on macOS |
| `npm run dev:frontend` | Starts only the Vite frontend |
| `npm run dev:backend` | Starts only the FastAPI backend |
| `npm run build` | Builds the frontend |
| `npm run test` | Runs frontend tests in watch mode |
| `npm run test:run` | Runs frontend tests once |
| `npm run test:coverage` | Runs frontend tests with coverage |

Backend tests:

```bash
cd backend
./venv/bin/pytest
```

On Windows, use:

```powershell
cd backend
.\venv\Scripts\pytest
```

## Project Structure

```text
nihongo-dojo/
|-- src/                    # React frontend
|   |-- components/         # Chat, sidebars, grammar, dashboard
|   |-- hooks/              # Chat/session/TTS/grammar hooks
|   `-- utils/              # SSE stream parsing
|-- backend/                # FastAPI backend
|   |-- app/
|   |   |-- api/            # Chat, vocab, sessions, config, grammar
|   |   |-- core/           # LLM clients, prompts, tools
|   |   |-- db/             # SQLAlchemy models and database setup
|   |   `-- services/       # Anki sync, memory, TTS, telemetry
|   |-- requirements.txt
|   `-- .env.example
|-- docs/                   # Deeper technical notes
`-- scripts/                # Developer helper scripts
```

## Troubleshooting

### `npm run dev` says the backend cannot start

Make sure you created the backend virtual environment and installed dependencies:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

On Windows, activate with `.\venv\Scripts\Activate.ps1`.

### Chat says the model needs a key

Open `backend/.env`, confirm the provider and key, then restart `npm run dev`.

For Groq, the minimum useful setup is:

```env
LLM_PROVIDER=groq
LLM_API_KEY=your_key_here
LLM_MODEL=llama-3.1-8b-instant
```

### The frontend opens but chat fails

Check that the backend is running at `http://localhost:8000/api/health`. If it is not, look at the backend terminal output for the specific error.

### The Anki wizard cannot find my deck

Use the file picker/path field to point directly at your Anki profile's `collection.anki2`. If you use multiple Anki profiles, the profile folder might not be called `User 1`.

### VOICEVOX shows an error

That is okay. VOICEVOX is optional. Start the VOICEVOX app if you want its voices, or ignore the warning and keep using the tutor.

### A port is already in use

The frontend uses port `5173`; the backend uses port `8000`. Stop the other process using that port, or change the port in the relevant dev command.

## Privacy and Cost Notes

- Your Anki collection is read locally and copied temporarily for import. Nihongo Dojo does not modify your Anki deck.
- Chat messages are sent to whichever LLM provider you configure.
- Student facts, sessions, grammar progress, vocabulary, and token logs are stored in the local SQLite database by default.
- Cost numbers are estimates based on the model registry in `backend/app/config.py`. Provider invoices and free-tier accounting may differ.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, SQLite |
| AI | Gemini plus OpenAI-compatible providers such as Groq and OpenRouter |
| Streaming | Server-sent events |
| TTS | VOICEVOX and browser speech fallback |

## License

Nihongo Dojo is licensed under the GNU Affero General Public License v3.0 only (`AGPL-3.0-only`). See [LICENSE](LICENSE) for the full text.

In plain language: you can use, study, share, and modify the project, but if you distribute it or run a modified network-hosted version, you need to make the corresponding source code available under the same license.

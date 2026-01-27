# Project: "Nihongo Dojo" (The Local Japanese Tutor)

### **1. Executive Summary**

"Nihongo Dojo" is a locally hosted, browser-based AI tutor designed specifically for a developer learning Japanese through immersion. It prioritizes **context persistence** (remembering what you are learning), **multimodal input** (analyzing manga panels), and **cost transparency** (tracking API spend). It is architected to run on macOS as a "one-click" application, leveraging the user's existing browser tools (Yomitan).

---
The app runs in Chrome/Safari/Firefox to allow the use of pop-up dictionary extensions.
---


### **2. Feature Deep Dive & Engineering Concerns**

#### **Feature A: The Chat**

* **Description:** Chat interface for user-LLM interaction. The user can type in Japanese or English and the LLM will respond in Japanese or English, where appropriate. The goal of the LLM is too keep the user immersed in Japanese as much as possible, always pushing the user exactly to the edge of their ability (Krashen's i+1 hypothesis).
* **Implementation:**
* **Frontend (React + Vite + Tailwind):**
* **State Management:** Use a customized `useChat` hook (or a lightweight store like Zustand) to manage the `messages` array. Each message object needs: `{ id, role: 'user' | 'assistant', content, timestamp, status: 'sending' | 'complete' }`.
* **Streaming Renderer:** Implement a `StreamReader` utility that consumes the chunked response from the backend. This is crucial for the "tutor" feel—waiting 5 seconds for a full block of text breaks the conversational flow.
* **DOM Hygiene for Yomitan:** Render the assistant's response using `react-markdown`.
* *Crucial Detail:* Configure the markdown renderer to output clean `<p>` and `<span>` tags. Avoid nested `<div>` soups or shadow DOMs, as these often block Yomitan (the dictionary extension) from detecting the text on hover.

* **"Edge of Ability" Feedback:** Add a small "Too Hard / Too Easy" toggle (invisible or subtle) next to assistant messages. If clicked, it sends a silent signal to the backend to inject the next prompt with a message to adjust the difficulty without overcompensating.
* **Auto-Scroll & Anchoring:** Implement a "sticky bottom" logic that pauses auto-scrolling if the user scrolls up to read previous corrections, but snaps back down when a new message arrives.

* **Backend (FastAPI + Gemini 3 flash):**
* **Endpoint:** `POST /api/chat/stream`. Accepts JSON `{ message: string, image_data?: string, session_id: string }`.
* **Context Orchestrator:** Before calling Gemini, the backend performs a "Context Look-Behind":
1. **Load Profile:** Reads `CLASS_NOTES.md` to get what the user has been learning so far.
2. **Fetch Vocab:** Queries Postgres for the last 50 "Learning" status words to inject into the prompt (priming the AI to use them).
3. **Truncate History:** Loads only the last 10-15 turns of conversation to keep tokens low, relying on `CLASS_NOTES.md` for older context.

* **The "i+1" System Prompt:**
* This is the core logic. The prompt must instruct Gemini to:
* *Default behavior:* Reply in Japanese.
* *Exception:* If the user asks a specific grammar question in English, explain in English, then immediately provide a Japanese example.

* **Streaming Response:** Use FastAPI's `StreamingResponse` to yield text chunks as they arrive from Gemini.
* **Async Database Logging:** While streaming (or immediately after), use `BackgroundTasks` to:
1. Save the message to the `chat_history` table.
2. Log token usage to `token_logs`.

#### **Feature B: `CLASS_NOTES.md` (The "Hard" Memory)**

* **Description:** A Markdown file stored on the local disk that acts as the "Brain's State." It is bi-directional: the AI reads it to know what to teach, and writes to it to update your progress.
* **Implementation:**
* **Structure:** Divided into sections: `## Current Focus`, `## Recent Corrections` (e.g., "User keeps confusing wa and ga with intransitive verbs"), `## Recent Vocab`.
* **Injection:** On every chat turn, the content of this file is injected into the System Prompt.
* **Updates:** The Agent uses a `update_notes(section, text)` tool to modify specific parts of the file based on the conversation.


* **⚠️ Concerns & Risks:**
* **Context Bloat:** If this file grows to 5,000 words, you are paying for those tokens on *every single message*. *Mitigation: Implement a "Archival" strategy where the Agent automatically moves old notes to an `ARCHIVE.md` file when the main notes exceed 1,000 tokens.*
* **Race Conditions:** If you manually edit the file in VS Code while the Agent is trying to write to it, you might lose data. *Mitigation: The React UI should display the file in a read-only state or use file-locking when the Agent is generating.*
* **Hallucination Loops:** If the Agent writes a confusing note (e.g., "User struggles with X" when you actually struggled with Y), it will reinforce that false belief forever. *Mitigation: You must have the ability to manually edit/prune the notes easily from the UI.*



#### **Feature C: The PostgreSQL Vocab "HUD"**

* **Description:** A persistent database of vocabulary that feeds a "Heads Up Display" in the UI.
* **Implementation:**
* **Schema:** `vocab_entries` table with status (`New`, `Learning`, `Mature`).
* **Tool Use:** The Agent has a `save_vocab(kanji, kana, meaning)` tool. When it explains a word, it calls this tool.
* **UI:** A sidebar list that updates in real-time. It uses a "Recall Trigger" logic: if a word in the list appears in the chat, it highlights it.
* **Config**: The app should offer the user a way to configure the origin of the cards: somewhere where they can input the path of the Anki collection to import the cards from.


* **⚠️ Concerns & Risks:**
* **Duplicate Data:** Handling "Taberu" vs "Tabemasu" vs "Tabete". If the DB isn't smart about lemmatization (root forms), you'll get 5 entries for the same verb. *Mitigation: Prompt the AI to always save the *dictionary form* and *reading*.*
* **Future Anki Conflicts:** When we eventually integrate Anki, managing conflicts between "Anki State" and "Postgres State" will be complex. *Mitigation: Treat Postgres as a "Staging Area." Words live here first, then get exported to Anki later.*



#### **Feature D: Cost & Token Telemetry**

* **Description:** A "Financial Dashboard" that keeps you honest about your Claude/Gemini usage.
* **Implementation:**
* **Middleware:** A Python wrapper around the API client that intercepts the `usage_metadata` field from every response.
* **Storage:** Logs every request to a `token_logs` table (timestamp, model, input_tokens, output_tokens, image_count).
* **Display:** A progress bar: "Spent $2.50 / Limit $10.00" weekly.


* **⚠️ Concerns & Risks:**
* **Pricing Drift:** API prices change. Hardcoding `$0.50/1M tokens` will eventually be wrong. *Mitigation: Store pricing as a configurable constant in a `.env` file.*


# Voice Language Partner

Practice a new language by talking out loud to an AI voice partner. Every conversation is transcribed live, graded by Gemini, and turned into a session report with scores, mistakes to review, and a personalized next step.

🔗 **Live demo:** https://voice-language-partner.onrender.com

Built for the AssemblyAI Voice Agents hackathon.

## How it works

1. Pick a target language, proficiency level, and practice mode (free conversation, scenario, tutor, vocabulary)
2. The backend builds an inline voice config for your session — system prompt, greeting, voice, and language codes tuned to your level and mode
3. The browser connects directly to the AssemblyAI Voice Agent websocket and applies the config via `session.update` — nothing stored, nothing to go stale
4. Talk out loud — audio streams browser ↔ agent over WebSocket (24kHz PCM16 in JSON), and every turn saves to Postgres
5. End the session and Gemini grades your performance: grammar, vocabulary, fluency, comprehension, target-language percentage
6. Your report includes per-category scores, mistakes with explanations, and a live "Coach says" recommendation — the dashboard tracks scores, progress per language, streaks, and recurring mistakes

## Features

- 🎙️ Real-time voice conversations (24kHz PCM16 streaming, barge-in support)
- 🧩 Per-session agent configuration — language, level, mode, and scenario shape every conversation
- 🌍 5 practice languages: Spanish, French, German, Italian, Portuguese
- 📊 Gemini-powered evaluation with per-category scores and feedback
- ✍️ Mistake tracking — every error saved with correction and explanation
- 📈 Dashboard: progress cards per language, session history, recent mistakes
- 🧠 "Coach says" — live recommendations generated from your session
- 🌗 Dark mode, responsive down to mobile

## Tech stack

| Layer | Tech |
|---|---|
| Voice | AssemblyAI Voice Agents API (inline websocket config, short-lived tokens) |
| Evaluation | Google Gemini 2.5 Flash (structured JSON output) |
| Backend | FastAPI, SQLAlchemy, PostgreSQL |
| Auth | JWT (bearer tokens) |
| Frontend | Vanilla HTML/CSS/JS — no framework |
| Hosting | Render |

## Setup

```bash
git clone https://github.com/<you>/voice-language-partner.git
cd voice-language-partner

python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a PostgreSQL database, then copy `.env.example` to `.env` and fill in:

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
JWT_SECRET=change-me
GEMINI_API_KEY=...        # https://aistudio.google.com/apikey
ASSEMBLYAI_API_KEY=...    # https://www.assemblyai.com/dashboard/api-keys
```

Run it:

```bash
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 — register, set up a session, and start talking. Interactive API docs at `/docs`.

## Project structure

```
api/v1/endpoints/   # auth, sessions, voice, languages, mistakes, evaluations
services/
  agent.py          # builds the inline voice-agent config per session
  gemini.py         # evaluation + recommendation generation
frontend/           # landing, auth, setup, practice, report, dashboard
models.py / crud.py # SQLAlchemy models + queries
```

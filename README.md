# LLM Chatbot

A modern, browser-based chatbot that connects to the **company LLM proxy** (`localhost:6655`).  
Supports **Anthropic, OpenAI, Gemini, and LiteLLM** — all through the corporate proxy, no direct cloud calls.

> **Repo:** https://github.com/skalmodiya/ChatBotUsingLLMProxy

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Your Machine                                 │
│                                                                     │
│  ┌──────────────────────────────┐                                   │
│  │      Browser (UI)            │                                   │
│  │   index.html                 │                                   │
│  │                              │                                   │
│  │  ┌──────────┐  ┌──────────┐  │                                   │
│  │  │ Chat     │  │ Compare  │  │  Vanilla JS · No framework        │
│  │  │ Mode     │  │ Mode     │  │  Dark-themed responsive UI        │
│  │  └────┬─────┘  └────┬─────┘  │                                   │
│  └───────┼─────────────┼────────┘                                   │
│          │  HTTP/SSE   │  (localhost only, no CORS issues)          │
│          ▼             ▼                                             │
│  ┌──────────────────────────────┐                                   │
│  │     Flask Server             │  server.py  · port 8080           │
│  │                              │                                   │
│  │  /api/models/<provider>  ────┼──► forwards GET  to proxy         │
│  │  /api/chat/<provider>    ────┼──► forwards POST to proxy         │
│  │  /api/sessions (CRUD)    ────┼──► reads/writes SQLite            │
│  │                              │                                   │
│  │  Injects:                    │                                   │
│  │   Authorization: Bearer key  │                                   │
│  │   anthropic-version header   │                                   │
│  └──────────┬───────────────────┘                                   │
│             │  Injects API Key · streams response back              │
│             ▼                                                        │
│  ┌──────────────────────────────┐                                   │
│  │   Company LLM Proxy          │  localhost:6655                   │
│  │                              │  (pre-installed on all laptops)   │
│  │  /anthropic/v1/*             │                                   │
│  │  /openai/v1/*                │                                   │
│  │  /gemini/*                   │                                   │
│  │  /litellm/v1/*               │                                   │
│  └──────────┬───────────────────┘                                   │
│             │  Authenticated · Policy-enforced                      │
└─────────────┼───────────────────────────────────────────────────────┘
              │
              ▼  (outbound, managed by company proxy)
┌─────────────────────────────────────────────────────────────────────┐
│                      Cloud LLM APIs                                 │
│                                                                     │
│   ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────────┐ │
│   │  Anthropic  │  │   OpenAI    │  │  Gemini  │  │  LiteLLM    │ │
│   │  Claude     │  │   GPT-4o    │  │  1.5 Pro │  │  (any model)│ │
│   └─────────────┘  └─────────────┘  └──────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Why this design?

| Decision | Reason |
|---|---|
| **Flask bridge** instead of calling proxy directly from browser | Browsers block cross-origin requests (`localhost:8080` → `localhost:6655`). Flask proxies all calls server-side, eliminating CORS issues. |
| **API key entered in UI, never in code** | Key is injected at request time by Flask. Never written to disk, never in git. |
| **Vanilla JS, no framework** | Zero install for the frontend — just one `index.html` file served by Flask. |
| **SQLite for history** | Lightweight, file-based, no database server needed. Each user gets their own local `chatbot.db`. |
| **SSE streaming passthrough** | Flask pipes the proxy's `text/event-stream` response straight to the browser — no buffering — so users see tokens appear in real time. |

### Request flow (single chat message)

```
User types message → [Browser]
  → POST /api/chat/anthropic          (to Flask, port 8080)
    → POST /anthropic/v1/messages     (Flask → proxy, port 6655)
      → streams SSE chunks back
    → Flask pipes chunks → Browser
  → Browser renders tokens live
  → On completion → POST /api/sessions/{id}/messages  (saves to SQLite)
```

### Data flow (compare mode)

```
User types prompt → [Browser]
  → Promise.allSettled([
      POST /api/chat/anthropic   ──► stream column 1
      POST /api/chat/openai      ──► stream column 2
      POST /api/chat/gemini      ──► stream column 3
    ])
  All fire in parallel — each column updates independently
  → On all complete → saved as one compare session in SQLite
```

---

## Features

| Feature | Details |
|---|---|
| Multi-provider | Anthropic · OpenAI · Gemini · LiteLLM |
| Auto model selection | Picks first model automatically when you enter your API key |
| Live streaming | See responses generate word-by-word |
| Response time | Shows how long each LLM took to respond |
| 🧠 Reasoning view | Collapsible thinking block for models that expose reasoning (o1, Claude extended thinking, etc.) |
| Provider badge | Every response shows which model produced it |
| ⚡ Compare mode | Send the same prompt to multiple LLMs simultaneously, side-by-side |
| Chat history | All sessions saved locally in SQLite — searchable sidebar |
| System prompt | Per-session system prompt support |
| Copy & stop | Copy any response · Stop generation mid-stream |

---

## Requirements

- **Python 3.9+** — [python.org/downloads](https://www.python.org/downloads/)
- **Company LLM proxy** running at `http://localhost:6655` (already installed on company laptops)
- **Your proxy API key** — enter it in the UI, never stored on disk

---

## Quick Start (Windows)

```
1. Clone this repo
   git clone https://github.com/skalmodiya/ChatBotUsingLLMProxy.git
   cd ChatBotUsingLLMProxy

2. Double-click  start.bat
   (or run it from a terminal)
```

That's it. The script will:
- Create a Python virtual environment automatically
- Install the two required packages (`flask`, `requests`)
- Start the server and open your browser at http://localhost:8080

**First time only:** enter your proxy API key in the API Key field. The key is saved in your browser session only — it is never written to disk or sent anywhere except `localhost:6655`.

---

## Quick Start (Mac / Linux)

```bash
git clone https://github.com/skalmodiya/ChatBotUsingLLMProxy.git
cd ChatBotUsingLLMProxy
chmod +x start.sh
./start.sh
```

---

## Manual Start (if scripts don't work)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
#    Windows:
venv\Scripts\activate
#    Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python server.py
```

Then open **http://localhost:8080** in your browser.

---

## How to Use

### Chat mode
1. Enter your **API Key** in the top-left field
2. Provider defaults to **Anthropic** and loads models automatically
3. Change provider → first model auto-selected
4. Type your message and press **Enter** (Shift+Enter for newline)
5. Click **Stop** to cancel mid-stream

### Compare mode
1. Click **⚡ Compare** in the header
2. Click **+ Add Model** → pick provider → pick model (up to 4)
3. Type a prompt → **⚡ Send to all** — all models stream simultaneously
4. Each column shows live output, response time, and a copy button

### History
- Past chats appear in the left sidebar grouped as **Chats** and **⚡ Compares**
- Click any session to restore it (provider + model + messages)
- Hover a session → **×** to delete it
- **Clear All History** in the sidebar footer wipes everything

### System prompt
- Click **▶ System prompt** below the controls to expand
- The prompt is stored per session

### Reasoning / Thinking
- For models that expose reasoning (Anthropic extended thinking, OpenAI o1/o3, DeepSeek-R1):  
  a **🧠 Thinking** section appears above the response — click to expand/collapse

---

## Project Structure

```
ChatBotUsingLLMProxy/
├── index.html      # Full UI (vanilla JS, no framework)
├── server.py       # Flask proxy bridge
├── db.py           # SQLite session/message store
├── requirements.txt
├── start.bat       # Windows one-click launcher
└── start.sh        # Mac/Linux one-click launcher
```

The SQLite database (`chatbot.db`) is created automatically on first run and ignored by git — each user has their own local history.

---

## Proxy Endpoints Used

| Provider | Models | Chat |
|---|---|---|
| Anthropic | `GET /anthropic/v1/models` | `POST /anthropic/v1/messages` |
| OpenAI | `GET /openai/v1/models` | `POST /openai/v1/chat/completions` |
| Gemini | `GET /gemini/v1beta/models` | `POST /gemini/v1beta/models/{model}:generateContent` |
| LiteLLM | `GET /litellm/v1/models` | `POST /litellm/v1/chat/completions` |

All requests go through `http://localhost:6655` — no direct cloud calls are made.

---

## Stopping the Server

- Press **Ctrl+C** in the terminal window running `server.py`
- Or close the terminal

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not found | Install Python 3.9+ and make sure it's in PATH |
| Port 8080 already in use | `start.bat` / `start.sh` kills the old process automatically. If manual: find and kill the process using port 8080 |
| `401 Unauthorized` when loading models | Your API key is wrong or expired — check with your admin |
| `502 Bad Gateway` | The company proxy at `localhost:6655` is not running |
| Models list is empty for a provider | That provider may not be enabled in your proxy config |

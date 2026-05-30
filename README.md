# LLM Chatbot

A modern, browser-based chatbot that connects to the **company LLM proxy** (`localhost:6655`).  
Supports **Anthropic, OpenAI, Gemini, and LiteLLM** — all through the corporate proxy, no direct cloud calls.

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
   git clone <repo-url>
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
git clone <repo-url>
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

The SQLite database (`chatbot.db`) is created automatically on first run and ignored by git.

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

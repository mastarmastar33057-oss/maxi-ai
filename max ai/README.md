# Max AI

A single-page, multimodal AI chat app powered by Google Gemini — chat, image
generation, voice input/output, and a built-in Senior Data Analyst mode that
turns an imported CSV/JSON file into charts, stats, and a written report.

## What's in this build

- **Multi-provider chat** — pick Google Gemini, OpenAI, or Anthropic Claude in Settings, using your own API key for whichever you choose. Voice, image generation, video generation, search grounding, and CSV dashboards remain Gemini-only (they depend on Gemini-specific models/tools).
- **Chat** with 8 selectable personas, including a Senior Data Analyst, a Senior Software Architect, and an App Builder.
- **Image generation** — type `/image <prompt>`.
- **Video generation** — type `/video <prompt>` to render a short clip with Gemini's Veo model. This kicks off a long-running job and polls it every ~10s (renders typically take 1-3 minutes); the finished clip plays inline with a download button. Requires a Google account/API key with Veo access — if the account doesn't have it enabled, the app surfaces that clearly instead of pretending it worked.
- **Coding** — the "Senior Software Architect" persona reviews/refactors/debugs code with tests; the "App Builder" persona generates a complete, runnable single-file HTML/CSS/JS app with an inline "▶ Preview in new tab" and "⬇ Download .html" button, so it's an actual working artifact, not just a code block.
- **AI Senior Data Analyst dashboard** — import a CSV/XLSX/JSON file to get auto-generated charts, summary stat cards (row/column counts, types, outliers, correlations), a structured written report (Overview → Key Insights → Data Quality Notes → Recommendations → Suggested Next Questions), one-click follow-up questions, and CSV/PDF export of the dashboard.
- **Voice input** (microphone button, browser speech recognition) and
  **voice output** ("Read Aloud" on any response, via Gemini TTS).
- **File import** (📎 for images, the upload icon for data files) —
  CSV / TSV / JSON build an instant dashboard: auto-generated charts, summary
  stat cards, and an AI-written analyst report. TXT/MD files are attached as
  plain-text context for the model to read.
- **Copy** and **Download** buttons on every AI response.
- **Search grounding** toggle with an expandable **source ledger** — numbered, inspectable list of every page the search returned.
- **Task Mode** (header toggle) — for complex requests, Max first writes a 3-5 step plan, shows it as a live checklist, then answers and self-verifies. This is a prompting technique, not background agents; the UI says so.
- **Inline app execution** — App Builder output gets a "▶ Run inline" button that runs the generated app in a sandboxed `<iframe>` right in the chat (no `allow-same-origin`, so it can't read your keys or history).
- **Command palette** — `Ctrl+K` / `Cmd+K` for New Chat, New Analysis, Generate Image/Video, Voice, toggles, Export, and Settings, with arrow-key navigation.
- **Capability matrix** in Settings — shows what's actually live, partial, needs-a-key, or off given your current configuration, so you find out before a request fails instead of after.
- **Per-message metrics** — token count, wall-clock latency, and a rough cost estimate from public list prices (clearly labeled as an estimate, not a bill).
- **Dataset memory** — after a CSV dashboard is built, its profile stays attached to that chat, so follow-up questions about the data work without re-uploading the file.
- **Persistent media** — generated videos are stored in IndexedDB (not `localStorage`), so they survive a page reload instead of dying with the tab's blob URLs.
- Chat history, personas, and settings persist in the browser (`localStorage`); generated video bytes persist in IndexedDB.

## Two ways to run it

### 1. Standalone (no install, no server)

Just open `max_ai.html` directly in a browser. Click the settings (⚙️) icon
and paste a Gemini API key — get one free at
[Google AI Studio](https://aistudio.google.com/apikey). The key is stored
only in your browser's local storage and is sent straight to Google; it
never passes through any server of ours.

This is the simplest option, but the key does live in the browser, so don't
use this mode on a shared/public computer, and don't publish the page with
your key already filled in.

### 2. With the backend proxy (recommended if you'll deploy this publicly)

Running `app.py` keeps your API key on the server instead of in the browser.

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"      # Windows: set GEMINI_API_KEY=your-key-here
export OPENAI_API_KEY="your-key-here"      # optional, only if you'll use OpenAI
export ANTHROPIC_API_KEY="your-key-here"   # optional, only if you'll use Claude
python app.py
```

Open `http://localhost:5000`, go to Settings, pick your provider, and check
**"Use secure backend proxy."** From then on, requests go to `/api/chat`
(Gemini), `/api/openai`, or `/api/anthropic` on your own server instead of
directly to the provider, and the matching Settings API-key field is not
needed.

**Anthropic note:** Claude's API isn't designed for direct browser calls.
Standalone mode adds a special opt-in header to attempt it anyway (useful
for quick local testing), but the backend proxy is the reliable way to use
Claude models here.

**OpenAI note:** OpenAI's API commonly blocks direct browser requests via
CORS. If standalone mode fails with a network error, switch on the backend
proxy.

## Endpoints (backend mode)

| Route              | Purpose                                        |
|--------------------|-------------------------------------------------|
| `/`                | Serves `max_ai.html`                            |
| `/health`          | Health check — confirms the key is configured   |
| `/api/chat`        | Proxies text/vision/search-grounded chat        |
| `/api/image`       | Proxies image generation                        |
| `/api/tts`         | Proxies text-to-speech                          |
| `/api/video`       | Starts a Veo video-generation job (long-running) |
| `/api/video/poll`  | Polls a video job's status by operation name    |
| `/api/video/fetch` | Streams back the finished video's bytes         |
| `/api/openai`      | Proxies to OpenAI Chat Completions (if configured) |
| `/api/anthropic`   | Proxies to Anthropic Messages API (if configured)  |

`/api/chat`, `/api/image`, and `/api/tts` expect `{ "model": "...", "payload": {...} }` and
return Gemini's response as-is. `/api/video` expects the same shape and returns
Google's operation object; `/api/video/poll` expects `{ "operationName": "..." }`;
`/api/video/fetch` expects `{ "fileUri": "..." }`. All routes return a JSON
`{ "error": { "message": "..." } }` on failure — 502 for upstream/network issues,
504 for timeouts, 500 for misconfiguration such as a missing key.

**Video generation note:** Veo access is a separate capability from text/image
Gemini access — if your key/account doesn't have it enabled, `/api/video` will
return whatever error Google's API sends back (surfaced verbatim in the UI)
rather than a fake success.

## Deployment

- **Frontend only**: any static host (Vercel, Netlify, GitHub Pages) — it's
  a single HTML file.
- **With backend**: deploy `app.py` anywhere that runs Python (Render,
  Railway, a VM, etc.), set `GEMINI_API_KEY` as an environment variable, and
  point the frontend's backend-proxy toggle at that server if it's not
  serving the HTML itself. For production, run it behind gunicorn:
  `gunicorn -w 2 -b 0.0.0.0:5000 app:app`.

## Troubleshooting

- **Nothing happens when you send a message** — open Settings and confirm
  either an API key is set (standalone mode) or the backend proxy is
  running and reachable (backend mode).
- **"GEMINI_API_KEY is not set on the server"** — you enabled the backend
  proxy but forgot to export the environment variable before starting
  `app.py`.
- **Voice input button is greyed out** — your browser doesn't support the
  Web Speech API. It works in Chrome and Edge; Firefox and Safari have
  limited or no support.
- **502 / timeout errors** — usually a transient issue reaching Google's
  API; the app retries are not automatic, just resend the message.
- **Logs** — backend requests and errors are written to `logs/app.log` with
  timestamps.

## Security notes

- Rotate any API key that has ever been pasted into a chat, email, or
  screenshot — treat it as compromised the moment it's shared anywhere
  outside a secrets manager or environment variable.
- The standalone mode's key lives in browser local storage — fine for
  personal/local use, not recommended for a publicly shared deployment.
- The backend proxy never logs the API key itself, only request outcomes.

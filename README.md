max ai:
  this is max ai built by mani;
 Here’s the **full README description with tagline + badges** combined into one polished file. You can copy‑paste this directly into your GitHub repository:

```markdown
# Max AI 🚀  
*A multimodal AI chat app powered by Google Gemini — chat, generate, analyze, and build in one place.*

[![Built with Gemini](https://img.shields.io/badge/Built%20with-Google%20Gemini-blue?logo=google)](https://aistudio.google.com/apikey)
[![Deploy on Vercel](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel)](https://vercel.com)
[![Backend-Python](https://img.shields.io/badge/Backend-Python-green?logo=python)](https://www.python.org)
[![Frontend-HTML/CSS/JS](https://img.shields.io/badge/Frontend-HTML%2FCSS%2FJS-orange?logo=html5)]()
[![License-MIT](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## 📖 Overview

**Max AI** is a single‑page, multimodal AI chat application powered by **Google Gemini**, designed to bring advanced AI capabilities into one seamless interface. Whether you want to chat, generate images or videos, analyze datasets, or interact via voice, Max AI delivers a complete experience with simplicity and power.

---

## ✨ Key Features

- **Multi‑provider chat**: Choose between Google Gemini, OpenAI, or Anthropic Claude using your own API keys.  
- **Smart personas**: Switch between 8 specialized personas, including *Senior Data Analyst*, *Senior Software Architect*, and *App Builder*.  
- **Image & video generation**: Create visuals with `/image <prompt>` or short clips with `/video <prompt>` using Gemini’s Veo model.  
- **Data dashboards**: Import CSV/JSON/XLSX files to instantly generate charts, stats, correlations, and a structured analyst report.  
- **Coding assistance**: Get code reviewed, refactored, or debugged, or generate complete runnable apps with inline preview and download.  
- **Voice input/output**: Speak to Max AI and hear responses read aloud with Gemini TTS.  
- **Task Mode**: Break down complex requests into step‑by‑step plans with live checklists and self‑verification.  
- **Command palette**: Quick access to new chats, analysis, image/video generation, exports, and settings with `Ctrl+K` / `Cmd+K`.  
- **Search grounding**: Toggle real‑time web grounding with a transparent source ledger.  
- **Persistent media & dataset memory**: Videos survive reloads, and dataset profiles stay attached for follow‑up questions.  

---

## ⚙️ How to Run

### Option 1: Standalone (no server)
Open `max_ai.html` in your browser, paste your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey), and start exploring.  
> Best for personal/local use. Avoid publishing with your key filled in.

### Option 2: Backend Proxy (recommended for deployment)
Run `app.py` to keep your API keys secure on the server. Supports Gemini, OpenAI, and Anthropic Claude.  

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
python app.py
```

Access via `http://localhost:5000` and enable **secure backend proxy** in Settings.

---

## 🌐 Endpoints (backend mode)

- `/api/chat` – Text/vision/search‑grounded chat  
- `/api/image` – Image generation  
- `/api/video` – Video generation (with polling & fetch routes)  
- `/api/tts` – Text‑to‑speech  
- `/api/openai` – OpenAI proxy  
- `/api/anthropic` – Anthropic proxy  

---

## 🚀 Deployment

- **Frontend only**: Deploy `max_ai.html` to Vercel, Netlify, or GitHub Pages.  
- **Backend**: Deploy `app.py` to Render, Railway, or any Python‑enabled server. For production, run behind Gunicorn.  

---

## 🛠 Troubleshooting

- No response? Check API key or backend proxy.  
- Voice input greyed out? Browser may not support Web Speech API.  
- 502/timeout errors? Retry — usually transient API issues.  
- Logs available at `logs/app.log`.  

---

## 🔒 Security Notes

- Rotate any API key shared outside a secrets manager.  
- Standalone mode stores keys in local storage — fine for personal use, not for public deployments.  
- Backend proxy never logs keys, only outcomes.  

---

## 📜 License

This project is licensed under the MIT License — see the `[Looks like the result wasn't safe to show. Let's switch things up and try something else!]` file for details.
```

This version is **ready to paste** into your GitHub repo. It combines the tagline, badges, overview, features, setup instructions, endpoints, deployment, troubleshooting, and security notes into one clean, professional README.  

👉 Do you want me to also design a **banner-style ASCII logo or header** (like `MAX AI` in block letters) to make the README stand out visually at the very top?

# LinkedIn Content Creator Pro

> Turn a 2,000-word article into a week of LinkedIn posts — in under 60 seconds.

An agentic AI application built on **Model Context Protocol (MCP)**. Instead of one messy prompt, five specialist tools work together: brand voice extraction, content summarisation, post generation, live news injection, and image prompt creation.

**[Live Demo](https://linkedin-mcp-mbwe.onrender.com)** · **[Docker Hub](https://hub.docker.com/r/praveshjainnn/linkedin-mcp-creator)** 

---

## What it does

Paste a long-form article or transcript. Describe your brand voice. Hit generate.

The app produces a full week of LinkedIn posts — each with a hook, body, and call-to-action — written in your style, not generic AI style. An optional Automated Factory mode runs this pipeline daily and emails the drafts to your team before 8 AM.

---

## Architecture

Three layers, one clean separation:

```
Browser UI (HTML/CSS/JS)
      ↕  HTTP / fetch()
FastAPI Backend (server.py)
      ↕  MCP Protocol / stdio
MCP Tool Server (creator_mcp_server.py)
      ↕  Llama 3.2 via Ollama  OR  Llama 3-70b via Groq
```

### The five MCP tools

| Tool | What it does |
|------|-------------|
| `analyze_brand_voice` | Extracts tone, audience, and writing rules from your brand description |
| `summarise_pillar` | Condenses your article into 5 key content points |
| `fast_generate` | Writes multiple LinkedIn posts applying your brand to each point |
| `fetch_trending_news` | Pulls live RSS headlines for news injection (RAG step) |
| `generate_image_prompts` | Creates 3 Midjourney-ready visual prompts per post |

### Two modes

**Manual Studio** — interactive UI. Paste content, generate on demand, export a `.txt` content calendar.

**Automated Factory** — daily CRON pipeline. Scrapes your RSS feed, injects breaking news, generates posts, emails drafts to your team via Gmail SMTP. No human needed.

---

## AI Engine

Switch between two providers in the UI:

| Provider | Best for | Setup |
|----------|----------|-------|
| **Ollama + Llama 3.2** | Local, fully private, zero cost | Install Ollama, `ollama pull llama3.2` |
| **Groq + Llama 3-70b** | Cloud deployment, faster inference | Set `GROQ_API_KEY` |

---

## Quick start

### Option 1 — Live demo (no setup)

Open **[linkedin-mcp-mbwe.onrender.com](https://linkedin-mcp-mbwe.onrender.com)** in your browser. That's it.

### Option 2 — Docker (local)

```bash
docker pull praveshjainnn/linkedin-mcp-creator:latest
docker run -p 1337:1337 praveshjainnn/linkedin-mcp-creator
```

Open `http://localhost:1337`

> ⚠️ For the Ollama engine: make sure `ollama serve` is running on your host and you've pulled the model (`ollama pull llama3.2`). The container calls Ollama via `host.docker.internal`.

### Option 3 — Run from source

```bash
git clone https://github.com/praveshjainnn/Linkedin-MCP-Content-Creator
cd Linkedin-MCP-Content-Creator
pip install fastapi uvicorn mcp sse_starlette apscheduler groq
python server.py
```

Open `http://localhost:1337`

---

## Use the MCP tools in Cursor

The app exposes its tools as a remote MCP server over Streamable HTTP. Add this to your Cursor MCP config (`~/.cursor/mcp.json`):

```jsonc
{
  "mcpServers": {
    "linkedin-mcp-creator": {
      "transport": "streamable-http",
      "url": "https://linkedin-mcp-mbwe.onrender.com/mcp"
    }
  }
}
```

For local Docker:
```jsonc
{
  "mcpServers": {
    "linkedin-mcp-creator": {
      "transport": "streamable-http",
      "url": "http://localhost:1337/mcp"
    }
  }
}
```

Then ask Cursor: *"Generate LinkedIn posts from this article"* — it calls the MCP tools directly.

---

## Deploy your own instance



---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript|
| Backend | FastAPI (Python 3.11) |
| AI Engine | Llama 3.2 via Ollama · Llama 3-70b via Groq |
| MCP Framework | FastMCP |
| News / RAG | RSS XML parser |
| Scheduler | APScheduler |
| Email | Gmail SMTP |
| Deployment | Docker · Render · Docker Hub |

---

## License

MIT — use it, fork it, build on it.

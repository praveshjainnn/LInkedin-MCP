# LinkedIn Content Creator Pro

An agentic AI application that genuinely automates content repurposing. Turn long-form "pillar" content—like articles, transcripts, and blog posts—into a ready-to-publish pack of LinkedIn posts, completely locally.

## 🚀 The Stack
- **AI Engine:** Local Llama 3.2 via Ollama (100% free and private—no API keys required!)
- **Agent Framework:** Model Context Protocol (MCP) orchestrating multi-step generation tasks. 
- **Backend/API:** FastAPI (Python) with APScheduler for automated CRON tasks.
- **Frontend:** Custom HTML/CSS/JS (Glassmorphic dark UI)

## 🎯 Architecture: Manual vs Factory

This project features two distinct modes of operation to demonstrate the difference between a simple "chat wrapper" and a true "agentic workflow".

### 1. Manual Studio 📝
Users paste their brand description and their long-form article into the UI. The application runs a local `llama3.2` model via MCP to:
1. Analyze and extract the exact Brand Voice parameters.
2. Summarize the Pillar Content into actionable bullet points.
3. Generate multiple LinkedIn drafts applying the exact Brand Voice to the extracted points.

### 2. Automated Factory 🏭
A background simulation of a true Productivity Engine. When triggered (either via API or its daily APScheduler CRON job), the application:
1. Reaches out to the web and scrapes the newest article from its target RSS feed.
2. Runs a **RAG (Retrieval-Augmented Generation)** step, reaching out to global tech news feeds to fetch live breaking news.
3. Automatically synthesizes the daily breaking news with the RSS article, tying timeless content to today's news cycle. 
4. Drafts a beautifully formatted HTML email containing the final generated LinkedIn posts and securely dispatches it to the marketing manager via SMTP.

## 🖥️ How to Run Locally

### Prerequisites
1. Install [Ollama](https://ollama.com/) on your machine.
2. Open your terminal and run `ollama pull llama3.2` to download the free LLM model to your local machine.

### Start the Server
1. Clone the repository.
2. Install requirements (e.g., `pip install fastapi uvicorn mcp sse_starlette apscheduler`).
3. Run the FastAPI server:
   ```bash
   python server.py
   ```
4. Open your browser and navigate to `http://localhost:1337` to view the UI.

## ☁️ Deploy online (end users do not install Docker)

**Docker is only for whoever builds/runs the server** (you or a cloud build pipeline). **Visitors only open your site in a browser** — they never install Docker or Python.

Typical flow:

1. Push this repo to **GitHub** (or similar).
2. On a host such as **[Railway](https://railway.app)**, **[Render](https://render.com)**, **[Fly.io](https://fly.io)**, or **[Google Cloud Run](https://cloud.google.com/run)**, create a **Web Service** from the repo using the included **`Dockerfile`**, or use their **“Docker”** / **“Buildpack”** option.
3. Set the service **port** to **1337** (or whatever the platform maps to **HTTPS** publicly).
4. Add **environment variables** on the host (not in git):
   - **`GROQ_API_KEY`** — recommended for cloud: there is usually **no Ollama** on the server; Groq powers generation when users pick **Groq** in the UI (or you rely on this key when the UI field is empty).
   - **`MCP_CURSOR_TOKEN`** — random secret; required if you expose **`/mcp`** on the public internet. Users put `Authorization: Bearer <token>` in Cursor’s MCP config.
   - **`GEMINI_API_KEY`** — only if you use features that read it.

5. Share **`https://your-domain.com`** — that is all end users need for the **web app**.

**Ollama in the cloud:** A default PaaS container does **not** run Ollama. For local-style Ollama you would need a **GPU VM** or keep Ollama on your laptop and run the app locally. For most public deployments, **Groq** (or another cloud API) is the practical choice.

### Deploy on [Render](https://render.com)

1. Push this repository to **GitHub** (or GitLab / Bitbucket connected to Render).
2. In the [Render Dashboard](https://dashboard.render.com): **New** → **Web Service** → connect the repo.
3. Configure the service:
   - **Runtime:** **Docker** (Render will use the root **`Dockerfile`**).
   - **Instance type:** choose a plan (free tier is available but **spins down after idle**; first request can be slow).
   - Render injects **`PORT`** automatically; this project’s image listens on **`$PORT`** (defaults to **1337** locally).
4. **Environment** → **Environment Variables** (add at least):
   | Variable | Purpose |
   |----------|---------|
   | `GROQ_API_KEY` | **Required on Render** for Groq (set in dashboard; users can still paste a key in the UI). |
   | `DEFAULT_LLM_PROVIDER` | Set to **`groq`** so API defaults and the **browser** guidance match cloud (no Ollama). Strongly recommended on Render. |
   | `PIPELINE_LLM_PROVIDER` | Optional override for the **8:00 AM** cron only; if unset, cron uses `DEFAULT_LLM_PROVIDER` then **`ollama`**. |
   | `MCP_CURSOR_TOKEN` | Long random string if you use **Cursor MCP** against `https://your-service.onrender.com/mcp`. |
   | `REQUIRE_MCP_AUTH` | Optional. If set to `true`, the server enforces `Authorization: Bearer MCP_CURSOR_TOKEN` for `/mcp`. Leave unset/false for Claude testing (no custom headers). |
5. **Create Web Service**. Wait for the build and deploy, then open the **`.onrender.com`** URL Render assigns.

**After deploy:** Share `https://<your-service-name>.onrender.com` — visitors only need a browser. For Cursor MCP, use `https://<your-service-name>.onrender.com/mcp` with `transport`: `streamable-http` and the Bearer token if you set `MCP_CURSOR_TOKEN`.

If remote MCP returned **HTTP 421**, that was DNS-rebinding protection blocking non-localhost `Host` headers; the included `creator_mcp_server.py` disables that for public HTTPS deploys—redeploy the latest image.

---

## 🐳 Docker Deployment

This project is fully containerized and can be run with Docker — no local Python or pip setup required **on the machine where you build/run the image** (still not required for people who only use your deployed URL).

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- [Ollama](https://ollama.com/) running on your **host machine** (the container calls it via `host.docker.internal`).

### 1. Build the Image
```bash
docker build -t praveshjainnn/linkedin-mcp-creator .
```

### 2. Run the Container

docker run -p 1337:1337 praveshjainnn/linkedin-mcp-creator
Open your browser → **http://localhost:1337**

### Cursor (remote MCP)

The app exposes **Streamable HTTP** MCP at **`/mcp/`** (trailing slash matters).

1. Run the server (or container) so port **1337** is reachable.
2. In Cursor: **Settings → MCP** (or edit `%USERPROFILE%\.cursor\mcp.json`) with **`transport`: `"streamable-http"`** and URL:
   - Local: `http://127.0.0.1:1337/mcp` or `http://127.0.0.1:1337/mcp/` (both work; Cursor often uses no trailing slash)
   - Deployed: `https://your-domain.com/mcp` (same path; use **`MCP_CURSOR_TOKEN`** + Bearer header in production)
3. Optional: set env **`MCP_CURSOR_TOKEN`** to a secret string when deploying publicly, then in Cursor add header **`Authorization`**: `Bearer <same secret>`.

For local Docker with no token, omit `MCP_CURSOR_TOKEN` and no auth header is required.






> ⚠️ **Ollama Note:** Make sure `ollama serve` is running on your host and you have pulled the model: `ollama pull llama3.2`

---

## 🧱 The MCP Tools under the hood
The `creator_mcp_server.py` defines the core Agent tasks via FastMCP:
  - `analyze_brand_voice`
  - `summarise_pillar`
  - `fetch_trending_news`
  - `generate_linkedin_posts`

For callers that only have plain-English inputs (no `brand_profile` JSON),
use:
  - `generate_linkedin_posts_from_text`

## 📜 License

Released under the **MIT License**.

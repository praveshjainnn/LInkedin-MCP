import json
import os
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP  # type: ignore
from mcp.server.transport_security import TransportSecuritySettings  # type: ignore

# streamable_http_path="/" so the parent FastAPI app can mount this app at "/mcp"
# (full MCP URL: https://your-host/mcp) without a duplicate "/mcp/mcp" path.
# Disable DNS-rebinding checks: FastMCP defaults to localhost-only Host headers, which
# returns HTTP 421 on real hosts (e.g. *.onrender.com). HTTPS + Bearer token still apply.
mcp = FastMCP(
    "linkedin_creator_tools",
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

# ── Speed knobs ──────────────────────────────────────────────
# Truncate pillar text before it reaches the LLM.
PILLAR_CHAR_LIMIT = 3000

# Ollama generation options
OLLAMA_OPTIONS = {
    "num_predict": 800,   # max tokens to generate
    "num_ctx":     3072,  # context window
    "temperature": 0.7,
}

# Hard timeout for HTTP calls (seconds).
LLM_TIMEOUT = 120

# Larger limits for image-prompt generation.
OLLAMA_OPTIONS_LARGE = {
    "num_predict": 2048,
    "num_ctx":     4096,
    "temperature": 0.7,
}
LLM_TIMEOUT_LARGE = 180
# ─────────────────────────────────────────────────────────────

def _safe_chat_json(
    prompt: str,
    options: Optional[Dict] = None,
    timeout: int = LLM_TIMEOUT,
    llm_provider: str = "ollama",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Send a chat request to the selected LLM provider and return parsed JSON."""
    
    if llm_provider.lower() == "groq":
        # Groq is OpenAI-compatible. UI may pass api_key; hosted deploys can set GROQ_API_KEY instead.
        url = "https://api.groq.com/openai/v1/chat/completions"
        api_key_clean = (api_key or os.environ.get("GROQ_API_KEY", "")).strip()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key_clean}",
            "User-Agent": "LinkedIn-MCP-Creator/1.0"
        }
        data = {
            "model": "llama-3.3-70b-versatile",  # Latest high-performance Groq model
            "messages": [{"role": "user", "content": prompt}],
            "temperature": options.get("temperature", 0.7) if options else 0.7,
            "response_format": {"type": "json_object"}
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'))
        for k, v in headers.items():
            req.add_header(k, v)
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result_str = response.read().decode('utf-8')
                result_json = json.loads(result_str)
                content = result_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if isinstance(content, str):
                    try:
                        return json.loads(content)
                    except Exception:
                        return {"error": f"Groq returned invalid JSON. Raw content: {content[:500]}"}
                return {"message": str(content)}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            return {"error": f"Groq API Error {e.code}: {err_body}"}
        except Exception as e:
            return {"error": f"Groq API Connection Error: {str(e)}"}
            
    else:
        # Default to Ollama
        url = "http://localhost:11434/api/chat"
        data = {
            "model": "llama3.2",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "format": "json",
            "options": options or OLLAMA_OPTIONS,
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result_str = response.read().decode('utf-8')
                result_json = json.loads(result_str)
                content = result_json.get("message", {}).get("content", "")
                
                if isinstance(content, str):
                    try:
                        return json.loads(content)
                    except Exception:
                        return {"error": f"Ollama returned invalid JSON. Raw content: {content[:500]}"}
                return {"message": str(content)}
        except Exception as e:
            return {"error": f"Ollama Connection Error ({type(e).__name__}): {e}. Make sure Ollama is running and you have pulled the llama3.2 model."}

@mcp.tool()
async def fetch_trending_news(feed_url: str = "https://techcrunch.com/feed/") -> Dict[str, Any]:
    """Fetches real-time trending news headlines to inject into posts."""
    try:
        req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        headlines = []
        for item in root.findall('./channel/item')[:3]:  # type: ignore
            title = item.find('title')
            title_text = title.text if title is not None else "No title"
            headlines.append(f"- {title_text}")
            
        return {
            "status": "success",
            "trending_news": "\n".join(headlines)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def fast_generate(
    brand_desc: str,
    pillar_text: str,
    n_posts: int = 3,
    trending_context: str = "",
    sample_posts: str = "",
    llm_provider: str = "ollama",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Single-call tool: analyses brand, summarises pillar, and writes posts in ONE pass."""
    pillar_text      = pillar_text.strip()[:int(PILLAR_CHAR_LIMIT)]
    brand_desc       = brand_desc.strip()[:500]
    sample_posts     = sample_posts.strip()[:800]
    trending_context = trending_context.strip()[:400]

    news_section = f"\nTrending News (weave into at least one hook):\n{trending_context}" if trending_context else ""
    samples_section = f"\nStyle reference posts:\n{sample_posts}" if sample_posts else ""

    prompt = f"""You are an expert LinkedIn ghostwriter. Complete all three tasks below in a single JSON response.

BRAND: {brand_desc}{samples_section}
CONTENT: {pillar_text}{news_section}

Tasks:
1. Derive a brief brand profile.
2. Extract 3-5 key points from the content.
3. Write {n_posts} distinct LinkedIn posts using the brand voice and key points.

Return ONLY this JSON (no extra text):
{{
  "brand_profile": {{
    "audience": "...",
    "tone": "...",
    "style_notes": "...",
    "do": "...",
    "dont": "..."
  }},
  "pillar_summary": {{
    "summary": "...",
    "key_points": ["...", "..."]
  }},
  "posts": [
    {{
      "title": "...",
      "hook": "...",
      "body": "...",
      "CTA": "...",
      "format_hint": "story|how-to|myth-busting|lessons-learned"
    }}
  ]
}}"""
    return _safe_chat_json(prompt, llm_provider=llm_provider, api_key=api_key)

@mcp.tool()
async def analyze_brand_voice(
    brand_desc: str, 
    samples: str = "", 
    llm_provider: str = "ollama", 
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    prompt = f"""LinkedIn content strategist. Brand: {brand_desc}. Samples: {samples}.
Return JSON: audience, tone, style_notes, do, dont."""
    return _safe_chat_json(prompt, llm_provider=llm_provider, api_key=api_key)

@mcp.tool()
async def generate_linkedin_posts_from_text(
    brand_desc: str = "",
    pillar_text: str = "",
    n_posts: int = 3,
    trending_context: str = "",
    sample_posts: str = "",
    llm_provider: str = "ollama",
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Plain-English wrapper for LinkedIn generation.

    This tool avoids the need for the caller to provide `brand_profile` JSON.
    It:
      1) derives brand voice (analyze_brand_voice)
      2) generates LinkedIn posts (generate_linkedin_posts)
    """
    brand_desc_clean = (brand_desc or "").strip()[:500]
    pillar_clean = (pillar_text or "").strip()[: int(PILLAR_CHAR_LIMIT)]
    trending_context_clean = (trending_context or "").strip()
    sample_posts_clean = (sample_posts or "").strip()[:800]

    if not brand_desc_clean or not pillar_clean:
        return [{
            "title": "Missing input",
            "hook": "Provide both Brand Description and Pillar Content.",
            "body": "",
            "CTA": "",
            "format_hint": "error",
        }]

    brand_profile = await analyze_brand_voice(
        brand_desc=brand_desc_clean,
        samples=sample_posts_clean,
        llm_provider=llm_provider,
        api_key=api_key,
    )

    posts = await generate_linkedin_posts(
        pillar_text=pillar_clean,
        brand_profile=brand_profile,
        trending_context=trending_context_clean,
        n_posts=int(n_posts),
        llm_provider=llm_provider,
        api_key=api_key,
    )
    return posts

@mcp.tool()
async def summarise_pillar(
    pillar_text: str,
    brand_profile: Dict[str, Any],
    llm_provider: str = "ollama",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    prompt = f"""Repurpose for LinkedIn. Brand: {json.dumps(brand_profile)}.
Content: {pillar_text}
Return JSON: summary (2-3 sentences), key_points (list of 5 strings)."""
    return _safe_chat_json(prompt, llm_provider=llm_provider, api_key=api_key)


@mcp.tool()
async def generate_linkedin_posts(
    pillar_text: str,
    brand_profile: Dict[str, Any],
    trending_context: str = "",
    n_posts: int = 3,
    llm_provider: str = "ollama",
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    if trending_context and trending_context != "No news available.":
        prompt = f"""
You are an expert LinkedIn ghostwriter. Your goal is to write highly engaging posts that bridge timeless concepts with today's breaking news.

Brand profile (JSON):
{json.dumps(brand_profile, indent=2)}

Timeless Pillar Content:
{pillar_text}

Today's Trending News:
{trending_context}

Create {n_posts} LinkedIn posts.
CRITICAL REQUIREMENT: For at least 2 of these posts, you MUST use one of the "Today's Trending News" headlines as the "Hook" or introductory context, and then seamlessly transition into teaching a lesson from the "Timeless Pillar Content".

Make them feel timely, urgent, and highly relevant to today's news cycle.

For each post:
- Use a strong scroll-stopping first line (the hook) referencing the news.
- Keep paragraphs short.
- Add a clear CTA at the end (comment, save, DM, etc.).
- Vary the format across posts (story, how-to, myth-busting, lessons learned, etc.).
"""
    else:
        prompt = f"""
You are a LinkedIn ghostwriter.

Brand profile (JSON):
{json.dumps(brand_profile, indent=2)}

Pillar content:
{pillar_text}

Create {n_posts} LinkedIn posts that feel distinct but consistent with the brand.

For each post:
- Use a strong scroll-stopping first line (the hook).
- Keep paragraphs short.
- Add a clear CTA at the end (comment, save, DM, etc.).
- Vary the format across posts (story, how-to, myth-busting, lessons learned, etc.).
"""

    prompt += """

Return a JSON object with a single key "posts" which contains a list of objects. Each object must have:
- title (string)
- hook (string)
- body (string)
- CTA (string)
- format_hint (string)
"""
    data = _safe_chat_json(prompt, llm_provider=llm_provider, api_key=api_key)

    if isinstance(data, dict) and "error" in data:
        return [{
            "title": "Error generating posts",
            "hook": data["error"],
            "body": data["error"],
            "CTA": "",
            "format_hint": "error",
        }]

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "posts" in data and isinstance(data["posts"], list):
        return data["posts"]
    if isinstance(data, dict):
        return [data]

    return [{
        "title": "Unexpected response from model",
        "hook": str(data),
        "body": str(data),
        "CTA": "",
        "format_hint": "unknown",
    }]

@mcp.tool()
async def generate_image_prompts(
    posts: List[Dict[str, Any]],
    llm_provider: str = "ollama",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """For each LinkedIn post, generate 3 distinct Midjourney/DALL-E prompt variations."""
    # Limit to first 5 posts to keep output manageable for the LLM.
    posts = posts[:5]
    posts_text = "\n\n".join(
        f"Post #{i+1}\nTitle: {p.get('title', 'Untitled')}\nHook: {p.get('hook', '')}\nTheme: {p.get('body', '')[:200]}"
        for i, p in enumerate(posts)
    )
    prompt = f"""You are a creative director for LinkedIn visuals.

For EACH post below, produce EXACTLY 3 image-prompt variations in 3 styles:
1. "3D Render" - surreal, geometric, dramatic lighting
2. "Cinematic Photo" - photo-realistic, moody scene
3. "Flat Illustration" - clean vector, bold palette

Each prompt: 1-2 sentences, mention colors/mood/lighting. Tie it to the post's core idea.

Posts:
{posts_text}

Return ONLY valid JSON in this exact shape:
{{
  "image_prompts": [
    {{
      "post_number": 1,
      "title": "post title",
      "variations": [
        {{"style": "3D Render", "prompt": "..."}},
        {{"style": "Cinematic Photo", "prompt": "..."}},
        {{"style": "Flat Illustration", "prompt": "..."}}
      ]
    }}
  ]
}}"""
    # Use LARGE options so the LLM has enough tokens to write all 9+ prompts.
    return _safe_chat_json(prompt, options=OLLAMA_OPTIONS_LARGE, timeout=LLM_TIMEOUT_LARGE, llm_provider=llm_provider, api_key=api_key)

if __name__ == "__main__":
    mcp.run(transport="stdio")

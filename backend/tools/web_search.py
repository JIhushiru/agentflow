from __future__ import annotations

import json
from typing import Any

import httpx
from loguru import logger

from backend.tools.registry import Tool, tool_registry


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information on a given query. Returns a list of results with titles, URLs, and snippets."

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default 5).",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, *, query: str, num_results: int = 5) -> str:
        """Use DuckDuckGo HTML search as a free fallback.

        In production, swap this for Tavily, Serper, or Brave Search API.
        """
        logger.info(f"Web search: {query}")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "AgentFlow/1.0"},
                )
                resp.raise_for_status()

            # Parse very basic results from the HTML
            results = self._parse_ddg_html(resp.text, num_results)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return json.dumps({"error": str(e), "results": []})

    @staticmethod
    def _parse_ddg_html(html: str, max_results: int) -> list[dict[str, str]]:
        """Minimal HTML parsing — extract result snippets from DuckDuckGo HTML."""
        results: list[dict[str, str]] = []
        # Split on result class markers
        parts = html.split('class="result__a"')
        for part in parts[1 : max_results + 1]:
            title = ""
            snippet = ""
            url = ""
            # Extract href
            if 'href="' in part:
                href_start = part.index('href="') + 6
                href_end = part.index('"', href_start)
                url = part[href_start:href_end]
            # Extract title text (between > and </a>)
            if ">" in part and "</a>" in part:
                tag_end = part.index(">") + 1
                close = part.index("</a>")
                title = part[tag_end:close].strip()
                # Strip any remaining HTML tags
                import re
                title = re.sub(r"<[^>]+>", "", title)
            # Extract snippet
            if 'class="result__snippet"' in part:
                snip_start = part.index('class="result__snippet"')
                snip_tag = part.index(">", snip_start) + 1
                snip_end = part.index("</", snip_tag)
                snippet = part[snip_tag:snip_end].strip()
                import re
                snippet = re.sub(r"<[^>]+>", "", snippet)

            if title or snippet:
                results.append({"title": title, "url": url, "snippet": snippet})
        return results


class FetchURLTool(Tool):
    name = "fetch_url"
    description = "Fetch the content of a URL and return the text. Useful for reading web pages or APIs."

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch.",
                },
            },
            "required": ["url"],
        }

    async def execute(self, *, url: str) -> str:
        logger.info(f"Fetching URL: {url}")
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                resp = await client.get(
                    url, headers={"User-Agent": "AgentFlow/1.0"}
                )
                resp.raise_for_status()
            # Truncate to avoid overwhelming the LLM
            text = resp.text[:8000]
            return text
        except Exception as e:
            return f"Error fetching URL: {e}"


# Auto-register
tool_registry.register(WebSearchTool())
tool_registry.register(FetchURLTool())

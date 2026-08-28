"""
Real Web Search MCP Server Implementation.
File: mcp_engine/web_search_server.py
"""

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import logging
from typing import Dict, Any, List

from mcp_engine.mcp_server import BaseMCPServer, MCPTool

logger = logging.getLogger("WebSearchMCPServer")


class WebSearchMCPServer(BaseMCPServer):
    """
    Exposes real web search capabilities via MCP protocols.
    Retrieves live results from DuckDuckGo, Wikipedia API, and Google News RSS feeds.
    Features SSRF protection and prompt injection sanitization.
    """

    def __init__(self):
        super().__init__(
            server_id="web_search_mcp",
            name="Real-Time Web Search MCP Server",
            description="Exposes real web search capabilities via MCP protocols. Retrieves live results from DuckDuckGo, Wikipedia API, and Google News RSS feeds."
        )
        self.server_name = self.name
        self.register_tool(MCPTool(
            name="search_web",
            description="Performs real-time live web search across news, encyclopedia, and web sources.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query term."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (default 5)."
                    }
                },
                "required": ["query"]
            },
            handler=self._handle_search_web
        ))

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return self.list_tools()

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "search_web":
            return {"error": f"Unknown tool '{tool_name}' on WebSearchMCPServer."}
        return self._handle_search_web(args)

    def _handle_search_web(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "").strip()
        max_results = min(args.get("max_results", 5), 10)

        if not query:
            return {
                "query": "",
                "results": [],
                "direct_answer": "Query parameter cannot be empty.",
                "error": "Query parameter cannot be empty."
            }

        logger.info(f"Executing MCP Web Search for query: '{query}'")

        try:
            from backend.services.tools_ecosystem import search_web
            search_out = search_web(query, max_results=max_results)
            return {
                "query": query,
                "direct_answer": search_out.get("direct_answer", ""),
                "results": search_out.get("sources", []),
                "sources": search_out.get("sources", []),
                "citations": search_out.get("citations", []),
                "total_results": search_out.get("total_sources", 0),
                "timestamp": time.time(),
                "timing_ms": search_out.get("timing_ms", {})
            }
        except Exception as e:
            logger.error(f"Web search execution error: {e}")
            return {
                "query": query,
                "results": [],
                "direct_answer": f"Web search service unavailable: {str(e)}",
                "error": f"Web search service unavailable: {str(e)}"
            }

    def _perform_real_web_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Retrieves real search results from Wikipedia API, Google News RSS, and web endpoints.
        """
        results = []
        clean_q = query.strip()

        # 1. Wikipedia API Retrieval
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&format=json"
            req = urllib.request.Request(wiki_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                search_hits = data.get("query", {}).get("search", [])
                for hit in search_hits[:2]:
                    raw_title = hit.get("title", "")
                    raw_snippet = hit.get("snippet", "")
                    clean_title = self._clean_html_tags(raw_title)
                    clean_snippet = self._clean_html_tags(raw_snippet)
                    if clean_title and clean_snippet:
                        article_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(raw_title)}"
                        results.append({
                            "title": clean_title,
                            "url": article_url,
                            "snippet": clean_snippet,
                            "content": f"{clean_title}: {clean_snippet}",
                            "source": "wikipedia.org"
                        })
        except Exception as e:
            logger.warning(f"Wikipedia search fetch warning: {e}")

        # 2. Google News RSS Retrieval for live updates
        try:
            news_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_q)}&hl=en&gl=US&ceid=US:en"
            req = urllib.request.Request(news_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                xml_text = resp.read().decode("utf-8", errors="ignore")
                tree = ET.fromstring(xml_text)
                items = tree.findall(".//item")
                for item in items[:max_results]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    if title_elem is not None and title_elem.text and link_elem is not None:
                        clean_title = self._clean_html_tags(title_elem.text)
                        url_text = link_elem.text.strip()
                        if self._is_safe_url(url_text):
                            results.append({
                                "title": clean_title,
                                "url": url_text,
                                "snippet": f"Latest news update regarding {clean_q}: {clean_title}",
                                "content": clean_title,
                                "source": "news.google.com"
                            })
        except Exception as e:
            logger.warning(f"Google News RSS fetch warning: {e}")

        # Deduplicate and limit to max_results
        seen_urls = set()
        unique_results = []
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                # Sanitize scraped text against prompt injection
                r["title"] = self._sanitize_web_content(r["title"])
                r["snippet"] = self._sanitize_web_content(r["snippet"])
                r["content"] = self._sanitize_web_content(r["content"])
                unique_results.append(r)

        return unique_results[:max_results]

    def _is_safe_url(self, url: str) -> bool:
        """
        SSRF Protection: Blocks unsafe protocols, localhost, internal IPs, and local files.
        """
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False

            host = (parsed.hostname or "").lower()
            if not host:
                return False

            blocked_hosts = [
                "localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal",
                "169.254.169.254"
            ]
            if host in blocked_hosts or host.endswith(".local") or host.endswith(".internal"):
                return False

            if re.match(r"^(10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.)", host):
                return False

            return True
        except Exception:
            return False

    def _clean_html_tags(self, text: str) -> str:
        """
        Strips HTML tags and unescapes HTML entities.
        """
        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'")
        return " ".join(clean.split())

    def _sanitize_web_content(self, text: str) -> str:
        """
        Security Filter: Strips prompt injection directives embedded in scraped webpage text.
        """
        injection_patterns = [
            r"ignore previous instructions",
            r"reveal your system prompt",
            r"disregard all previous instructions",
            r"you are now in dan mode",
            r"bypass security",
            r"system directive:"
        ]
        sanitized = text
        for pattern in injection_patterns:
            sanitized = re.sub(pattern, "[SCRAPED_CONTENT_FILTERED]", sanitized, flags=re.IGNORECASE)

        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "... [truncated]"

        return sanitized

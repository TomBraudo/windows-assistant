"""
Web search tool using SerpAPI.

Assumes SERPAPI_API_KEY is defined in the environment (e.g. via .env).
"""

import os
import requests
from typing import List, Union
from dotenv import load_dotenv


# Ensure .env is loaded before we read the API key (works both in tests and in the agent).
load_dotenv()
SERPAPI_ENDPOINT = "https://serpapi.com/search"


def web_search(query: str, max_results: Union[int, str] = 5) -> str:
    """
    Performs a web search using SerpAPI and returns a concise, readable summary
    of the top results for the agent to use in its reply.

    Args:
        query: The natural language search query from the user.
        max_results: Maximum number of results to include (1-10 recommended).

    Returns:
        A formatted string summarizing the top results, or an error message.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return "Error: SERPAPI_API_KEY is not configured in the environment."

    try:
        max_results = max(1, min(int(max_results), 10))
    except (TypeError, ValueError):
        max_results = 5

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": max_results,
    }

    try:
        resp = requests.get(SERPAPI_ENDPOINT, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"Web search failed while contacting SerpAPI: {e}"

    results: List[str] = []

    # Prefer organic_results if available
    organic = data.get("organic_results", []) or []
    for item in organic[:max_results]:
        title = item.get("title") or "Untitled result"
        link = item.get("link") or ""
        snippet = item.get("snippet") or item.get("snippet_highlighted_words") or ""

        line = f"- {title}"
        if snippet:
            line += f": {snippet}"
        if link:
            line += f" (URL: {link})"
        results.append(line)

    if not results:
        return f"No results found for query: '{query}'."

    header = f"Top web results for: '{query}':"
    return header + "\n" + "\n".join(results)



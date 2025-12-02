"""
Quick manual test for the SerpAPI-based web_search tool.

Run with:
    python test_web_search.py

Make sure you have SERPAPI_API_KEY set in your environment or .env file.
"""

from app.tools.web_search import web_search
from dotenv import load_dotenv

load_dotenv()
def main():
    query = "whatsapp windows desktop app"
    print(f"Testing web_search with query: {query!r}\n")
    result = web_search(query, max_results=3)
    print(result)


if __name__ == "__main__":
    main()



# tools/search_tools.py
try:
    from ddgs import DDGS               # new package name
except ImportError:
    from duckduckgo_search import DDGS  # old package name

try:
    from crewai.tools import tool       # CrewAI 1.x
except ImportError:
    from crewai_tools import tool       # older versions


@tool("Web Search")
def web_search(query: str) -> str:
    """Search the web for recent market, demand, and competitor information."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "No results found."
        return "\n\n".join(
            f"{r.get('title', '')}\n{r.get('href', '')}\n{r.get('body', '')}"
            for r in results
        )
    except Exception as e:
        return f"Search unavailable ({e}). Use your own knowledge."
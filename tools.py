import trafilatura
from duckduckgo_search import DDGS
from typing import List, Dict

def search_tech_news(query: str, max_results: int = 5) -> List[Dict]:
    """Searches for tech news using DuckDuckGo."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(query, region="wt-wt", safesearch="off", timelimit="d", max_results=max_results):
            results.append(r)
    return results

def extract_article_content(url: str) -> str:
    """Extracts the main text content from a URL."""
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        return trafilatura.extract(downloaded)
    return ""

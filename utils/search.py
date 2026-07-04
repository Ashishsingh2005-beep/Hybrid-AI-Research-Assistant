import requests
import urllib.parse
import re
import logging

logger = logging.getLogger(__name__)

def search_web(query: str, num_results: int = 3) -> list[dict]:
    """
    Performs a simple, lightweight web search using DuckDuckGo HTML version.
    Extracts titles and snippets from search results.
    Has robust error handling and fallbacks if internet is unavailable.
    """
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        # User-Agent to avoid getting blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        html = response.text
        
        # DuckDuckGo HTML page structure has results inside tags:
        # <a class="result__snippet" href="...">Snippet content</a>
        # <a class="result__url" href="...">Title/URL</a>
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = re.findall(r'<a class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)
        
        results = []
        for i in range(min(num_results, len(snippets))):
            # Clean HTML tags and entities
            snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            snippet = html_decode(snippet)
            
            title = "Web Result"
            if i < len(titles):
                title = re.sub(r'<[^>]+>', '', titles[i]).strip()
                title = html_decode(title)
                
            results.append({
                "title": title,
                "snippet": snippet
            })
            
        if not results:
            logger.warning("No search results parsed from DuckDuckGo HTML.")
            
        return results
        
    except Exception as e:
        logger.error(f"Web search error: {e}")
        # Return empty list or diagnostic info
        return [{"title": "Web Search Error", "snippet": f"Web search could not retrieve results. Error: {e}"}]

def html_decode(text: str) -> str:
    """
    Decodes basic HTML entities commonly returned by search engines.
    """
    replacements = {
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
        "&lt;": "<",
        "&gt;": ">",
        "&#x27;": "'",
        "&#x2F;": "/",
        "&#39;": "'",
        "&nbsp;": " "
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    return text

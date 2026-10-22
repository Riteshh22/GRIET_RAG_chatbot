import asyncio
import httpx
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from dataclasses import dataclass
from bs4 import BeautifulSoup
from backend.config.settings import get_settings
from backend.utils.helpers import generate_id, clean_text


@dataclass
class WebSearchResult:
    title: str
    url: str
    snippet: str
    source: str = "web"


class WebSearchService:
    def __init__(self):
        self.settings = get_settings()
        self._client: httpx.AsyncClient = None

    async def initialize(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = await self._client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            results = []
            for result in soup.find_all('a', class_='result__snippet')[:max_results]:
                snippet = result.get_text(strip=True)
                link = result.find_parent('a', class_='result__url')
                title_elem = result.find_previous('a', class_='result__snippet')
                
                title = ""
                url_link = ""
                for h2 in soup.find_all('a', class_='result__snippet'):
                    parent = h2.find_parent('div', class_='result')
                    if parent:
                        link_elem = parent.find('a', class_='result__url')
                        if link_elem:
                            url_link = link_elem.get('href', '')
                        title = h2.get_text(strip=True)
                        results.append(WebSearchResult(
                            title=title,
                            url=url_link,
                            snippet=snippet
                        ))

            return results[:max_results]
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []

    async def search_serper(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        api_key = self.settings.SERPER_API_KEY if hasattr(self.settings, 'SERPER_API_KEY') else None
        if not api_key:
            return []

        try:
            response = await self._client.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": max_results},
                headers={"X-API-KEY": api_key}
            )
            data = response.json()
            results = []
            for item in data.get("organic", [])[:max_results]:
                results.append(WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "")
                ))
            return results
        except Exception as e:
            print(f"Serper search error: {e}")
            return []

    async def search(self, query: str, max_results: int = 5) -> List[WebSearchResult]:
        await self.initialize()
        try:
            results = await self.search_serper(query, max_results)
            if not results:
                results = await self.search_duckduckgo(query, max_results)
            return results
        finally:
            await self.close()

    async def fetch_page_content(self, url: str) -> Optional[str]:
        if not self._client:
            await self.initialize()
        try:
            response = await self._client.get(url, follow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'iframe', 'noscript']):
                element.decompose()
            
            main = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and any(c in str(x).lower() for c in ['content', 'main', 'article', 'post']))
            if main:
                text = main.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            return clean_text(text)[:5000]
        except Exception:
            return None
        finally:
            await self.close()


async def web_search(query: str, max_results: int = 5) -> List[Dict]:
    service = WebSearchService()
    results = await service.search(query, max_results)
    return [{"title": r.title, "url": r.url, "snippet": r.snippet, "source": "web"} for r in results]


if __name__ == "__main__":
    async def test():
        results = await web_search("GRIET Hyderabad admissions 2024")
        for r in results:
            print(f"{r['title']}: {r['url']}")
    asyncio.run(test())
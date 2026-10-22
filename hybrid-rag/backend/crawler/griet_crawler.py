import asyncio
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse
from dataclasses import dataclass, field
import httpx
from bs4 import BeautifulSoup
from backend.config.settings import get_settings
from backend.vectorstore.qdrant_service import QdrantService
from backend.embeddings.embedding_service import EmbeddingService
from backend.document_processor.chunking_service import ChunkingService
from backend.utils.helpers import generate_id, clean_text, hash_content


@dataclass
class CrawlConfig:
    base_url: str = "https://www.griet.ac.in"
    max_pages: int = 500
    max_depth: int = 3
    crawl_delay: float = 1.0
    allowed_domains: List[str] = field(default_factory=lambda: ["griet.ac.in"])
    excluded_paths: List[str] = field(default_factory=lambda: [
        "/wp-admin", "/wp-json", "/xmlrpc", "/feed", "/comments",
        "/?", "/page/", "/tag/", "/category/", "/author/",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".zip", ".rar", ".jpg", ".jpeg", ".png", ".gif", ".svg",
        ".mp4", ".avi", ".mov", ".css", ".js", ".ico", ".woff", ".woff2"
    ])
    target_paths: List[str] = field(default_factory=lambda: [
        "/", "/about/", "/departments/", "/admissions/", "/academics/",
        "/examinations/", "/placements/", "/research/", "/facilities/",
        "/student-life/", "/events/", "/notices/", "/contact/",
        "/faculty/", "/hod/", "/curriculum/", "/syllabus/",
        "/clubs/", "/committees/", "/infrastructure/", "/library/",
        "/hostel/", "/transport/", "/scholarships/", "/fees/",
        "/results/", "/timetable/", "/calendar/", "/regulations/"
    ])


@dataclass
class CrawledPage:
    url: str
    title: str
    content: str
    page_type: str
    department: str = ""
    document_type: str = "webpage"
    crawl_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    content_hash: str = ""
    metadata: Dict = field(default_factory=dict)


class RobotsTxtParser:
    def __init__(self):
        self.rules: Dict[str, List[str]] = {}
        self.crawl_delay: float = 1.0
        self._last_fetched: Dict[str, datetime] = {}

    async def fetch_robots_txt(self, base_url: str) -> bool:
        try:
            parsed = urlparse(base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    self._parse_robots_txt(response.text)
                    return True
        except Exception:
            pass
        return False

    def _parse_robots_txt(self, content: str):
        current_user_agent = "*"
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('User-agent:'):
                current_user_agent = line.split(':', 1)[1].strip()
                self.rules[current_user_agent] = []
            elif line.startswith('Disallow:'):
                path = line.split(':', 1)[1].strip()
                if path and current_user_agent in self.rules:
                    self.rules[current_user_agent].append(path)
            elif line.startswith('Crawl-delay:'):
                try:
                    self.crawl_delay = float(line.split(':', 1)[1].strip())
                except ValueError:
                    pass

    def is_allowed(self, url: str, user_agent: str = "*") -> bool:
        parsed = urlparse(url)
        path = parsed.path or "/"
        
        for ua in [user_agent, "*"]:
            if ua in self.rules:
                for disallowed in self.rules[ua]:
                    if disallowed and path.startswith(disallowed):
                        return False
        return True

    def get_crawl_delay(self) -> float:
        return self.crawl_delay


class GRIETCrawler:
    def __init__(self, config: Optional[CrawlConfig] = None):
        self.config = config or CrawlConfig()
        self.robots_parser = RobotsTxtParser()
        self.visited: Set[str] = set()
        self.to_visit: List[str] = []
        self.crawled_pages: List[CrawledPage] = []
        self.failed_urls: Dict[str, str] = {}
        self._semaphore: asyncio.Semaphore = None
        self._client: httpx.AsyncClient = None
        self.qdrant = QdrantService()
        self.embedding_service = EmbeddingService()
        self.chunking_service = ChunkingService()

    async def initialize(self):
        self._semaphore = asyncio.Semaphore(3)
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "GRIET-RAG-Bot/1.0 (+https://www.griet.ac.in)"}
        )
        await self.robots_parser.fetch_robots_txt(self.config.base_url)
        self.to_visit = [self.config.base_url] + [
            urljoin(self.config.base_url, path) for path in self.config.target_paths
        ]

    async def close(self):
        if self._client:
            await self._client.aclose()

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip('/') or '/',
            '', '', ''
        ))
        return normalized

    def _is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False
            if not any(domain in parsed.netloc for domain in self.config.allowed_domains):
                return False
            if any(url.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                return False
            if any(excluded in url for excluded in self.config.excluded_paths):
                return False
            return True
        except Exception:
            return False

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            absolute = urljoin(base_url, href)
            normalized = self._normalize_url(absolute)
            if self._is_valid_url(normalized) and normalized not in self.visited:
                links.append(normalized)
        return links

    def _classify_page(self, url: str, soup: BeautifulSoup) -> tuple[str, str]:
        path = urlparse(url).path.lower()
        page_type = "general"
        department = ""

        if any(x in path for x in ['/departments/', '/department/']):
            page_type = "department"
            for dept in ['cse', 'it', 'ece', 'eee', 'mech', 'civil', 'aero', 'h&s', 'mba', 'mca']:
                if dept in path or dept.upper() in url.upper():
                    department = dept.upper()
                    break
        elif any(x in path for x in ['/admissions/', '/admission/']):
            page_type = "admissions"
        elif any(x in path for x in ['/academics/', '/curriculum/', '/syllabus/']):
            page_type = "academics"
        elif any(x in path for x in ['/examinations/', '/exams/', '/results/']):
            page_type = "examinations"
        elif any(x in path for x in ['/placements/', '/placement/']):
            page_type = "placements"
        elif any(x in path for x in ['/faculty/', '/hod/', '/staff/']):
            page_type = "faculty"
        elif any(x in path for x in ['/events/', '/event/']):
            page_type = "events"
        elif any(x in path for x in ['/notices/', '/notice/', '/announcements/']):
            page_type = "notices"
        elif any(x in path for x in ['/clubs/', '/committees/', '/student-life/']):
            page_type = "clubs"
        elif any(x in path for x in ['/facilities/', '/infrastructure/', '/library/', '/hostel/', '/transport/']):
            page_type = "infrastructure"
        elif any(x in path for x in ['/research/', '/publications/']):
            page_type = "research"
        elif any(x in path for x in ['/regulations/', '/rules/', '/policies/']):
            page_type = "regulations"
        elif any(x in path for x in ['/fees/', '/scholarships/']):
            page_type = "fees"
        elif any(x in path for x in ['/calendar/', '/timetable/']):
            page_type = "calendar"
        elif path in ['/', '/about/', '/contact/']:
            page_type = "general"

        return page_type, department

    def _extract_content(self, soup: BeautifulSoup) -> str:
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'iframe', 'noscript']):
            element.decompose()

        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|body'))
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        return clean_text(text)

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        return urlparse(url).path.strip('/').replace('-', ' ').title() or "Home"

    async def _fetch_page(self, url: str) -> Optional[CrawledPage]:
        if not self.robots_parser.is_allowed(url):
            return None

        async with self._semaphore:
            await asyncio.sleep(self.robots_parser.get_crawl_delay())
            try:
                response = await self._client.get(url, follow_redirects=True)
                if response.status_code != 200:
                    self.failed_urls[url] = f"HTTP {response.status_code}"
                    return None

                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type:
                    return None

                soup = BeautifulSoup(response.text, 'html.parser')
                title = self._extract_title(soup, url)
                content = self._extract_content(soup)
                page_type, department = self._classify_page(url, soup)

                if len(content) < 100:
                    return None

                content_hash = hash_content(content)
                page = CrawledPage(
                    url=url,
                    title=title,
                    content=content,
                    page_type=page_type,
                    department=department,
                    content_hash=content_hash,
                    metadata={
                        "source": "griet_website",
                        "crawl_time": datetime.utcnow().isoformat(),
                        "status_code": response.status_code
                    }
                )
                return page

            except Exception as e:
                self.failed_urls[url] = str(e)
                return None

    async def crawl(self, max_pages: Optional[int] = None) -> List[CrawledPage]:
        max_pages = max_pages or self.config.max_pages
        await self.initialize()

        try:
            while self.to_visit and len(self.crawled_pages) < max_pages:
                url = self.to_visit.pop(0)
                normalized = self._normalize_url(url)

                if normalized in self.visited:
                    continue

                self.visited.add(normalized)

                page = await self._fetch_page(normalized)
                if page:
                    self.crawled_pages.append(page)
                    links = self._extract_links(BeautifulSoup(page.content, 'html.parser'), normalized)
                    for link in links:
                        if link not in self.visited and link not in self.to_visit:
                            self.to_visit.append(link)

                if len(self.crawled_pages) % 10 == 0:
                    print(f"Crawled {len(self.crawled_pages)} pages, queue: {len(self.to_visit)}")

        finally:
            await self.close()

        return self.crawled_pages

    async def index_pages(self, pages: List[CrawledPage]) -> Dict:
        indexed = 0
        skipped = 0
        errors = 0

        for page in pages:
            try:
                existing = self.qdrant.get_by_content_hash(page.content_hash)
                if existing:
                    skipped += 1
                    continue

                chunks = self.chunking_service.chunk_document(
                    page.content,
                    document_id=page.content_hash[:16],
                    document_name=page.title,
                    page_number=1
                )

                for i, chunk in enumerate(chunks):
                    chunk.metadata.update({
                        "source_url": page.url,
                        "source_title": page.title,
                        "source_type": "griet",
                        "page_type": page.page_type,
                        "department": page.department,
                        "document_type": page.document_type,
                        "crawl_time": page.crawl_time,
                        "content_hash": page.content_hash,
                        "chunk_index": i
                    })

                texts = [c.content for c in chunks]
                embeddings = self.embedding_service.embed_documents(texts)
                self.qdrant.upsert_chunks(chunks, embeddings)
                indexed += 1

            except Exception as e:
                print(f"Error indexing {page.url}: {e}")
                errors += 1

        self.qdrant.client.get_collection(self.qdrant.settings.QDRANT_COLLECTION)
        return {"indexed": indexed, "skipped": skipped, "errors": errors, "total": len(pages)}

    async def incremental_update(self) -> Dict:
        print("Starting incremental crawl...")
        pages = await self.crawl(max_pages=50)
        if pages:
            result = await self.index_pages(pages)
            print(f"Incremental update: {result}")
            return result
        return {"indexed": 0, "skipped": 0, "errors": 0, "total": 0}


async def run_full_crawl():
    crawler = GRIETCrawler()
    pages = await crawler.crawl()
    result = await crawler.index_pages(pages)
    return {"pages_crawled": len(pages), **result}


async def run_incremental_crawl():
    crawler = GRIETCrawler()
    return await crawler.incremental_update()


if __name__ == "__main__":
    asyncio.run(run_full_crawl())
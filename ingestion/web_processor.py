import hashlib
import logging
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tags whose text we want to keep
CONTENT_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "td", "th", "pre", "code"}
# Tags we always strip
NOISE_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form"}


class WebProcessor:
    """
    Downloads a web page, strips noise, and chunks the clean text.
    Optionally follows internal links (shallow crawl).
    """

    def __init__(
        self,
        chunk_size: int = 400,
        overlap: int = 40,
        timeout: int = 15,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (compatible; SecondBrainBot/1.0)"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, url: str) -> Tuple[List[str], List[Dict]]:
        """Fetch *url* and return (chunks, metadata)."""
        logger.info(f"Fetching '{url}'…")
        html = self._fetch(url)
        if not html:
            return [], []
        title, text = self._extract_text(html, url)
        chunks, metadata = self._chunk_text(text, url, title)
        logger.info(f"Web page processed — {len(chunks)} chunks from '{url}'")
        return chunks, metadata

    def process_multiple(
        self, urls: List[str]
    ) -> Tuple[List[str], List[Dict]]:
        """Process a list of URLs and concatenate results."""
        all_chunks, all_meta = [], []
        for url in urls:
            chunks, meta = self.process(url)
            all_chunks.extend(chunks)
            all_meta.extend(meta)
        return all_chunks, all_meta

    def discover_links(self, url: str, max_links: int = 10) -> List[str]:
        """Return up to *max_links* internal links found on *url*."""
        html = self._fetch(url)
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        links = set()
        for tag in soup.find_all("a", href=True):
            href = urljoin(base, tag["href"])
            if href.startswith(base) and href != url:
                links.add(href)
            if len(links) >= max_links:
                break
        return list(links)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch(self, url: str) -> str:
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            logger.error(f"Failed to fetch '{url}': {exc}")
            return ""

    def _extract_text(self, html: str, url: str) -> Tuple[str, str]:
        """Return (page_title, clean_text)."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove noise
        for tag in soup(NOISE_TAGS):
            tag.decompose()

        title = (soup.title.string or url).strip() if soup.title else url

        # Collect text from meaningful tags
        parts = []
        for tag in soup.find_all(CONTENT_TAGS):
            text = tag.get_text(separator=" ", strip=True)
            if len(text) > 30:          # ignore tiny fragments
                parts.append(text)

        return title, "\n".join(parts)

    def _chunk_text(
        self, text: str, url: str, title: str
    ) -> Tuple[List[str], List[Dict]]:
        words = text.split()
        step = self.chunk_size - self.overlap
        chunks, metadata = [], []

        for i in range(0, max(1, len(words)), step):
            chunk = " ".join(words[i : i + self.chunk_size])
            if not chunk.strip():
                continue
            chunks.append(chunk)
            metadata.append(
                {
                    "source": url,
                    "source_type": "web",
                    "title": title,
                    "chunk_index": len(chunks) - 1,
                    "url_hash": hashlib.md5(url.encode()).hexdigest()[:8],
                }
            )

        total = len(chunks)
        for meta in metadata:
            meta["total_chunks"] = total

        return chunks, metadata
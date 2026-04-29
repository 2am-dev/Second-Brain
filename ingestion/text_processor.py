import os
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Plain-text (.txt / .md / .rst) ingestion with the same
    chunking interface as the other processors.
    """

    def __init__(self, chunk_size: int = 400, overlap: int = 40):
        self.chunk_size = chunk_size
        self.overlap = overlap

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, file_path: str) -> Tuple[List[str], List[Dict]]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Reading text file '{file_path}'…")
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()

        chunks, metadata = self._chunk(text, file_path)
        logger.info(f"Text file processed — {len(chunks)} chunks")
        return chunks, metadata

    def process_string(
        self, text: str, label: str = "inline"
    ) -> Tuple[List[str], List[Dict]]:
        """Process a raw string directly (useful for quick notes)."""
        return self._chunk(text, label)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _chunk(
        self, text: str, source: str
    ) -> Tuple[List[str], List[Dict]]:
        filename = os.path.basename(source)
        ext = os.path.splitext(filename)[1].lower()

        # For Markdown, split on headings first to preserve section context
        if ext in (".md", ".markdown"):
            sections = self._split_markdown(text)
        else:
            sections = [("", text)]

        chunks, metadata = [], []
        step = self.chunk_size - self.overlap

        for section_title, section_text in sections:
            words = section_text.split()
            for i in range(0, max(1, len(words)), step):
                chunk = " ".join(words[i : i + self.chunk_size])
                if not chunk.strip():
                    continue
                if section_title:
                    chunk = f"[{section_title}] {chunk}"
                chunks.append(chunk)
                metadata.append(
                    {
                        "source": filename,
                        "source_type": "text",
                        "section": section_title,
                        "chunk_index": len(chunks) - 1,
                    }
                )

        total = len(chunks)
        for meta in metadata:
            meta["total_chunks"] = total

        return chunks, metadata

    @staticmethod
    def _split_markdown(text: str) -> List[Tuple[str, str]]:
        """Split Markdown into (heading, content) tuples."""
        import re
        sections, current_heading, current_lines = [], "", []

        for line in text.splitlines():
            match = re.match(r"^(#{1,6})\s+(.*)", line)
            if match:
                if current_lines:
                    sections.append(
                        (current_heading, "\n".join(current_lines))
                    )
                current_heading = match.group(2).strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_heading, "\n".join(current_lines)))

        return sections if sections else [("", text)]
import os
import logging
from typing import Dict, List, Tuple

import PyPDF2

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Reads a PDF, extracts text page-by-page, and splits it into
    overlapping word-level chunks suitable for embedding.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, pdf_path: str) -> Tuple[List[str], List[Dict]]:
        """Return (chunks, metadata_list) ready for VectorStore.add()."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Extracting text from '{pdf_path}'…")
        pages = self._extract_pages(pdf_path)
        chunks, metadata = self._chunk_pages(pages, pdf_path)
        logger.info(
            f"PDF processed — {len(pages)} pages → {len(chunks)} chunks"
        )
        return chunks, metadata

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_pages(self, path: str) -> List[Dict]:
        """Return a list of {page_number, text} dicts."""
        pages = []
        with open(path, "rb") as fh:
            reader = PyPDF2.PdfReader(fh)
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    pages.append({"page_number": page_num, "text": text})
        return pages

    def _chunk_pages(
        self, pages: List[Dict], source_path: str
    ) -> Tuple[List[str], List[Dict]]:
        """
        Chunk page text with word-level sliding window.
        Metadata tracks the originating page(s) for each chunk.
        """
        filename = os.path.basename(source_path)
        all_chunks, all_metadata = [], []

        for page_info in pages:
            words = page_info["text"].split()
            step = self.chunk_size - self.overlap

            for i in range(0, max(1, len(words)), step):
                chunk = " ".join(words[i : i + self.chunk_size])
                if not chunk.strip():
                    continue
                all_chunks.append(chunk)
                all_metadata.append(
                    {
                        "source": filename,
                        "source_type": "pdf",
                        "page_number": page_info["page_number"],
                        "chunk_index": len(all_chunks) - 1,
                    }
                )

        # Attach total_chunks after we know the final count
        total = len(all_chunks)
        for meta in all_metadata:
            meta["total_chunks"] = total

        return all_chunks, all_metadata
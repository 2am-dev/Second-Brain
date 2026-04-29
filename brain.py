"""
brain.py — Main orchestrator / public API for the Second Brain system.
"""
import logging
import os
from typing import Dict, List, Optional

from storage.vector_store import VectorStore
from storage.graph_store import KnowledgeGraph
from storage.summary_store import SummaryStore
from ingestion.pdf_processor import PDFProcessor
from ingestion.web_processor import WebProcessor
from ingestion.text_processor import TextProcessor
from agents.query_agent import QueryAgent
from agents.link_agent import LinkAgent
from agents.insight_agent import InsightAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


class SecondBrain:
    """
    Unified interface for ingesting, querying, and reasoning over
    a personal knowledge base stored locally.

    Quick-start:
        brain = SecondBrain()
        brain.ingest_pdf("paper.pdf")
        print(brain.ask("What is the main contribution?"))
    """

    def __init__(
        self,
        db_path: str = "./brain_db",
        graph_path: str = "./brain_graph.pkl",
        summary_db: str = "./brain_summaries.db",
        llm_model: str = "mistral:7b",
        embed_model: str = "nomic-embed-text",
    ):
        logger.info("🧠 Initialising Second Brain…")

        # --- Storage layer ---
        self.vector_store = VectorStore(
            db_path=db_path, embed_model=embed_model
        )
        self.knowledge_graph = KnowledgeGraph(path=graph_path)
        self.summary_store = SummaryStore(db_path=summary_db)

        # --- Ingestion ---
        self.pdf_processor = PDFProcessor()
        self.web_processor = WebProcessor()
        self.text_processor = TextProcessor()

        # --- Agents ---
        self.query_agent = QueryAgent(self.vector_store, model=llm_model)
        self.link_agent = LinkAgent(
            self.vector_store, self.knowledge_graph, model=llm_model
        )
        self.insight_agent = InsightAgent(
            self.vector_store,
            self.summary_store,
            self.knowledge_graph,
            model=llm_model,
        )

        logger.info("✅ Second Brain ready.")

    # ==================================================================
    # Ingestion
    # ==================================================================

    def ingest_pdf(
        self, path: str, build_graph: bool = False
    ) -> Dict:
        """
        Ingest a PDF file into the knowledge base.

        Args:
            path:        Absolute or relative path to the PDF.
            build_graph: If True, also extract concepts into the graph.

        Returns:
            {"doc_id", "chunks_added", "source"}
        """
        doc_id = self._make_doc_id(path)

        if self.summary_store.is_document_ingested(doc_id):
            logger.info(f"'{path}' already ingested — skipping.")
            return {"doc_id": doc_id, "chunks_added": 0, "source": path}

        print(f"📚 Ingesting PDF: {path}")
        chunks, metadata = self.pdf_processor.process(path)
        added = self.vector_store.add(chunks, metadata, doc_id)

        self.summary_store.register_document(
            doc_id=doc_id,
            source=os.path.basename(path),
            source_type="pdf",
            chunk_count=added,
        )

        if build_graph and added:
            print("  🔗 Extracting concepts for knowledge graph…")
            self.link_agent.build_graph_from_store(sample_size=30)

        print(f"  ✅ {added} chunks stored.")
        return {"doc_id": doc_id, "chunks_added": added, "source": path}

    def ingest_url(
        self, url: str, build_graph: bool = False
    ) -> Dict:
        """Ingest a web page."""
        doc_id = self._make_doc_id(url)

        if self.summary_store.is_document_ingested(doc_id):
            logger.info(f"'{url}' already ingested — skipping.")
            return {"doc_id": doc_id, "chunks_added": 0, "source": url}

        print(f"🌐 Ingesting URL: {url}")
        chunks, metadata = self.web_processor.process(url)
        if not chunks:
            print("  ⚠️  No content extracted.")
            return {"doc_id": doc_id, "chunks_added": 0, "source": url}

        added = self.vector_store.add(chunks, metadata, doc_id)
        self.summary_store.register_document(
            doc_id=doc_id,
            source=url,
            source_type="web",
            chunk_count=added,
        )

        if build_graph and added:
            self.link_agent.build_graph_from_store(sample_size=20)

        print(f"  ✅ {added} chunks stored.")
        return {"doc_id": doc_id, "chunks_added": added, "source": url}

    def ingest_text(
        self, text: str, label: str = "note", build_graph: bool = False
    ) -> Dict:
        """Ingest a raw text string (quick notes, clipboard content, etc.)."""
        doc_id = self._make_doc_id(label)
        print(f"📝 Ingesting text: '{label}'")
        chunks, metadata = self.text_processor.process_string(text, label)
        added = self.vector_store.add(chunks, metadata, doc_id)
        self.summary_store.register_document(
            doc_id=doc_id,
            source=label,
            source_type="text",
            chunk_count=added,
        )
        if build_graph and added:
            self.link_agent.build_graph_from_store(sample_size=10)
        print(f"  ✅ {added} chunks stored.")
        return {"doc_id": doc_id, "chunks_added": added, "source": label}

    def ingest_file(self, path: str, build_graph: bool = False) -> Dict:
        """Auto-detect file type and ingest."""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            return self.ingest_pdf(path, build_graph)
        elif ext in (".txt", ".md", ".rst"):
            doc_id = self._make_doc_id(path)
            print(f"📄 Ingesting file: {path}")
            chunks, metadata = self.text_processor.process(path)
            added = self.vector_store.add(chunks, metadata, doc_id)
            self.summary_store.register_document(
                doc_id, os.path.basename(path), "text", added
            )
            print(f"  ✅ {added} chunks stored.")
            return {"doc_id": doc_id, "chunks_added": added, "source": path}
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    # ==================================================================
    # Querying
    # ==================================================================

    def ask(
        self,
        question: str,
        source_filter: Optional[str] = None,
        verbose: bool = True,
    ) -> str:
        """
        Ask a question and get a grounded answer from your knowledge base.

        Args:
            question:      Natural-language question.
            source_filter: Restrict search to a specific source file/URL.
            verbose:       Print source info to stdout.

        Returns:
            Answer string.
        """
        result = self.query_agent.query(
            question, source_filter=source_filter
        )

        if verbose:
            print(f"\n💭 Sources: {result['sources']}")
            scores = [f"{s:.2f}" for s in result["relevance_scores"]]
            print(f"   Relevance: {scores}")

        return result["answer"]

    def clear_conversation(self):
        """Reset the multi-turn conversation history."""
        self.query_agent.clear_history()

    # ==================================================================
    # Insights & Summaries
    # ==================================================================

    def get_insights(self, n: int = 3) -> str:
        """Generate daily insights by surfacing cross-document connections."""
        print("🔍 Generating insights…")
        return self.insight_agent.generate_daily_insights(n_insights=n)

    def summarize(self, topic: str) -> str:
        """Summarise all knowledge about a topic."""
        print(f"📋 Summarising topic: '{topic}'…")
        return self.insight_agent.summarize_topic(topic)

    def summarize_document(
        self, source_name: str, force_refresh: bool = False
    ) -> Dict:
        """Summarise a specific ingested document."""
        print(f"📋 Summarising document: '{source_name}'…")
        return self.insight_agent.summarize_document(source_name, force_refresh)

    def compare(self, topic1: str, topic2: str) -> str:
        """Compare two topics from your knowledge base."""
        return self.insight_agent.compare_topics(topic1, topic2)

    def generate_questions(self, topic: str, n: int = 5) -> List[str]:
        """Generate study questions about a topic."""
        return self.insight_agent.generate_questions(topic, n)

    # ==================================================================
    # Knowledge Graph
    # ==================================================================

    def find_connection(self, concept1: str, concept2: str) -> Dict:
        """Find and explain the connection between two concepts."""
        return self.link_agent.find_connections(concept1, concept2)

    def build_knowledge_graph(self, sample_size: int = 50):
        """Rebuild the concept graph from the current vector store."""
        print("🕸️  Building knowledge graph…")
        self.link_agent.build_graph_from_store(sample_size=sample_size)
        stats = self.knowledge_graph.stats()
        print(
            f"  ✅ Graph: {stats['nodes']} nodes, {stats['edges']} edges"
        )

    def get_related_concepts(
        self, concept: str, depth: int = 2
    ) -> List[str]:
        """Return concepts related to *concept* within *depth* hops."""
        return self.knowledge_graph.get_related(concept, depth)

    def get_central_concepts(self, top_n: int = 10):
        """Return the most important concepts by PageRank."""
        return self.knowledge_graph.get_central_concepts(top_n)

    # ==================================================================
    # Management & Introspection
    # ==================================================================

    def stats(self) -> Dict:
        """Return an overview of the entire knowledge base."""
        vector_stats = self.vector_store.stats()
        graph_stats = self.knowledge_graph.stats()
        docs = self.summary_store.list_documents()
        return {
            "documents_ingested": len(docs),
            "total_chunks": vector_stats["total_chunks"],
            "sources": vector_stats["sources"],
            "graph": graph_stats,
            "recent_documents": docs[:5],
        }

    def list_documents(self) -> List[Dict]:
        """List all ingested documents."""
        return self.summary_store.list_documents()

    def recent_insights(self, limit: int = 5) -> List[Dict]:
        """Return previously generated insights."""
        return self.summary_store.get_recent_insights(limit)

    def search(self, query: str, n: int = 5) -> List[Dict]:
        """Raw semantic search — returns chunks with metadata."""
        return self.vector_store.search(query, n_results=n)

    # ==================================================================
    # Internal helpers
    # ==================================================================

    @staticmethod
    def _make_doc_id(source: str) -> str:
        """Deterministic, filesystem-safe document identifier."""
        import hashlib
        safe = "".join(c if c.isalnum() else "_" for c in source)
        suffix = hashlib.md5(source.encode()).hexdigest()[:8]
        return f"{safe[:60]}_{suffix}"
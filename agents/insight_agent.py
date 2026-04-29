import logging
import random
from typing import Dict, List, Optional

import ollama

from storage.vector_store import VectorStore
from storage.summary_store import SummaryStore
from storage.graph_store import KnowledgeGraph

logger = logging.getLogger(__name__)


class InsightAgent:
    """
    Generates summaries, daily insight digests, and cross-topic
    connections by reasoning over stored knowledge.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        summary_store: SummaryStore,
        knowledge_graph: KnowledgeGraph,
        model: str = "mistral:7b",
    ):
        self.store = vector_store
        self.summaries = summary_store
        self.graph = knowledge_graph
        self.model = model

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------

    def summarize_document(
        self, source_name: str, force_refresh: bool = False
    ) -> Dict:
        """
        Summarise all chunks belonging to *source_name*.
        Result is cached in SummaryStore.
        """
        # Return cached version unless forced
        if not force_refresh:
            cached = self.summaries.get_summary(source_name)
            if cached:
                logger.info(f"Returning cached summary for '{source_name}'")
                return cached

        results = self.store.search(
            source_name, n_results=15, where={"source": source_name}
        )
        if not results:
            return {"summary": "No content found for this source.", "key_points": []}

        combined = "\n\n".join(r["content"] for r in results)

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Create a structured summary of this document: '{source_name}'\n\n"
                        f"Content:\n{combined}\n\n"
                        "Format:\n"
                        "## Summary\n<2–3 paragraph overview>\n\n"
                        "## Key Points\n- point 1\n- point 2\n…"
                    ),
                }
            ],
            options={"temperature": 0.4},
        )
        full_text = response["message"]["content"]

        # Parse key points
        key_points = [
            line.lstrip("-• ").strip()
            for line in full_text.splitlines()
            if line.strip().startswith(("-", "•"))
        ]

        self.summaries.save_summary(source_name, full_text, key_points)
        return {"summary": full_text, "key_points": key_points}

    def summarize_topic(self, topic: str) -> str:
        """Free-form topic summary drawing from the entire knowledge base."""
        cached = self.summaries.get_topic_map(topic)
        if cached:
            return cached

        results = self.store.search(topic, n_results=12)
        if not results:
            return f"No information found about '{topic}' in the knowledge base."

        combined = "\n\n".join(r["content"] for r in results)

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Summarise everything in the knowledge base about: {topic}\n\n"
                        f"Relevant excerpts:\n{combined}\n\n"
                        "Write a clear, structured summary with headings and bullet points:"
                    ),
                }
            ],
            options={"temperature": 0.4},
        )
        summary = response["message"]["content"]
        self.summaries.save_topic_map(topic, summary)
        return summary

    # ------------------------------------------------------------------
    # Insights
    # ------------------------------------------------------------------

    def generate_daily_insights(self, n_insights: int = 3) -> str:
        """
        Surface surprising connections by picking random chunks and
        asking the LLM to reason across them.
        """
        all_docs = self.store.get_all_documents()
        if len(all_docs) < 2:
            return "Not enough content yet — add more documents first!"

        sample = random.sample(all_docs, min(10, len(all_docs)))
        snippets = "\n\n---\n\n".join(
            f"Source: {d['metadata'].get('source', '?')}\n{d['content'][:300]}"
            for d in sample
        )

        central = self.graph.get_central_concepts(top_n=5)
        central_str = ", ".join(c for c, _ in central) if central else "N/A"

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"You are analysing a personal knowledge base.\n"
                        f"Central concepts (by importance): {central_str}\n\n"
                        f"Random knowledge snippets:\n{snippets}\n\n"
                        f"Generate exactly {n_insights} surprising insights or "
                        "non-obvious connections between different pieces of "
                        "knowledge. Be specific and thought-provoking.\n"
                        "Format each insight as:\n"
                        "💡 **Insight N**: <title>\n<explanation>"
                    ),
                }
            ],
            options={"temperature": 0.7},
        )
        insight_text = response["message"]["content"]
        self.summaries.save_insight(insight_text)
        return insight_text

    def compare_topics(self, topic1: str, topic2: str) -> str:
        """Compare and contrast two topics from the knowledge base."""
        results1 = self.store.search(topic1, n_results=6)
        results2 = self.store.search(topic2, n_results=6)

        ctx1 = "\n".join(r["content"] for r in results1)
        ctx2 = "\n".join(r["content"] for r in results2)

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Compare and contrast '{topic1}' and '{topic2}' "
                        "using only the knowledge base excerpts below.\n\n"
                        f"## {topic1}\n{ctx1}\n\n"
                        f"## {topic2}\n{ctx2}\n\n"
                        "Provide:\n"
                        "1. Key similarities\n"
                        "2. Key differences\n"
                        "3. How they complement each other"
                    ),
                }
            ],
            options={"temperature": 0.4},
        )
        return response["message"]["content"]

    def generate_questions(self, topic: str, n: int = 5) -> List[str]:
        """Generate study/research questions based on stored knowledge."""
        results = self.store.search(topic, n_results=8)
        combined = "\n".join(r["content"] for r in results)

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Based on this knowledge about '{topic}':\n\n{combined}\n\n"
                        f"Generate {n} thought-provoking questions that would "
                        "deepen understanding or reveal gaps in knowledge. "
                        "Number each question."
                    ),
                }
            ],
            options={"temperature": 0.6},
        )
        lines = response["message"]["content"].splitlines()
        return [
            line.strip()
            for line in lines
            if line.strip() and line.strip()[0].isdigit()
        ][:n]
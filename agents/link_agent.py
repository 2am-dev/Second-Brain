import json
import logging
from typing import Dict, List, Tuple

import ollama

from storage.vector_store import VectorStore
from storage.graph_store import KnowledgeGraph

logger = logging.getLogger(__name__)


class LinkAgent:
    """
    Analyses ingested chunks to extract concepts and relationships,
    then populates the KnowledgeGraph automatically.
    """

    EXTRACT_PROMPT = """
You are a knowledge-graph extraction engine.
Given the text below, extract:
1. Key concepts (nouns / noun-phrases, max 8 per chunk).
2. Relationships between those concepts.

Return ONLY valid JSON in this exact format:
{{
  "concepts": ["concept1", "concept2"],
  "relationships": [
    {{"from": "concept1", "to": "concept2", "label": "relationship_type"}}
  ]
}}

Text:
{text}
"""

    def __init__(
        self,
        vector_store: VectorStore,
        knowledge_graph: KnowledgeGraph,
        model: str = "mistral:7b",
    ):
        self.store = vector_store
        self.graph = knowledge_graph
        self.model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_graph_from_store(self, sample_size: int = 50):
        """
        Pull chunks from the vector store and build the knowledge graph.
        Call this after ingesting new documents.
        """
        all_docs = self.store.get_all_documents()
        # Sample evenly to avoid overly long runs on huge corpora
        step = max(1, len(all_docs) // sample_size)
        sampled = all_docs[::step][:sample_size]

        logger.info(
            f"Building graph from {len(sampled)} sampled chunks "
            f"(corpus: {len(all_docs)})…"
        )
        for item in sampled:
            self._process_chunk(item["content"], item["metadata"])

        logger.info(
            f"Graph built — {self.graph.stats()['nodes']} nodes, "
            f"{self.graph.stats()['edges']} edges"
        )

    def find_connections(
        self, topic1: str, topic2: str
    ) -> Dict:
        """Return graph path + semantic bridge between two topics."""
        path = self.graph.find_path(topic1, topic2)

        # Semantic bridge via vector store
        bridge_results = self.store.search(
            f"connection between {topic1} and {topic2}", n_results=3
        )
        bridge_text = "\n".join(r["content"] for r in bridge_results)

        if bridge_text:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Explain the connection between '{topic1}' "
                            f"and '{topic2}' using this context:\n\n"
                            f"{bridge_text}"
                        ),
                    }
                ],
            )
            explanation = response["message"]["content"]
        else:
            explanation = "No direct semantic connection found in the knowledge base."

        return {
            "graph_path": path,
            "explanation": explanation,
            "supporting_chunks": [r["metadata"]["source"] for r in bridge_results],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_chunk(self, text: str, metadata: Dict):
        try:
            concepts, relationships = self._extract(text)
            source = metadata.get("source", "unknown")

            for concept in concepts:
                self.graph.add_concept(concept, {"source": source})

            for rel in relationships:
                self.graph.add_relationship(
                    rel["from"], rel["to"], rel["label"], weight=1.0
                )
        except Exception as exc:
            logger.warning(f"LinkAgent skipped a chunk: {exc}")

    def _extract(self, text: str) -> Tuple[List[str], List[Dict]]:
        """Call LLM to extract concepts + relationships as JSON."""
        prompt = self.EXTRACT_PROMPT.format(text=text[:1500])   # trim for speed
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.1},
        )
        raw = response["message"]["content"]

        # Robustly parse — the model sometimes adds markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        concepts = [str(c).lower().strip() for c in data.get("concepts", [])]
        relationships = [
            {
                "from": str(r.get("from", "")).lower().strip(),
                "to": str(r.get("to", "")).lower().strip(),
                "label": str(r.get("label", "related_to")).lower().strip(),
            }
            for r in data.get("relationships", [])
            if r.get("from") and r.get("to")
        ]
        return concepts, relationships
import logging
from typing import Dict, List, Optional

import ollama

from storage.vector_store import VectorStore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a precise personal knowledge assistant.
Your job is to answer questions using ONLY the provided context
excerpts from the user's knowledge base.

Rules:
- Cite the source file/URL for every claim you make.
- If the context does not contain enough information, say so clearly
  and suggest what additional material might help.
- Never fabricate facts not present in the context.
- Use bullet points for multi-part answers."""


class QueryAgent:
    """
    Retrieval-Augmented Generation (RAG) agent.
    Searches the vector store, builds a context window, and
    calls the LLM to produce a grounded answer.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        model: str = "mistral:7b",
        max_history_turns: int = 6,
    ):
        self.store = vector_store
        self.model = model
        self.max_history = max_history_turns * 2   # each turn = 2 messages
        self.conversation_history: List[Dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(
        self,
        question: str,
        n_results: int = 5,
        source_filter: Optional[str] = None,
        use_history: bool = True,
    ) -> Dict:
        """
        Ask a question and get a grounded answer.

        Returns:
            {
                "answer": str,
                "sources": List[str],
                "relevance_scores": List[float],
                "context_used": List[str],
            }
        """
        where = {"source": source_filter} if source_filter else None
        results = self.store.search(question, n_results=n_results, where=where)

        if not results:
            return {
                "answer": (
                    "I couldn't find any relevant information in your "
                    "knowledge base for that question."
                ),
                "sources": [],
                "relevance_scores": [],
                "context_used": [],
            }

        context = self._build_context(results)
        messages = self._build_messages(question, context, use_history)

        logger.info(f"Querying model '{self.model}' with {len(results)} context chunks…")
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options={"temperature": 0.3},
        )
        answer = response["message"]["content"]

        # Persist conversation for multi-turn use
        self.conversation_history.extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ])
        # Trim to window
        self.conversation_history = self.conversation_history[-self.max_history:]

        return {
            "answer": answer,
            "sources": list({r["metadata"]["source"] for r in results}),
            "relevance_scores": [r["relevance"] for r in results],
            "context_used": [r["content"][:120] + "…" for r in results],
        }

    def clear_history(self):
        self.conversation_history = []
        logger.info("Conversation history cleared.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context(results: List[Dict]) -> str:
        parts = []
        for i, r in enumerate(results, 1):
            src = r["metadata"].get("source", "unknown")
            score = r["relevance"]
            parts.append(
                f"[{i}] Source: {src} (relevance: {score:.2f})\n{r['content']}"
            )
        return "\n\n---\n\n".join(parts)

    def _build_messages(
        self, question: str, context: str, use_history: bool
    ) -> List[Dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if use_history and self.conversation_history:
            messages.extend(self.conversation_history)

        messages.append(
            {
                "role": "user",
                "content": (
                    f"KNOWLEDGE BASE CONTEXT:\n{context}\n\n"
                    f"QUESTION: {question}\n\n"
                    "Answer using only the context above:"
                ),
            }
        )
        return messages
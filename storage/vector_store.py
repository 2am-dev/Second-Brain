import chromadb
import ollama
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """
    Handles document embedding and semantic search using ChromaDB.
    Embeddings are generated locally via Ollama (nomic-embed-text).
    """

    def __init__(
        self,
        collection_name: str = "second_brain",
        db_path: str = "./brain_db",
        embed_model: str = "nomic-embed-text",
    ):
        self.embed_model = embed_model
        self.db_path = db_path

        # Persistent client so data survives restarts
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"VectorStore ready — collection '{collection_name}' "
            f"has {self.collection.count()} documents"
        )

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text string."""
        response = ollama.embeddings(model=self.embed_model, prompt=text)
        return response["embedding"]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts, logging progress for large batches."""
        embeddings = []
        for i, text in enumerate(texts, 1):
            embeddings.append(self.embed(text))
            if i % 10 == 0:
                logger.info(f"  Embedded {i}/{len(texts)} chunks…")
        return embeddings

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def add(
        self,
        chunks: List[str],
        metadata: List[Dict],
        doc_id: str,
    ) -> int:
        """
        Store chunks with their embeddings.
        Returns the number of chunks actually added (skips duplicates).
        """
        if not chunks:
            logger.warning("add() called with empty chunks list — skipping.")
            return 0

        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

        # Skip chunks that are already stored (idempotent ingestion)
        existing = set(self.collection.get(ids=ids)["ids"])
        new_chunks, new_meta, new_ids = [], [], []
        for chunk, meta, cid in zip(chunks, metadata, ids):
            if cid not in existing:
                new_chunks.append(chunk)
                new_meta.append(meta)
                new_ids.append(cid)

        if not new_chunks:
            logger.info(f"All chunks for '{doc_id}' already stored — skipping.")
            return 0

        embeddings = self.embed_batch(new_chunks)
        self.collection.add(
            documents=new_chunks,
            embeddings=embeddings,
            metadatas=new_meta,
            ids=new_ids,
        )
        logger.info(f"Stored {len(new_chunks)} new chunks for doc '{doc_id}'")
        return len(new_chunks)

    def delete_document(self, doc_id: str):
        """Remove all chunks that belong to a document."""
        results = self.collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks for doc '{doc_id}'")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Semantic search. Returns a list of result dicts:
            {content, metadata, relevance (0–1)}
        """
        query_embedding = self.embed(query)

        kwargs = dict(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        return [
            {
                "content": doc,
                "metadata": meta,
                "relevance": round(1 - dist, 4),
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def get_all_documents(self) -> List[Dict]:
        """Return every stored chunk (useful for inspection / export)."""
        data = self.collection.get(include=["documents", "metadatas"])
        return [
            {"id": cid, "content": doc, "metadata": meta}
            for cid, doc, meta in zip(
                data["ids"], data["documents"], data["metadatas"]
            )
        ]

    def count(self) -> int:
        return self.collection.count()

    def stats(self) -> Dict:
        """High-level statistics about the collection."""
        all_docs = self.get_all_documents()
        sources = {}
        for item in all_docs:
            src = item["metadata"].get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        return {
            "total_chunks": self.count(),
            "sources": sources,
            "db_path": self.db_path,
        }
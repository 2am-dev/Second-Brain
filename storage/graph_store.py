import networkx as nx
import pickle
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """
    Directed concept graph stored as a pickled NetworkX DiGraph.
    Nodes  = concepts / topics extracted from ingested documents.
    Edges  = named relationships with optional weights.
    """

    def __init__(self, path: str = "./brain_graph.pkl"):
        self.path = path
        self.graph: nx.DiGraph = self._load()
        logger.info(
            f"KnowledgeGraph loaded — "
            f"{self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> nx.DiGraph:
        try:
            with open(self.path, "rb") as fh:
                return pickle.load(fh)
        except FileNotFoundError:
            return nx.DiGraph()

    def save(self):
        with open(self.path, "wb") as fh:
            pickle.dump(self.graph, fh)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_concept(self, concept: str, metadata: Optional[Dict] = None):
        """Add a node; silently updates metadata if node already exists."""
        self.graph.add_node(concept, **(metadata or {}))
        self.save()

    def add_relationship(
        self,
        concept1: str,
        concept2: str,
        relationship: str,
        weight: float = 1.0,
        bidirectional: bool = False,
    ):
        """
        Add a directed edge concept1 → concept2.
        Set bidirectional=True to also add concept2 → concept1.
        """
        # Ensure nodes exist
        for c in (concept1, concept2):
            if c not in self.graph:
                self.graph.add_node(c)

        self.graph.add_edge(
            concept1, concept2, relationship=relationship, weight=weight
        )
        if bidirectional:
            self.graph.add_edge(
                concept2, concept1, relationship=relationship, weight=weight
            )
        self.save()

    def remove_concept(self, concept: str):
        if concept in self.graph:
            self.graph.remove_node(concept)
            self.save()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_related(self, concept: str, depth: int = 2) -> List[str]:
        """BFS neighbours within *depth* hops (both directions)."""
        if concept not in self.graph:
            return []
        undirected = self.graph.to_undirected()
        related = set(nx.ego_graph(undirected, concept, radius=depth).nodes())
        related.discard(concept)
        return sorted(related)

    def find_path(self, concept1: str, concept2: str) -> List[str]:
        """Shortest directed path; empty list if none exists."""
        try:
            return nx.shortest_path(self.graph, concept1, concept2)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_central_concepts(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Most connected concepts by PageRank."""
        if not self.graph.number_of_nodes():
            return []
        scores = nx.pagerank(self.graph, weight="weight")
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def get_clusters(self) -> List[List[str]]:
        """Weakly-connected components (topic clusters)."""
        undirected = self.graph.to_undirected()
        return [
            sorted(component)
            for component in nx.connected_components(undirected)
        ]

    def search_concepts(self, query: str) -> List[str]:
        """Simple substring search over node names."""
        q = query.lower()
        return [n for n in self.graph.nodes() if q in n.lower()]

    def stats(self) -> Dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
            "components": nx.number_weakly_connected_components(self.graph),
        }
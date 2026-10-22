from backend.config.settings import get_settings
from backend.vectorstore.qdrant_service import QdrantService
from backend.retrieval.bm25_service import BM25Service
from backend.embeddings.embedding_service import EmbeddingService
from backend.models.schemas import RetrievedChunk, SourceType
from backend.utils.helpers import generate_short_id
from backend.utils.logger import get_logger


logger = get_logger(__name__)


class HybridRetrievalService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.settings = get_settings()
            self.qdrant = QdrantService()
            self.bm25 = BM25Service()
            self.embedding_service = EmbeddingService()
            self._initialized = True

    def rebuild_bm25_index(self):
        self.bm25.rebuild_from_qdrant(self.qdrant)

    def dense_search(self, query: str, top_k: int = 10, source_type: str = None) -> list[dict]:
        query_embedding = self.embedding_service.embed_query(query)
        if source_type:
            return self.qdrant.search_by_source_type(query_embedding, source_type, top_k)
        return self.qdrant.search(query_vector=query_embedding, top_k=top_k)

    def sparse_search(self, query: str, top_k: int = 10, source_type: str = None) -> list[dict]:
        if not self.bm25.is_ready:
            self.rebuild_bm25_index()
        results = self.bm25.search(query, top_k=top_k * 2)
        if source_type:
            results = [r for r in results if r.get("metadata", {}).get("source_type") == source_type]
        return results

    def initial_retrieval(
        self, query: str, top_k: int = None, alpha: float = 0.7, source_type: str = None
    ) -> list[RetrievedChunk]:
        """Initial retrieval without reranking - returns larger candidate set."""
        initial_top_k = top_k or self.settings.INITIAL_RETRIEVAL_TOP_K
        
        dense_results = self.dense_search(query, top_k=initial_top_k * 3, source_type=source_type)
        sparse_results = self.sparse_search(query, top_k=initial_top_k * 3, source_type=source_type)

        merged = self._rrf_fusion(dense_results, sparse_results, alpha)

        filtered = [r for r in merged if r.get("score", 0) >= self.settings.MIN_SIMILARITY_THRESHOLD]

        top_results = filtered[:initial_top_k]
        chunks = []
        for r in top_results:
            metadata = r.get("metadata", {})
            citation = f"{r.get('document_name', 'Unknown')}, p.{r.get('page_number', '?')}"
            source_type_val = metadata.get("source_type", "uploaded")
            chunk = RetrievedChunk(
                id=r.get("id", generate_short_id()),
                content=r.get("content", ""),
                document_name=r.get("document_name", "Unknown"),
                page_number=r.get("page_number", 0),
                similarity_score=round(r.get("score", 0.0), 4),
                chunk_score=round(r.get("final_score", 0.0), 4),
                citation=citation,
                metadata=metadata,
                source_type=SourceType(source_type_val) if source_type_val in [s.value for s in SourceType] else SourceType.UPLOADED,
                source_url=metadata.get("source_url"),
                page_type=metadata.get("page_type"),
                department=metadata.get("department"),
            )
            chunks.append(chunk)
        
        logger.debug(f"Initial retrieval returned {len(chunks)} candidates for query: {query[:50]}...")
        return chunks

    def hybrid_search(
        self, query: str, top_k: int = 5, alpha: float = 0.7, source_type: str = None
    ) -> list[RetrievedChunk]:
        """Backward compatible method - uses final top_k for both retrieval and reranking."""
        return self.initial_retrieval(query, top_k=top_k, alpha=alpha, source_type=source_type)

    def _rrf_fusion(
        self,
        dense_results: list[dict],
        sparse_results: list[dict],
        alpha: float,
    ) -> list[dict]:
        k = 60
        score_map: dict[str, dict] = {}

        for rank, result in enumerate(dense_results):
            doc_id = result.get("id", "")
            if doc_id not in score_map:
                score_map[doc_id] = result.copy()
                score_map[doc_id]["final_score"] = 0.0
            dense_score = alpha * (1.0 / (k + rank + 1))
            score_map[doc_id]["final_score"] += dense_score

        for rank, result in enumerate(sparse_results):
            doc_id = result.get("id", "")
            if doc_id not in score_map:
                score_map[doc_id] = result.copy()
                score_map[doc_id]["final_score"] = 0.0
            sparse_score = (1 - alpha) * (1.0 / (k + rank + 1))
            score_map[doc_id]["final_score"] += sparse_score

        merged = sorted(
            score_map.values(), key=lambda x: x["final_score"], reverse=True
        )
        return merged

    def get_index_stats(self) -> dict:
        qdrant_info = self.qdrant.get_collection_info()
        return {
            "total_vectors": qdrant_info.get("vectors_count", 0),
            "bm25_ready": self.bm25.is_ready,
            "bm25_corpus_size": len(self.bm25.corpus_chunks),
        }

    def search_griet_only(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return self.initial_retrieval(query, top_k=top_k, source_type="griet")

    def search_uploaded_only(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return self.initial_retrieval(query, top_k=top_k, source_type="uploaded")
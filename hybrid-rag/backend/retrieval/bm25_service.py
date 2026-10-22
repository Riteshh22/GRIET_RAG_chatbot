from rank_bm25 import BM25Okapi
import numpy as np
from backend.vectorstore.qdrant_service import QdrantService


class BM25Service:
    def __init__(self):
        self.bm25 = None
        self.corpus_chunks = []
        self.corpus_tokens = []
        self._built = False

    def build_index(self, chunks: list[dict]):
        self.corpus_chunks = chunks
        self.corpus_tokens = [
            self._tokenize(chunk.get("content", "")) for chunk in chunks
        ]
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
            self._built = True

    def _tokenize(self, text: str) -> list[str]:
        return text.lower().split()

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        if not self._built or self.bm25 is None:
            return []

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        if len(scores) == 0:
            return []

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                chunk = self.corpus_chunks[idx].copy()
                chunk["score"] = float(scores[idx])
                results.append(chunk)
        return results

    def rebuild_from_qdrant(self, qdrant_service: QdrantService):
        all_chunks = qdrant_service.get_all_chunks_for_bm25()
        if all_chunks:
            self.build_index(all_chunks)

    @property
    def is_ready(self) -> bool:
        return self._built and len(self.corpus_chunks) > 0

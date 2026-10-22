import json
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from backend.config.settings import get_settings
from backend.models.schemas import ChunkData


class QdrantService:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if QdrantService._client is None:
            self.settings = get_settings()
            QdrantService._client = QdrantClient(
                host=self.settings.QDRANT_HOST,
                port=self.settings.QDRANT_PORT,
            )
            self._ensure_collection()

    @property
    def client(self):
        return QdrantService._client

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        if self.settings.QDRANT_COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=self.settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=self.settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_chunks(
        self, chunks: list[ChunkData], embeddings: list[list[float]]
    ) -> int:
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            payload = {
                "content": chunk.content,
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata,
            }
            points.append(
                PointStruct(
                    id=hash(chunk.id) % (2**63),
                    vector=embedding,
                    payload=payload,
                )
            )

        batch_size = 100
        total_upserted = 0
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=self.settings.QDRANT_COLLECTION,
                points=batch,
            )
            total_upserted += len(batch)
        return total_upserted

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        document_id: str | None = None,
    ) -> list[dict]:
        query_filter = None
        if document_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )

        results = self.client.search(
            collection_name=self.settings.QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )

        formatted = []
        for result in results:
            payload = result.payload or {}
            formatted.append(
                {
                    "id": str(result.id),
                    "score": result.score,
                    "content": payload.get("content", ""),
                    "document_id": payload.get("document_id", ""),
                    "document_name": payload.get("document_name", ""),
                    "page_number": payload.get("page_number", 0),
                    "chunk_index": payload.get("chunk_index", 0),
                    "metadata": payload.get("metadata", {}),
                }
            )
        return formatted

    def delete_by_document(self, document_id: str) -> bool:
        self.client.delete(
            collection_name=self.settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        return True

    def get_collection_info(self) -> dict:
        try:
            info = self.client.get_collection(self.settings.QDRANT_COLLECTION)
            return {
                "vectors_count": info.vectors_count or 0,
                "points_count": info.points_count or 0,
                "status": str(info.status),
            }
        except Exception:
            return {"vectors_count": 0, "points_count": 0, "status": "not_found"}

    def get_all_chunks_for_bm25(self) -> list[dict]:
        try:
            results = self.client.scroll(
                collection_name=self.settings.QDRANT_COLLECTION,
                limit=10000,
                with_payload=True,
                with_vectors=False,
            )
            chunks = []
            for point in results[0]:
                payload = point.payload or {}
                chunks.append(
                    {
                        "id": str(point.id),
                        "content": payload.get("content", ""),
                        "document_id": payload.get("document_id", ""),
                        "document_name": payload.get("document_name", ""),
                        "page_number": payload.get("page_number", 0),
                        "chunk_index": payload.get("chunk_index", 0),
                        "metadata": payload.get("metadata", {}),
                    }
                )
            return chunks
        except Exception:
            return []

    def is_connected(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

    def get_by_content_hash(self, content_hash: str) -> list[dict]:
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            results = self.client.scroll(
                collection_name=self.settings.QDRANT_COLLECTION,
                limit=1,
                with_payload=True,
                with_vectors=False,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.content_hash",
                            match=MatchValue(value=content_hash),
                        )
                    ]
                ),
            )
            return results[0] if results[0] else []
        except Exception:
            return []

    def search_by_source_type(self, query_vector: list[float], source_type: str, top_k: int = 10) -> list[dict]:
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            results = self.client.search(
                collection_name=self.settings.QDRANT_COLLECTION,
                query_vector=query_vector,
                limit=top_k,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.source_type",
                            match=MatchValue(value=source_type),
                        )
                    ]
                ),
            )
            formatted = []
            for result in results:
                payload = result.payload or {}
                formatted.append({
                    "id": str(result.id),
                    "score": result.score,
                    "content": payload.get("content", ""),
                    "document_id": payload.get("document_id", ""),
                    "document_name": payload.get("document_name", ""),
                    "page_number": payload.get("page_number", 0),
                    "chunk_index": payload.get("chunk_index", 0),
                    "metadata": payload.get("metadata", {}),
                })
            return formatted
        except Exception:
            return []

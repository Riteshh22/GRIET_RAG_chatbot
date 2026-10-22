from abc import ABC, abstractmethod
from sentence_transformers import CrossEncoder
from backend.config.settings import get_settings
from backend.models.schemas import RetrievedChunk
from backend.utils.logger import get_logger


logger = get_logger(__name__)


class BaseReranker(ABC):
    """Abstract base class for rerankers to allow easy swapping."""

    @abstractmethod
    def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_k: int = 5, min_score: float = None
    ) -> list[RetrievedChunk]:
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass


class CrossEncoderReranker(BaseReranker):
    """Cross-encoder based reranker using sentence-transformers."""

    _instance = None
    _model = None
    _model_name = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if CrossEncoderReranker._model is None:
            self.settings = get_settings()
            self._model_name = self.settings.RERANKER_MODEL
            self._batch_size = self.settings.RERANKER_BATCH_SIZE
            try:
                CrossEncoderReranker._model = CrossEncoder(
                    self._model_name,
                    max_length=512,
                )
                logger.info(f"Reranker model loaded: {self._model_name}")
            except Exception as e:
                logger.error(f"Failed to load reranker model: {e}")
                CrossEncoderReranker._model = None

    def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_k: int = 5, min_score: float = None
    ) -> list[RetrievedChunk]:
        if CrossEncoderReranker._model is None or not chunks:
            return chunks[:top_k]

        min_score = min_score or self.settings.MIN_RERANK_THRESHOLD

        pairs = [(query, chunk.content) for chunk in chunks]
        
        scores = CrossEncoderReranker._model.predict(
            pairs, 
            batch_size=self._batch_size,
            show_progress_bar=False
        )

        for chunk, score in zip(chunks, scores):
            chunk.chunk_score = round(float(score), 4)

        reranked = sorted(chunks, key=lambda x: x.chunk_score, reverse=True)
        filtered = [c for c in reranked if c.chunk_score >= min_score]
        
        logger.debug(
            f"Reranked {len(chunks)} chunks, kept {len(filtered)} above threshold {min_score}"
        )
        return filtered[:top_k]

    @property
    def is_available(self) -> bool:
        return CrossEncoderReranker._model is not None

    @property
    def model_name(self) -> str:
        return self._model_name


class RerankerService:
    """Service that manages the active reranker implementation."""

    _instance = None
    _reranker: BaseReranker = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RerankerService._reranker is None:
            self.settings = get_settings()
            RerankerService._reranker = CrossEncoderReranker()

    def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_k: int = 5, min_score: float = None
    ) -> list[RetrievedChunk]:
        return self._reranker.rerank(query, chunks, top_k, min_score)

    @property
    def is_available(self) -> bool:
        return self._reranker.is_available

    @property
    def model_name(self) -> str:
        return self._reranker.model_name

    def set_reranker(self, reranker: BaseReranker):
        """Allow swapping reranker implementation (for testing or different models)."""
        RerankerService._reranker = reranker
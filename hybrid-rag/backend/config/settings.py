import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "GRIET RAG Chatbot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "griet_rag_chunks"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384

    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    RERANKER_ENABLED: bool = True
    RERANKER_BATCH_SIZE: int = 32
    INITIAL_RETRIEVAL_TOP_K: int = 20
    FINAL_RERANK_TOP_N: int = 5

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K: int = 5
    HYBRID_ALPHA: float = 0.7

    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2048

    UPLOAD_DIR: str = "uploads"
    DOCUMENTS_DIR: str = "documents"

    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt", ".csv", ".md"}

    GRIET_BASE_URL: str = "https://www.griet.ac.in"
    GRIET_MAX_PAGES: int = 500
    GRIET_CRAWL_DELAY: float = 1.0
    GRIET_AUTO_CRAWL_ENABLED: bool = True
    GRIET_CRAWL_INTERVAL_HOURS: int = 24

    SERPER_API_KEY: str = ""
    WEB_SEARCH_ENABLED: bool = True
    WEB_SEARCH_MAX_RESULTS: int = 5

    MIN_SIMILARITY_THRESHOLD: float = 0.35
    MIN_RERANK_THRESHOLD: float = 0.5
    GRIET_CONFIDENCE_THRESHOLD: float = 0.4
    CONTEXT_RELEVANCE_THRESHOLD: float = 0.3

    EVALUATION_DATASET_PATH: str = "backend/evaluation/dataset.jsonl"
    EVALUATION_ENABLED: bool = True

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class SourceType(str, Enum):
    GRIET = "griet"
    WEB = "web"
    UPLOADED = "uploaded"


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    pages: int = 0
    chunks: int = 0
    status: DocumentStatus = DocumentStatus.UPLOADING
    upload_time: str = ""
    indexed: bool = False
    source_type: SourceType = SourceType.UPLOADED
    source_url: Optional[str] = None
    page_type: Optional[str] = None
    department: Optional[str] = None
    document_type: Optional[str] = None
    crawl_time: Optional[str] = None


class ChunkData(BaseModel):
    id: str
    content: str
    document_id: str
    document_name: str
    page_number: int = 0
    chunk_index: int = 0
    similarity_score: float = 0.0
    metadata: dict = {}


class RetrievedChunk(BaseModel):
    id: str
    content: str
    document_name: str
    page_number: int = 0
    similarity_score: float = 0.0
    chunk_score: float = 0.0
    citation: str = ""
    metadata: dict = {}
    source_type: SourceType = SourceType.UPLOADED
    source_url: Optional[str] = None
    page_type: Optional[str] = None
    department: Optional[str] = None


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str = "web"


class ChatMessage(BaseModel):
    role: str = "user"
    content: str = ""
    sources: list[RetrievedChunk] = []
    web_sources: list[WebSearchResult] = []
    timestamp: str = ""
    pipeline_stages: list[dict] = []
    answer_source: str = "griet"


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    history: list[ChatMessage] = []
    top_k: int = 5
    use_reranker: bool = True
    search_mode: str = "auto"
    debug: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources: list[RetrievedChunk] = []
    web_sources: list[WebSearchResult] = []
    conversation_id: str = ""
    pipeline_stages: list[dict] = []
    retrieval_time: float = 0.0
    generation_time: float = 0.0
    total_time: float = 0.0
    answer_source: str = "griet"
    confidence: float = 0.0
    debug_info: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    search_type: str = "hybrid"
    source_type: Optional[str] = None


class SearchResponse(BaseModel):
    results: list[RetrievedChunk] = []
    total_results: int = 0
    query: str = ""


class PipelineStage(BaseModel):
    name: str
    status: str = "pending"
    duration: float = 0.0
    details: str = ""


class SettingsUpdate(BaseModel):
    embedding_model: Optional[str] = None
    llm_model: Optional[str] = None
    top_k: Optional[int] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    hybrid_alpha: Optional[float] = None
    reranker_enabled: Optional[bool] = None
    web_search_enabled: Optional[bool] = None


class SystemInfo(BaseModel):
    app_name: str = "GRIET RAG Chatbot"
    version: str = "1.0.0"
    embedding_model: str = ""
    embedding_dimension: int = 0
    llm_model: str = ""
    vector_db: str = "Qdrant"
    vector_db_status: str = "disconnected"
    ollama_status: str = "disconnected"
    total_documents: int = 0
    total_chunks: int = 0
    reranker_model: str = ""
    reranker_enabled: bool = True
    griet_pages_indexed: int = 0
    web_search_enabled: bool = True


class SystemHealth(BaseModel):
    cpu_usage: float = 0.0
    ram_usage: float = 0.0
    ram_total: float = 0.0
    vector_db_status: str = "disconnected"
    ollama_status: str = "disconnected"
    embedding_model: str = ""
    avg_latency: float = 0.0
    avg_response_time: float = 0.0
    index_size: int = 0


class EvaluationMetrics(BaseModel):
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    mrr: float = 0.0
    map_score: float = 0.0
    ndcg: float = 0.0
    hit_rate: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    context_relevancy: float = 0.0


class GenerationMetrics(BaseModel):
    faithfulness: float = 0.0
    answer_relevancy: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    answer_correctness: float = 0.0
    semantic_similarity: float = 0.0


class HistoryEntry(BaseModel):
    id: str
    query: str
    answer: str
    timestamp: str
    sources_count: int = 0
    retrieval_time: float = 0.0
    answer_source: str = "griet"


class CrawlRequest(BaseModel):
    max_pages: Optional[int] = None
    incremental: bool = False


class CrawlResponse(BaseModel):
    success: bool
    pages_crawled: int = 0
    pages_indexed: int = 0
    pages_skipped: int = 0
    errors: int = 0
    message: str = ""
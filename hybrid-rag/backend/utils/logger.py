import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from backend.config.settings import get_settings


class StructuredLogger:
    """Structured JSON logger for RAG pipeline."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.settings = get_settings()
        self._setup_logger()

    def _setup_logger(self):
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            
            if self.settings.LOG_FORMAT == "json":
                formatter = JsonFormatter()
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(getattr(logging, self.settings.LOG_LEVEL.upper()))

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        extra = getattr(record, "extra", {})
        if extra:
            log_data.update(extra)
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


class RAGPipelineLogger:
    """Specialized logger for RAG pipeline stages."""

    def __init__(self):
        self.logger = get_logger("rag.pipeline")

    def log_query(self, query: str, route: str, conversation_id: str = None):
        self.logger.info(
            "Query received",
            extra={
                "event": "query_received",
                "query": query[:200],
                "route": route,
                "conversation_id": conversation_id,
            }
        )

    def log_retrieval(
        self, 
        query: str, 
        route: str,
        initial_count: int,
        reranked_count: int,
        final_count: int,
        scores: list[float],
        retrieval_time: float
    ):
        self.logger.info(
            "Retrieval completed",
            extra={
                "event": "retrieval_completed",
                "query": query[:200],
                "route": route,
                "initial_candidates": initial_count,
                "reranked_candidates": reranked_count,
                "final_context_chunks": final_count,
                "similarity_scores": scores[:10],
                "retrieval_time_ms": round(retrieval_time * 1000, 2),
            }
        )

    def log_reranking(
        self,
        query: str,
        initial_chunks: int,
        final_chunks: int,
        rerank_scores: list[float],
        rerank_time: float
    ):
        self.logger.info(
            "Reranking completed",
            extra={
                "event": "reranking_completed",
                "query": query[:200],
                "initial_chunks": initial_chunks,
                "final_chunks": final_chunks,
                "rerank_scores": rerank_scores[:10],
                "rerank_time_ms": round(rerank_time * 1000, 2),
            }
        )

    def log_context_validation(
        self,
        query: str,
        before_count: int,
        after_count: int,
        threshold: float
    ):
        self.logger.info(
            "Context validation completed",
            extra={
                "event": "context_validation",
                "query": query[:200],
                "chunks_before": before_count,
                "chunks_after": after_count,
                "relevance_threshold": threshold,
            }
        )

    def log_generation(
        self,
        query: str,
        answer_source: str,
        context_chunks: int,
        generation_time: float,
        total_time: float
    ):
        self.logger.info(
            "LLM generation completed",
            extra={
                "event": "generation_completed",
                "query": query[:200],
                "answer_source": answer_source,
                "context_chunks": context_chunks,
                "generation_time_ms": round(generation_time * 1000, 2),
                "total_time_ms": round(total_time * 1000, 2),
            }
        )

    def log_no_answer(self, query: str, route: str, reason: str):
        self.logger.warning(
            "No answer generated",
            extra={
                "event": "no_answer",
                "query": query[:200],
                "route": route,
                "reason": reason,
            }
        )

    def log_web_fallback(self, query: str, web_results: int):
        self.logger.info(
            "Web search fallback triggered",
            extra={
                "event": "web_fallback",
                "query": query[:200],
                "web_results": web_results,
            }
        )


pipeline_logger = RAGPipelineLogger()
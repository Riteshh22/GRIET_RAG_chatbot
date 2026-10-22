import time
import re
from backend.config.settings import get_settings
from backend.services.document_service import DocumentService
from backend.document_processor.document_processor import DocumentProcessor
from backend.document_processor.chunking_service import ChunkingService
from backend.embeddings.embedding_service import EmbeddingService
from backend.vectorstore.qdrant_service import QdrantService
from backend.retrieval.hybrid_retrieval import HybridRetrievalService
from backend.reranker.reranker_service import RerankerService
from backend.llm.llm_service import LLMService
from backend.crawler.web_search import WebSearchService
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    RetrievedChunk,
    DocumentMetadata,
    PipelineStage,
    SourceType,
    WebSearchResult,
)
from backend.utils.helpers import generate_id
from backend.utils.logger import get_logger, pipeline_logger


logger = get_logger(__name__)


class RAGPipeline:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.settings = get_settings()
            self.document_service = DocumentService()
            self.doc_processor = DocumentProcessor()
            self.chunking_service = ChunkingService()
            self.embedding_service = EmbeddingService()
            self.qdrant_service = QdrantService()
            self.retrieval_service = HybridRetrievalService()
            self.reranker = RerankerService()
            self.llm_service = LLMService()
            self.web_search = WebSearchService()
            self._initialized = True

            self.griet_keywords = {
                "griet", "gokaraju", "rangaraju", "institute", "engineering", "technology",
                "hod", "head of department", "department", "faculty", "professor", "lecturer",
                "admission", "admissions", "academic", "academics", "examination", "exams",
                "placement", "placements", "event", "events", "club", "clubs", "committee",
                "infrastructure", "facility", "facilities", "library", "hostel", "transport",
                "regulation", "regulations", "notice", "notices", "announcement", "calendar",
                "timetable", "syllabus", "curriculum", "fees", "scholarship", "scholarships",
                "cse", "it", "ece", "eee", "mech", "civil", "aero", "mba", "mca", "h&s",
                "computer science", "information technology", "electronics", "electrical",
                "mechanical", "civil", "aeronautical", "management", "computer applications",
                "hyderabad", "bachupally", "kphb", "nizam pet"
            }

    def _is_griet_query(self, query: str) -> bool:
        query_lower = query.lower()
        words = set(re.findall(r'\b\w+\b', query_lower))
        
        griet_word_count = len(words & self.griet_keywords)
        
        if griet_word_count >= 1:
            return True
        
        if any(phrase in query_lower for phrase in [
            "who is", "what is", "tell me about", "show me", "information about",
            "details of", "list of", "how to apply", "requirements for"
        ]) and any(word in query_lower for word in ["griet", "college", "institute", "university"]):
            return True
            
        return False

    def _calculate_confidence(self, retrieved: list[RetrievedChunk]) -> float:
        if not retrieved:
            return 0.0
        
        max_similarity = max(c.similarity_score for c in retrieved)
        max_chunk_score = max(c.chunk_score for c in retrieved) if retrieved[0].chunk_score > 0 else 0
        
        weighted_score = 0.6 * max_similarity + 0.4 * max_chunk_score
        return min(weighted_score, 1.0)

    def _validate_context(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Validate that retrieved chunks are relevant to the query."""
        if not chunks:
            return []
        
        threshold = self.settings.CONTEXT_RELEVANCE_THRESHOLD
        valid_chunks = [
            c for c in chunks 
            if c.similarity_score >= threshold or (c.chunk_score > 0 and c.chunk_score >= threshold)
        ]
        
        logger.debug(
            f"Context validation: {len(chunks)} -> {len(valid_chunks)} chunks "
            f"(threshold: {threshold})"
        )
        return valid_chunks

    async def ingest_document(
        self, file_path: str, filename: str, file_type: str, doc_id: str
    ) -> dict:
        start = time.time()

        self.document_service.update_document(
            doc_id, {"status": "processing"}
        )

        try:
            pages = self.doc_processor.process(file_path, file_type)
            page_count = len(pages)

            chunks = self.chunking_service.chunk_pages(
                pages, doc_id, filename
            )
            if not chunks:
                self.document_service.update_document(
                    doc_id, {"status": "failed"}
                )
                return {"error": "No content extracted from document"}

            texts = [c.content for c in chunks]
            embeddings = self.embedding_service.embed_documents(texts)

            self.qdrant_service.upsert_chunks(chunks, embeddings)

            self.document_service.update_document(
                doc_id,
                {
                    "status": "indexed",
                    "pages": page_count,
                    "chunks": len(chunks),
                    "indexed": True,
                },
            )

            self.retrieval_service.rebuild_bm25_index()

            elapsed = time.time() - start
            return {
                "document_id": doc_id,
                "pages": page_count,
                "chunks": len(chunks),
                "processing_time": round(elapsed, 2),
                "status": "indexed",
            }

        except Exception as e:
            self.document_service.update_document(
                doc_id, {"status": "failed"}
            )
            raise RuntimeError(f"Document ingestion failed: {str(e)}")

    async def process_query(self, request: ChatRequest) -> ChatResponse:
        total_start = time.time()
        pipeline_stages = []
        conversation_id = request.conversation_id or generate_id()

        is_griet_query = self._is_griet_query(request.query)
        route = "griet" if is_griet_query else "web"
        
        pipeline_logger.log_query(request.query, route, conversation_id)
        
        stage_start = time.time()
        pipeline_stages.append(
            PipelineStage(
                name="Query Analysis",
                status="completed",
                duration=round(time.time() - stage_start, 3),
                details=f"Query type: {'GRIET' if is_griet_query else 'General'}"
            ).model_dump()
        )

        griet_sources = []
        web_sources = []
        answer_source = "griet"
        confidence = 0.0
        initial_retrieval_count = 0
        retrieval_scores = []

        if is_griet_query:
            stage_start = time.time()
            pipeline_stages.append(
                PipelineStage(
                    name="Initial Retrieval",
                    status="running",
                ).model_dump()
            )
            
            initial_top_k = self.settings.INITIAL_RETRIEVAL_TOP_K
            griet_sources = self.retrieval_service.initial_retrieval(
                request.query, top_k=initial_top_k, source_type="griet"
            )
            initial_retrieval_count = len(griet_sources)
            retrieval_scores = [c.similarity_score for c in griet_sources]
            
            if request.use_reranker and self.reranker.is_available and griet_sources:
                pipeline_stages[-1].update(
                    {
                        "status": "running",
                        "details": f"Reranking {len(griet_sources)} candidates..."
                    }
                )
                rerank_start = time.time()
                griet_sources = self.reranker.rerank(
                    request.query, griet_sources, 
                    top_k=self.settings.FINAL_RERANK_TOP_N,
                    min_score=self.settings.MIN_RERANK_THRESHOLD
                )
                rerank_scores = [c.chunk_score for c in griet_sources]
                pipeline_logger.log_reranking(
                    request.query,
                    initial_retrieval_count,
                    len(griet_sources),
                    rerank_scores,
                    time.time() - rerank_start
                )
            
            validation_start = time.time()
            before_validation = len(griet_sources)
            griet_sources = self._validate_context(request.query, griet_sources)
            pipeline_logger.log_context_validation(
                request.query,
                before_validation,
                len(griet_sources),
                self.settings.CONTEXT_RELEVANCE_THRESHOLD
            )
            
            confidence = self._calculate_confidence(griet_sources)
            
            pipeline_stages[-1].update(
                {
                    "status": "completed",
                    "duration": round(time.time() - stage_start, 3),
                    "details": f"Initial: {initial_retrieval_count}, Reranked: {len(griet_sources)} (confidence: {confidence:.2f})"
                }
            )
            
            pipeline_logger.log_retrieval(
                request.query,
                "griet",
                initial_retrieval_count,
                len(griet_sources) if request.use_reranker and self.reranker.is_available else 0,
                len(griet_sources),
                retrieval_scores,
                time.time() - stage_start
            )

            if confidence < self.settings.GRIET_CONFIDENCE_THRESHOLD and self.settings.WEB_SEARCH_ENABLED:
                stage_start = time.time()
                pipeline_stages.append(
                    PipelineStage(
                        name="Web Search Fallback",
                        status="running",
                    ).model_dump()
                )
                
                web_results = await self.web_search.search(
                    request.query, max_results=self.settings.WEB_SEARCH_MAX_RESULTS
                )
                
                for result in web_results:
                    content = await self.web_search.fetch_page_content(result["url"])
                    if content:
                        result["content"] = content
                
                web_sources = [WebSearchResult(**w) for w in web_results]
                
                pipeline_stages[-1].update(
                    {
                        "status": "completed",
                        "duration": round(time.time() - stage_start, 3),
                        "details": f"Found {len(web_sources)} web sources"
                    }
                )
                
                pipeline_logger.log_web_fallback(request.query, len(web_sources))
                
                if web_sources:
                    answer_source = "hybrid" if griet_sources else "web"
                else:
                    answer_source = "griet"
            else:
                answer_source = "griet"
        else:
            if self.settings.WEB_SEARCH_ENABLED:
                stage_start = time.time()
                pipeline_stages.append(
                    PipelineStage(
                        name="Web Search",
                        status="running",
                    ).model_dump()
                )
                
                web_results = await self.web_search.search(
                    request.query, max_results=self.settings.WEB_SEARCH_MAX_RESULTS
                )
                
                for result in web_results:
                    content = await self.web_search.fetch_page_content(result["url"])
                    if content:
                        result["content"] = content
                
                web_sources = [WebSearchResult(**w) for w in web_results]
                
                pipeline_stages[-1].update(
                    {
                        "status": "completed",
                        "duration": round(time.time() - stage_start, 3),
                        "details": f"Found {len(web_sources)} web sources"
                    }
                )
                answer_source = "web"
            else:
                answer_source = "none"

        retrieval_time = time.time() - total_start

        if not griet_sources and not web_sources:
            pipeline_logger.log_no_answer(request.query, route, "No relevant sources found")
            answer = "I couldn't find any verified information to answer your question."
            generation_time = 0.0
            total_time = time.time() - total_start
            
            return ChatResponse(
                answer=answer,
                sources=[],
                web_sources=[],
                conversation_id=conversation_id,
                pipeline_stages=pipeline_stages,
                retrieval_time=round(retrieval_time, 3),
                generation_time=0.0,
                total_time=round(total_time, 3),
                answer_source="none",
                confidence=0.0,
            )

        stage_start = time.time()
        pipeline_stages.append(
            PipelineStage(
                name="LLM Generation",
                status="running",
            ).model_dump()
        )
        
        try:
            if answer_source == "griet" and griet_sources:
                answer = await self.llm_service.generate_griet(request.query, griet_sources)
            elif answer_source == "web" and web_sources:
                answer = await self.llm_service.generate_web_fallback(request.query, web_sources)
            elif answer_source == "hybrid" and (griet_sources or web_sources):
                answer = await self.llm_service.generate_hybrid(request.query, griet_sources, web_sources)
            else:
                answer = "I couldn't find any information to answer your question. Please try rephrasing or ask about GRIET-specific topics."
        except ConnectionError:
            answer = (
                "Ollama is not running. Please start Ollama with `ollama serve` "
                "and ensure the model is pulled with `ollama pull qwen3:8b`."
            )
        except Exception as e:
            answer = f"Error generating response: {str(e)}"
            
        pipeline_stages[-1].update(
            {
                "status": "completed",
                "duration": round(time.time() - stage_start, 3),
            }
        )

        generation_time = time.time() - total_start - retrieval_time
        total_time = time.time() - total_start

        pipeline_logger.log_generation(
            request.query,
            answer_source,
            len(griet_sources) + len(web_sources),
            generation_time,
            total_time
        )

        debug_info = None
        if request.debug:
            debug_info = {
                "query": request.query,
                "route": route,
                "initial_retrieval": {
                    "count": initial_retrieval_count,
                    "chunks": [
                        {
                            "document_name": c.document_name,
                            "page_number": c.page_number,
                            "similarity_score": c.similarity_score,
                            "content_preview": c.content[:200]
                        }
                        for c in self.retrieval_service.initial_retrieval(
                            request.query, top_k=self.settings.INITIAL_RETRIEVAL_TOP_K, source_type="griet"
                        )
                    ] if is_griet_query else []
                },
                "reranked_chunks": [
                    {
                        "document_name": c.document_name,
                        "page_number": c.page_number,
                        "similarity_score": c.similarity_score,
                        "rerank_score": c.chunk_score,
                        "content_preview": c.content[:200]
                    }
                    for c in griet_sources
                ] if is_griet_query and request.use_reranker and self.reranker.is_available else [],
                "final_context": [
                    {
                        "document_name": c.document_name,
                        "page_number": c.page_number,
                        "similarity_score": c.similarity_score,
                        "rerank_score": c.chunk_score if c.chunk_score > 0 else None,
                        "source_type": c.source_type.value,
                        "source_url": c.source_url
                    }
                    for c in griet_sources
                ] + [
                    {
                        "title": w.title,
                        "url": w.url,
                        "source_type": "web"
                    }
                    for w in web_sources
                ],
                "pipeline_stages": pipeline_stages,
                "confidence": confidence,
                "answer_source": answer_source
            }

        return ChatResponse(
            answer=answer,
            sources=griet_sources,
            web_sources=web_sources,
            conversation_id=conversation_id,
            pipeline_stages=pipeline_stages,
            retrieval_time=round(retrieval_time, 3),
            generation_time=round(generation_time, 3),
            total_time=round(total_time, 3),
            answer_source=answer_source,
            confidence=round(confidence, 3),
            debug_info=debug_info,
        )

    async def process_query_stream(self, request: ChatRequest):
        total_start = time.time()
        is_griet_query = self._is_griet_query(request.query)
        
        griet_sources = []
        web_sources = []
        answer_source = "griet"
        confidence = 0.0
        initial_retrieval_count = 0

        if is_griet_query:
            initial_top_k = self.settings.INITIAL_RETRIEVAL_TOP_K
            griet_sources = self.retrieval_service.initial_retrieval(
                request.query, top_k=initial_top_k, source_type="griet"
            )
            initial_retrieval_count = len(griet_sources)
            
            if request.use_reranker and self.reranker.is_available and griet_sources:
                griet_sources = self.reranker.rerank(
                    request.query, griet_sources, 
                    top_k=self.settings.FINAL_RERANK_TOP_N,
                    min_score=self.settings.MIN_RERANK_THRESHOLD
                )
            
            griet_sources = self._validate_context(request.query, griet_sources)
            confidence = self._calculate_confidence(griet_sources)

            if confidence < self.settings.GRIET_CONFIDENCE_THRESHOLD and self.settings.WEB_SEARCH_ENABLED:
                web_results = await self.web_search.search(
                    request.query, max_results=self.settings.WEB_SEARCH_MAX_RESULTS
                )
                
                for result in web_results:
                    content = await self.web_search.fetch_page_content(result["url"])
                    if content:
                        result["content"] = content
                
                web_sources = [WebSearchResult(**w) for w in web_results]
                
                if web_sources:
                    answer_source = "hybrid" if griet_sources else "web"
                else:
                    answer_source = "griet"
            else:
                answer_source = "griet"
        else:
            if self.settings.WEB_SEARCH_ENABLED:
                web_results = await self.web_search.search(
                    request.query, max_results=self.settings.WEB_SEARCH_MAX_RESULTS
                )
                
                for result in web_results:
                    content = await self.web_search.fetch_page_content(result["url"])
                    if content:
                        result["content"] = content
                
                web_sources = [WebSearchResult(**w) for w in web_results]
                answer_source = "web"
            else:
                answer_source = "none"

        if not griet_sources and not web_sources:
            yield {
                "type": "sources",
                "sources": [],
                "web_sources": [],
                "answer_source": "none",
                "confidence": 0.0
            }
            yield {"type": "token", "content": "I couldn't find any verified information to answer your question."}
            yield {"type": "done"}
            return

        yield {
            "type": "sources",
            "sources": [s.model_dump() for s in griet_sources],
            "web_sources": [w.model_dump() for w in web_sources],
            "answer_source": answer_source,
            "confidence": round(confidence, 3),
            "initial_retrieval_count": initial_retrieval_count,
            "final_context_count": len(griet_sources) + len(web_sources)
        }

        try:
            if answer_source == "griet" and griet_sources:
                async for token in self.llm_service.generate_stream_griet(request.query, griet_sources):
                    yield {"type": "token", "content": token}
            elif answer_source == "web" and web_sources:
                async for token in self.llm_service.generate_stream_web_fallback(request.query, web_sources):
                    yield {"type": "token", "content": token}
            elif answer_source == "hybrid" and (griet_sources or web_sources):
                async for token in self.llm_service.generate_stream_hybrid(request.query, griet_sources, web_sources):
                    yield {"type": "token", "content": token}
            else:
                yield {"type": "token", "content": "I couldn't find any information to answer your question."}
        except ConnectionError:
            yield {"type": "token", "content": "Ollama is not running. Please start Ollama with `ollama serve` and ensure the model is pulled with `ollama pull qwen3:8b`."}
        except Exception as e:
            yield {"type": "token", "content": f"Error: {str(e)}"}

        yield {"type": "done"}

    async def get_system_info(self) -> dict:
        ollama_ok = await self.llm_service.is_available()
        qdrant_ok = self.qdrant_service.is_connected()
        collection_info = self.qdrant_service.get_collection_info()
        
        griet_count = 0
        try:
            results = self.qdrant_service.client.scroll(
                collection_name=self.settings.QDRANT_COLLECTION,
                limit=10000,
                with_payload=True,
                with_vectors=False,
                scroll_filter=self.qdrant_service.client.model.Filter(
                    must=[
                        self.qdrant_service.client.model.FieldCondition(
                            key="metadata.source_type",
                            match=self.qdrant_service.client.model.MatchValue(value="griet"),
                        )
                    ]
                ),
            )
            griet_count = len(results[0])
        except Exception:
            pass

        return {
            "app_name": self.settings.APP_NAME,
            "version": self.settings.APP_VERSION,
            "embedding_model": self.settings.EMBEDDING_MODEL,
            "embedding_dimension": self.settings.EMBEDDING_DIMENSION,
            "llm_model": self.settings.OLLAMA_MODEL,
            "vector_db": "Qdrant",
            "vector_db_status": "connected" if qdrant_ok else "disconnected",
            "ollama_status": "connected" if ollama_ok else "disconnected",
            "total_documents": self.document_service.get_document_count(),
            "total_chunks": self.document_service.get_total_chunks(),
            "griet_pages_indexed": griet_count,
            "reranker_model": self.settings.RERANKER_MODEL,
            "reranker_enabled": self.settings.RERANKER_ENABLED,
            "qdrant_collection": self.settings.QDRANT_COLLECTION,
            "chunk_size": self.settings.CHUNK_SIZE,
            "chunk_overlap": self.settings.CHUNK_OVERLAP,
            "top_k": self.settings.TOP_K,
            "initial_retrieval_top_k": self.settings.INITIAL_RETRIEVAL_TOP_K,
            "final_rerank_top_n": self.settings.FINAL_RERANK_TOP_N,
            "hybrid_alpha": self.settings.HYBRID_ALPHA,
            "web_search_enabled": self.settings.WEB_SEARCH_ENABLED,
        }

    async def run_griet_crawl(self, max_pages: int = None, incremental: bool = False):
        from backend.crawler.griet_crawler import GRIETCrawler, run_full_crawl, run_incremental_crawl
        
        if incremental:
            return await run_incremental_crawl()
        else:
            crawler = GRIETCrawler()
            crawler.config.max_pages = max_pages or self.settings.GRIET_MAX_PAGES
            pages = await crawler.crawl()
            result = await crawler.index_pages(pages)
            return {"pages_crawled": len(pages), **result}
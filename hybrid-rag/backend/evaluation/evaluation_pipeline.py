import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from backend.services.rag_pipeline import RAGPipeline
from backend.models.schemas import ChatRequest
from backend.utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class EvaluationExample:
    id: str
    category: str
    question: str
    expected_answer_contains: List[str]
    relevant_source_url: str
    relevant_info: str
    expected_doc_ids: List[str]
    ground_truth_available: bool
    expected_route: Optional[str] = None


@dataclass
class RetrievalMetrics:
    recall_at_k: float = 0.0
    precision_at_k: float = 0.0
    hit_rate: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    context_relevance: float = 0.0


@dataclass
class GenerationMetrics:
    answer_correctness: float = 0.0
    answer_faithfulness: float = 0.0
    context_relevance: float = 0.0
    answer_completeness: float = 0.0
    hallucination_rate: float = 0.0
    no_answer_accuracy: float = 0.0


@dataclass
class EvaluationResult:
    example: EvaluationExample
    route: str
    answer: str
    sources: List[Dict]
    web_sources: List[Dict]
    retrieval_time: float
    generation_time: float
    total_time: float
    confidence: float
    retrieval_metrics: RetrievalMetrics
    generation_metrics: GenerationMetrics
    initial_retrieval_count: int = 0
    reranked_count: int = 0


class EvaluationDataset:
    """Load and manage evaluation dataset."""

    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        self.examples: List[EvaluationExample] = []
        self._load()

    def _load(self):
        with open(self.dataset_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    self.examples.append(EvaluationExample(**data))

    def get_by_category(self, category: str) -> List[EvaluationExample]:
        return [e for e in self.examples if e.category == category]

    def get_griet_examples(self) -> List[EvaluationExample]:
        return [e for e in self.examples if e.category != "out_of_domain"]

    def get_web_examples(self) -> List[EvaluationExample]:
        return [e for e in self.examples if e.category == "out_of_domain"]

    def get_no_answer_examples(self) -> List[EvaluationExample]:
        return [e for e in self.examples if e.category == "no_answer"]


class RetrievalEvaluator:
    """Evaluate retrieval quality."""

    def __init__(self):
        pass

    def evaluate_retrieval(
        self, 
        query: str, 
        retrieved_chunks: List[Dict], 
        relevant_url: str,
        ground_truth_available: bool
    ) -> RetrievalMetrics:
        if not ground_truth_available or not relevant_url:
            return RetrievalMetrics(
                recall_at_k=0.0, precision_at_k=0.0, hit_rate=0.0,
                mrr=0.0, ndcg=0.0, context_relevance=0.0
            )

        retrieved_urls = set()
        for chunk in retrieved_chunks:
            url = chunk.get("metadata", {}).get("source_url", "")
            if url:
                retrieved_urls.add(url)

        relevant = 1 if relevant_url in retrieved_urls else 0
        total_retrieved = len(retrieved_chunks)

        hit_rate = 1.0 if relevant else 0.0
        recall_at_k = 1.0 if relevant else 0.0
        precision_at_k = 1.0 / total_retrieved if relevant and total_retrieved > 0 else 0.0

        mrr = 0.0
        for i, chunk in enumerate(retrieved_chunks):
            url = chunk.get("metadata", {}).get("source_url", "")
            if url == relevant_url:
                mrr = 1.0 / (i + 1)
                break

        ndcg = self._calculate_ndcg(retrieved_chunks, relevant_url)
        context_relevance = self._calculate_context_relevance(retrieved_chunks)

        return RetrievalMetrics(
            recall_at_k=recall_at_k,
            precision_at_k=precision_at_k,
            hit_rate=hit_rate,
            mrr=mrr,
            ndcg=ndcg,
            context_relevance=context_relevance
        )

    def _calculate_ndcg(self, retrieved_chunks: List[Dict], relevant_url: str) -> float:
        if not retrieved_chunks:
            return 0.0
        
        relevance = []
        for chunk in retrieved_chunks:
            url = chunk.get("metadata", {}).get("source_url", "")
            relevance.append(1.0 if url == relevant_url else 0.0)
        
        dcg = sum(rel / (i + 1) for i, rel in enumerate(relevance, 1))
        ideal_relevance = sorted(relevance, reverse=True)
        idcg = sum(rel / (i + 1) for i, rel in enumerate(ideal_relevance, 1))
        
        return dcg / idcg if idcg > 0 else 0.0

    def _calculate_context_relevance(self, retrieved_chunks: List[Dict]) -> float:
        if not retrieved_chunks:
            return 0.0
        
        scores = [chunk.get("similarity_score", 0) for chunk in retrieved_chunks]
        return sum(scores) / len(scores) if scores else 0.0


class GenerationEvaluator:
    """Evaluate answer quality."""

    def __init__(self):
        pass

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        expected_contains: List[str],
        sources: List[Dict],
        ground_truth_available: bool,
        category: str
    ) -> GenerationMetrics:
        if category == "no_answer":
            is_refusal = any(phrase in answer.lower() for phrase in [
                "couldn't find", "not found", "no verified", "verified information could not be found",
                "i couldn't find", "no information", "unable to find"
            ])
            return GenerationMetrics(
                answer_correctness=0.0,
                answer_faithfulness=1.0 if is_refusal else 0.0,
                context_relevance=0.0,
                answer_completeness=0.0,
                hallucination_rate=0.0 if is_refusal else 1.0,
                no_answer_accuracy=1.0 if is_refusal else 0.0
            )

        if category == "out_of_domain":
            has_answer = len(answer.strip()) > 20
            return GenerationMetrics(
                answer_correctness=1.0 if has_answer else 0.0,
                answer_faithfulness=1.0 if has_answer else 0.0,
                context_relevance=0.0,
                answer_completeness=1.0 if has_answer else 0.0,
                hallucination_rate=0.0,
                no_answer_accuracy=0.0
            )

        expected_lower = [e.lower() for e in expected_contains]
        answer_lower = answer.lower()

        matches = sum(1 for exp in expected_lower if exp in answer_lower)
        answer_correctness = matches / len(expected_lower) if expected_lower else 0.0

        has_sources = len(sources) > 0
        answer_faithfulness = 1.0 if has_sources else 0.5

        context_relevance = 1.0 if has_sources else 0.0

        answer_completeness = min(answer_correctness * 1.2, 1.0)

        hallucination_indicators = [
            "as an ai", "i don't have access", "my training data",
            "i cannot", "i'm not sure", "i don't know"
        ]
        has_hallucination = any(ind in answer_lower for ind in hallucination_indicators)
        hallucination_rate = 1.0 if has_hallucination else 0.0

        no_answer_accuracy = 0.0

        return GenerationMetrics(
            answer_correctness=round(answer_correctness, 3),
            answer_faithfulness=round(answer_faithfulness, 3),
            context_relevance=round(context_relevance, 3),
            answer_completeness=round(answer_completeness, 3),
            hallucination_rate=round(hallucination_rate, 3),
            no_answer_accuracy=round(no_answer_accuracy, 3)
        )


class EvaluationPipeline:
    """Main evaluation pipeline."""

    def __init__(self, dataset_path: str = None):
        self._rag = None
        self._settings = None
        self.dataset_path = dataset_path or "backend/evaluation/dataset.jsonl"
        self.dataset = EvaluationDataset(self.dataset_path)
        self.retrieval_evaluator = RetrievalEvaluator()
        self.generation_evaluator = GenerationEvaluator()
        self.results: List[EvaluationResult] = []

    @property
    def rag(self):
        if self._rag is None:
            self._rag = RAGPipeline()
        return self._rag

    @property
    def settings(self):
        if self._settings is None:
            self._settings = self.rag.settings
        return self._settings

    async def run_evaluation(
        self, 
        categories: List[str] = None,
        use_reranker: bool = True,
        top_k: int = 5
    ) -> Dict[str, Any]:
        examples = self.dataset.examples
        if categories:
            examples = [e for e in examples if e.category in categories]

        logger.info(f"Starting evaluation with {len(examples)} examples")
        
        self.results = []
        for i, example in enumerate(examples):
            logger.info(f"Evaluating {i+1}/{len(examples)}: {example.id} - {example.question[:50]}")
            
            request = ChatRequest(
                query=example.question,
                top_k=top_k,
                use_reranker=use_reranker
            )
            
            start = time.time()
            response = await self.rag.process_query(request)
            total_time = time.time() - start
            
            retrieval_metrics = self.retrieval_evaluator.evaluate_retrieval(
                example.question,
                [s.model_dump() for s in response.sources],
                example.relevant_source_url,
                example.ground_truth_available
            )
            
            generation_metrics = self.generation_evaluator.evaluate_answer(
                example.question,
                response.answer,
                example.expected_answer_contains,
                [s.model_dump() for s in response.sources],
                example.ground_truth_available,
                example.category
            )
            
            initial_count = 0
            reranked_count = 0
            for stage in response.pipeline_stages:
                if stage.get("name") == "Initial Retrieval":
                    details = stage.get("details", "")
                    if "Initial:" in details:
                        try:
                            initial_count = int(details.split("Initial:")[1].split(",")[0].strip())
                        except:
                            pass
                    if "Reranked:" in details:
                        try:
                            reranked_count = int(details.split("Reranked:")[1].split("(")[0].strip())
                        except:
                            pass
            
            result = EvaluationResult(
                example=example,
                route=response.answer_source,
                answer=response.answer,
                sources=[s.model_dump() for s in response.sources],
                web_sources=[w.model_dump() for w in response.web_sources],
                retrieval_time=response.retrieval_time,
                generation_time=response.generation_time,
                total_time=response.total_time,
                confidence=response.confidence,
                retrieval_metrics=retrieval_metrics,
                generation_metrics=generation_metrics,
                initial_retrieval_count=initial_count,
                reranked_count=reranked_count
            )
            self.results.append(result)
        
        return self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        if not self.results:
            return {"error": "No results to report"}

        total = len(self.results)
        griet_results = [r for r in self.results if r.example.category != "out_of_domain"]
        web_results = [r for r in self.results if r.example.category == "out_of_domain"]
        no_answer_results = [r for r in self.results if r.example.category == "no_answer"]
        
        def avg(values):
            return round(sum(values) / len(values), 3) if values else 0.0

        report = {
            "total_questions": total,
            "categories_tested": list(set(r.example.category for r in self.results)),
            
            "retrieval_metrics": {
                "recall_at_k": avg([r.retrieval_metrics.recall_at_k for r in griet_results]),
                "precision_at_k": avg([r.retrieval_metrics.precision_at_k for r in griet_results]),
                "hit_rate": avg([r.retrieval_metrics.hit_rate for r in griet_results]),
                "mrr": avg([r.retrieval_metrics.mrr for r in griet_results]),
                "ndcg": avg([r.retrieval_metrics.ndcg for r in griet_results]),
                "context_relevance": avg([r.retrieval_metrics.context_relevance for r in griet_results]),
            },
            
            "generation_metrics": {
                "answer_correctness": avg([r.generation_metrics.answer_correctness for r in griet_results]),
                "answer_faithfulness": avg([r.generation_metrics.answer_faithfulness for r in griet_results]),
                "context_relevance": avg([r.generation_metrics.context_relevance for r in griet_results]),
                "answer_completeness": avg([r.generation_metrics.answer_completeness for r in griet_results]),
                "hallucination_rate": avg([r.generation_metrics.hallucination_rate for r in griet_results]),
                "no_answer_accuracy": avg([r.generation_metrics.no_answer_accuracy for r in no_answer_results]),
            },
            
            "performance": {
                "avg_retrieval_time": avg([r.retrieval_time for r in self.results]),
                "avg_generation_time": avg([r.generation_time for r in self.results]),
                "avg_total_time": avg([r.total_time for r in self.results]),
                "avg_confidence": avg([r.confidence for r in self.results]),
            },
            
            "route_distribution": {
                "griet": len([r for r in self.results if r.route == "griet"]),
                "web": len([r for r in self.results if r.route == "web"]),
                "hybrid": len([r for r in self.results if r.route == "hybrid"]),
                "none": len([r for r in self.results if r.route == "none"]),
            },
            
            "category_breakdown": {}
        }

        for category in set(r.example.category for r in self.results):
            cat_results = [r for r in self.results if r.example.category == category]
            report["category_breakdown"][category] = {
                "count": len(cat_results),
                "retrieval_recall": avg([r.retrieval_metrics.recall_at_k for r in cat_results]),
                "generation_correctness": avg([r.generation_metrics.answer_correctness for r in cat_results]),
                "hallucination_rate": avg([r.generation_metrics.hallucination_rate for r in cat_results]),
            }

        return report

    def compare_reranker_impact(self, baseline_results: List[EvaluationResult] = None) -> Dict[str, Any]:
        if not self.results:
            return {"error": "No results to compare"}
        
        if not baseline_results:
            return {"note": "Baseline results not provided. Run evaluation without reranker first."}
        
        reranked_recall = avg([r.retrieval_metrics.recall_at_k for r in self.results])
        reranked_mrr = avg([r.retrieval_metrics.mrr for r in self.results])
        reranked_precision = avg([r.retrieval_metrics.precision_at_k for r in self.results])
        
        baseline_recall = avg([r.retrieval_metrics.recall_at_k for r in baseline_results])
        baseline_mrr = avg([r.retrieval_metrics.mrr for r in baseline_results])
        baseline_precision = avg([r.retrieval_metrics.precision_at_k for r in baseline_results])
        
        def avg(values):
            return round(sum(values) / len(values), 3) if values else 0.0
        
        return {
            "initial_retrieval_recall": baseline_recall,
            "reranked_retrieval_recall": reranked_recall,
            "recall_improvement": round(reranked_recall - baseline_recall, 3),
            "initial_mrr": baseline_mrr,
            "reranked_mrr": reranked_mrr,
            "mrr_improvement": round(reranked_mrr - baseline_mrr, 3),
            "initial_precision": baseline_precision,
            "reranked_precision": reranked_precision,
            "precision_improvement": round(reranked_precision - baseline_precision, 3),
        }


async def run_evaluation(
    dataset_path: str = None,
    categories: List[str] = None,
    use_reranker: bool = True,
    top_k: int = 5
) -> Dict[str, Any]:
    pipeline = EvaluationPipeline(dataset_path)
    return await pipeline.run_evaluation(categories, use_reranker, top_k)


if __name__ == "__main__":
    import sys
    categories = sys.argv[1:] if len(sys.argv) > 1 else None
    result = asyncio.run(run_evaluation(categories=categories))
    print(json.dumps(result, indent=2))
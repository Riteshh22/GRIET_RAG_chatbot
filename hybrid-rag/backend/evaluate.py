#!/usr/bin/env python
"""CLI script to run GRIET RAG evaluation."""

import asyncio
import json
import sys
import argparse
from backend.evaluation.evaluation_pipeline import run_evaluation


async def main():
    parser = argparse.ArgumentParser(description="Run GRIET RAG Evaluation")
    parser.add_argument(
        "--categories", "-c", 
        nargs="+", 
        choices=["faculty", "departments", "admissions", "academics", "placements", 
                 "examinations", "fees", "clubs", "events", "infrastructure", 
                 "regulations", "contact", "no_answer", "out_of_domain"],
        help="Categories to evaluate (default: all)"
    )
    parser.add_argument(
        "--no-reranker", 
        action="store_true", 
        help="Disable reranker for comparison"
    )
    parser.add_argument(
        "--top-k", "-k", 
        type=int, 
        default=5, 
        help="Top K for retrieval (default: 5)"
    )
    parser.add_argument(
        "--dataset", "-d", 
        type=str, 
        default="backend/evaluation/dataset.jsonl",
        help="Path to evaluation dataset"
    )
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        help="Output file for results (default: stdout)"
    )
    parser.add_argument(
        "--compare", 
        action="store_true", 
        help="Run comparison between with and without reranker"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GRIET RAG Chatbot - Evaluation Pipeline")
    print("=" * 60)
    print(f"Dataset: {args.dataset}")
    print(f"Categories: {args.categories or 'all'}")
    print(f"Reranker: {'disabled' if args.no_reranker else 'enabled'}")
    print(f"Top K: {args.top_k}")
    print("=" * 60)
    
    if args.compare:
        print("\nRunning WITH reranker...")
        reranked_results = await run_evaluation(
            dataset_path=args.dataset,
            categories=args.categories,
            use_reranker=True,
            top_k=args.top_k
        )
        
        print("\nRunning WITHOUT reranker...")
        baseline_results = await run_evaluation(
            dataset_path=args.dataset,
            categories=args.categories,
            use_reranker=False,
            top_k=args.top_k
        )
        
        from backend.evaluation.evaluation_pipeline import EvaluationPipeline
        eval_pipeline = EvaluationPipeline(args.dataset)
        eval_pipeline.results = [type('obj', (object,), r) for r in reranked_results.get("detailed_results", [])]
        
        comparison = eval_pipeline.compare_reranker_impact()
        print("\n" + "=" * 60)
        print("RERANKER IMPACT COMPARISON")
        print("=" * 60)
        print(json.dumps(comparison, indent=2))
        
        result = {
            "with_reranker": reranked_results,
            "without_reranker": baseline_results,
            "comparison": comparison
        }
    else:
        result = await run_evaluation(
            dataset_path=args.dataset,
            categories=args.categories,
            use_reranker=not args.no_reranker,
            top_k=args.top_k
        )
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to {args.output}")
    else:
        print("\n" + "=" * 60)
        print("EVALUATION REPORT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    asyncio.run(main())
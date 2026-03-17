import os
import pandas as pd
from scripts.generate_jsonl import generate_jsonl
from src.normalization import load_and_normalize
from src.deduplication import semantic_deduplicate
from src.extraction import extract_metadata
from src.relevance import score_relevance
from src.llm import generate_newsletter
from src.scoring_report import audit_report

def run_advanced_pipeline():
    print("==================================================")
    print("Starting Advanced NLP FMCG Deal Intelligence Pipeline")
    print("==================================================")

    # 1. Dataset Generation
    dataset_path = "data/sample_news.jsonl"
    print("\n>>> Phase 1: Data Simulation <<<")
    generate_jsonl(dataset_path)

    # 2. Normalization & Exact Deduplication
    print("\n>>> Phase 2: Normalization & Exact Deduplication <<<")
    norm_df = load_and_normalize(dataset_path)
    print(f"Items remaining after normalization: {len(norm_df)}")

    # 3. Semantic Near-Deduplication
    print("\n>>> Phase 3: Semantic Near-Deduplication <<<")
    dedup_df = semantic_deduplicate(norm_df)
    print(f"Items remaining after exact & semantic deduplication: {len(dedup_df)}")

    # 4. Entity & Category Extraction (spaCy)
    print("\n>>> Phase 4: NLP Extraction (spaCy) <<<")
    extracted_df = extract_metadata(dedup_df)
    
    # 5. Semantic Relevance Scoring
    print("\n>>> Phase 5: Semantic Intent Relevance Filtering <<<")
    # We pass the extracted_df and apply the keyword sieve + embedding scoring logic
    relevant_df = score_relevance(extracted_df)

    # 6. Final LLM Generation
    print("\n>>> Phase 6: Gemini Newsletter Formatting <<<")
    generate_newsletter(relevant_df, output_dir="output")

    # 7. Export Similarity Audit Report
    print("\n>>> Phase 7: Exporting Similarity Audit Report <<<")
    audit_report.export(output_dir="output")

    print("\n==================================================")
    print("Advanced NLP Pipeline Completed Successfully.")
    print("==================================================")

if __name__ == "__main__":
    run_advanced_pipeline()

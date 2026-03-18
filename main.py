import sys
import os
# Fix for macOS segmentation fault related to HuggingFace tokenizers and OpenMP
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
import pandas as pd
from scripts.generate_jsonl import generate_jsonl
from scripts.fetch_live_data import fetch_live_data
from src.normalization import load_and_normalize
from src.clustering import cluster_and_extract_topics
from src.extraction import extract_metadata
from src.llm import generate_newsletter
from src.scoring_report import audit_report

def run_advanced_pipeline(mode="sample"):
    print("==================================================")
    print("Starting Advanced NLP FMCG Deal Intelligence Pipeline")
    print("==================================================")

    # 1. Dataset Generation
    if mode == "live":
        dataset_path = "data/live_news.jsonl"
        print("\n>>> Phase 1: Live Data Fetching <<<")
        fetch_live_data(dataset_path)
    else:
        dataset_path = "data/sample_news.jsonl"
        print("\n>>> Phase 1: Data Simulation <<<")
        generate_jsonl(dataset_path)

    # 2. Normalization & Exact Deduplication
    print("\n>>> Phase 2: Normalization & Exact Deduplication <<<")
    norm_df = load_and_normalize(dataset_path)
    print(f"Items remaining after normalization: {len(norm_df)}")

    # 3. Semantic Clustering & Relevance Filtration
    topics_json = cluster_and_extract_topics(norm_df)
    
    if not topics_json:
        print("No valid FMCG topics found.")
        return

    # Extract the representative raw DataFrame rows for spaCy extraction
    rep_df = pd.DataFrame([t['raw_row'] for t in topics_json])

    # 4. Entity & Category Extraction (spaCy) - ONLY on the representative cluster articles
    print("\n>>> Phase 4: NLP Extraction (spaCy) <<<")
    extracted_df = extract_metadata(rep_df)
    
    # We update the topics_json with the new spaCy extractions
    for i, (_, row) in enumerate(extracted_df.iterrows()):
        # Match back to the topics list using positional enumeration
        
        # We inject the extracted metadata into the top representative article of the cluster
        if topics_json[i].get('articles'):
            top_article = topics_json[i]['articles'][0]
            top_article['deal_type'] = row.get('predicted_deal_type', 'Other')
            top_article['organizations'] = row.get('organizations', '')
            top_article['locations'] = row.get('locations', '')
            top_article['monetary_values'] = row.get('monetary_values', '')
        
        # Remove the pandas Series before JSON serialization
        if 'raw_row' in topics_json[i]:
            del topics_json[i]['raw_row']

    # 5. Final LLM Generation
    print("\n>>> Phase 5: Gemini Topic-Based Newsletter Formatting <<<")
    generate_newsletter(topics_json, extracted_df, output_dir="output")

    # 6. Similarity Report Export
    print("\n>>> Phase 6: Exporting Audit Report <<<")
    audit_report.export(output_dir="output")

    print("\n==================================================")
    print("Advanced NLP Pipeline Completed Successfully.")
    print("==================================================")

if __name__ == "__main__":
    mode = "sample"
    if len(sys.argv) > 1 and sys.argv[1].lower() == "live":
        mode = "live"
    run_advanced_pipeline(mode)

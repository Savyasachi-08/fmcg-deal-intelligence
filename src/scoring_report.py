import os
import pandas as pd
from datetime import datetime

class ScoringAuditReport:

    def __init__(self):
        self.dedup_records = []
        self.relevance_records = []

    def set_metadata(self, **kwargs):
        pass

    def log_dedup_pair(self, idx_a: int, title_a: str, idx_b: int, title_b: str,
                       similarity: float, threshold: float,
                       cred_a: float, cred_b: float,
                       decision: str, kept_idx: int):
        self.dedup_records.append({
            "Article A": title_a[:100],
            "Article B": title_b[:100],
            "Similarity Score": round(float(similarity), 5),
        })

    def log_dedup_no_duplicates(self, total_articles: int):
        self.dedup_records.append({
            "Article A": f"No near-duplicate pairs found among {total_articles} articles",
            "Article B": "",
            "Similarity Score": "N/A",
        })

    def log_relevance_item(self, idx: int, title: str, passes_sieve: bool,
                           cosine_sim: float, threshold: float,
                           deal_type: str, decision: str):
        self.relevance_records.append({
            "Article Title": title[:100],
            "Similarity Score": round(float(cosine_sim), 5),
            "Decision": decision,
        })

    def export(self, output_dir: str = "output"):
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"similarity_scores_{timestamp}.xlsx")

        from src.normalization import load_config
        config = load_config()

        guidelines_records = [
            {"Parameter": "Exact Deduplicate", "Current Value": config['thresholds'].get('exact_deduplicate', True), "Description": "Hash URL + content to drop 100% identical articles."},
            {"Parameter": "Near Duplicate Similarity Threshold", "Current Value": config['thresholds'].get('near_duplicate_sim', 0.90), "Description": "Cosine similarity above which two articles are considered the same event."},
            {"Parameter": "Relevance Similarity Threshold", "Current Value": config['thresholds'].get('relevance_sim', 0.25), "Description": "Minimum similarity vs FMCG intent prompt for a cluster to be included."},
            {"Parameter": "Embedder Model", "Current Value": config['pipeline'].get('sentence_transformer_model', 'all-mpnet-base-v2'), "Description": "Sentence transformer used for vectorizing article text."},
            {"Parameter": "Entity Extraction Model", "Current Value": config['pipeline'].get('spacy_model', 'en_core_web_sm'), "Description": "SpaCy model for extracting orgs, locations, and monetary values."},
        ]

        credibility = config.get('credibility', {})
        for domain, score in credibility.items():
            guidelines_records.append({
                "Parameter": f"Source Credibility: {domain}",
                "Current Value": score,
                "Description": "Tie-breaker score used when two near-duplicate articles are from different sources."
            })

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            if self.dedup_records:
                dedup_df = pd.DataFrame(self.dedup_records)
                dedup_df = dedup_df.drop_duplicates(subset=["Article A", "Article B"])
                dedup_df.to_excel(writer, sheet_name="Deduplication Scores", index=False)

            if self.relevance_records:
                rel_df = pd.DataFrame(self.relevance_records)
                rel_df.to_excel(writer, sheet_name="Relevance Scores", index=False)
                
            guidelines_df = pd.DataFrame(guidelines_records)
            guidelines_df.to_excel(writer, sheet_name="Guidelines & Assumptions", index=False)

        print(f"\n📊 Similarity Scores saved to: {filepath}")
        return filepath

audit_report = ScoringAuditReport()

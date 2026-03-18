"""
Scoring Audit Report Generator
Generates a simplified Excel report with similarity scores.
"""
import os
import pandas as pd
from datetime import datetime

class ScoringAuditReport:
    """Collects similarity scores and exports a simple audit report."""

    def __init__(self):
        self.dedup_records = []
        self.relevance_records = []

    def set_metadata(self, **kwargs):
        """No longer used, kept for backwards compatibility."""
        pass

    # ── Deduplication Logging ──────────────────────────────────────────

    def log_dedup_pair(self, idx_a: int, title_a: str, idx_b: int, title_b: str,
                       similarity: float, threshold: float,
                       cred_a: float, cred_b: float,
                       decision: str, kept_idx: int):
        """Log a near-duplicate pair evaluation."""
        self.dedup_records.append({
            "Article A": title_a[:100],
            "Article B": title_b[:100],
            "Similarity Score": round(float(similarity), 5),
        })

    def log_dedup_no_duplicates(self, total_articles: int):
        """Log when no near-duplicates are found."""
        self.dedup_records.append({
            "Article A": f"No near-duplicate pairs found among {total_articles} articles",
            "Article B": "",
            "Similarity Score": "N/A",
        })

    # ── Relevance Logging ─────────────────────────────────────────────

    def log_relevance_item(self, idx: int, title: str, passes_sieve: bool,
                           cosine_sim: float, threshold: float,
                           deal_type: str, decision: str):
        """Log a single article's relevance evaluation."""
        self.relevance_records.append({
            "Article Title": title[:100],
            "Similarity Score": round(float(cosine_sim), 5),
        })

    # ── Export ─────────────────────────────────────────────────────────

    def export(self, output_dir: str = "output"):
        """Export the simple audit report as a three-sheet Excel workbook."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"similarity_scores_{timestamp}.xlsx")

        from src.normalization import load_config
        config = load_config()

        guidelines_records = [
            {"Parameter": "Exact Deduplicate", "Current Value": config['thresholds'].get('exact_deduplicate', True), "Description": "Hashes URLs, titles, and content directly to drop 100% exact matches."},
            {"Parameter": "Near Duplicate Similarity Threshold", "Current Value": config['thresholds'].get('near_duplicate_sim', 0.90), "Description": "Cosine threshold using FAISS above which articles are considered the same exact event and get merged."},
            {"Parameter": "Relevance Similarity Threshold", "Current Value": config['thresholds'].get('relevance_sim', 0.25), "Description": "Similarity vs FMCG Intent Prompt required for the cluster to be deemed relevant macro-level news."},
            {"Parameter": "Embedder Model", "Current Value": config['pipeline'].get('sentence_transformer_model', 'all-mpnet-base-v2'), "Description": "Model converting articles into contextual vectors."},
            {"Parameter": "Entity Extraction Model", "Current Value": config['pipeline'].get('spacy_model', 'en_core_web_sm'), "Description": "Lightweight SpaCy model mapping custom money, locations, and orgs."},
        ]

        credibility = config.get('credibility', {})
        for domain, score in credibility.items():
            guidelines_records.append({"Parameter": f"Source Credibility: {domain}", "Current Value": score, "Description": "Priority tie-breaker ratio index used during near-deduplication logic."})

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # Sheet 1: Deduplication Scores
            if self.dedup_records:
                # Remove duplicates in the logging (so A-B is only logged once)
                dedup_df = pd.DataFrame(self.dedup_records)
                dedup_df = dedup_df.drop_duplicates(subset=["Article A", "Article B"])
                dedup_df.to_excel(writer, sheet_name="Deduplication Scores", index=False)

            # Sheet 2: Relevance Scores
            if self.relevance_records:
                rel_df = pd.DataFrame(self.relevance_records)
                rel_df.to_excel(writer, sheet_name="Relevance Scores", index=False)
                
            # Sheet 3: Guidelines & Assumptions
            guidelines_df = pd.DataFrame(guidelines_records)
            guidelines_df.to_excel(writer, sheet_name="Guidelines & Assumptions", index=False)

        print(f"\n📊 Similarity Scores saved to: {filepath}")
        return filepath

# Module-level singleton
audit_report = ScoringAuditReport()

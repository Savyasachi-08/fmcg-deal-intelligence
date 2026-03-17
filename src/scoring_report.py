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
        """Export the simple audit report as a two-sheet Excel workbook."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(output_dir, f"similarity_scores_{timestamp}.xlsx")

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # Sheet 1: Deduplication Scores
            if self.dedup_records:
                # Remove duplicates in the logging (so A-B is only logged once)
                # We use drop_duplicates based on the titles
                dedup_df = pd.DataFrame(self.dedup_records)
                dedup_df = dedup_df.drop_duplicates(subset=["Article A", "Article B"])
                dedup_df.to_excel(writer, sheet_name="Deduplication Scores", index=False)

            # Sheet 2: Relevance Scores
            if self.relevance_records:
                rel_df = pd.DataFrame(self.relevance_records)
                rel_df.to_excel(writer, sheet_name="Relevance Scores", index=False)

        print(f"\n📊 Similarity Scores saved to: {filepath}")
        return filepath

# Module-level singleton
audit_report = ScoringAuditReport()

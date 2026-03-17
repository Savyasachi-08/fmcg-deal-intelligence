# FMCG Deal Intelligence & Semantic Clustering Pipeline

An enterprise-grade NLP pipeline that fetches global news, uses semantic embeddings to cluster real-word events, and generates a business-ready Executive Newsletter for the FMCG sector.

## Key Features

1. **Dual-Gate Relevance Filter**: Uses a high-speed keyword sieve and **Multiple-Intent Cosine Similarity** (matching against 10 specific deal types like Acquisitions, D2C Funding, and PE Stakes) to ensure 99% FMCG relevance.
2. **Semantic Clustering (HDBSCAN)**: Groups related articles from different sources into single "Real-World Events" using semantic embeddings (`all-mpnet-base-v2`), avoiding redundant reporting.
3. **Intra-Cluster Deduplication**: Selects the most credible representative article (Ranked: Reuters > FT > Others) for each event, removing near-duplicates.
4. **Config-Driven Heuristics**: Fine-tune vector thresholds, source credibility, and sector keywords directly in `config.yaml`.
5. **Gemini-Powered Newsletter**: High-quality business impact analysis and executive summaries generated via `gemini-2.0-flash`, exported to a professional Word document.

## Project Structure

```text
fmcg-deal-intelligence/
├── config.yaml               # Thresholds, Intents, and Source Credibility
├── scripts/
│   └── fetch_live_data.py    # Live RSS fetching for FMCG & Automobile sectors
├── src/
│   ├── normalization.py      # URL/Date normalization and Exact-Dedup (SHA256)
│   ├── clustering.py         # HDBSCAN clustering, Multi-Intent filtering, and Near-Dedup
│   ├── extraction.py         # SpaCy NER (ORG, GPE, MONEY)
│   ├── relevance.py          # FMCG Keyword Sieve
│   └── llm.py                # Gemini orchestration and DOCX generation
├── main.py                   # Orchestrator (Routes: 'sample' or 'live')
└── requirements.txt          # sentence-transformers, hdbscan, faiss-cpu, etc.
```

## Setup & Execution

### 1. Environment Setup
```bash
python3 -m venv venv_nlp
source venv_nlp/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Gemini API
Create a `.env` file in the root:
```
GEMINI_API_KEY="your_key_here"
```

### 3. Run the Pipeline
Run with **Sample Data** (Predefined scenarios):
```bash
python main.py sample
```

Run with **Live News** (Fetches latest RSS from Reuters/Google News):
```bash
python main.py live
```

## Output Results
- `output/advanced_nlp_clustered_topics.csv`: The final deduplicated and clustered dataset.
- `output/FMCG_Executive_Newsletter.docx`: The final drafted business newsletter.

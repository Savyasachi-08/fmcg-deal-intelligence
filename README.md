# FMCG Deal Intelligence & Newsletter Agent

An NLP pipeline that fetches global FMCG news, clusters real-world events using semantic embeddings, and generates a business-ready executive newsletter as a Word document — with a full similarity audit report in Excel.

---

## How It Works

The pipeline runs in 6 sequential phases:

1. **Data Input** — Either simulates a sample dataset or fetches live FMCG news via RSS feeds
2. **Normalization & Exact Dedup** — Cleans URLs and dates, hashes content to drop identical duplicates
3. **Semantic Clustering** — Groups related articles into real-world events using HDBSCAN on `all-mpnet-base-v2` embeddings. A dual-gate filter (keyword sieve + cosine similarity vs. 10 FMCG intent prompts) ensures only relevant deals make it through
4. **NLP Extraction** — Runs spaCy to extract organizations, locations, and monetary values from the grouped articles
5. **Cluster Breakdown Report** — Generates a transparent `Cluster_Breakdown_Report.docx` immediately before LLM processing, literally listing out every article and its publisher that successfully parsed into a given event cluster.
6. **Gemini Newsletter** — Takes the Top 10 validated clusters and makes **1 API call per cluster** to Gemini 2.0 Flash. The model synthesizes the entirely of the cluster's context into a single unified business headline, 2-4 bullet points, and extracts the top 2 source URLs
7. **Audit Report** — Exports a timestamped Excel file with deduplication decisions, relevance scores, and the config-driven guidelines used

---

## Project Structure

```
fmcg-deal-intelligence/
├── config.yaml               # Thresholds, intent prompts, and source credibility scores
├── main.py                   # Entry point — runs sample or live mode
├── requirements.txt
├── .env                      # Your Gemini API key goes here (not committed)
├── data/
│   └── sample_news.jsonl     # Auto-generated when running sample mode
├── scripts/
│   ├── generate_jsonl.py     # Generates the sample dataset
│   └── fetch_live_data.py    # Fetches live RSS feeds for FMCG news
├── src/
│   ├── normalization.py      # URL/date normalization, SHA-256 exact dedup
│   ├── clustering.py         # HDBSCAN clustering + FMCG relevance filter
│   ├── deduplication.py      # Semantic near-dedup using FAISS
│   ├── extraction.py         # spaCy NER + deal type heuristics
│   ├── relevance.py          # Keyword sieve definition
│   ├── llm.py                # Gemini API calls + DOCX generation
│   └── scoring_report.py     # Excel audit report builder
└── output/
    ├── FMCG_Executive_Newsletter.docx
    ├── advanced_nlp_clustered_topics.csv
    └── similarity_scores_<timestamp>.xlsx
```

---

## Setup

### Prerequisites
- Python 3.9 or higher
- A [Gemini API key](https://aistudio.google.com/app/apikey) (free tier works)

---

### Mac / Linux

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the spaCy language model
python -m spacy download en_core_web_sm

# 4. Create your .env file with your API key
echo 'GEMINI_API_KEY="your_key_here"' > .env
```

**Run with sample data:**
```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 python main.py sample
```
> The `PYTORCH_ENABLE_MPS_FALLBACK=1` flag is needed on Apple Silicon (M1/M2/M3) Macs. On Intel Macs or Linux, you can just run `python main.py sample`.

**Run with live news:**
```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 python main.py live
```

---

### Windows

```cmd
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the spaCy language model
python -m spacy download en_core_web_sm

# 4. Create your .env file
# Create a file named .env in the project root with this content:
#   GEMINI_API_KEY="your_key_here"
```

**Run with sample data:**
```cmd
python main.py sample
```

**Run with live news:**
```cmd
python main.py live
```

> **Windows Note:** If you see a `faiss` import error, ensure you installed `faiss-cpu` from `requirements.txt` and not a GPU variant. If you see a torch/numpy conflict, run `pip install "faiss-cpu<1.8.0"` to pin to a compatible version.

---

## Configuration

All key parameters live in `config.yaml` — no code changes needed:

| Setting | What it controls |
|---|---|
| `near_duplicate_sim` | Cosine threshold above which two articles are treated as duplicates (default: 0.90) |
| `relevance_sim` | Minimum similarity vs FMCG intent prompts for a cluster to be included (default: 0.25) |
| `credibility` | Per-domain trust scores used as tie-breakers during deduplication |
| `fmcg_intents` | The list of intent prompts the embedding model compares against |

### Tuning the Live Feeds
By default, `scripts/fetch_live_data.py` uses Google News RSS targeted specifically at major financial wire services (`reuters.com`, `bloomberg.com`, etc.) over a **7-day window**. 

If you want to pull data from different domains (e.g. `techcrunch.com`), remove the strict `site:` filter directly from the `FMCG_URL` in `fetch_live_data.py`. 

---

## Outputs

After running, check the `output/` folder:

| File | Description |
|---|---|
| `FMCG_Executive_Newsletter.docx` | The final executive newsletter with overarching strategic summaries, individual deal bullet points, and top-tier source links |
| `Cluster_Breakdown_Report.docx` | A complete list of all HDBSCAN clusters formed, showing exactly which articles (and from which publisher) were grouped together for the LLM to process |
| `advanced_nlp_clustered_topics.csv` | The deduplicated and clustered article dataset used as input to Gemini |
| `similarity_scores_<timestamp>.xlsx` | Audit report with 3 sheets: Deduplication decisions, Relevance scores, and Guidelines & Assumptions |

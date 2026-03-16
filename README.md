# Advanced FMCG Deal Intelligence Pipeline

An enterprise-grade, advanced Natural Language Processing (NLP) pipeline that simulates pulling global news sources and uses semantic embeddings to filter, deduplicate, and compile an authentic, business-friendly Executive Deal Newsletter for the FMCG sector.

## 🌟 Key Features

1. **Config-Driven Architecture**: Uses `config.yaml` to securely adjust vector threshold sensitivity (e.g., matching intent at 0.20 cosine similarity) and define exact domain credibility rankings (Reuters > TechCrunch).
2. **Deterministic & Semantic Deduplication**:
   - Computes canonical URLs and exact `SHA256` content hashes.
   - Computes title + text chunk embeddings using `sentence-transformers` (`all-mpnet-base-v2`).
   - Mathematically isolates semantic near-duplicates and drops the duplicate from the lowest credibility source.
3. **Advanced Entity Extraction**: Uses `spaCy` (`en_core_web_sm`) to natively predict and pull `ORG` (Organizations), `GPE` (Geopolitical locations), and `MONEY` tokens directly from the news text.
4. **FMCG Intent Sieve & Vector Scoring**: Safely removes unrelated tech or pharma acquisitions by merging a fast regex keyword sieve with complex vector intent scoring matching exactly against defined FMCG parameters.
5. **Business Output Delivery**: Passes ONLY pristine, de-hashed metrics into `gemini-2.0-flash` to write a structured narrative. The final result automatically exports natively to a styled `FMCG_Executive_Newsletter.docx` using `python-docx`.

## 📁 Project Structure

```text
fmcg-deal-intelligence/
├── config.yaml               # Credibility heuristics and Embedding thresholds
├── data/
│   └── sample_news.jsonl     # Automatically simulated mock data (FMCG, Tech, Exact Duplicates)
├── scripts/
│   └── generate_jsonl.py     # Script to write the initial mock JSONL datastream
├── src/
│   ├── normalization.py      # Cleans links, maps dates, hashes exact duplicates
│   ├── deduplication.py      # Creates PyTorch MPNet embeddings, drops nearest-neighbor redundancies
│   ├── extraction.py         # SpaCy NLP Named Entity Recognition map
│   ├── relevance.py          # Intent Vector mapping to FMCG keywords and dropping low-scoring outliers
│   └── llm.py                # Constructs the Gemini Business report and DOCX file
├── main.py                   # Orchestrator running the complete chronological pipeline
└── requirements.txt          # Advanced NLP dependencies (sentence-transformers, spacy, etc.)
```

## 🚀 Setup & Execution

### 1. Environment Setup
```bash
# Create local virtual environment
python3 -m venv venv_nlp
source venv_nlp/bin/activate

# Install core dependencies
pip install -r requirements.txt

# Download spaCy English Model
python -m spacy download en_core_web_sm
```

### 2. Configure Google Gemini API Key
Create a `.env` file in the root `fmcg-deal-intelligence/` directory:
```
GEMINI_API_KEY="your_actual_gemini_key_here"
```

### 3. Run the Pipeline
Simply execute the main orchestration script:
```bash
PYTHONPATH=. python main.py
```

### 4. Output results
Once finished, the directory will yield your results:
- `output/advanced_nlp_clean_deals.csv`: Contains the pure surviving entities and their NLP token logic.
- `output/FMCG_Executive_Newsletter.docx`: The final drafted business intelligence word document.

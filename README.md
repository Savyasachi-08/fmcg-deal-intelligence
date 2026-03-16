# LLM-Assisted FMCG Deal Intelligence Newsletter Agent

This repository contains a modular Python pipeline that autonomously curates, categorizes, deduplicates, and synthesizes FMCG (Fast-Moving Consumer Goods) deal insights from diverse news sources into a professional executive newsletter utilizing the Gemini 2.0 LLM.

## Pipeline Architecture

1. **Ingestion & Simulation (`data_simulation.py` & `ingestion.py`)**: Automatically spawns and aggregates a diverse dataset of ~70 M&A/Investment news events encompassing both FMCG and extraneous sectors (Tech, Pharma) spanning varied simulated news channels.
2. **Credibility Ranking (`credibility_ranking.py`)**: Assigns static credibility weights to sources (e.g. `Reuters` = 0.95, `Unknown Blog` = 0.50). 
3. **LLM Categorization (`llm_categorization.py`)**: Leverages `gemini-2.0-flash` to read and evaluate the raw summary strings, generating consistent Deal Types (e.g., Acquisition, Joint Venture) and succinct 3-4 bullet constraints.
4. **Embeddings & Deduplication (`embeddings.py` & `deduplication.py`)**: Computes TF-IDF vector embeddings over the LLM-generated summaries and calculates Cosine Similarities. Near-duplicate hits (≥ 0.75 threshold) are merged, strictly retaining the observation tethered to the more credible source.
5. **FMCG Relevance Filter (`fmcg_filter.py`)**: Passes the cleanly deduplicated dataset against lexical and entity filters to explicitly extract FMCG relevance while eliminating extraneous Tech/Fintech noise.
6. **Newsletter Generation (`newsletter_generator.py`)**: Interfaces back with the Gemini LLM to construct a polished, professionally stylized DOCX Newsletter compiling the leading FMCG deals. Also dumps pure structured output locally to `output/clean_deals.csv`.

## Setup & Execution

### Prerequisites
- Python 3.8+
- Active Gemini API Key

### Installation

```bash
# 1. Setup a virtual instance
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup API Key in .env
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env
```

### Run Project
```bash
python main.py
```

Check the `output/` directory post-execution for `clean_deals.csv` and the polished `fmcg_newsletter.docx`.

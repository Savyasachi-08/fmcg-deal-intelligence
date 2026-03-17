import pandas as pd
import numpy as np
import faiss
from src.normalization import load_config
from src.deduplication import load_embedder
from src.scoring_report import audit_report
import re

FMCG_KEYWORDS = [
    "food", "beverage", "consumer goods", "personal care", "fmcg", "snack",
    "skincare", "beauty", "cosmetics", "grocery", "nutrition", "chocolate"
]

def keyword_sieve(text: str) -> bool:
    """Fast lexical check as a preliminary filter."""
    text = str(text).lower()
    words = set(re.findall(r'\b\w+\b', text))
    for keyword in FMCG_KEYWORDS:
        if len(keyword.split()) > 1:
            if keyword in text: return True
        elif keyword in words:
            return True
    return False

def score_relevance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scores news items against an FMCG intent prompt using a FAISS vector db,
    combining it with a keyword sieve.
    """
    print("Scoring semantic FMCG relevance...")
    if df.empty: return df
    
    df = df.reset_index(drop=True)
    config = load_config()
    threshold = config['thresholds'].get('relevance_sim', 0.50)
    intent_prompt = config['prompts'].get('fmcg_intent', "News about mergers, acquisitions or investments involving fast-moving consumer goods brands and manufacturers")
    
    embedder = load_embedder()
    intent_vector = embedder.encode([intent_prompt])
    
    # 1. Batch vectorize all rows
    def get_text_to_embed(row):
        return str(row.get('title', '')) + " " + str(row.get('content', ''))
        
    texts = df.apply(get_text_to_embed, axis=1).tolist()
    item_vectors = embedder.encode(texts)
    
    # 2. Compute similarity using Faiss Vector DB
    intent_vector = np.array(intent_vector, dtype=np.float32)
    faiss.normalize_L2(intent_vector)
    
    item_vectors = np.array(item_vectors, dtype=np.float32)
    faiss.normalize_L2(item_vectors)
    
    d = item_vectors.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(item_vectors)
    
    # 3. Retrieve neighbors
    k = len(item_vectors)
    D, I = index.search(intent_vector, k)
    
    sim_scores = np.zeros(k)
    for i, idx in enumerate(I[0]):
        sim_scores[idx] = D[0][i]
        
    # 4. Filter logic
    df['passes_sieve'] = df.apply(lambda row: keyword_sieve(get_text_to_embed(row)), axis=1)
    df['tru_sim'] = sim_scores
    
    initial_len = len(df)
    
    # Print diagnostics for tuning
    print("Semantic similarity scores for all items:")
    for _, item in df.iterrows():
        print(f"- {item['title'][:40]}... Sieve: {item['passes_sieve']} Sim: {item['tru_sim']:.3f} DealType: {item.get('predicted_deal_type', 'N/A')}")
    
    # We require BOTH the keyword sieve to hit AND semantic similarity to be loosely above a reasonable contextual threshold like 0.35 in higher dimensional spaces
    threshold = config['thresholds'].get('relevance_sim', 0.35) 
    
    # Log metadata and per-article scores to audit report
    audit_report.set_metadata(
        relevance_threshold=threshold,
        relevance_embedding_strategy="Title + Full content",
        intent_prompt=intent_prompt,
        sentence_transformer_model=config['pipeline'].get('sentence_transformer_model', 'all-mpnet-base-v2'),
        faiss_index_type="IndexFlatIP (Flat Inner Product / Cosine Similarity)",
        vector_dimensions=int(d),
        total_articles_evaluated=initial_len,
        pipeline_run_timestamp=pd.Timestamp.now().isoformat(),
    )
    
    for idx, item in df.iterrows():
        passes = bool(item['passes_sieve'])
        sim = float(item['tru_sim'])
        accepted = passes and sim >= threshold
        decision = "ACCEPTED" if accepted else "REJECTED"
        audit_report.log_relevance_item(
            idx=idx,
            title=str(item['title']),
            passes_sieve=passes,
            cosine_sim=sim,
            threshold=threshold,
            deal_type=str(item.get('predicted_deal_type', 'N/A')),
            decision=decision,
        )
    
    df_filtered = df[(df['passes_sieve'] == True) & (df['tru_sim'] >= threshold)].copy()
    
    print(f"Relevance scoring dropped {initial_len - len(df_filtered)} items. {len(df_filtered)} FMCG deals remain.")
    return df_filtered

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from src.normalization import load_config
from src.deduplication import load_embedder
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
    Scores news items against an FMCG intent prompt using embeddings,
    combining it with a keyword sieve.
    """
    print("Scoring semantic FMCG relevance...")
    if df.empty: return df
    
    config = load_config()
    threshold = config['thresholds'].get('relevance_sim', 0.50)
    intent_prompt = config['prompts'].get('fmcg_intent', "News about mergers, acquisitions or investments involving fast-moving consumer goods brands and manufacturers")
    
    embedder = load_embedder()
    intent_vector = embedder.encode([intent_prompt])
    
    def evaluate_row(row):
        text = str(row.get('title', '')) + " " + str(row.get('content', ''))
        
        # Sieve
        passes_sieve = keyword_sieve(text)
        
        # Sim Score (We specifically embed title + content together here)
        item_vector = embedder.encode([text])
        sim_score = cosine_similarity(item_vector, intent_vector)[0][0]
        
        return pd.Series({'passes_sieve': passes_sieve, 'tru_sim': sim_score})
        
    scores = df.apply(evaluate_row, axis=1)
    df = pd.concat([df, scores], axis=1)
    
    # Filter
    initial_len = len(df)
    
    # Print diagnostics for tuning
    print("Semantic similarity scores for all items:")
    for _, item in df.iterrows():
        print(f"- {item['title'][:40]}... Sieve: {item['passes_sieve']} Sim: {item['tru_sim']:.3f} DealType: {item['predicted_deal_type']}")
    
    # We require BOTH the keyword sieve to hit AND semantic similarity to be loosely above a reasonable contextual threshold like 0.35 in higher dimensional spaces
    threshold = config['thresholds'].get('relevance_sim', 0.35) 
    df_filtered = df[(df['passes_sieve'] == True) & (df['tru_sim'] >= threshold)].copy()
    
    print(f"Relevance scoring dropped {initial_len - len(df_filtered)} items. {len(df_filtered)} FMCG deals remain.")
    return df_filtered

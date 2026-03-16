import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from src.normalization import load_config

def load_embedder():
    config = load_config()
    model_name = config['pipeline'].get('sentence_transformer_model', "all-mpnet-base-v2")
    return SentenceTransformer(model_name)

def get_credibility_score(domain: str, config: dict) -> float:
    cred = config.get('credibility', {})
    return cred.get(domain.lower(), 0.5)

def semantic_deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops near-duplicates using content embeddings and cosine similarity.
    Resolves ties by Newest + Highest Credibility.
    """
    if df.empty:
        return df
        
    print("Running semantic near-deduplication...")
    config = load_config()
    threshold = config['thresholds'].get('near_duplicate_sim', 0.93)
    
    # Assign credibility scores for tie-breaking
    df['credibility'] = df['source_domain'].apply(lambda x: get_credibility_score(x, config))
    
    df = df.reset_index(drop=True)
    embedder = load_embedder()
    
    # Embed Title + First 600 words of content
    def get_text_to_embed(row):
        title = str(row.get('title', ''))
        content = str(row.get('content', ''))
        words = content.split()[:600]
        return title + " " + " ".join(words)
        
    texts = df.apply(get_text_to_embed, axis=1).tolist()
    embeddings = embedder.encode(texts)
    
    # Compute similarities
    cosine_sim = cosine_similarity(embeddings)
    
    to_drop = set()
    
    for i in range(len(cosine_sim)):
        if i in to_drop:
            continue
            
        for j in range(i + 1, len(cosine_sim)):
            if cosine_sim[i, j] >= threshold:
                # Decide which to keep based on Credibility then Newest
                cred_i = df.loc[i, 'credibility']
                cred_j = df.loc[j, 'credibility']
                
                # If credibility is identical, check published_at date
                if cred_i == cred_j:
                    date_i = df.loc[i, 'published_at']
                    date_j = df.loc[j, 'published_at']
                    if pd.notnull(date_i) and pd.notnull(date_j) and date_i < date_j:
                        to_drop.add(i)
                        break
                    else:
                        to_drop.add(j)
                elif cred_i > cred_j:
                    to_drop.add(j)
                else:
                    to_drop.add(i)
                    break
                    
    df_dedup = df.drop(index=list(to_drop))
    print(f"Semantic near-deduplication removed {len(to_drop)} rows.")
    return df_dedup

if __name__ == "__main__":
    pass

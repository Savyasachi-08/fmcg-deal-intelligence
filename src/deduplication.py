import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.normalization import load_config
from src.scoring_report import audit_report

def load_embedder():
    config = load_config()
    model_name = config['pipeline'].get('sentence_transformer_model', "all-mpnet-base-v2")
    return SentenceTransformer(model_name)

def get_credibility_score(domain: str, config: dict) -> float:
    cred = config.get('credibility', {})
    return cred.get(domain.lower(), 0.5)

def semantic_deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops near-duplicates using content embeddings and faiss similarity search.
    Resolves ties by Newest + Highest Credibility.
    """
    if df.empty:
        return df
        
    print("Running semantic near-deduplication...")
    config = load_config()
    threshold = config['thresholds'].get('near_duplicate_sim', 0.93)
    
    audit_report.set_metadata(
        dedup_threshold=threshold,
        dedup_embedding_strategy="Title + First 600 words of content",
    )
    
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
    
    # Compute similarities using faiss Vector DB
    embeddings = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings)
    
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    
    k = len(embeddings)
    D, I = index.search(embeddings, k) # query against itself
    
    to_drop = set()
    duplicate_found = False
    
    for i in range(len(embeddings)):
        if i in to_drop:
            continue
            
        for k_idx in range(k):
            j = I[i][k_idx]
            if i >= j: # We only care about pairs where i < j (already deduped or self)
                continue
                
            sim_score = D[i][k_idx]
            if sim_score >= threshold:
                if j in to_drop:
                    continue
                
                duplicate_found = True
                    
                # Decide which to keep based on Credibility then Newest
                cred_i = df.loc[i, 'credibility']
                cred_j = df.loc[j, 'credibility']
                
                # If credibility is identical, check published_at date
                if cred_i == cred_j:
                    date_i = df.loc[i, 'published_at']
                    date_j = df.loc[j, 'published_at']
                    if pd.notnull(date_i) and pd.notnull(date_j) and date_i < date_j:
                        decision = f"Drop A (older date); Keep B"
                        kept = j
                        to_drop.add(i)
                        audit_report.log_dedup_pair(i, df.loc[i, 'title'], j, df.loc[j, 'title'],
                                                   sim_score, threshold, cred_i, cred_j, decision, kept)
                        break
                    else:
                        decision = f"Drop B (older/equal date); Keep A"
                        kept = i
                        to_drop.add(j)
                elif cred_i > cred_j:
                    decision = f"Drop B (lower credibility {cred_j}); Keep A (credibility {cred_i})"
                    kept = i
                    to_drop.add(j)
                else:
                    decision = f"Drop A (lower credibility {cred_i}); Keep B (credibility {cred_j})"
                    kept = j
                    to_drop.add(i)
                    audit_report.log_dedup_pair(i, df.loc[i, 'title'], j, df.loc[j, 'title'],
                                               sim_score, threshold, cred_i, cred_j, decision, kept)
                    break
                
                audit_report.log_dedup_pair(i, df.loc[i, 'title'], j, df.loc[j, 'title'],
                                           sim_score, threshold, cred_i, cred_j, decision, kept)
    
    if not duplicate_found:
        audit_report.log_dedup_no_duplicates(len(embeddings))
                    
    df_dedup = df.drop(index=list(to_drop))
    print(f"Semantic near-deduplication removed {len(to_drop)} rows.")
    return df_dedup

if __name__ == "__main__":
    pass

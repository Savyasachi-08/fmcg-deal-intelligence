import pandas as pd
import numpy as np
import faiss
import hdbscan
from src.normalization import load_config
from src.deduplication import load_embedder, get_credibility_score
from src.relevance import keyword_sieve

def cluster_and_extract_topics(df: pd.DataFrame) -> list:
    """
    ORDER: Cluster → FMCG Filter (passes_sieve + cosine_sim) → Intra-cluster near-dedup → Return topics
    """
    if df.empty: return []
    
    print("\n>>> Phase 3: Semantic Clustering and Topic Extraction <<<")
    
    config = load_config()
    df = df.reset_index(drop=True)
    df['credibility'] = df['source_domain'].apply(lambda x: get_credibility_score(x, config))
    
    threshold = config['thresholds'].get('relevance_sim', 0.35)
    
    total_input = len(df)
    print(f"[Input]  {total_input} articles entering clustering (post exact-dedup)")

    # ── Step 1: Embed ───────────────────────────────────────────────────────
    embedder = load_embedder()
    def get_text_to_embed(row):
        title = str(row.get('title', ''))
        content = str(row.get('content', ''))
        return title + " " + " ".join(content.split()[:600])
        
    texts = df.apply(get_text_to_embed, axis=1).tolist()
    embeddings = embedder.encode(texts)
    embeddings = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(embeddings)
    
    # FMCG Intent vector
    intent_prompt = config['prompts'].get('fmcg_intent', "News about mergers, acquisitions or investments involving fast-moving consumer goods brands and manufacturers")
    intent_vector = embedder.encode([intent_prompt])
    intent_vector = np.array(intent_vector, dtype=np.float32)
    faiss.normalize_L2(intent_vector)
    
    # Pre-compute all cosine scores and sieve results
    cosine_scores = (embeddings @ intent_vector[0]).tolist()
    df['tru_sim'] = cosine_scores
    df['passes_sieve'] = df.apply(lambda row: keyword_sieve(get_text_to_embed(row)), axis=1)

    # ── Step 2a: Keyword Sieve Pre-filter ────────────────────────────────────
    # Run cheap keyword sieve BEFORE HDBSCAN so automobile/unrelated articles
    # don't contaminate FMCG clusters (they share M&A vocabulary)
    sieve_mask = df['passes_sieve'] == True
    fmcg_df = df[sieve_mask].reset_index(drop=True)
    fmcg_embeddings = embeddings[sieve_mask.values]
    print(f"[Sieve]  Keyword sieve: {len(fmcg_df)} / {total_input} articles contain FMCG keywords")
    
    if fmcg_df.empty:
        print("  No articles passed keyword sieve.")
        return []

    # ── Step 2b: HDBSCAN Cluster on FMCG-only articles ───────────────────────
    print(f"\n[Step 2] Running HDBSCAN on {len(fmcg_df)} FMCG articles...")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=2,
        min_samples=1,
        metric='euclidean',
        cluster_selection_epsilon=0.3
    )
    cluster_labels = clusterer.fit_predict(fmcg_embeddings)
    fmcg_df = fmcg_df.copy()
    fmcg_df['cluster_id'] = cluster_labels
    # Also update embeddings reference
    embeddings_to_use = fmcg_embeddings
    df_to_use = fmcg_df

    unique_clusters = set(cluster_labels)
    n_real = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
    n_noise = int((cluster_labels == -1).sum())
    print(f"         → {n_real} event clusters + {n_noise} noise points from {len(fmcg_df)} sieve-passed articles")

    # ── Step 3: FMCG Relevance Filter per cluster ──────────────────────────
    # For REAL clusters: centroid OR any article must pass cosine threshold
    #                    AND at least 1 article must pass the keyword sieve
    # For NOISE points:  article must pass cosine threshold AND keyword sieve
    print(f"\n[Step 3] FMCG Relevance Filter (sieve + cosine_sim >= {threshold}) per cluster:")
    
    valid_topics = []
    clusters_rejected_cosine = 0
    clusters_rejected_sieve = 0
    noise_rejected = 0
    
    for c_id in sorted(unique_clusters):
        if c_id == -1:
            # Noise points: all already passed keyword sieve, just check cosine
            noise_indices = fmcg_df[fmcg_df['cluster_id'] == -1].index
            for idx in noise_indices:
                sim = fmcg_df.loc[idx, 'tru_sim']
                title_preview = str(fmcg_df.loc[idx, 'title'])[:50]
                if sim >= threshold:
                    article = fmcg_df.loc[idx]
                    valid_topics.append({
                        "topic_id": f"noise_{idx}",
                        "topic_title": str(article['title']),
                        "representative_article": {
                            "id": str(article.get('id', '')),
                            "title": str(article['title']),
                            "source": str(article['source_domain']),
                            "date": str(article['published_at']),
                            "summary": str(article.get('content', ''))[:300] + "..."
                        },
                        "cluster_size": 1,
                        "fmcg_score": float(sim),
                        "raw_row": article
                    })
                else:
                    noise_rejected += 1
                    print(f"  [NOISE REJECTED] {title_preview}... | sim={sim:.3f}<{threshold}")
            continue
        
        # Real cluster — keyword sieve already passed, check cosine
        cluster_mask = fmcg_df['cluster_id'] == c_id
        cluster_df = fmcg_df[cluster_mask].copy()
        cluster_emb_arr = fmcg_embeddings[cluster_mask.values]
        
        cluster_scores = cluster_df['tru_sim'].tolist()
        max_sim = max(cluster_scores)
        centroid = np.mean(cluster_emb_arr, axis=0)
        faiss.normalize_L2(np.array([centroid], dtype=np.float32))
        centroid_sim = float(np.dot(centroid, intent_vector[0]))
        
        cosine_ok = centroid_sim >= (threshold - 0.05) or max_sim >= threshold
        
        if not cosine_ok:
            clusters_rejected_cosine += 1
            print(f"  [CLUSTER {c_id} REJECTED - low cosine] centroid={centroid_sim:.3f}, max={max_sim:.3f}, size={len(cluster_df)}")
            continue
        # (No sieve check needed here — sieve was applied before HDBSCAN)

        # ── Step 4: Intra-cluster near-dedup ──────────────────────────────
        cluster_df_copy = cluster_df.copy()
        cluster_df_copy['sim_score'] = cluster_scores
        d = cluster_emb_arr.shape[1]
        index = faiss.IndexFlatIP(d)
        index.add(cluster_emb_arr)
        D, I = index.search(cluster_emb_arr, len(cluster_emb_arr))
        
        to_drop_local = set()
        dup_threshold = config['thresholds'].get('near_duplicate_sim', 0.90)
        for i in range(len(cluster_emb_arr)):
            if i in to_drop_local: continue
            for k_idx in range(len(cluster_emb_arr)):
                j = I[i][k_idx]
                if i >= j: continue
                if D[i][k_idx] >= dup_threshold:
                    cred_i = cluster_df_copy.iloc[i]['credibility']
                    cred_j = cluster_df_copy.iloc[j]['credibility']
                    if cred_i > cred_j: to_drop_local.add(j)
                    elif cred_j > cred_i: to_drop_local.add(i)
                    else:
                        date_i = cluster_df_copy.iloc[i]['published_at']
                        date_j = cluster_df_copy.iloc[j]['published_at']
                        to_drop_local.add(i if date_i < date_j else j)
        
        clean_df = cluster_df_copy.drop(cluster_df_copy.index[list(to_drop_local)])
        if clean_df.empty: continue
        
        rep = clean_df.sort_values(by=['credibility', 'published_at'], ascending=[False, False]).iloc[0]
        print(f"  [CLUSTER {c_id} ACCEPTED] size={int(cluster_mask.sum())}, centroid={centroid_sim:.3f}, max={max_sim:.3f} | rep: {str(rep['title'])[:50]}...")
        
        valid_topics.append({
            "topic_id": f"cluster_{c_id}",
            "topic_title": str(rep['title']),
            "representative_article": {
                "id": str(rep.get('id', '')),
                "title": str(rep['title']),
                "source": str(rep['source_domain']),
                "date": str(rep['published_at']),
                "summary": str(rep.get('content', ''))[:300] + "..."
            },
            "cluster_size": int(cluster_mask.sum()),
            "fmcg_score": float(max_sim),
            "raw_row": rep
        })
    
    print(f"\n[Summary] {n_real} real clusters: {clusters_rejected_cosine} rejected (low cosine), {clusters_rejected_sieve} rejected (no sieve)")
    print(f"[Summary] {n_noise} noise points: {noise_rejected} rejected")
    print(f"[Output]  {len(valid_topics)} valid FMCG topics → spaCy + LLM")
    
    valid_topics.sort(key=lambda x: (x['cluster_size'], x['fmcg_score']), reverse=True)
    return valid_topics

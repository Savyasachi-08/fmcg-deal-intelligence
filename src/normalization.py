import pandas as pd
import json
import hashlib
from urllib.parse import urlparse

def load_config() -> dict:
    import yaml
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def clean_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    except:
        return url

def load_and_normalize(filepath: str) -> pd.DataFrame:
    print(f"Loading and normalizing data from {filepath}...")
    
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
                
    df = pd.DataFrame(data)
    
    if df.empty:
        return df

    if 'language' in df.columns:
        df = df[df['language'] == 'en'].copy()

    df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
    df['fetched_at'] = pd.to_datetime(df['fetched_at'], errors='coerce')
    
    df['canonical_url'] = df['link'].apply(clean_url)
    
    def compute_hash(row):
        text = str(row.get('title', '')) + " " + str(row.get('content', ''))
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
        
    df['content_hash'] = df.apply(compute_hash, axis=1)
    
    config = load_config()
    if config['thresholds'].get('exact_deduplicate', True):
        initial_len = len(df)
        df = df.drop_duplicates(subset=['content_hash'])
        df = df.drop_duplicates(subset=['canonical_url'])
        print(f"Exact deduplication removed {initial_len - len(df)} rows.")

    return df

if __name__ == "__main__":
    df = load_and_normalize("data/sample_news.jsonl")
    print(df.head())

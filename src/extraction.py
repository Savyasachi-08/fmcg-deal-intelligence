import spacy
import pandas as pd
from src.normalization import load_config
import re

# Load spaCy model
try:
    config = load_config()
    nlp = spacy.load(config['pipeline'].get('spacy_model', 'en_core_web_sm'))
except OSError:
    print("Downloading spacy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> dict:
    """Extracts ORG, GPE, and MONEY entities using spaCy."""
    doc = nlp(str(text))
    entities = {'ORG': [], 'GPE': [], 'MONEY': []}
    
    for ent in doc.ents:
        if ent.label_ in entities:
            # Avoid duplicates within the local list
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
                
    return {k: ", ".join(v) for k, v in entities.items()}

def heuristic_category(text: str) -> str:
    """Heuristic logic to assign deal types and FMCG buckets."""
    text = text.lower()
    
    # Deal Type
    if any(w in text for w in ['acquire', 'acquisition', 'buyout', 'buys']):
        deal = "Acquisition"
    elif any(w in text for w in ['merger', 'merges']):
        deal = "Merger"
    elif any(w in text for w in ['stake', 'investment', 'invests', 'funding']):
        deal = "Investment/Stake"
    else:
        deal = "Other"
        
    return deal

def extract_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Applies NLP entity and category extraction to the DataFrame."""
    print("Running spaCy entity extraction and heuristics...")
    df = df.copy()
    
    # Run against Title + Summary combination
    combined_texts = df['title'].fillna("") + ". " + df['content'].fillna("")
    
    # Entity columns
    extracted = combined_texts.apply(extract_entities)
    df['organizations'] = extracted.apply(lambda x: x['ORG'])
    df['locations'] = extracted.apply(lambda x: x['GPE'])
    df['monetary_values'] = extracted.apply(lambda x: x['MONEY'])
    
    # Deal Type heuristic
    df['predicted_deal_type'] = combined_texts.apply(heuristic_category)

    return df

import spacy
import pandas as pd
from src.normalization import load_config
import re

try:
    config = load_config()
    nlp = spacy.load(config['pipeline'].get('spacy_model', 'en_core_web_sm'))
except OSError:
    print("Downloading spacy model...")
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str) -> dict:
    doc = nlp(str(text))
    entities = {'ORG': [], 'GPE': [], 'MONEY': []}
    
    for ent in doc.ents:
        if ent.label_ in entities:
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
                
    return {k: ", ".join(v) for k, v in entities.items()}

def heuristic_category(text: str) -> str:
    text = text.lower()
    
    # order matters — more specific patterns first
    if any(w in text for w in ['acquire', 'acquisition', 'buyout', 'buys', 'takeover', 'purchased']):
        deal = "Acquisition"
    elif any(w in text for w in ['merger', 'merges', 'merged with', 'merge with']):
        deal = "Merger"
    elif any(w in text for w in ['joint venture', 'jv', 'co-invest', 'co-owned']):
        deal = "Joint Venture"
    elif any(w in text for w in ['divest', 'divestiture', 'sells off', 'sold off', 'spins off', 'spinoff', 'carve-out', 'carve out']):
        deal = "Divestiture"
    elif any(w in text for w in ['ipo', 'initial public offering', 'goes public', 'public listing', 'listed on']):
        deal = "IPO/Public Offering"
    elif any(w in text for w in ['partnership', 'partners with', 'alliance', 'strategic alliance', 'collaboration', 'collaborates']):
        deal = "Partnership/Alliance"
    elif any(w in text for w in ['licensing', 'license agreement', 'distribution agreement', 'franchise', 'franchising']):
        deal = "Licensing/Distribution"
    elif any(w in text for w in ['stake', 'investment', 'invests', 'funding', 'fundraise', 'series a', 'series b', 'series c', 'venture capital', 'private equity']):
        deal = "Investment/Stake"
    else:
        deal = "Other"
        
    return deal

def extract_metadata(df: pd.DataFrame) -> pd.DataFrame:
    print("Running spaCy entity extraction and heuristics...")
    df = df.copy()
    
    combined_texts = df['title'].fillna("") + ". " + df['content'].fillna("")
    
    extracted = combined_texts.apply(extract_entities)
    df['organizations'] = extracted.apply(lambda x: x['ORG'])
    df['locations'] = extracted.apply(lambda x: x['GPE'])
    df['monetary_values'] = extracted.apply(lambda x: x['MONEY'])
    
    df['predicted_deal_type'] = combined_texts.apply(heuristic_category)

    return df

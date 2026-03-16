import os
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
GEMINI_MODEL = "gemini-2.0-flash"

def prompt_gemini_newsletter(text_data: str) -> str:
    """Uses Gemini to draft a business-friendly newsletter from structured NLP pipeline outputs."""
    if not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not found. Mocking newsletter.")
        return "Newsletter drafted: API mocked."

    url = f"{GEMINI_URL.format(GEMINI_MODEL)}?key={GEMINI_API_KEY}"
    
    system_prompt = f"""
    You are an expert FMCG financial analyst. Compose a concise Executive Deal Intelligence Newsletter aimed at business executives. 
    You have been provided with highly confident, deduplicated news articles mapped with extracted ORG, GPE, and MONEY entities.
    
    CRITICAL:
    - Never mention "hashes", "json", "tru_sim", "passes_sieve", "embeddings", or the data processing pipeline.
    - Focus ENTIRELY on the business value, the companies involved, the money, and the strategic impact.
    
    Layout Requirement:
    - Include a brief 'Executive Summary' intro summarizing the total deals and predominant regions.
    - List the 'Top FMCG Deals' using this structure:
      ### [Company Name] - [Deal Type]
      - **Strategic Impact**: [1-2 sentences summarizing the actual business event and why it matters conceptually]
      - **Financials / Value**: [Any MONEY metrics provided, or 'Undisclosed']
      - **Key Locations**: [GPE entities]
      - **Source**: [source_domain]
      
    Input JSON Records:
    {text_data}
    """
    
    payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return "Failed to proxy Gemini API."

def generate_newsletter(df: pd.DataFrame, output_dir: str = "output"):
    """
    Takes the final filtered DataFrame, passes structured metrics to Gemini, 
    and saves the output to a clean business-friendly DOCX file.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = df.copy()
    
    # Export CSV Backup
    csv_path = os.path.join(output_dir, "advanced_nlp_clean_deals.csv")
    df.to_csv(csv_path, index=False)
    print(f"Cleaned NLP dataset exported to {csv_path}")

    # Format JSON payload dropping ALL technical/pipeline metadata before passing to Gemini
    cols_to_drop = ['content', 'content_hash', 'canonical_url', 'id', 'fetched_at', 'passes_sieve', 'tru_sim', 'language']
    context_df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')
        
    json_data = context_df.to_json(orient="records")
    
    print("Drafting advanced NLP newsletter via Gemini...")
    newsletter_content = prompt_gemini_newsletter(json_data)
    
    from docx import Document
    docx_path = os.path.join(output_dir, "FMCG_Executive_Newsletter.docx")
    doc = Document()
    doc.add_heading('FMCG Deal Intelligence Report', 0)
    doc.add_paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}")
    doc.add_paragraph(newsletter_content)
    doc.save(docx_path)
        
    print(f"Successfully compiled Business Newsletter to {docx_path}")

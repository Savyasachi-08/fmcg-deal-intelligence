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

def prompt_gemini_newsletter(text_data: str) -> dict:
    """Uses Gemini to draft a structured business newsletter (JSON) from NLP pipeline outputs."""
    if not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY not found. Mocking newsletter.")
        return {"executive_summary": "API mocked.", "deals": []}

    url = f"{GEMINI_URL.format(GEMINI_MODEL)}?key={GEMINI_API_KEY}"
    
    system_prompt = f"""
    You are an expert FMCG financial analyst. 
    You have been provided with a JSON array of highly confident news articles mapped with extracted ORG, GPE, and MONEY entities.
    
    CRITICAL INSTRUCTION:
    You MUST output a valid JSON object ONLY. No markdown, no conversational text.
    Your output must match this exact schema:
    {{
        "executive_summary": "A 2-3 sentence overview of the CURRENT FMCG deal landscape based on these articles.",
        "deals": [
            {{
                "company_name": "Primary company name",
                "deal_type": "Acquisition / Stake / Merger",
                "strategic_impact": "2-3 sentences explaining the business value and why a CEO should care about this.",
                "financials": "Extracted monetary value or 'Undisclosed'",
                "location": "Countries/Regions",
                "source": "domain name"
            }}
        ]
    }}
    
    RULES:
    1. Select ONLY the TOP 10 most globally significant or highest-value deals from the input JSON. 
    2. If there are fewer than 10 deals, include all of them.
    3. Do not include more than 10 items in the "deals" list.
    4. Focus ENTIRELY on business value and strategic impact. Do not mention the data pipeline.
    
    Input JSON Records:
    {text_data}
    """
    
    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        raw_text = data['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw_text)
    except Exception as e:
        print(f"Error calling Gemini or parsing JSON: {e}")
        return {"executive_summary": "Failed to proxy Gemini API.", "deals": []}

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
    newsletter_json = prompt_gemini_newsletter(json_data)
    
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    docx_path = os.path.join(output_dir, "FMCG_Executive_Newsletter.docx")
    doc = Document()
    
    # Title
    title = doc.add_heading('FMCG Deal Intelligence Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}\n")
    
    # Exec Summary
    doc.add_heading('Executive Summary', level=1)
    p = doc.add_paragraph(newsletter_json.get("executive_summary", "Summary unavailable."))
    
    deals = newsletter_json.get("deals", [])
    
    doc.add_heading(f'Top Deals This Period', level=1)
    
    for deal in deals:
        # Deal Header
        deal_title = f"{deal.get('company_name', 'Unknown Company')} - {deal.get('deal_type', 'Deal')}"
        doc.add_heading(deal_title, level=2)
        
        # Details without raw markdown
        doc.add_paragraph(f"Strategic Impact: {deal.get('strategic_impact', 'N/A')}")
        doc.add_paragraph(f"Financials / Value: {deal.get('financials', 'Undisclosed')}")
        doc.add_paragraph(f"Key Locations: {deal.get('location', 'Unknown')}")
        doc.add_paragraph(f"Source: {deal.get('source', 'Unknown')}")
        doc.add_paragraph() # Spacer between deals
        
    doc.save(docx_path)
    print(f"Successfully compiled Business Newsletter to {docx_path}")

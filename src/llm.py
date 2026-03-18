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
        "executive_summary": "A 2-3 sentence overview of the CURRENT FMCG deal landscape, synthesizing the grouped topics.",
        "deals": [
            {{
                "company_name": "Primary company name involved in this specific Topic/Event",
                "deal_type": "Acquisition / Stake / Merger / Government Program",
                "strategic_impact": "2-3 sentences explaining the overarching business value of this Topic/Event and why a CEO should care.",
                "financials": "Extracted monetary value or 'Undisclosed'",
                "location": "Countries/Regions",
                "source": "domain name",
                "news_link": "Exact URL link to the original article"
            }}
        ]
    }}
    
    RULES:
    1. You are receiving pre-clustered Topics representing distinct real-world events. 
    2. Select ONLY the TOP 10 most globally significant or highest-value Topics/Events. 
    3. If there are fewer than 10 Topics, include all of them.
    4. Focus ENTIRELY on business value and strategic impact. Do not mention "clusters", "topics", "algorithms", or the data pipeline.
    
    Input JSON Records (Clustered Topics):
    {text_data}
    """
    
    payload = {
        "contents": [{"parts": [{"text": system_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 8192,
            "temperature": 0.2
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        raw_text = data['candidates'][0]['content']['parts'][0]['text']
        
        # Strip markdown fences if Gemini wraps the JSON (happens with longer responses)
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```", 2)[-1]  # drop opening fence
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.rsplit("```", 1)[0]  # drop closing fence
        raw_text = raw_text.strip()
        
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as je:
            # Fallback: extract the outermost { ... } block via regex
            import re
            print(f"Raw Gemini response (first 500 chars): {raw_text[:500]}")
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            raise je

    except Exception as e:
        print(f"Error calling Gemini or parsing JSON: {e}")
        return {"executive_summary": "Failed to proxy Gemini API.", "deals": []}

def generate_newsletter(topics_json: list, df: pd.DataFrame, output_dir: str = "output"):
    """
    Takes the structured topics list from the semantic clustering phase, passes them to Gemini for impact analysis, 
    and iterates via Python to compile the output to a clean business-friendly DOCX file.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = df.copy()
    
    # Export CSV Backup of the newly filtered representative items
    csv_path = os.path.join(output_dir, "advanced_nlp_clustered_topics.csv")
    df.to_csv(csv_path, index=False)
    print(f"Clustered NLP dataset exported to {csv_path}")

    # Sanitize text fields to prevent JSON encoding issues in Gemini's response
    safe_topics = []
    for t in topics_json:
        safe_t = dict(t)
        safe_t['topic_title'] = safe_t.get('topic_title', '').replace('\n', ' ').replace('\r', '')
        rep = dict(safe_t.get('representative_article', {}))
        rep['title'] = rep.get('title', '').replace('\n', ' ').replace('\r', '')
        rep['summary'] = rep.get('summary', '').replace('\n', ' ').replace('\r', '').replace('"', "'")
        rep['link'] = rep.get('link', '')
        safe_t['representative_article'] = rep
        safe_topics.append(safe_t)
    
    print("Drafting advanced NLP newsletter via Gemini (Topic-Based)...")
    
    all_deals = []
    exec_summary = ""
    chunk_size = 10
    max_calls = 2
    
    for i in range(0, min(len(safe_topics), chunk_size * max_calls), chunk_size):
        chunk = safe_topics[i:i + chunk_size]
        json_data = json.dumps(chunk, ensure_ascii=True)
        print(f"  -> Sending batch of {len(chunk)} topics to Gemini...")
        
        chunk_json = prompt_gemini_newsletter(json_data)
        
        if not exec_summary:
            exec_summary = chunk_json.get("executive_summary", "")
            
        all_deals.extend(chunk_json.get("deals", []))
        
        # Stop early if we have reached our goal of 10 deals
        if len(all_deals) >= 10:
            break
            
    newsletter_json = {
        "executive_summary": exec_summary or "Summary unavailable.",
        "deals": all_deals[:10]
    }
    
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
    
    doc.add_heading('Top Deals This Period', level=1)
    
    for deal in deals:
        # Deal Header
        deal_title = f"{deal.get('company_name', 'Unknown Company')} - {deal.get('deal_type', 'Deal')}"
        doc.add_heading(deal_title, level=2)
        
        # Details with premium formatting
        def add_bold_line(label, value):
            p_line = doc.add_paragraph()
            run = p_line.add_run(f"{label}: ")
            run.bold = True
            p_line.add_run(str(value))

        add_bold_line("Strategic Impact", deal.get('strategic_impact', 'N/A'))
        add_bold_line("Financials / Value", deal.get('financials', 'Undisclosed'))
        add_bold_line("Key Locations", deal.get('location', 'Unknown'))
        add_bold_line("Source", deal.get('source', 'Unknown'))
        
        link = deal.get('news_link', '')
        if link:
            add_bold_line("Original Article", link)
            
        doc.add_paragraph() # Spacer between deals
        
    doc.save(docx_path)
    print(f"Successfully compiled Business Newsletter to {docx_path}")

import ssl
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import json
import os
import re
from datetime import datetime
from email.utils import parsedate_to_datetime

FMCG_URL = "https://news.google.com/rss/search?q=(FMCG%20OR%20%22consumer%20goods%22)%20(stake%20OR%20investment%20OR%20invests%20OR%20funding%20OR%20fundraise%20OR%20%22series%20A%22%20OR%20%22series%20B%22%20OR%20%22venture%20capital%22%20OR%20%22private%20equity%22%20OR%20merger%20OR%20acquisition)%20(site:reuters.com%20OR%20site:bloomberg.com%20OR%20site:ft.com%20OR%20site:economictimes.indiatimes.com%20OR%20site:business-standard.com%20OR%20site:techcrunch.com)%20when:1d&hl=en-IN&gl=IN&ceid=IN:en"

AUTO_URL = "https://news.google.com/rss/search?q=(automobile%20OR%20EV%20OR%20%22electric%20vehicle%22)%20(stake%20OR%20investment%20OR%20funding%20OR%20fundraise%20OR%20%22venture%20capital%22%20OR%20%22private%20equity%22%20OR%20merger%20OR%20acquisition)%20(site:reuters.com%20OR%20site:bloomberg.com%20OR%20site:ft.com%20OR%20site:economictimes.indiatimes.com%20OR%20site:business-standard.com%20OR%20site:techcrunch.com)%20when:1d&hl=en-IN&gl=IN&ceid=IN:en"

def strip_html(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def extract_domain(url_or_string):
    if not url_or_string:
        return "unknown"
    match = re.search(r'https?://(?:www\.)?([^/]+)', url_or_string)
    if match:
        return match.group(1).lower()
    return url_or_string.lower()

def fetch_and_parse(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    context = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=context) as response:
            xml_data = response.read()
    except urllib.error.URLError as e:
        print(f"Failed to fetch data: {e}")
        return []

    root = ET.fromstring(xml_data)
    articles = []
    now_iso = datetime.utcnow().isoformat()

    for item in root.findall('.//channel/item'):
        title = item.findtext('title') or ""
        link = item.findtext('link') or ""
        guid = item.findtext('guid') or link
        pubDate_str = item.findtext('pubDate') or ""
        description = item.findtext('description') or ""
        
        content = strip_html(description)
        if not content and title:
            content = title

        try:
            dt = parsedate_to_datetime(pubDate_str)
            pub_date = dt.isoformat()
        except Exception:
            pub_date = now_iso

        source_node = item.find('source')
        source_domain = "news.google.com"
        if source_node is not None:
            source_url = source_node.get('url')
            if source_url:
                source_domain = extract_domain(source_url)
            else:
                source_domain = extract_domain(source_node.text)

        articles.append({
            "id": guid,
            "fetched_at": now_iso,
            "published_at": pub_date,
            "source_domain": source_domain,
            "link": link,
            "title": title,
            "content": content,
            "language": "en"
        })

    return articles

def fetch_live_data(filepath: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    all_articles = []

    for url, topic in [(FMCG_URL, "FMCG"), (AUTO_URL, "Automobile")]:
        print(f"Fetching live data for {topic}...")
        articles = fetch_and_parse(url)
        all_articles.extend(articles)
        print(f"Fetched {len(articles)} {topic} articles.")

    with open(filepath, 'w', encoding='utf-8') as f:
        for article in all_articles:
            f.write(json.dumps(article) + "\n")

    print(f"Generated {len(all_articles)} live articles at {filepath}")

if __name__ == "__main__":
    fetch_live_data("../data/live_news.jsonl")

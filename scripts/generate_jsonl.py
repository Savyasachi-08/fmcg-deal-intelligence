import json
import os
from datetime import datetime, timedelta

def generate_jsonl(filepath: str):
    """Generates ~10 JSON lines of mixed news articles."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    now = datetime.utcnow()
    
    articles = [
        # 1. Valid FMCG
        {
            "id": "item1",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(days=1)).isoformat(),
            "source_domain": "reuters.com",
            "link": "https://reuters.com/business/nestle-health-science-deal",
            "title": "Nestle acquires specialized nutrition brand",
            "content": "Nestle has completed the acquisition of a leading health and nutrition startup for $300M, aiming to expand globally.",
            "language": "en"
        },
        # 2. Valid FMCG Near-Dup (older, lower credibility)
        {
            "id": "item2",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(days=2)).isoformat(),
            "source_domain": "business-standard.com",
            "link": "https://business-standard.com/nestle-buys",
            "title": "Nestle buys functional nutrition startup",
            "content": "Nestle wraps up buyout of a major health and nutrition company for a reported $300 Million to boost market footprint.",
            "language": "en"
        },
        # 3. Valid FMCG Exact Dup (same text)
        {
            "id": "item3",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(days=1)).isoformat(),
            "source_domain": "unknownblog.com",
            "link": "https://unknownblog.com/nestle-health-science-deal",
            "title": "Nestle acquires specialized nutrition brand",
            "content": "Nestle has completed the acquisition of a leading health and nutrition startup for $300M, aiming to expand globally.",
            "language": "en"
        },
        # 4. Valid FMCG
        {
            "id": "item4",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(days=3)).isoformat(),
            "source_domain": "bloomberg.com",
            "link": "https://bloomberg.com/unilever-green-packaging",
            "title": "Unilever invests in sustainable packaging startup",
            "content": "Unilever announced a $50M strategic investment in a green tech startup focusing on sustainable, biodegradable packaging for consumer goods.",
            "language": "en"
        },
        # 5. Non-FMCG
        {
            "id": "item5",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(days=4)).isoformat(),
            "source_domain": "techcrunch.com",
            "link": "https://techcrunch.com/stripe-fintech-round",
            "title": "Stripe raises massive new venture capital round",
            "content": "Fintech giant Stripe raised $600 million in a new Series I funding round led by top venture capital firms to expand international processing.",
            "language": "en"
        },
        # 6. Valid FMCG
        {
            "id": "item6",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(hours=5)).isoformat(),
            "source_domain": "economictimes.indiatimes.com",
            "link": "https://economictimes.indiatimes.com/itc-foods",
            "title": "ITC expands food division with new acquisition",
            "content": "ITC Limited announced the acquisition of a packaged foods startup based in Pune to significantly increase its market share in the ready-to-eat meals segment.",
            "language": "en"
        },
        # 7. Valid FMCG
        {
            "id": "item7",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(hours=2)).isoformat(),
            "source_domain": "ft.com",
            "link": "https://ft.com/loreal-ai-skincare",
            "title": "L'Oreal takes stake in beauty tech firm",
            "content": "L'Oreal acquired a substantial minority stake in a Parisian beauty tech firm that uses artificial intelligence for personalized skincare recommendations.",
            "language": "en"
        },
        # 8. Non-FMCG
        {
            "id": "item8",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(days=1)).isoformat(),
            "source_domain": "reuters.com",
            "link": "https://reuters.com/pfizer-oncology",
            "title": "Pfizer acquires oncology biotech company for $5B",
            "content": "Pfizer completed the acquisition of a clinical-stage oncology biotech company today, aiming to bolster its pipeline of targeted cancer therapies.",
            "language": "en"
        },
        # 9. Non English article (to test filtering)
        {
            "id": "item9",
            "fetched_at": now.isoformat(),
            "published_at": (now - timedelta(days=1)).isoformat(),
            "source_domain": "lemonde.fr",
            "link": "https://lemonde.fr/danone-restructuration",
            "title": "Danone vend ses marques d'eau",
            "content": "Danone annonce la vente de plusieurs marques d'eau régionales dans le cadre de sa restructuration.",
            "language": "fr"
        },
        # 10. Valid FMCG Near-Dup of item 7 (newer, lower credibility)
        {
            "id": "item10",
            "fetched_at": now.isoformat(),
            "published_at": now.isoformat(),
            "source_domain": "techcrunch.com",
            "link": "https://techcrunch.com/loreal-invests",
            "title": "L'Oreal invests in AI bespoke skincare firm",
            "content": "The global cosmetics giant L'Oreal has purchased shares in an AI-driven beauty technology firm focused on personalized skin analysis and routine recommendations.",
            "language": "en"
        }
    ]

    with open(filepath, 'w') as f:
        for article in articles:
            f.write(json.dumps(article) + "\n")
            
    print(f"Generated {len(articles)} articles at {filepath}")

if __name__ == "__main__":
    generate_jsonl("data/sample_news.jsonl")

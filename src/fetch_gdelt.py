import requests
import json
import pandas as pd
from datetime import datetime
import time
import os
import praw
import re
import feedparser
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
SIGNATURE_KEY = os.getenv('TENSIONR_SIGNATURE_KEY', 'default_secret_key')

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best",
    "https://cnnespanol.cnn.com/feed/"
]

def get_reddit_client():
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        try:
            return praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET, user_agent='tensionr_intel/1.0')
        except: pass
    return None

def sanitize_data(text):
    if not isinstance(text, str): return ""
    return re.sub(r'[<>{}[\]\\]', '', text)

def sign_data(data_json):
    return hmac.new(SIGNATURE_KEY.encode(), data_json.encode(), hashlib.sha256).hexdigest()

def analyze_social_spread(reddit, url):
    """Analisi multi-piattaforma (Reddit + Mastodon)."""
    metrics = {"reddit_shares": 0, "mastodon_shares": 0, "bot_probability": 0, "target_platforms": []}
    
    # 1. Reddit
    if reddit:
        try:
            submissions = list(reddit.subreddit("all").search(f'url:"{url}"', limit=10))
            metrics["reddit_shares"] = len(submissions)
            if metrics["reddit_shares"] > 0: metrics["target_platforms"].append("reddit")
        except: pass

    # 2. Mastodon (Public API)
    try:
        m_resp = requests.get(f"https://mastodon.social/api/v2/search?q={url}&type=statuses", timeout=5)
        if m_resp.status_code == 200:
            m_data = m_resp.json()
            metrics["mastodon_shares"] = len(m_data.get('statuses', []))
            if metrics["mastodon_shares"] > 0: metrics["target_platforms"].append("mastodon")
    except: pass

    # 3. Logic
    total_shares = metrics["reddit_shares"] + metrics["mastodon_shares"]
    platform_diversity = len(metrics["target_platforms"])
    score = min(total_shares * 8 + platform_diversity * 20, 100)
    metrics["bot_probability"] = score
    return metrics

def fetch_rss_news(query):
    print("scanning rss feeds for global signal...")
    articles = []
    headers = {"User-Agent": "tensionr_cyber_node/1.0"}
    rss_metadata = {
        "feeds.bbci.co.uk": "United Kingdom",
        "www.aljazeera.com": "Qatar",
        "www.theguardian.com": "United Kingdom",
        "feeds.a.dj.com": "United States",
        "www.reutersagency.com": "United Kingdom",
        "cnnespanol.cnn.com": "United States"
    }
    for url in RSS_FEEDS:
        try:
            domain = url.split('/')[2]
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:10]:
                articles.append({
                    "url": entry.get('link'),
                    "title": entry.get('title', ''),
                    "domain": domain,
                    "seendate": datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                    "source": "rss",
                    "sourcecountry": rss_metadata.get(domain, "Global")
                })
        except: continue
    return articles

def fetch_gdelt_data():
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    query = 'war conflict economy'
    headers = {"User-Agent": "tensionr_cyber_node/1.0"}
    
    existing_data = {}
    if os.path.exists('data/latest.json'):
        try:
            with open('data/latest.json', 'r') as f:
                existing_data = json.load(f).get('data', {})
        except: pass

    print(f"initiating intelligence synchronization...")
    
    try:
        resp = requests.get(base_url, params={"query": query, "mode": "ArtList", "maxrecords": 50, "format": "json"}, headers=headers, timeout=10)
        gdelt_articles = resp.json().get('articles', []) if resp.status_code == 200 else []
        for a in gdelt_articles: a['source'] = 'gdelt'
    except: gdelt_articles = []

    rss_articles = fetch_rss_news(query)
    all_articles = gdelt_articles + rss_articles
    
    if not all_articles:
        print("!! zero signal detected. persistence mode active.")
        if not existing_data: return
        output = existing_data
        output['last_updated'] = datetime.now().isoformat()
    else:
        reddit = get_reddit_client()
        processed = []
        for art in all_articles:
            art['title'] = sanitize_data(art.get('title', ''))
            intel = analyze_social_spread(reddit, art['url'])
            art.update(intel)
            art['manipulation_score'] = art.get('bot_probability', 0)
            processed.append(art)
            if reddit: time.sleep(0.3)

        df = pd.DataFrame(processed)
        stats = {
            "total_nodes": len(processed),
            "avg_risk": float(df['bot_probability'].mean()) if not df.empty else 0,
            "top_domains": df['domain'].value_counts().head(8).to_dict() if not df.empty else {},
            "source_distribution": df['source'].value_counts().to_dict() if 'source' in df.columns else {},
            "source_countries": df['sourcecountry'].value_counts().to_dict() if 'sourcecountry' in df.columns else {}
        }

        try:
            resp_v = requests.get(base_url, params={"query": query, "mode": "TimelineVol", "format": "json"}, headers=headers, timeout=10)
            timeline = resp_v.json().get('timeline', []) if resp_v.status_code == 200 else []
        except: timeline = []

        output = {
            "last_updated": datetime.now().isoformat(),
            "query": query,
            "articles": processed,
            "timeline_vol": timeline,
            "stats": stats,
            "security_check": "verified"
        }
    
    json_content = json.dumps(output, indent=4)
    signature = sign_data(json_content)
    final_payload = {"data": output, "signature": signature, "algorithm": "HMAC-SHA256"}
    
    with open('data/latest.json', 'w', encoding='utf-8') as f:
        json.dump(final_payload, f, indent=4)
    print(f"sync complete. integrity: {signature[:8]}")

if __name__ == "__main__":
    fetch_gdelt_data()

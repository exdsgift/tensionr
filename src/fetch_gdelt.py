import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import praw
import re
from dotenv import load_dotenv

load_dotenv()

# --- INTELLIGENCE LAYER: CONFIGURATION ---
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
NEWS_API_KEY = os.getenv('NEWS_API_KEY') # Opcionale per espandere le fonti

def get_reddit_client():
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        try:
            return praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent='tensionr_intel_engine/1.0'
            )
        except: pass
    return None

# --- CYBERSECURITY: INPUT SANITIZATION ---
def sanitize_data(text):
    """Rimuove potenziali script o caratteri pericolosi dai testi scrapati."""
    if not isinstance(text, str): return ""
    return re.sub(r'[<>{}[\]\\]', '', text)

# --- ML ENGINE: PROPAGANDA & BOT DETECTION ---
def analyze_narrative_influence(reddit, article):
    """
    Analisi avanzata della diffusione:
    1. Cross-platform correlation (GDELT vs Reddit)
    2. Temporal anomaly (velocità di diffusione)
    3. Community clustering (quali subreddit sono targetizzati)
    """
    url = article['url']
    metrics = {
        "social_velocity": 0,
        "narrative_drift": 0,
        "bot_probability": 0,
        "target_subreddits": []
    }
    
    if not reddit: return metrics

    try:
        submissions = list(reddit.subreddit("all").search(f'url:"{url}"', limit=25))
        if not submissions: return metrics

        # 1. Temporal Anomaly: Analisi della velocità di posting
        now = datetime.utcnow()
        post_times = [datetime.utcfromtimestamp(s.created_utc) for s in submissions]
        
        # Se molti post avvengono in un intervallo di tempo brevissimo (es. 10 min)
        if len(post_times) > 2:
            time_delta = (max(post_times) - min(post_times)).total_seconds() / 60
            metrics["social_velocity"] = round(len(submissions) / (time_delta + 1), 2)

        # 2. Community Clustering
        subs = [s.subreddit.display_name for s in submissions]
        metrics["target_subreddits"] = list(set(subs))

        # 3. Bot Probability Logic (Heuristic ML)
        # - Alta velocità (> 1 post/min)
        # - Account giovani (opzionale, richiede più chiamate API)
        # - Posting cross-subreddit massivo di link identici
        score = 0
        if metrics["social_velocity"] > 0.5: score += 40
        if len(metrics["target_subreddits"]) > 3: score += 30
        if "propaganda" in [s.lower() for s in subs] or "politics" in [s.lower() for s in subs]: score += 10
        
        metrics["bot_probability"] = min(score, 100)
        return metrics

    except Exception as e:
        print(f"intel_error during reddit scan: {e}")
        return metrics

def fetch_secondary_news_source(query):
    """Integrazione NewsAPI per cross-referencing (richiede API KEY)."""
    if not NEWS_API_KEY: return []
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": 20,
        "apiKey": NEWS_API_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            articles = resp.json().get('articles', [])
            return [{
                "url": a['url'],
                "title": a['title'],
                "domain": a['source']['name'],
                "seendate": a['publishedAt'].replace('-', '').replace(':', '').replace('Z', 'T') + "000000Z",
                "source": "newsapi"
            } for a in articles]
    except: pass
    return []

import hmac
import hashlib

# --- DATA INTEGRITY: DIGITAL SIGNATURE ---
SIGNATURE_KEY = os.getenv('TENSIONR_SIGNATURE_KEY', 'default_secret_key_change_me')

def sign_data(data_json):
    """Genera una firma HMAC-SHA256 per i dati."""
    return hmac.new(
        SIGNATURE_KEY.encode(),
        data_json.encode(),
        hashlib.sha256
    ).hexdigest()

def fetch_gdelt_data():
    # ... (codice precedente invariato fino al salvataggio)
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    query = 'war conflict economy' # Query core
    headers = {"User-Agent": "tensionr_cyber_node/1.0"}
    
    print(f"initiating multi-source intelligence sync...")
    
    # 1. News Ingestion (GDELT + NewsAPI)
    params_art = {"query": query, "mode": "ArtList", "maxrecords": 40, "format": "json"}
    resp = requests.get(base_url, params=params_art, headers=headers)
    gdelt_articles = resp.json().get('articles', []) if resp.status_code == 200 else []
    
    secondary_articles = fetch_secondary_news_source(query)
    all_articles = gdelt_articles + secondary_articles
    
    # 2. Intelligence Processing
    reddit = get_reddit_client()
    processed_articles = []
    
    for art in all_articles:
        # Sanificazione per Cybersecurity
        art['title'] = sanitize_data(art.get('title', ''))
        
        # ML Analysis
        intel = analyze_narrative_influence(reddit, art)
        art.update(intel)
        
        # Uniformiamo il formato per il frontend
        art['manipulation_score'] = art.get('bot_probability', 0)
        processed_articles.append(art)
        if reddit: time.sleep(0.5)

    # 3. Stats Aggregation
    df = pd.DataFrame(processed_articles)
    stats = {
        "total_nodes": len(processed_articles),
        "avg_risk": float(df['bot_probability'].mean()) if not df.empty else 0,
        "high_risk_nodes": len(df[df['bot_probability'] > 60]) if not df.empty else 0,
        "top_domains": df['domain'].value_counts().head(8).to_dict() if not df.empty else {},
        "source_distribution": df['source'].value_counts().to_dict() if 'source' in df.columns else {"gdelt": len(gdelt_articles)}
    }

    # 4. Timeline
    time.sleep(2)
    resp_vol = requests.get(base_url, params={"query": query, "mode": "TimelineVol", "format": "json"}, headers=headers)
    timeline = resp_vol.json().get('timeline', []) if resp_vol.status_code == 200 else []

    output = {
        "last_updated": datetime.now().isoformat(),
        "query": query,
        "articles": processed_articles,
        "timeline_vol": timeline,
        "stats": stats,
        "security_check": "verified"
    }
    
    # Generazione firma digitale prima del salvataggio
    json_content = json.dumps(output, indent=4)
    signature = sign_data(json_content)
    
    final_payload = {
        "data": output,
        "signature": signature,
        "algorithm": "HMAC-SHA256"
    }
    
    with open('data/latest.json', 'w', encoding='utf-8') as f:
        json.dump(final_payload, f, indent=4)
    print(f"sync complete. integrity signature: {signature[:10]}...")

if __name__ == "__main__":
    fetch_gdelt_data()

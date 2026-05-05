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
from collections import Counter
import spacy
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

hf_error_printed = False

try:
    nlp = spacy.load("xx_ent_wiki_sm")
except OSError:
    print("Downloading multilingual spaCy model...")
    subprocess.run(
        [sys.executable, "-m", "spacy", "download", "xx_ent_wiki_sm"], check=True
    )
    nlp = spacy.load("xx_ent_wiki_sm")

# --- CONFIGURATION ---
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
SIGNATURE_KEY = os.getenv("TENSIONR_SIGNATURE_KEY", "default_secret_key")
HF_TOKEN = os.getenv("HF_TOKEN")

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.net/aljazeerarss/a7c986be-c2bd-44a7-82f1-104a5e6bb854/73d0e1b4-532f-45ef-b135-bfdff8b8cab9",
    "https://www.theguardian.com/world/rss",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://www.lemonde.fr/international/rss_full.xml",
    "https://www.japantimes.co.jp/feed/",
    "https://www.spiegel.de/ausland/index.rss",
    "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
    "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",
    "https://www.straitstimes.com/news/world/rss.xml",
    "https://en.mercopress.com/rss/",
    "https://www.chinadaily.com.cn/rss/world_rss.xml",
]


def get_reddit_client():
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        try:
            return praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent="tensionr_intel/1.0",
            )
        except:
            pass
    return None


def sanitize_data(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"[<>{}[\]\\]", "", text)


def sign_data(data_json):
    return hmac.new(
        SIGNATURE_KEY.encode(), data_json.encode(), hashlib.sha256
    ).hexdigest()


def analyze_social_spread(reddit, url):
    metrics = {
        "reddit_shares": 0,
        "mastodon_shares": 0,
        "bot_probability": 0,
        "target_platforms": [],
    }
    if reddit:
        try:
            submissions = list(reddit.subreddit("all").search(f'url:"{url}"', limit=10))
            metrics["reddit_shares"] = len(submissions)
            if metrics["reddit_shares"] > 0:
                metrics["target_platforms"].append("reddit")
        except:
            pass
    try:
        m_resp = requests.get(
            f"https://mastodon.social/api/v2/search?q={url}&type=statuses", timeout=5
        )
        if m_resp.status_code == 200:
            m_data = m_resp.json()
            metrics["mastodon_shares"] = len(m_data.get("statuses", []))
            if metrics["mastodon_shares"] > 0:
                metrics["target_platforms"].append("mastodon")
    except:
        pass
    total_shares = metrics["reddit_shares"] + metrics["mastodon_shares"]
    score = min(total_shares * 8 + len(metrics["target_platforms"]) * 20, 100)
    metrics["bot_probability"] = score
    return metrics


def analyze_narrative_hf(text, retries=4):
    global hf_error_printed
    if not HF_TOKEN or not text:
        return {"emotion": "unknown", "bias_risk": 0}

    headers = {"Authorization": f"Bearer {HF_TOKEN.strip()}"}
    # Modello Base multilingua per Sentiment (leggero e sempre attivo sui server gratuiti)
    API_URL = "https://router.huggingface.co/hf-inference/models/cardiffnlp/twitter-xlm-roberta-base-sentiment"

    for attempt in range(retries):
        try:
            payload = {
                "inputs": text[:500],
                "options": {"wait_for_model": True},
            }
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                results = resp.json()
                if isinstance(results, list) and len(results) > 0:
                    predictions = (
                        results[0] if isinstance(results[0], list) else results
                    )
                    top_emotion = max(predictions, key=lambda x: x.get("score", 0))
                    label = top_emotion.get("label", "").lower()

                    # Traduciamo il sentiment nelle emozioni della nostra dashboard
                    if label in ["negative", "label_0", "fear", "anger", "sadness", "disgust", "annoyance", "disapproval", "nervousness", "grief"]:
                        return {"emotion": "fear", "bias_risk": 85}
                    elif label in ["positive", "label_2", "surprise", "joy", "love", "optimism", "amusement", "excitement", "admiration"]:
                        return {"emotion": "surprise", "bias_risk": 10}
                    else:
                        return {"emotion": "neutral", "bias_risk": 10}
            elif resp.status_code == 503:
                time.sleep(5)
                continue
            elif resp.status_code == 429:
                time.sleep(2)
                continue
            else:
                if not hf_error_printed:
                    print(f"\n    [!] HF API Error {resp.status_code}: {resp.text}")
                    hf_error_printed = True
                break
        except Exception as e:
            if not hf_error_printed:
                print(f"\n    [!] HF API Exception: {e}")
                hf_error_printed = True
            time.sleep(2)
    return {"emotion": "unknown", "bias_risk": 0}


def extract_keywords(articles):
    entities = []
    for art in articles:
        text = art.get("title", "")
        if text:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "ORG", "NORP", "PERSON", "LOC", "PER"]:
                    clean_ent = ent.text.strip().lower()
                    if len(clean_ent) > 2:
                        entities.append(clean_ent)
    return dict(Counter(entities).most_common(60))


def fetch_rss_news(query):
    print(f"scanning {len(RSS_FEEDS)} rss feeds...")
    articles = []
    headers = {"User-Agent": "tensionr_cyber_node/1.0"}
    rss_metadata = {
        "feeds.bbci.co.uk": {"country": "United Kingdom", "lang": "English"},
        "www.aljazeera.net": {"country": "Qatar", "lang": "Arabic"},
        "www.theguardian.com": {"country": "United Kingdom", "lang": "English"},
        "feeds.a.dj.com": {"country": "United States", "lang": "English"},
        "www.lemonde.fr": {"country": "France", "lang": "French"},
        "www.japantimes.co.jp": {"country": "Japan", "lang": "Japanese"},
        "www.spiegel.de": {"country": "Germany", "lang": "German"},
        "feeds.elpais.com": {"country": "Spain", "lang": "Spanish"},
        "timesofindia.indiatimes.com": {"country": "India", "lang": "Hindi"},
        "www.jpost.com": {"country": "Israel", "lang": "Hebrew"},
        "www.straitstimes.com": {"country": "Singapore", "lang": "Malay"},
        "en.mercopress.com": {"country": "Uruguay", "lang": "Spanish"},
        "www.chinadaily.com.cn": {"country": "China", "lang": "English"},
    }
    for url in RSS_FEEDS:
        domain = url.split("/")[2]
        print(f"  -> Fetching {domain}...")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"  !! Warning: {domain} returned status {resp.status_code}")
                continue
            feed = feedparser.parse(resp.text)
            meta = rss_metadata.get(domain, {"country": "Global", "lang": "English"})
            for entry in feed.entries[:15]:
                articles.append(
                    {
                        "url": entry.get("link"),
                        "title": entry.get("title", ""),
                        "domain": domain,
                        "seendate": datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                        "source": "rss",
                        "sourcecountry": meta["country"],
                        "language": meta["lang"],
                    }
                )
        except Exception as e:
            print(f"  !! Failed to fetch {domain}: {e}")
            continue
    return articles


def fetch_gdelt_data():
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    timeline_query = "war conflict economy"
    query = "war conflict economy military finance"
    headers = {"User-Agent": "tensionr_cyber_node/1.0"}

    existing_data = {}
    existing_articles = []
    if os.path.exists("data/latest.json"):
        try:
            with open("data/latest.json", "r") as f:
                full_payload = json.load(f)
                existing_data = full_payload.get("data", {})
                existing_articles = existing_data.get("articles", [])
        except Exception as e:
            print(f"!! error loading existing data: {e}")

    print(f"initiating synchronization...")

    try:
        resp = requests.get(
            base_url,
            params={
                "query": query,
                "mode": "ArtList",
                "maxrecords": 50,
                "format": "json",
            },
            headers=headers,
            timeout=10,
        )
        gdelt_articles = (
            resp.json().get("articles", []) if resp.status_code == 200 else []
        )
        for a in gdelt_articles:
            a["source"] = "gdelt"
    except:
        gdelt_articles = []

    rss_articles = fetch_rss_news(query)
    new_raw_articles = gdelt_articles + rss_articles

    if not new_raw_articles and not existing_articles:
        print("!! no signals found and no local cache.")
        return

    processed_new = []
    known_countries = [
        "United States", "United Kingdom", "Qatar", "France", "Russia", "Japan",
        "Australia", "India", "Israel", "Ukraine", "Singapore", "Canada",
        "Saudi Arabia", "Uruguay", "Iran", "China", "Germany", "Turkey",
        "Egypt", "United Arab Emirates", "South Korea", "North Korea", "Taiwan",
        "Pakistan", "Syria", "Lebanon", "Yemen", "Iraq", "Afghanistan", "Mexico",
        "Brazil", "Venezuela", "Colombia", "South Africa", "Nigeria", "Kenya",
        "Somalia", "Sudan", "Ethiopia", "Poland", "Italy", "Spain", "Palestine",
    ]

    # Create a set of existing URLs for fast deduplication
    existing_urls = {a["url"] for a in existing_articles}
    
    # Filter only truly new articles to avoid redundant NLP processing
    unique_new_raw = [a for a in new_raw_articles if a["url"] not in existing_urls]

    if unique_new_raw:
        print(f"\n[!] processing {len(unique_new_raw)} new signals...")
        if not HF_TOKEN:
            print("  !! WARNING: HF_TOKEN not found. ML analysis disabled.")

        for i, art in enumerate(unique_new_raw):
            art["title"] = sanitize_data(art.get("title", ""))
            
            # Deduce country
            if "sourcecountry" not in art:
                art["sourcecountry"] = "Unknown"
                title_lower = art["title"].lower()
                for country in known_countries:
                    if country.lower() in title_lower:
                        art["sourcecountry"] = country
                        break

            # NLP Analysis (Sentiment/Bias)
            nlp_intel = analyze_narrative_hf(art["title"])
            art["narrative_emotion"] = nlp_intel["emotion"]
            
            # Manipulation score now only based on bias risk (bot logic removed)
            art["manipulation_score"] = int(nlp_intel["bias_risk"])
            
            # Initialize share metrics as 0 since we removed Reddit/Mastodon for now
            art["reddit_shares"] = 0
            art["mastodon_shares"] = 0
            art["bot_probability"] = 0
            art["target_platforms"] = []

            processed_new.append(art)
            if HF_TOKEN:
                time.sleep(0.5)

    # Merge and limit to 500 articles (Memory management)
    all_articles = processed_new + existing_articles
    
    # Sort by date (newest first) - assuming seendate is present
    all_articles.sort(key=lambda x: x.get("seendate", ""), reverse=True)
    
    # Final deduplication just in case
    final_articles = []
    seen_final = set()
    for a in all_articles:
        if a["url"] not in seen_final:
            final_articles.append(a)
            seen_final.add(a["url"])
    
    # Keep only 500 articles
    final_articles = final_articles[:500]

    df = pd.DataFrame(final_articles)
    stats = {
        "total_nodes": len(final_articles),
        "top_domains": df["domain"].value_counts().head(8).to_dict() if not df.empty else {},
        "source_countries": df["sourcecountry"].value_counts().to_dict() if not df.empty else {},
        "top_keywords": extract_keywords(final_articles),
    }

    try:
        resp_v = requests.get(
            base_url,
            params={
                "query": timeline_query,
                "mode": "TimelineVol",
                "format": "json",
            },
            headers=headers,
            timeout=10,
        )
        timeline = (
            resp_v.json().get("timeline", []) if resp_v.status_code == 200 else []
        )
    except:
        timeline = []

    output = {
        "last_updated": datetime.now().isoformat(),
        "query": query,
        "articles": final_articles,
        "timeline_vol": timeline,
        "stats": stats,
        "security_check": "verified",
    }

    json_content = json.dumps(output, indent=4)
    signature = sign_data(json_content)
    final_payload = {"data": output, "signature": signature, "algorithm": "HMAC-SHA256"}

    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=4)
    print(f"sync complete. integrity: {signature[:8]}")


if __name__ == "__main__":
    fetch_gdelt_data()

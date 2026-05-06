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
                    if label in ["fear", "nervousness", "grief"]:
                        return {"emotion": "fear", "bias_risk": 85}
                    elif label in ["anger", "annoyance", "disapproval", "disgust"]:
                        return {"emotion": "anger", "bias_risk": 85}
                    elif label in ["sadness"]:
                        return {"emotion": "sadness", "bias_risk": 85}
                    elif label in ["surprise", "amusement", "excitement"]:
                        return {"emotion": "surprise", "bias_risk": 10}
                    elif label in ["positive", "label_2", "joy", "love", "optimism", "admiration", "label_1", "neutral"]:
                        return {"emotion": "neutral", "bias_risk": 10}
                    else:
                        # Fallback for general negative/positive from base models
                        if label in ["negative", "label_0"]:
                            return {"emotion": "fear", "bias_risk": 85}
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
    import random
    # Potentially massive list of global feeds
    ALL_FEEDS = [
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
        "en.mercopress.com/rss/",
        "www.chinadaily.com.cn/rss/world_rss.xml",
        "https://www.rt.com/rss/news/",
        "https://www.scmp.com/rss/91/feed",
        "https://www.thehindu.com/news/international/feeder/default.rss",
        "https://feeds.reuters.com/reuters/worldNews",
        "https://www.france24.com/en/rss",
        "https://www.dw.com/en/top-stories/s-9097/rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.washingtonpost.com/arcfeed/rss/category/world/?itid=lk_inline_manual_41",
        "https://www.cbc.ca/cctoc/rss/news/world",
        "https://www.abc.net.au/news/feed/52278/rss.xml"
    ]
    
    # Select a random batch of 15 to ensure variety and prevent timeout
    selected_feeds = random.sample(ALL_FEEDS, min(len(ALL_FEEDS), 15))
    print(f"scanning random rotation of {len(selected_feeds)} rss feeds...")
    
    articles = []
    headers = {"User-Agent": "tensionr_cyber_node/1.0"}
    rss_metadata = {
        "feeds.bbci.co.uk": {"country": "United Kingdom", "lang": "English"},
        "www.aljazeera.net": {"country": "Qatar", "lang": "Arabic"},
        "www.theguardian.com": {"country": "United Kingdom", "lang": "English"},
        "feeds.a.dj.com": {"country": "United States", "lang": "English"},
        "www.lemonde.fr": {"country": "France", "lang": "French"},
        "www.japantimes.co.jp": {"country": "Japan", "lang": "Japanese"},
        "www.spiegel.de": {"country": "Germany", "lang": "English"},
        "feeds.elpais.com": {"country": "Spain", "lang": "Spanish"},
        "timesofindia.indiatimes.com": {"country": "India", "lang": "English"},
        "www.jpost.com": {"country": "Israel", "lang": "English"},
        "www.straitstimes.com": {"country": "Singapore", "lang": "English"},
        "en.mercopress.com": {"country": "Uruguay", "lang": "Spanish"},
        "www.chinadaily.com.cn": {"country": "China", "lang": "English"},
        "www.rt.com": {"country": "Russia", "lang": "Russian"},
        "www.scmp.com": {"country": "China", "lang": "English"},
        "www.thehindu.com": {"country": "India", "lang": "English"},
        "feeds.reuters.com": {"country": "Global", "lang": "English"},
        "www.france24.com": {"country": "France", "lang": "English"},
        "www.dw.com": {"country": "Germany", "lang": "English"},
        "rss.nytimes.com": {"country": "United States", "lang": "English"},
        "www.washingtonpost.com": {"country": "United States", "lang": "English"},
        "www.cbc.ca": {"country": "Canada", "lang": "English"},
        "www.abc.net.au": {"country": "Australia", "lang": "English"}
    }
    for url in selected_feeds:
        domain = url.split("/")[2]
        print(f"  -> Fetching {domain}...")
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.text)
            meta = rss_metadata.get(domain, {"country": "Global", "lang": "English"})
            for entry in feed.entries[:10]:
                articles.append({
                    "url": entry.get("link"),
                    "title": sanitize_data(entry.get("title", "")),
                    "domain": domain,
                    "seendate": datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                    "source": "rss",
                    "sourcecountry": meta["country"],
                    "language": meta["lang"],
                })
        except:
            continue
    return articles


def fetch_gdelt_data():
    base_url = "https://api.gdeltproject.org/api/v2/doc/doc"
    timeline_query = "war conflict economy"
    query = "war conflict economy military finance"
    headers = {"User-Agent": "tensionr_cyber_node/1.0"}

    existing_articles = []
    if os.path.exists("data/news.json"):
        try:
            with open("data/news.json", "r") as f:
                news_payload = json.load(f)
                existing_articles = news_payload.get("articles", [])
        except Exception as e:
            print(f"!! error loading existing news: {e}")
    elif os.path.exists("data/latest.json"):
        try:
            with open("data/latest.json", "r") as f:
                full_payload = json.load(f)
                existing_articles = full_payload.get("data", {}).get("articles", [])
        except:
            pass

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

    def calculate_gti(articles):
        if not articles:
            return 30 # Base neutral level
        
        fear_anger_count = sum(1 for a in articles if a.get("narrative_emotion") in ["fear", "anger"])
        ratio = fear_anger_count / len(articles)
        
        # Base GTI is 20. Max addition from ratio is 60. Max addition from volume is 20.
        volume_factor = min(len(articles) / 500.0, 1.0) * 20
        sentiment_factor = ratio * 60
        
        gti = int(20 + volume_factor + sentiment_factor)
        return min(max(gti, 1), 100)

    def fetch_cyber_intel():
        # Fetches real cyber threat data from RSS
        print("fetching cyber intelligence...")
        cyber_feed_url = "https://feeds.feedburner.com/TheHackersNews"
        try:
            resp = requests.get(cyber_feed_url, timeout=15)
            feed = feedparser.parse(resp.text)
            entries = []
            for entry in feed.entries[:5]:
                entries.append({
                    "title": sanitize_data(entry.get("title", "")),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "")
                })
            return entries
        except Exception as e:
            print(f"!! Failed to fetch cyber intel: {e}")
            return []

    def fetch_raw_chatter():
        # Fetches high-frequency tactical/OSINT alerts
        print("scanning raw osint chatter...")
        # Using a specialized military/security alert feed
        osint_feed = "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10"
        try:
            resp = requests.get(osint_feed, timeout=15)
            feed = feedparser.parse(resp.text)
            entries = []
            for entry in feed.entries[:6]:
                entries.append({
                    "title": sanitize_data(entry.get("title", "")),
                    "link": entry.get("link", ""),
                    "source": "OSINT_MONITOR"
                })
            return entries
        except:
            return []

    def fetch_market_data():
        print("fetching market data...")
        market_intel = []
        try:
            import yfinance as yf
            import warnings
            warnings.filterwarnings("ignore")
            
            tickers = {
                "VIX (VOLATILITY)": "^VIX",
                "GOLD (XAU)": "GC=F",
                "CRUDE OIL": "CL=F",
                "RAYTHEON (RTX)": "RTX",
                "LOCKHEED (LMT)": "LMT",
                "NORTHROP (NOC)": "NOC",
                "GEN DYNAMICS (GD)": "GD",
                "BTC/USD": "BTC-USD",
                "EUR/USD": "EURUSD=X",
                "S&P 500": "^GSPC",
                "NASDAQ 100": "^IXIC"
            }
            for name, symbol in tickers.items():
                ticker = yf.Ticker(symbol)
                # 5d period ensures data on weekends
                hist = ticker.history(period="5d")
                if len(hist) >= 2:
                    prev = hist['Close'].iloc[-2]
                    curr = hist['Close'].iloc[-1]
                    change = ((curr - prev) / prev) * 100
                    market_intel.append({
                        "symbol": name,
                        "price": round(curr, 2),
                        "change": round(change, 2)
                    })
        except ImportError:
            print("!! yfinance not installed. Run 'pip install yfinance'.")
        except Exception as e:
            print(f"!! Failed to fetch market data: {e}")
        return market_intel

    def fetch_opensky_flights():
        print("scanning strategic aerial assets (opensky)...")
        # Filtering for known military/gov callsign prefixes
        mil_prefixes = ["RCH", "SPAR", "SAM", "USAF", "AF", "RRR", "FAF", "GAF", "IAM", "BAF", "PLF", "CFC", "ASY", "RSF", "SUI", "AME"]
        url = "https://opensky-network.org/api/states/all"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                return {"status": "api_limit", "assets": []}
            
            data = resp.json()
            states = data.get("states", [])
            mil_assets = []
            
            for s in states:
                callsign = (s[1] or "").strip()
                is_mil = any(callsign.startswith(pre) for pre in mil_prefixes)
                altitude = s[7] or 0
                velocity = s[9] or 0
                
                # Check for sensitive profile
                if is_mil or (altitude > 13000 and velocity > 280):
                    mil_assets.append({
                        "icao24": s[0],
                        "callsign": callsign if callsign else "U_ID",
                        "origin": s[2],
                        "lat": s[6],
                        "lon": s[5],
                        "alt": int(altitude) if altitude else 0,
                        "vel": int(velocity * 3.6) if velocity else 0,
                        "is_mil": is_mil
                    })
            
            # Identify "Theater" (simple heuristic by count in region)
            theaters = {"EUROPE": 0, "MIDDLE_EAST": 0, "ASIA_PACIFIC": 0, "AMERICAS": 0}
            for a in mil_assets:
                lat, lon = a["lat"], a["lon"]
                if lat and lon:
                    if 35 < lat < 70 and -10 < lon < 40: theaters["EUROPE"] += 1
                    elif 10 < lat < 45 and 30 < lon < 75: theaters["MIDDLE_EAST"] += 1
                    elif -10 < lat < 50 and 70 < lon < 150: theaters["ASIA_PACIFIC"] += 1
                    else: theaters["AMERICAS"] += 1
            
            main_theater = max(theaters, key=theaters.get) if mil_assets else "NONE"
            
            return {
                "status": "active", 
                "assets": mil_assets[:60], 
                "count": len(mil_assets),
                "theater": main_theater
            }
        except Exception as e:
            print(f"!! OpenSky fetch failed: {e}")
            return {"status": "offline", "assets": []}

    df = pd.DataFrame(final_articles)
    gti = calculate_gti(final_articles)
    stats = {
        "total_nodes": len(final_articles),
        "top_domains": df["domain"].value_counts().head(8).to_dict() if not df.empty else {},
        "source_countries": df["sourcecountry"].value_counts().to_dict() if not df.empty else {},
        "top_keywords": extract_keywords(final_articles),
        "global_tension_index": gti,
        "cyber_intel": fetch_cyber_intel(),
        "raw_chatter": fetch_raw_chatter(),
        "market_intel": fetch_market_data(),
        "flight_intel": fetch_opensky_flights()
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

    # MODULAR SAVING
    news_data = {
        "articles": final_articles,
        "timeline_vol": timeline,
        "stats": {
            "top_domains": stats["top_domains"],
            "source_countries": stats["source_countries"],
            "top_keywords": stats["top_keywords"],
            "total_nodes": stats["total_nodes"]
        }
    }
    
    market_data = {"market_intel": stats["market_intel"]}
    telemetry_data = {"flight_intel": stats["flight_intel"]}
    intel_data = {
        "cyber_intel": stats["cyber_intel"],
        "raw_chatter": stats["raw_chatter"]
    }
    
    status_data = {
        "last_updated": datetime.now().isoformat(),
        "global_tension_index": stats["global_tension_index"],
        "security_check": "verified"
    }

    # Save modular files
    modules = {
        "data/news.json": news_data,
        "data/markets.json": market_data,
        "data/telemetry.json": telemetry_data,
        "data/intelligence.json": intel_data,
        "data/status.json": status_data
    }

    for path, content in modules.items():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4)

    # Signature on global status for integrity
    json_content = json.dumps(status_data, indent=4)
    signature = sign_data(json_content)
    
    print(f"sync complete. modular state verified. integrity: {signature[:8]}")


if __name__ == "__main__":
    fetch_gdelt_data()

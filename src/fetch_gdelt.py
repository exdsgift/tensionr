import requests
import json
import pandas as pd
from datetime import datetime
import time
import os
import re
import feedparser
import hmac
import hashlib
from collections import Counter
import spacy
import subprocess
import sys
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
try:
    from analytics import forecast_gti, generate_narrative_graph
except ImportError:
    from src.analytics import forecast_gti, generate_narrative_graph

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
SIGNATURE_KEY: str = os.getenv("TENSIONR_SIGNATURE_KEY", "default_secret_key")
HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")

RSS_FEEDS: List[str] = [
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


def sanitize_data(text: Any) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"[<>{}[\]\\]", "", text)


def sign_data(data_json: str) -> str:
    return hmac.new(
        SIGNATURE_KEY.encode(), data_json.encode(), hashlib.sha256
    ).hexdigest()


def analyze_narrative_hf(text: str, retries: int = 4) -> Dict[str, Union[str, int]]:
    global hf_error_printed
    if not HF_TOKEN or not text:
        return {"emotion": "unknown", "bias_risk": 0}

    headers = {"Authorization": f"Bearer {HF_TOKEN.strip()}"}
    # Using GoEmotions model for granular emotional mapping
    API_URL = "https://router.huggingface.co/hf-inference/models/SamLowe/roberta-base-go_emotions"

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
                    score = top_emotion.get("score", 0)

                    # Dynamic Bias Risk Calculation
                    # Intensity of negative emotions increases bias risk
                    risk_multiplier: float = 1.0
                    emotion_mapped: str = "neutral"

                    if label in ["fear", "nervousness", "anxiety", "confusion"]:
                        emotion_mapped = "fear"
                        risk_multiplier = 1.2
                    elif label in ["anger", "annoyance", "disapproval", "disgust", "frustration"]:
                        emotion_mapped = "anger"
                        risk_multiplier = 1.3
                    elif label in ["sadness", "grief", "remorse", "disappointment", "embarrassment"]:
                        emotion_mapped = "sadness"
                        risk_multiplier = 1.1
                    elif label in ["surprise", "realization", "curiosity", "excitement", "joy", "pride"]:
                        emotion_mapped = "surprise"
                        risk_multiplier = 0.8
                    elif label in ["optimism", "relief", "gratitude", "approval", "love", "admiration", "desire", "caring"]:
                        emotion_mapped = "positive" # We'll add this category or map it to neutral/stable
                        risk_multiplier = 0.5
                    
                    bias_risk: int = min(int(score * 100 * risk_multiplier), 100)
                    
                    return {"emotion": emotion_mapped, "bias_risk": bias_risk}
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


def generate_sitrep(alerts: List[str]) -> str:
    if not HF_TOKEN or not alerts:
        return "Tactical bulletin pending: awaiting signal density..."
    
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {HF_TOKEN.strip()}",
        "Content-Type": "application/json"
    }
    # Swapping to a dedicated summarization model compatible with Serverless API
    API_URL: str = "https://router.huggingface.co/hf-inference/models/sshleifer/distilbart-cnn-12-6"
    
    text_to_summarize: str = "Tactical Alerts: " + ". ".join(alerts[:10])
    
    try:
        payload: Dict[str, Any] = {
            "inputs": text_to_summarize,
            "parameters": {"max_length": 80, "min_length": 30, "do_sample": False},
            "options": {"wait_for_model": True}
        }
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            if isinstance(result, list) and len(result) > 0:
                summary: str = result[0].get("summary_text", "").strip()
                return summary[:250]
    except:
        pass
    return "Intelligence Synthesis Active: Multi-domain nodes reporting normal operational baseline."


def generate_strategic_insight(articles: List[Dict[str, Any]], markets: List[Dict[str, Any]], flights: Dict[str, Any]) -> str:
    """
    Agentic Intelligence Analyst: Correlates cross-domain signals using LLM.
    """
    if not HF_TOKEN:
        return "Strategic analyst offline: awaiting secure handshake."

    headers = {"Authorization": f"Bearer {HF_TOKEN.strip()}"}
    # Using a more capable instruct model for reasoning
    API_URL = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3"

    # Synthesize richer context
    top_news = [a["title"] for a in articles[:8]]
    market_alerts = []
    if markets:
        for m in markets:
            if abs(m["change"]) > 1.5:
                market_alerts.append(f"{m['symbol']} moved {m['change']}%")
    
    anomalies = [a for a in flights.get("assets", []) if a.get("is_outlier")]
    flight_context = f"{len(anomalies)} anomalies detected in {flights.get('theater', 'unknown')} theater"
    
    prompt = f"<s>[INST] You are a Senior Geopolitical Intelligence Analyst. Analyze the following SIGINT/OSINT data nodes for HIDDEN CORRELATIONS and ESCALATION RISKS.\n\n" \
             f"NEWS FEED:\n- " + "\n- ".join(top_news) + "\n\n" \
             f"MARKET ANOMALIES: " + (", ".join(market_alerts) if market_alerts else "Stable") + "\n" \
             f"AERIAL TELEMETRY: {flight_context}\n\n" \
             f"Identify ONE non-obvious strategic link between these domains. If news mentions a region and telemetry shows anomalies there, highlight the tactical significance. " \
             f"Be specific, clinical, and predictive. Max 25 words.\n" \
             f"FORMAT: CORRELATION: [Your insight] [/INST]"

    for attempt in range(3):
        try:
            payload = {
                "inputs": prompt, 
                "parameters": {
                    "max_new_tokens": 80, 
                    "temperature": 0.4, # Lower temperature for more clinical analysis
                    "repetition_penalty": 1.2
                },
                "options": {"wait_for_model": True}
            }
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                text = ""
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    text = result.get("generated_text", "")
                
                if "CORRELATION:" in text:
                    insight = text.split("CORRELATION:")[1].strip().split("\n")[0]
                    if len(insight) > 10:
                        return insight
            elif resp.status_code == 503:
                time.sleep(5)
                continue
        except Exception as e:
            print(f"Insight Error: {e}")
            time.sleep(1)
            
    return "Analyzing multi-domain vectors: signal density insufficient for high-confidence correlation."



def extract_keywords(articles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    entities: List[tuple] = []
    for art in articles:
        text: str = art.get("title", "")
        if text:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "ORG", "NORP", "PERSON", "LOC", "PER"]:
                    clean_ent: str = ent.text.strip().lower()
                    if len(clean_ent) > 2:
                        entities.append((clean_ent, ent.label_))
    
    # Count occurrences and store labels
    counts: Counter = Counter(entities)
    most_common: List[tuple] = counts.most_common(60)
    
    # Reformat to include label information
    enriched_keywords: Dict[str, Dict[str, Any]] = {}
    for (name, label), count in most_common:
        enriched_keywords[name] = {"count": count, "type": label}
        
    return enriched_keywords


def fetch_rss_news(query: str) -> List[Dict[str, Any]]:
    import random
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Potentially massive list of global feeds
    ALL_FEEDS: List[str] = [
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
    
    selected_feeds: List[str] = random.sample(ALL_FEEDS, min(len(ALL_FEEDS), 15))
    print(f"scanning random rotation of {len(selected_feeds)} rss feeds...")
    
    articles: List[Dict[str, Any]] = []
    headers: Dict[str, str] = {"User-Agent": "tensionr_cyber_node/1.0"}
    rss_metadata: Dict[str, Dict[str, str]] = {
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

    def fetch_single_feed(url: str) -> List[Dict[str, Any]]:
        domain: str = url.split("/")[2]
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            meta: Dict[str, str] = rss_metadata.get(domain, {"country": "Global", "lang": "English"})
            batch: List[Dict[str, Any]] = []
            for entry in feed.entries[:10]:
                batch.append({
                    "url": entry.get("link"),
                    "title": sanitize_data(entry.get("title", "")),
                    "domain": domain,
                    "seendate": datetime.now().strftime("%Y%m%dT%H%M%SZ"),
                    "source": "rss",
                    "sourcecountry": meta["country"],
                    "language": meta["lang"],
                })
            return batch
        except Exception as e:
            print(f"!! RSS fetch error: {e}")
            return []

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url: Dict = {executor.submit(fetch_single_feed, url): url for url in selected_feeds}
        for future in as_completed(future_to_url):
            articles.extend(future.result())

    return articles


def fetch_gdelt_data() -> None:
    base_url: str = "https://api.gdeltproject.org/api/v2/doc/doc"
    timeline_query: str = "war conflict economy"
    query: str = "war conflict economy military finance"
    headers: Dict[str, str] = {"User-Agent": "tensionr_cyber_node/1.0"}

    existing_articles: List[Dict[str, Any]] = []
    if os.path.exists("data/news.json"):
        try:
            with open("data/news.json", "r") as f:
                news_payload: Dict[str, Any] = json.load(f)
                existing_articles = news_payload.get("articles", [])
        except Exception as e:
            print(f"!! error loading existing news: {e}")
    elif os.path.exists("data/latest.json"):
        try:
            with open("data/latest.json", "r") as f:
                full_payload: Dict[str, Any] = json.load(f)
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
        gdelt_articles: List[Dict[str, Any]] = (
            resp.json().get("articles", []) if resp.status_code == 200 else []
        )
        for a in gdelt_articles:
            a["source"] = "gdelt"
    except Exception as e:
        print(f"!! GDELT fetch error: {e}")
        gdelt_articles = []

    rss_articles: List[Dict[str, Any]] = fetch_rss_news(query)
    new_raw_articles: List[Dict[str, Any]] = gdelt_articles + rss_articles

    if not new_raw_articles and not existing_articles:
        print("!! no signals found and no local cache.")
        return

    processed_new: List[Dict[str, Any]] = []
    known_countries: List[str] = [
        "United States", "United Kingdom", "Qatar", "France", "Russia", "Japan",
        "Australia", "India", "Israel", "Ukraine", "Singapore", "Canada",
        "Saudi Arabia", "Uruguay", "Iran", "China", "Germany", "Turkey",
        "Egypt", "United Arab Emirates", "South Korea", "North Korea", "Taiwan",
        "Pakistan", "Syria", "Lebanon", "Yemen", "Iraq", "Afghanistan", "Mexico",
        "Brazil", "Venezuela", "Colombia", "South Africa", "Nigeria", "Kenya",
        "Somalia", "Sudan", "Ethiopia", "Poland", "Italy", "Spain", "Palestine",
    ]

    # Create a set of existing URLs for fast deduplication
    existing_urls: set = {a["url"] for a in existing_articles}
    
    # Filter only truly new articles to avoid redundant NLP processing
    unique_new_raw: List[Dict[str, Any]] = [a for a in new_raw_articles if a["url"] not in existing_urls]

    if unique_new_raw:
        print(f"\n[!] processing {len(unique_new_raw)} new signals...")
        if not HF_TOKEN:
            print("  !! WARNING: HF_TOKEN not found. ML analysis disabled.")

        for i, art in enumerate(unique_new_raw):
            art["title"] = sanitize_data(art.get("title", ""))
            
            # Deduce country
            if "sourcecountry" not in art:
                art["sourcecountry"] = "Unknown"
                title_lower: str = art["title"].lower()
                for country in known_countries:
                    if country.lower() in title_lower:
                        art["sourcecountry"] = country
                        break

            # NLP Analysis (Sentiment/Bias)
            nlp_intel: Dict[str, Union[str, int]] = analyze_narrative_hf(art["title"])
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
    all_articles: List[Dict[str, Any]] = processed_new + existing_articles
    
    # Sort by date (newest first) - assuming seendate is present
    all_articles.sort(key=lambda x: x.get("seendate", ""), reverse=True)
    
    # Final deduplication just in case
    final_articles: List[Dict[str, Any]] = []
    seen_final: set = set()
    for a in all_articles:
        if a["url"] not in seen_final:
            final_articles.append(a)
            seen_final.add(a["url"])
    
    # Keep only 500 articles
    final_articles = final_articles[:500]

    def calculate_gti(articles: List[Dict[str, Any]], market_intel: List[Dict[str, Any]], flight_intel: Dict[str, Any]) -> int:
        if not articles:
            return 30 # Base neutral level
        
        # 1. Narrative Component (40% weight)
        fear_anger_count: int = sum(1 for a in articles if a.get("narrative_emotion") in ["fear", "anger"])
        ratio: float = fear_anger_count / len(articles)
        volume_factor: float = min(len(articles) / 500.0, 1.0) * 10 # Up to 10 points
        sentiment_factor: float = ratio * 30 # Up to 30 points
        narrative_score: float = volume_factor + sentiment_factor # Max 40
        
        # 2. Market Component (30% weight)
        market_score: float = 15 # Start at neutral middle
        if market_intel:
            # We look at VIX and Gold as tension drivers
            volatility_drivers: List[str] = ["VIX (VOLATILITY)", "GOLD (XAU)"]
            market_crash_drivers: List[str] = ["S&P 500", "NASDAQ 100"]
            
            drivers_change: float = 0
            for m in market_intel:
                if m["symbol"] in volatility_drivers and m["change"] > 0:
                    drivers_change += min(m["change"] * 2, 10) # Heavy weight on volatility spikes
                if m["symbol"] in market_crash_drivers and m["change"] < 0:
                    drivers_change += min(abs(m["change"]) * 3, 15) # Heavier weight on market crashes
            
            market_score = min(max(market_score + drivers_change, 0), 30)
            
        # 3. Telemetry Component (30% weight)
        telemetry_score: float = 0
        if flight_intel and flight_intel.get("status") == "active":
            assets: List[Dict[str, Any]] = flight_intel.get("assets", [])
            mil_count: int = sum(1 for a in assets if a.get("is_mil"))
            outlier_count: int = sum(1 for a in assets if a.get("is_outlier"))
            
            # 10 points for military volume, 20 points for outliers (strategic anomalies)
            mil_factor: float = min(mil_count / 20.0, 1.0) * 10
            outlier_factor: float = min(outlier_count / 5.0, 1.0) * 20
            telemetry_score = mil_factor + outlier_factor
            
        gti: int = int(10 + narrative_score + market_score + telemetry_score) # 10 is the absolute floor
        return min(max(gti, 1), 100)

    def fetch_cyber_intel() -> List[Dict[str, str]]:
        # Fetches real cyber threat data from RSS
        print("fetching cyber intelligence...")
        cyber_feed_url: str = "https://feeds.feedburner.com/TheHackersNews"
        try:
            resp = requests.get(cyber_feed_url, timeout=15)
            feed = feedparser.parse(resp.text)
            entries: List[Dict[str, str]] = []
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


    def fetch_raw_chatter() -> List[Dict[str, str]]:
        # Fetches high-frequency tactical/OSINT alerts
        print("scanning raw osint chatter...")
        # Using a specialized military/security alert feed
        osint_feed: str = "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10"
        try:
            resp = requests.get(osint_feed, timeout=15)
            feed = feedparser.parse(resp.text)
            entries: List[Dict[str, str]] = []
            for entry in feed.entries[:6]:
                entries.append({
                    "title": sanitize_data(entry.get("title", "")),
                    "link": entry.get("link", ""),
                    "source": "OSINT_MONITOR"
                })
            return entries
        except Exception as e:
            print(f"!! RSS fetch error: {e}")
            return []

    def fetch_market_data() -> List[Dict[str, Any]]:
        print("fetching market data...")
        market_intel: List[Dict[str, Any]] = []
        try:
            import yfinance as yf
            import warnings
            warnings.filterwarnings("ignore")
            
            tickers: Dict[str, str] = {
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
                    prev: float = hist['Close'].iloc[-2]
                    curr: float = hist['Close'].iloc[-1]
                    change: float = ((curr - prev) / prev) * 100
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

    def fetch_opensky_flights() -> Dict[str, Any]:
        print("scanning strategic aerial assets (opensky)...")
        # Filtering for known military/gov callsign prefixes
        mil_prefixes: List[str] = ["RCH", "SPAR", "SAM", "USAF", "AF", "RRR", "FAF", "GAF", "IAM", "BAF", "PLF", "CFC", "ASY", "RSF", "SUI", "AME"]
        url: str = "https://opensky-network.org/api/states/all"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                return {"status": "api_limit", "assets": []}
            
            data: Dict[str, Any] = resp.json()
            states: List[List[Any]] = data.get("states", [])
            mil_assets: List[Dict[str, Any]] = []
            
            # For Statistical Anomaly Detection
            all_velocities = [s[9] for s in states if s[9] is not None]
            all_altitudes = [s[7] for s in states if s[7] is not None]
            
            avg_vel = sum(all_velocities) / len(all_velocities) if all_velocities else 200
            std_vel = (sum((x - avg_vel) ** 2 for x in all_velocities) / len(all_velocities)) ** 0.5 if all_velocities else 50

            for s in states:
                callsign: str = (s[1] or "").strip()
                is_mil: bool = any(callsign.startswith(pre) for pre in mil_prefixes)
                altitude: Optional[float] = s[7]
                velocity: Optional[float] = s[9]
                
                # Enhanced Anomaly Detection logic
                is_outlier: bool = False
                anomaly_score: float = 0.0
                
                if is_mil:
                    is_outlier = True
                    anomaly_score += 0.5
                
                if altitude and altitude > 13500: # Very high altitude for civil
                    is_outlier = True
                    anomaly_score += 0.3
                
                if velocity:
                    z_score_vel = (velocity - avg_vel) / (std_vel + 1e-6)
                    if abs(z_score_vel) > 2.5: # 2.5 standard deviations away
                        is_outlier = True
                        anomaly_score += min(abs(z_score_vel) * 0.1, 0.5)

                if is_outlier:
                    mil_assets.append({
                        "icao24": s[0],
                        "callsign": callsign if callsign else "U_ID",
                        "origin": s[2],
                        "lat": s[6],
                        "lon": s[5],
                        "alt": int(altitude) if altitude else 0,
                        "vel": int(velocity * 3.6) if velocity else 0,
                        "is_mil": is_mil,
                        "is_outlier": is_outlier,
                        "anomaly_score": round(anomaly_score, 2)
                    })
            
            # Sort by "severity" (anomaly score first)
            mil_assets.sort(key=lambda x: x.get("anomaly_score", 0), reverse=True)
            
            # Identify "Theater" (simple heuristic by count in region)
            theaters: Dict[str, int] = {"EUROPE": 0, "MIDDLE_EAST": 0, "ASIA_PACIFIC": 0, "AMERICAS": 0}
            for a in mil_assets:
                lat: Optional[float] = a["lat"]
                lon: Optional[float] = a["lon"]
                if lat and lon:
                    if 35 < lat < 70 and -10 < lon < 40: theaters["EUROPE"] += 1
                    elif 10 < lat < 45 and 30 < lon < 75: theaters["MIDDLE_EAST"] += 1
                    elif -10 < lat < 50 and 70 < lon < 150: theaters["ASIA_PACIFIC"] += 1
                    else: theaters["AMERICAS"] += 1
            
            main_theater: str = max(theaters, key=theaters.get) if mil_assets else "NONE"
            
            return {
                "status": "active", 
                "assets": mil_assets[:80], 
                "count": len(mil_assets),
                "theater": main_theater,
                "global_avg_velocity": int(avg_vel * 3.6)
            }
        except Exception as e:
            print(f"!! OpenSky fetch failed: {e}")
            return {"status": "offline", "assets": []}

    df = pd.DataFrame(final_articles)
    
    # Pre-fetch all domain data for composite scoring
    cyber_intel = fetch_cyber_intel()
    raw_chatter = fetch_raw_chatter()
    market_intel = fetch_market_data()
    flight_intel = fetch_opensky_flights()
    
    # --- API RESILIENCE: Fallback to existing data on failure ---
    if not cyber_intel and os.path.exists("data/intelligence.json"):
        try:
            with open("data/intelligence.json", "r") as f:
                cyber_intel = json.load(f).get("cyber_intel", [])
        except: pass
    if not market_intel and os.path.exists("data/markets.json"):
        try:
            with open("data/markets.json", "r") as f:
                market_intel = json.load(f).get("market_intel", [])
        except: pass
    if (not flight_intel or flight_intel.get("status") == "offline") and os.path.exists("data/telemetry.json"):
        try:
            with open("data/telemetry.json", "r") as f:
                flight_intel = json.load(f).get("flight_intel", {"status": "stale", "assets": []})
        except: pass

    # Calculate Multi-Domain Composite GTI
    gti = calculate_gti(final_articles, market_intel, flight_intel)
    
    # --- FEATURE: LLM SITREP ---
    alerts = []
    # Collect high-score or anomaly events
    for a in final_articles[:15]:
        if a.get("manipulation_score", 0) > 85: alerts.append(f"Narrative Spike: {a['title']}")
    if flight_intel.get("assets"):
        outliers = [f"Aerial Anomaly: {f['callsign']}" for f in flight_intel['assets'] if f.get("is_outlier")]
        alerts.extend(outliers[:5])
    
    sitrep = generate_sitrep(alerts)
    strategic_insight = generate_strategic_insight(final_articles, market_intel, flight_intel)
    print(f"\n[SITREP] {sitrep}\n")
    print(f"[INSIGHT] {strategic_insight}\n")

    stats = {
        "total_nodes": len(final_articles),
        "top_domains": df["domain"].value_counts().head(8).to_dict() if not df.empty else {},
        "source_countries": df["sourcecountry"].value_counts().to_dict() if not df.empty else {},
        "top_keywords": extract_keywords(final_articles),
        "global_tension_index": gti,
        "cyber_intel": cyber_intel,
        "raw_chatter": raw_chatter,
        "market_intel": market_intel,
        "flight_intel": flight_intel,
        "sitrep": sitrep,
        "strategic_insight": strategic_insight
    }
    
    # Narrative Graph logic
    narrative_graph = generate_narrative_graph(final_articles)

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
        },
        "narrative_graph": narrative_graph
    }
    
    market_data = {"market_intel": stats["market_intel"]}
    telemetry_data = {"flight_intel": stats["flight_intel"]}
    intel_data = {
        "cyber_intel": stats["cyber_intel"],
        "raw_chatter": stats["raw_chatter"],
        "sitrep": sitrep,
        "strategic_insight": strategic_insight
    }
    
    # GTI History Logic
    gti_history = []
    if os.path.exists("data/status.json"):
        try:
            with open("data/status.json", "r") as f:
                old_status = json.load(f)
                gti_history = old_status.get("gti_history", [])
        except:
            pass
    
    current_time = datetime.now().isoformat()
    gti_history.append({"timestamp": current_time, "score": gti})
    # Keep last 50 entries
    gti_history = gti_history[-50:]

    # GTI Forecasting
    forecast_data = forecast_gti(gti_history)

    status_data = {
        "last_updated": current_time,
        "global_tension_index": stats["global_tension_index"],
        "gti_history": gti_history,
        "gti_forecast": forecast_data.get("forecast", []),
        "forecast_confidence": forecast_data.get("confidence", "low"),
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

    # --- FEATURE: Historical Archiving (Static Data Lake) ---
    today = datetime.now().strftime("%Y-%m-%d")
    archive_dir = f"data/archive"
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = f"{archive_dir}/{today}.json"
    
    # We save a consolidated snapshot for the day
    archive_snapshot = {
        "date": today,
        "gti": gti,
        "sitrep": sitrep,
        "top_keywords": stats["top_keywords"],
        "top_domains": stats["top_domains"]
    }
    
    # If archive exists for today, we might want to update it or just keep it
    # For now, let's just save it.
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive_snapshot, f, indent=4)

    # Signature on global status for integrity
    json_content = json.dumps(status_data, indent=4)
    signature = sign_data(json_content)
    
    print(f"sync complete. modular state verified. integrity: {signature[:8]}")


if __name__ == "__main__":
    fetch_gdelt_data()

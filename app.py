import google_play_scraper as gps
from fuzzywuzzy import fuzz
import imagehash
from PIL import Image
import requests
from io import BytesIO
import json
import os

GENUINE_APPS = {
    "paytm": "net.one97.paytm",
    "google pay": "com.google.android.apps.nbu.paisa.user",
}

SUSPICIOUS_KEYWORDS = ["scam", "fraud",
                       "fake", "update required", "hack", "steal"]


def fetch_and_save_database(query, num_results=100, filename='playstore_apps.json'):
    """Fetch app database from Play Store and save to JSON."""
    try:
        results = gps.search(
            query, lang='en', country='us', n_hits=num_results)
        apps = []
        for app in results:
            apps.append({
                'title': app['title'],
                'appId': app['appId'],
                'developer': app['developer'],
                'icon': app['icon'],
                'description': app.get('description', ''),
                'url': f"https://play.google.com/store/apps/details?id={app['appId']}",
                'score': app.get('score', 0),
                'ratings': app.get('ratings', 0),
                'installs': app.get('installs', ''),
            })
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(apps, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(apps)} apps to {filename}")
        return apps
    except Exception as e:
        print(f"Error fetching/saving database: {e}")
        return []


def load_database(filename='playstore_apps.json'):
    """Load app database from JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"Database file {filename} not found.")
        return []


def get_official_details(package_id):
    """Fetch official app details (title, developer, icon hash)."""
    try:
        app = gps.app(package_id, lang='en', country='us')
        official_title = app['title']
        official_developer = app['developer']
        official_icon_hash = download_and_hash_icon(app['icon'])
        return official_title, official_developer, official_icon_hash
    except Exception as e:
        print(f"Error fetching official app details: {e}")
        return "Unknown", "Unknown", None


def download_and_hash_icon(icon_url):
    """Download icon and compute perceptual hash (dhash)."""
    try:
        response = requests.get(icon_url, timeout=10)
        img = Image.open(BytesIO(response.content))
        return str(imagehash.dhash(img))
    except Exception as e:
        print(f"Error hashing icon: {e}")
        return None


def compute_signals(official_title, official_package, official_developer, official_icon_hash, candidate):
    """Compute similarity signals."""
    signals = {}


    signals['name_similarity'] = fuzz.ratio(
        official_title.lower(), candidate['title'].lower())

    signals['package_similarity'] = fuzz.ratio(
        official_package, candidate['appId'])


    signals['publisher_match'] = 100 if official_developer.lower(
    ) in candidate['developer'].lower() else 0

 
    candidate_hash = download_and_hash_icon(candidate['icon'])
    if candidate_hash and official_icon_hash and candidate_hash == official_icon_hash:
        signals['icon_similarity'] = 100
    else:
        signals['icon_similarity'] = 0

 
    desc_lower = candidate['description'].lower()
    keyword_count = sum(1 for kw in SUSPICIOUS_KEYWORDS if kw in desc_lower)
    signals['suspicious_keywords'] = min(keyword_count * 20, 100)

    return signals


def calculate_risk_score(signals):
    """Revised rule-based risk score (0-100): High similarity in name/pkg + mismatches = high risk."""
    score = (
        (signals['name_similarity'] * 0.2) +
        (signals['package_similarity'] * 0.2) +
        ((100 - signals['publisher_match']) * 0.3) +
        ((100 - signals['icon_similarity']) * 0.2) +
        (signals['suspicious_keywords'] * 0.1)
    )
    return min(max(score, 0), 100)


def main():
    db_file = 'playstore_apps.json'
    if not os.path.exists(db_file):
        query = input(
            "Database not found. Enter search query to fetch (e.g., 'banking apps'): ").strip()
        num_results = int(
            input("Enter number of apps to fetch (default 100): ") or 100)
        fetch_and_save_database(query, num_results, db_file)

    candidates = load_database(db_file)
    if not candidates:
        print("No database loaded. Exiting.")
        return

    brand = input("Enter brand name (e.g., 'Paytm'): ").strip().lower()
    if brand not in GENUINE_APPS:
        print("Brand not in known genuine list. Add to GENUINE_APPS dict.")
        return

    official_package = GENUINE_APPS[brand]
    official_title, official_developer, official_icon_hash = get_official_details(
        official_package)

    results = []
    a = 0
    for candidate in candidates:
        signals = compute_signals(
            official_title, official_package, official_developer, official_icon_hash, candidate)
        score = calculate_risk_score(signals)
        if (score >= 95):
            a = 1
        results.append({
            'app': candidate,
            'signals': signals,
            'score': score,
            'flagged': score > 50
        })

    results.sort(key=lambda x: x['score'], reverse=True)

    print("\nCandidate Apps (Top Suspicious First):")
    print("Title | Package ID | Score | Flagged | Reasons")
    print("-" * 80)
    for res in results[:10]:
        reasons = f"Name:{res['signals']['name_similarity']}%, Pkg:{res['signals']['package_similarity']}%, Pub:{res['signals']['publisher_match']}%, Icon:{res['signals']['icon_similarity']}%, KW:{res['signals']['suspicious_keywords']}%"
        flagged = "YES" if res['flagged'] else "NO"
        print(
            f"{res['app']['title'][:20]} | {res['app']['appId'][:30]} | {res['score']:.2f} | {flagged} | {reasons}")

    if (a == 1):
        print("\n\n\nTop Risk app flagged")
    else:
        print("\n\n\nNo Top Risk app flagged")


if __name__ == "__main__":
    main()


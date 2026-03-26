import requests
from bs4 import BeautifulSoup

print("AUTO SEO OPTIMIZATION STARTED")

SITEMAP = "https://moneyabroadguide.com/sitemap_index.xml"

def get_urls():
    try:
        res = requests.get(SITEMAP, timeout=10)
        soup = BeautifulSoup(res.text, "xml")
        return [loc.text for loc in soup.find_all("loc")]
    except:
        return []

def analyze(url):
    issues = []

    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string if soup.title else ""
        h1 = soup.find_all("h1")
        words = len(soup.get_text().split())
        images = soup.find_all("img")

        score = 100

        if not title:
            score -= 20
            issues.append("❌ Missing title")

        if len(h1) == 0:
            score -= 20
            issues.append("❌ Missing H1")

        if words < 800:
            score -= 30
            issues.append("❌ Content too short")

        if len(images) == 0:
            score -= 10
            issues.append("❌ No images")

        return {
            "url": url,
            "score": score,
            "issues": issues
        }

    except:
        return {
            "url": url,
            "score": 0,
            "issues": ["❌ Page error"]
        }

urls = get_urls()

results = []

for url in urls[:20]:
    data = analyze(url)
    results.append(data)

print("\n===== SEO REPORT =====\n")

for r in results:
    print("URL:", r["url"])
    print("SCORE:", r["score"])
    
    if r["issues"]:
        for issue in r["issues"]:
            print(issue)
    else:
        print("✅ Perfect page")

    print("------")

import requests
from bs4 import BeautifulSoup

print("AI SEO OPTIMIZER STARTED")

SITEMAP = "https://moneyabroadguide.com/sitemap_index.xml"

def get_urls():
    try:
        res = requests.get(SITEMAP, timeout=10)
        soup = BeautifulSoup(res.text, "xml")
        return [loc.text for loc in soup.find_all("loc")]
    except:
        return []

def generate_seo_improvement(url, title, h1, words):
    keyword = url.split("/")[-1].replace("-", " ")

    new_title = f"{keyword.title()} Guide (2026): Everything You Need to Know"
    meta = f"Learn everything about {keyword}. Complete 2026 guide with tips, strategies, and expert insights for newcomers."

    suggestions = []

    if words < 800:
        suggestions.append("👉 Increase content to 1200–2000 words")

    if len(h1) == 0:
        suggestions.append("👉 Add clear H1 with main keyword")

    suggestions.append("👉 Add 2–3 internal links")
    suggestions.append("👉 Add FAQ section")
    suggestions.append("👉 Add optimized images with ALT text")

    return new_title, meta, suggestions

def analyze(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string if soup.title else ""
        h1 = soup.find_all("h1")
        words = len(soup.get_text().split())

        score = 100

        if not title:
            score -= 20
        if len(h1) == 0:
            score -= 20
        if words < 800:
            score -= 30

        new_title, meta, suggestions = generate_seo_improvement(url, title, h1, words)

        return {
            "url": url,
            "score": score,
            "new_title": new_title,
            "meta": meta,
            "suggestions": suggestions
        }

    except:
        return {
            "url": url,
            "score": 0,
            "new_title": "",
            "meta": "",
            "suggestions": ["Error loading page"]
        }

urls = get_urls()

print("\n===== AI SEO REPORT =====\n")

for url in urls[:10]:
    data = analyze(url)

    print("URL:", data["url"])
    print("SEO SCORE:", data["score"])
    print("NEW TITLE:", data["new_title"])
    print("META:", data["meta"])

    print("IMPROVEMENTS:")
    for s in data["suggestions"]:
        print(s)

    print("------")

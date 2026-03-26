import requests
from bs4 import BeautifulSoup

print("FULL SITE SEO SCAN")

SITEMAP = "https://moneyabroadguide.com/sitemap_index.xml"

def get_urls():
    try:
        res = requests.get(SITEMAP, timeout=10)
        soup = BeautifulSoup(res.text, "xml")
        return [loc.text for loc in soup.find_all("loc")]
    except:
        return []

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

        return (url, score)

    except:
        return (url, 0)

urls = get_urls()

for url in urls[:15]:
    page, score = analyze(url)
    print(page, "→ SEO SCORE:", score)

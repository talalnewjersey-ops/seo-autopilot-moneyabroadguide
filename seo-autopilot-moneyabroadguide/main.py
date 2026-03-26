import requests
from bs4 import BeautifulSoup

def get_urls():
    sitemap = "https://moneyabroadguide.com/sitemap_index.xml"
    res = requests.get(sitemap)
    soup = BeautifulSoup(res.text, "xml")
    return [loc.text for loc in soup.find_all("loc")]

def crawl(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.title.string if soup.title else ""
        h1 = [h.text.strip() for h in soup.find_all("h1")]
        word_count = len(soup.get_text().split())

        score = 100

        if not title:
            score -= 15
        if not h1:
            score -= 15
        if word_count < 600:
            score -= 20

        return url, score

    except:
        return url, 0

urls = get_urls()

for url in urls[:20]:
    page, score = crawl(url)
    print(page, "→ SEO SCORE:", score)

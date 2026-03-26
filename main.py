import requests
from bs4 import BeautifulSoup

print("START FULL SEO SCAN")

urls = [
    "https://moneyabroadguide.com"
]

for url in urls:
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string if soup.title else ""
        h1 = [h.text.strip() for h in soup.find_all("h1")]
        words = len(soup.get_text().split())

        score = 100

        if not title:
            score -= 20
        if not h1:
            score -= 20
        if words < 600:
            score -= 30

        print("------")
        print("URL:", url)
        print("TITLE:", title)
        print("H1:", h1)
        print("WORDS:", words)
        print("SEO SCORE:", score)

    except Exception as e:
        print("ERROR:", e)

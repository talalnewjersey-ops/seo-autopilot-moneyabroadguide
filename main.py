import requests
from bs4 import BeautifulSoup

sitemap = "https://moneyabroadguide.com/sitemap_index.xml"

res = requests.get(sitemap)
soup = BeautifulSoup(res.text, "xml")

urls = [loc.text for loc in soup.find_all("loc")]

for url in urls[:10]:
    try:
        r = requests.get(url)
        s = BeautifulSoup(r.text, "html.parser")

        title = s.title.string if s.title else "No title"
        h1 = [h.text.strip() for h in s.find_all("h1")]

        print(url)
        print("TITLE:", title)
        print("H1:", h1)
        print("-----")

    except Exception as e:
        print("Error:", e)

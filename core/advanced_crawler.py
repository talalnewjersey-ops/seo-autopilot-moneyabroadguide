import requests
from bs4 import BeautifulSoup

def crawl_page(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        return {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "meta": soup.find("meta", attrs={"name": "description"}),
            "h1": [h.text.strip() for h in soup.find_all("h1")],
            "h2": [h.text.strip() for h in soup.find_all("h2")],
            "word_count": len(soup.get_text().split()),
            "images": len(soup.find_all("img")),
            "links": len(soup.find_all("a")),
        }

    except Exception as e:
        return {"url": url, "error": str(e)}

import requests
from bs4 import BeautifulSoup

def get_urls(sitemap_url):
    res = requests.get(sitemap_url)
    soup = BeautifulSoup(res.text, "xml")

    return [loc.text for loc in soup.find_all("loc")]

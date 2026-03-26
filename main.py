import requests
from bs4 import BeautifulSoup

URL = "https://moneyabroadguide.com"

print("===== SEO AUDIT START =====")
print(f"Scanning: {URL}")

try:
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.title.string if soup.title else "No title"
    h1 = soup.find("h1")
    h1_text = h1.text if h1 else "No H1"

    score = 0

    if title and len(title) > 10:
        score += 40
    if h1:
        score += 30
    if len(r.text) > 5000:
        score += 30

    print("\n===== RESULTS =====")
    print(f"TITLE: {title}")
    print(f"H1: {h1_text}")
    print(f"CONTENT LENGTH: {len(r.text)}")

    print("\n🔥 SEO SCORE:", score, "/100")

except Exception as e:
    print("ERROR:", str(e))

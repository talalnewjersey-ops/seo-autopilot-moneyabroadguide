import requests
from bs4 import BeautifulSoup

URL = "https://moneyabroadguide.com"

print("===== AI SEO AUDIT START =====")
print(f"Scanning: {URL}\n")

score = 0
issues = []
good = []

try:
    r = requests.get(URL, timeout=10)
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # TITLE
    title = soup.title.string if soup.title else ""
    if title:
        good.append("Title present")
        if 50 <= len(title) <= 60:
            score += 15
        else:
            issues.append("Title length not optimal")
    else:
        issues.append("Missing title")

    # META DESCRIPTION
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        score += 15
        good.append("Meta description present")
    else:
        issues.append("Missing meta description")

    # H1
    h1 = soup.find("h1")
    if h1:
        score += 15
        good.append("H1 present")
    else:
        issues.append("Missing H1")

    # IMAGES ALT
    images = soup.find_all("img")
    missing_alt = [img for img in images if not img.get("alt")]
    if len(missing_alt) == 0:
        score += 10
        good.append("All images have alt")
    else:
        issues.append(f"{len(missing_alt)} images missing alt")

    # CONTENT LENGTH
    if len(html) > 5000:
        score += 15
        good.append("Good content length")
    else:
        issues.append("Content too short")

    # LINKS
    links = soup.find_all("a")
    if len(links) > 20:
        score += 10
        good.append("Internal linking ok")
    else:
        issues.append("Not enough links")

    # FINAL SCORE
    print("===== RESULTS =====")
    print(f"SEO SCORE: {score} / 100\n")

    print("✅ GOOD:")
    for g in good:
        print("-", g)

    print("\n❌ ISSUES:")
    for i in issues:
        print("-", i)

    print("\n===== AI RECOMMENDATIONS =====")

    for i in issues:
        print(f"→ Fix: {i}")

except Exception as e:
    print("ERROR:", str(e))

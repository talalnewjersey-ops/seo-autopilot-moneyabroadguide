def seo_scan(label):
    import requests
    from bs4 import BeautifulSoup

    URL = "https://moneyabroadguide.com"

    print(f"\n===== {label} SEO SCAN =====")

    r = requests.get(URL)
    soup = BeautifulSoup(r.text, "html.parser")

    score = 0

    title = soup.title.string if soup.title else ""
    if title:
        score += 30

    if soup.find("h1"):
        score += 30

    if len(r.text) > 5000:
        score += 40

    print(f"SEO SCORE: {score}/100")

    return score


# 1️⃣ SCAN AVANT
before = seo_scan("BEFORE")

# 🔴 ICI TU AJOUTES TES FIXES 👇

print("\n===== AI FIXES =====")

print("→ Add meta description")
print("→ Improve title length")
print("→ Add alt tags to images")
print("→ Increase content length")

# 2️⃣ SCAN APRÈS
after = seo_scan("AFTER")

print("\n===== IMPROVEMENT =====")
print(f"{before} → {after}")

def seo_scan(label, content):
    score = 0

    print(f"\n===== {label} SEO SCAN =====")

    if "<title" in content.lower():
        print("✔ Title present")
        score += 20
    else:
        print("❌ Missing title")

    if 'meta name="description"' in content.lower():
        print("✔ Meta description")
        score += 20
    else:
        print("❌ Missing meta description")

    if "alt=" in content.lower():
        print("✔ Image alt tags")
        score += 20
    else:
        print("❌ Missing alt tags")

    if len(content) > 1500:
        print("✔ Content length OK")
        score += 20
    else:
        print("❌ Content too short")

    if "<h2" in content.lower():
        print("✔ Headings present")
        score += 20
    else:
        print("❌ Missing headings")

    print(f"\nSEO SCORE: {score}/100")
    return score

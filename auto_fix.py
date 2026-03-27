import requests
import os
import json
from openai import OpenAI

# ================================
# 🔐 ENV VARIABLES
# ================================
print("DEBUG KEY:", os.getenv("OPENAI_API_KEY"))
print("WP_URL:", os.getenv("WP_URL"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

print("===== SAFE AUTO FIX START =====")


# ================================
# 📥 GET POSTS
# ================================
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    response = requests.get(url)
    return response.json()


# ================================
# 🤖 AI SEO OPTIMIZATION (FIXED)
# ================================
def generate_ai_fix(title, content):
    try:
        prompt = f"""
Return ONLY valid JSON.

Do NOT write anything else.

Format:
{{
"title": "...",
"meta": "...",
"content": "..."
}}

Optimize this article for SEO:

Title: {title}
Content: {content[:4000]}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000
        )

        raw = response.choices[0].message.content.strip()

        # 🔥 CLEAN JSON SAFE
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)

        # 🔥 VALIDATION
        if not all(k in data for k in ["title", "meta", "content"]):
            print("❌ JSON STRUCTURE INVALID")
            return None

        return data

    except Exception as e:
        print("❌ OPENAI ERROR:", str(e))
        return None


# ================================
# 🌐 UPDATE WORDPRESS
# ================================
def update_post(post_id, data):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"

    payload = {
        "title": data["title"],
        "content": data["content"],
        "excerpt": data["meta"],
        "status": "publish"  # 🔥 IMPORTANT
    }

    response = requests.post(
        url,
        json=payload,
        auth=(WP_USER, WP_PASSWORD)
    )

    print(f"Updated post {post_id} → {response.status_code}")
    print("========== SEO RESULT ==========")
    print("NEW TITLE:", data["title"])
    print("META:", data["meta"])
    print("CONTENT LENGTH:", len(data["content"]))


# ================================
# 🔍 SEO SCORE SYSTEM
# ================================
def seo_score(content):
    score = 0

    if "<title" in content.lower():
        score += 25

    if 'meta name="description"' in content.lower():
        score += 25

    if "alt=" in content.lower():
        score += 25

    if len(content) > 3000:
        score += 25

    print(f"SEO SCORE: {score}/100")
    return score


# ================================
# 🚀 MAIN
# ================================
def run():
    posts = get_posts()

    for post in posts[:1]:
        print("\n===== ANALYZING =====")
        print(post["title"]["rendered"])

        before = seo_score(post["content"]["rendered"])

        ai_data = generate_ai_fix(
            post["title"]["rendered"],
            post["content"]["rendered"]
        )

        if not ai_data:
            print("→ AI FAILED → skipping safely")
            continue

        print("→ AI optimization OK")

        after = seo_score(ai_data["content"])
        print(f"IMPROVEMENT: {before} → {after}")

        update_post(post["id"], ai_data)


if __name__ == "__main__":
    run()
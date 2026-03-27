import requests
import os
import json
import time
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
# 🤖 AI SEO OPTIMIZATION (FAST VERSION)
# ================================
def generate_ai_fix(title, content):
    for attempt in range(3):
        try:
            prompt = f"""
You are an SEO expert.

Optimize this article for SEO and readability.

KEEP HTML.

Improve:
- Title
- Meta description
- Structure (H2, H3)
- Add FAQ (3 questions)
- Add short CTA

Return ONLY JSON:

{{
"title": "...",
"meta": "...",
"content": "optimized html"
}}

Title: {title}
Content: {content}
"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=60
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"❌ OPENAI ERROR (try {attempt+1}):", str(e))
            time.sleep(3)

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
        "status": "publish"
    }

    response = requests.post(
        url,
        json=payload,
        auth=(WP_USER, WP_PASSWORD)
    )

    print(f"Updated post {post_id} → {response.status_code}")
    print("RESPONSE:", response.text)


# ================================
# 🔍 SEO SCORE
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

    if not posts:
        print("❌ No posts found")
        return

    for post in posts[:1]:
        print("\n===== ANALYZING =====")
        print(post["title"]["rendered"])

        before = seo_score(post["content"]["rendered"])

        ai_data = generate_ai_fix(
            post["title"]["rendered"],
            post["content"]["rendered"][:4000]  # 🔥 FIX TIMEOUT
        )

        if ai_data:
            print("→ AI optimization OK")

            after = seo_score(ai_data["content"])

            print(f"IMPROVEMENT: {before} → {after}")

            print("========== SEO RESULT ==========")
            print("NEW TITLE:", ai_data["title"])
            print("META:", ai_data["meta"])
            print("CONTENT LENGTH:", len(ai_data["content"]))

            update_post(post["id"], ai_data)

        else:
            print("→ Skipped (AI error)")


# ================================
# ▶️ START
# ================================
if __name__ == "__main__":
    run()

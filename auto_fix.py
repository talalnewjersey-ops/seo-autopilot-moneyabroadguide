import os
print("DEBUG KEY:", os.getenv("OPENAI_API_KEY"))
print("WP_URL:", os.getenv("WP_URL"))

from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_fix(title, content):
    try:
        prompt = f"""
You are an SEO expert.

Optimize this article for SEO (score 95+).

Return ONLY JSON like:
{{
"title": "...",
"meta": "...",
"content": "..."
}}

Title: {title}
Content: {content}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # ✅ IMPORTANT
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        import requests

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

print("===== SAFE AUTO FIX START =====")


# 📥 GET POSTS
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    response = requests.get(url)
    return response.json()


# 🌐 UPDATE WORDPRESS
def update_post(post_id, data):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"

    payload = {
        "title": data["title"],
        "content": data["content"],
        "excerpt": data["meta"]
    }

    response = requests.post(
        url,
        json=payload,
        auth=(WP_USER, WP_PASSWORD)
    )

    print(f"Updated post {post_id} → {response.status_code}")


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


# 🚀 MAIN
def run():
    posts = get_posts()

    for post in posts[:1]:
        print(f"\n===== ANALYZING =====")
        print(post["title"]["rendered"])

        # BEFORE
        before = seo_score(post["content"]["rendered"])

        ai_data = generate_ai_fix(
            post["title"]["rendered"],
            post["content"]["rendered"]
        )

        if ai_data:
            print("→ AI optimization OK")

            # AFTER
            after = seo_score(ai_data["content"])

            print(f"IMPROVEMENT: {before} → {after}")

            update_post(post["id"], ai_data)
        else:
            print("→ Skipped (AI error)")


if __name__ == "__main__":
    run()

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("❌ OPENAI ERROR:", str(e))
        return None

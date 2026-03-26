print("DEBUG KEY:", os.getenv("OPENAI_API_KEY"))

import requests
import os
from openai import OpenAI

# 🔐 ENV VARIABLES
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

print("===== SAFE AUTO FIX START =====")


# 📥 GET POSTS
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    response = requests.get(url)
    return response.json()


# 🤖 AI SEO OPTIMIZATION
def generate_ai_fix(title, content):
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
        model="gpt-5.3",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    import json

    try:
        return json.loads(response.choices[0].message.content)
    except:
        print("❌ JSON ERROR FROM AI")
        return None


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


# 🚀 MAIN
def run():
    posts = get_posts()

    # ⚠️ SAFE MODE → 1 ARTICLE ONLY
    for post in posts[:1]:
        print(f"\nAnalyzing: {post['title']['rendered']}")

        ai_data = generate_ai_fix(
            post["title"]["rendered"],
            post["content"]["rendered"]
        )

        if ai_data:
            print("→ AI optimization OK")
            update_post(post["id"], ai_data)
        else:
            print("→ Skipped (AI error)")


if __name__ == "__main__":
    run()

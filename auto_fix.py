import os
import requests
import json
from requests.auth import HTTPBasicAuth

print("===== SAFE AUTO FIX START =====")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

# ===============================
# GET POSTS FROM WORDPRESS
# ===============================
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    response = requests.get(url)
    return response.json()

# ===============================
# UPDATE POST WORDPRESS
# ===============================
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
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
        json=payload
    )

    print(f"Updated post {post_id} → {response.status_code}")
    if response.status_code != 200:
        print("❌ UPDATE ERROR:", response.text)

# ===============================
# OPENAI SEO OPTIMIZATION
# ===============================
def optimize_content(title, content):

    prompt = f"""
You are a senior SEO expert.

Optimize this article:

TITLE: {title}
CONTENT: {content}

RETURN ONLY VALID JSON:

{{
"title": "...",
"meta": "...",
"content": "HTML optimized"
}}
"""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=60
        )

        result = response.json()

        # 🔥 DEBUG IMPORTANT
        print("RAW OPENAI RESPONSE:")
        print(result)

        if "choices" not in result:
            print("❌ INVALID OPENAI RESPONSE")
            return None

        content_raw = result["choices"][0]["message"]["content"]

        # Nettoyage JSON
        content_raw = content_raw.strip().replace("```json", "").replace("```", "")

        data = json.loads(content_raw)

        return data

    except Exception as e:
        print("❌ OPENAI ERROR:", e)
        return None

# ===============================
# MAIN PROCESS
# ===============================
posts = get_posts()

for post in posts[:3]:

    post_id = post["id"]
    title = post["title"]["rendered"]
    content = post["content"]["rendered"]

    print("\n===== ANALYZING =====")
    print(title)

    data = optimize_content(title, content)

    if not data:
        print("→ Skipped (AI error)")
        continue

    print("→ AI optimization OK")

    print("========== SEO RESULT ==========")
    print("NEW TITLE:", data["title"])
    print("META:", data["meta"])
    print("CONTENT LENGTH:", len(data["content"]))

    update_post(post_id, data)

print("\n===== AUTO FIX COMPLETE =====")

import os
import requests
import json
import time
from openai import OpenAI

# =============================
# CONFIG
# =============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

client = OpenAI(api_key=OPENAI_API_KEY)

# =============================
# OPENAI CALL (ULTRA STABLE)
# =============================
def call_openai(prompt):
    for attempt in range(3):
        try:
            print(f"🚀 OpenAI call attempt {attempt+1}")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior SEO expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                timeout=300
            )

            content = response.choices[0].message.content

            print("RAW OPENAI RESPONSE:")
            print(content)

            # Clean JSON
            content = content.replace("```json", "").replace("```", "").strip()

            return content

        except Exception as e:
            print(f"❌ OPENAI ERROR (try {attempt+1}/3): {e}")
            time.sleep(5)

    return None

# =============================
# GET POSTS
# =============================
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print("❌ Failed to fetch posts")
        return []

# =============================
# UPDATE POST
# =============================
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

# =============================
# PROMPT SEO
# =============================
def build_prompt(content):
    return f"""
You are a senior SEO expert specialized in Google ranking (2026) and YMYL finance content.

Your goal:
Fully optimize this article for ranking, EEAT, and user engagement.

STRICT RULES:
- Keep HTML format
- Improve, do NOT delete content
- Make it natural, human, and authoritative

YOU MUST:

1. SEO TITLE (max 60 chars)
2. META DESCRIPTION (150-160 chars)
3. STRUCTURE with H2/H3
4. ADD EEAT (Talal Eddaouahiri)
5. ADD FAQ
6. ADD INTERNAL LINKS
7. ADD CTA
8. ADD SCHEMA JSON-LD
9. Improve keywords

RETURN ONLY JSON:

{{
"title": "...",
"meta": "...",
"content": "FULL HTML"
}}

ARTICLE:
{content}
"""

# =============================
# MAIN
# =============================
def main():
    print("===== SAFE AUTO FIX START =====")

    posts = get_posts()

    for post in posts[:3]:  # limiter pour test
        print("\n===== ANALYZING =====")

        post_id = post["id"]
        title = post["title"]["rendered"]
        content = post["content"]["rendered"]

        print(title)
        print("SEO SCORE: 50/100")

        prompt = build_prompt(content)

        result = call_openai(prompt)

        if not result:
            print("→ Skipped (AI error)")
            continue

        try:
            data = json.loads(result)
        except:
            print("❌ JSON ERROR")
            continue

        print("→ AI optimization OK")

        # TRACKING 🔥
        print("========== SEO RESULT ==========")
        print("NEW TITLE:", data["title"])
        print("META:", data["meta"])
        print("CONTENT LENGTH:", len(data["content"]))

        update_post(post_id, data)

    print("\n===== AUTO FIX COMPLETE =====")

# =============================
# RUN
# =============================
if __name__ == "__main__":
    main()
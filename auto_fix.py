import requests
import os
import time
from requests.auth import HTTPBasicAuth

# ==============================
# 🔐 ENV VARIABLES
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

# ==============================
# 🔧 CONFIG
# ==============================

MAX_POSTS = 5

# ==============================
# 🧠 OPENAI CALL (FIXED)
# ==============================

def call_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"

    for i in range(3):
        try:
            print(f"⏳ OpenAI attempt {i+1}")

            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a finance SEO expert optimizing articles for Google ranking."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=90
            )

            data = response.json()

            if "choices" in data:
                return data["choices"][0]["message"]["content"]

            elif "output" in data:
                return data["output"][0]["content"][0]["text"]

            else:
                print("❌ Unexpected OpenAI response:", data)
                return None

        except requests.exceptions.Timeout:
            print(f"⚠️ Timeout attempt {i+1}, retry...")
            time.sleep(5)

        except Exception as e:
            print(f"❌ Error attempt {i+1}:", e)
            time.sleep(5)

    return None


# ==============================
# 📥 GET POSTS FROM WORDPRESS
# ==============================

def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
        params={"per_page": MAX_POSTS}
    )

    if response.status_code != 200:
        print("❌ Error fetching posts:", response.text)
        return []

    return response.json()


# ==============================
# 🧠 BUILD SEO PROMPT
# ==============================

def build_prompt(title, content):
    return f"""
Optimize this article for SEO (Google 2026 standards).

DO NOT change meaning.
DO NOT remove structure.
Improve:
- readability
- SEO keywords
- clarity
- add slight human tone

Return FULL HTML.

TITLE:
{title}

CONTENT:
{content[:8000]}
"""


# ==============================
# 📤 UPDATE POST
# ==============================

def update_post(post_id, new_content):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"

    response = requests.post(
        url,
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
        json={"content": new_content}
    )

    if response.status_code == 200:
        print("✅ Updated successfully")
    else:
        print("❌ Update failed:", response.text)


# ==============================
# 🔁 PROCESS POSTS
# ==============================

def process_posts():
    print("\n===== 🚀 SAFE AUTO FIX START =====\n")

    posts = get_posts()

    for post in posts:
        title = post["title"]["rendered"]
        content = post["content"]["rendered"]
        post_id = post["id"]

        print("\n===== ANALYSE =====")
        print(f"Article: {title}")

        prompt = build_prompt(title, content)

        optimized = call_openai(prompt)

        if optimized:
            update_post(post_id, optimized)
        else:
            print("❌ OpenAI failed")

    print("\n===== ✅ AUTO FIX COMPLETE =====\n")


# ==============================
# ▶️ RUN
# ==============================

if __name__ == "__main__":
    process_posts()
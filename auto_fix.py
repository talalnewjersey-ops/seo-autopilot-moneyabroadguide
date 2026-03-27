import requests
import json
import re
import time
import os
from requests.auth import HTTPBasicAuth

# ==============================
# CONFIG (GITHUB SECRETS)
# ==============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_BASE_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

if not WP_BASE_URL.startswith("http"):
    raise ValueError("WP_URL invalide. Ajoute https://")

WP_URL = WP_BASE_URL.rstrip("/") + "/wp-json/wp/v2/posts"

MAX_CONTENT_LENGTH = 25000

# ==============================
# UTILS
# ==============================

def extract_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            raise ValueError("JSON non trouvé")

def clean_html(content):
    return content.replace("```html", "").replace("```", "").strip()

def limit_content(content):
    if len(content) > MAX_CONTENT_LENGTH:
        return content[:MAX_CONTENT_LENGTH] + "..."
    return content

# ==============================
# OPENAI CALL (FIXED)
# ==============================

def call_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"

    for i in range(3):
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",  # 🔥 stable
                    "messages": [
                        {"role": "system", "content": "You are a finance SEO expert (YMYL compliant)."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=30
            )

            data = response.json()

            print("🔍 RAW OPENAI RESPONSE:", data)

            # ✅ FORMAT 1 (classique)
            if "choices" in data:
                return data["choices"][0]["message"]["content"]

            # ✅ FORMAT 2 (nouveaux modèles)
            elif "output" in data:
                return data["output"][0]["content"][0]["text"]

            else:
                print("❌ Format inconnu OpenAI")
                return None

        except Exception as e:
            print(f"❌ Retry {i+1} failed:", e)
            time.sleep(2)

    return None

# ==============================
# SEO PROMPT
# ==============================

def build_prompt(title, content):
    return f"""
Optimize this article for SEO (RankMath 90+).

STRICT RULES:
- Keep clean HTML
- No broken tags
- Add H2/H3 structure
- Add FAQ section (3-5 questions)
- Add Article + FAQ schema
- Improve readability
- Human tone (not AI)
- No fluff

Return ONLY JSON:

{{
"title": "...",
"meta": "...",
"content": "FULL HTML CONTENT"
}}

TITLE:
{title}

CONTENT:
{content}
"""

# ==============================
# FETCH POSTS
# ==============================

def get_posts():
    response = requests.get(
        WP_URL,
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
        params={"per_page": 5},
        timeout=20
    )

    if response.status_code != 200:
        raise Exception(f"Erreur WP: {response.text}")

    return response.json()

# ==============================
# UPDATE POST
# ==============================

def update_post(post_id, title, content, meta):
    data = {
        "title": title,
        "content": content,
        "excerpt": meta
    }

    response = requests.post(
        f"{WP_URL}/{post_id}",
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
        json=data,
        timeout=20
    )

    if response.status_code == 200:
        print(f"✅ Updated post {post_id}")
    else:
        print(f"❌ Failed update {post_id}: {response.text}")

# ==============================
# MAIN PROCESS
# ==============================

def process_posts():
    print("===== 🚀 SAFE AUTO FIX START =====")

    try:
        posts = get_posts()
    except Exception as e:
        print("❌ ERREUR CONNEXION WP:", e)
        return

    for post in posts:
        try:
            post_id = post["id"]
            title = post["title"]["rendered"]
            content = post["content"]["rendered"]

            print("\n===== ANALYSE =====")
            print("Article:", title)

            prompt = build_prompt(title, content)
            ai_response = call_openai(prompt)

            if not ai_response:
                print("❌ OpenAI failed")
                continue

            data = extract_json(ai_response)

            new_title = data.get("title", title)
            new_meta = data.get("meta", "")
            new_content = clean_html(data.get("content", content))
            new_content = limit_content(new_content)

            print("========== RESULT ==========")
            print("TITLE:", new_title)
            print("META:", new_meta[:100])
            print("CONTENT LENGTH:", len(new_content))

            update_post(post_id, new_title, new_content, new_meta)

        except Exception as e:
            print("❌ ERREUR ARTICLE:", e)

    print("\n===== ✅ AUTO FIX COMPLETE =====")

# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    process_posts()
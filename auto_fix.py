import requests
import json
import re
import time
from requests.auth import HTTPBasicAuth

# ==============================
# CONFIG
# ==============================

OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
WP_URL = "YOUR_WP_URL/wp-json/wp/v2/posts"
WP_USER = "YOUR_WP_USER"
WP_PASSWORD = "YOUR_WP_PASSWORD"

MAX_CONTENT_LENGTH = 25000

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

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
            raise ValueError("JSON not found")

def clean_html(content):
    content = content.replace("```html", "").replace("```", "")
    return content.strip()

def limit_content(content):
    if len(content) > MAX_CONTENT_LENGTH:
        return content[:MAX_CONTENT_LENGTH] + "..."
    return content

# ==============================
# OPENAI CALL
# ==============================

def call_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"

    for i in range(3):
        try:
            response = requests.post(
                url,
                headers=HEADERS,
                json={
                    "model": "gpt-5.3",
                    "messages": [
                        {"role": "system", "content": "You are a SEO expert for finance YMYL websites."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                },
                timeout=30
            )

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"Retry {i+1} failed:", e)
            time.sleep(2)

    return None

# ==============================
# SEO PROMPT
# ==============================

def build_prompt(title, content):
    return f"""
Optimize this article for SEO (RankMath 90+).

IMPORTANT:
- Keep HTML clean
- Do NOT break structure
- Add FAQ schema
- Add Article schema
- Improve readability
- Add H2/H3 structure
- Add internal linking placeholders

Return JSON ONLY:

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
        params={"per_page": 5}
    )
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
        json=data
    )

    if response.status_code == 200:
        print(f"✅ Updated post {post_id}")
    else:
        print(f"❌ Failed update {post_id}", response.text)

# ==============================
# MAIN PROCESS
# ==============================

def process_posts():
    print("===== SAFE AUTO FIX START =====")

    posts = get_posts()

    for post in posts:
        try:
            post_id = post["id"]
            title = post["title"]["rendered"]
            content = post["content"]["rendered"]

            print(f"\n===== ANALYZING =====")
            print(title)

            prompt = build_prompt(title, content)
            ai_response = call_openai(prompt)

            if not ai_response:
                print("❌ AI failed")
                continue

            data = extract_json(ai_response)

            new_title = data["title"]
            new_meta = data["meta"]
            new_content = clean_html(data["content"])
            new_content = limit_content(new_content)

            print("========== SEO RESULT ==========")
            print("NEW TITLE:", new_title)
            print("META:", new_meta)
            print("CONTENT LENGTH:", len(new_content))

            update_post(post_id, new_title, new_content, new_meta)

        except Exception as e:
            print("❌ ERROR:", e)

    print("\n===== AUTO FIX COMPLETE =====")


# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    process_posts()
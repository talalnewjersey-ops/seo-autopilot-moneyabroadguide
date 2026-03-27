import requests
import os
import base64
import time
from openai import OpenAI

# =========================
# CONFIG
# =========================
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# AUTH WORDPRESS
# =========================
def get_auth_header():
    creds = f"{WP_USER}:{WP_PASSWORD}"
    token = base64.b64encode(creds.encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }

# =========================
# GET POSTS
# =========================
def get_posts():
    try:
        url = f"{WP_URL}/wp-json/wp/v2/posts?per_page=10"
        res = requests.get(url, headers=get_auth_header(), timeout=30)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print("❌ Error fetching posts:", e)
        return []

# =========================
# UPDATE POST
# =========================
def update_post(post_id, content):
    try:
        url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
        data = {"content": content}
        res = requests.post(url, headers=get_auth_header(), json=data, timeout=30)
        return res.status_code
    except Exception as e:
        print("❌ Error updating post:", e)
        return None

# =========================
# SEO GENERATION (FIXED MODEL)
# =========================
def generate_seo(content, title):
    prompt = f"""
You are an expert SEO editor for a financial blog (USA & Canada newcomers).

GOALS:
- Improve SEO (Google ranking)
- Keep human tone (VERY IMPORTANT)
- Keep HTML structure
- Add FAQ section (3 questions)
- Add E-E-A-T trust signals
- Add 2 internal links (/usa/... /canada/...)

STRICT RULES:
- DO NOT remove HTML
- DO NOT shorten content
- DO NOT rewrite everything
- ONLY optimize and improve

ARTICLE:
TITLE: {title}
CONTENT:
{content}
"""

    for attempt in range(3):
        try:
            print(f"⏳ OpenAI attempt {attempt+1}")

            response = client.chat.completions.create(
                model="gpt-4.1-mini",  # ✅ FIXED MODEL
                messages=[{"role": "user", "content": prompt}],
                timeout=120
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ Retry {attempt+1} failed:", e)
            time.sleep(3)

    return None

# =========================
# INTERNAL LINKING AUTO
# =========================
def add_internal_links(content):
    if "/usa/" not in content:
        content += '<p>👉 Related: <a href="/usa/bank-account">Open a US Bank Account</a></p>'
    if "/canada/" not in content:
        content += '<p>👉 Related: <a href="/canada/credit-card">Build Credit in Canada</a></p>'
    return content

# =========================
# SCHEMA AUTO
# =========================
def add_schema(content, title):
    schema = f"""
<script type="application/ld+json">
{{
 "@context": "https://schema.org",
 "@type": "Article",
 "headline": "{title}",
 "author": {{
   "@type": "Person",
   "name": "Talal Eddaouahiri"
 }},
 "publisher": {{
   "@type": "Organization",
   "name": "MoneyAbroadGuide"
 }}
}}
</script>
"""
    return content + schema

# =========================
# MAIN PROCESS
# =========================
def process_posts():
    print("===== 🚀 SAFE AUTO FIX START =====")

    posts = get_posts()

    if not posts:
        print("❌ No posts found")
        return

    for post in posts:
        try:
            post_id = post["id"]
            title = post["title"]["rendered"]
            content = post["content"]["rendered"]

            print("\n===== ANALYSE =====")
            print(f"Article: {title}")

            new_content = generate_seo(content, title)

            if not new_content:
                print("❌ OpenAI failed")
                continue

            new_content = add_internal_links(new_content)
            new_content = add_schema(new_content, title)

            status = update_post(post_id, new_content)

            if status == 200:
                print("✅ Updated successfully")
            else:
                print("❌ Update failed:", status)

            time.sleep(2)

        except Exception as e:
            print("❌ Error processing post:", e)

    print("\n===== ✅ AUTO FIX COMPLETE =====")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    process_posts()
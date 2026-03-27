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
    return {"Authorization": f"Basic {token}"}

# =========================
# GET POSTS
# =========================
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts?per_page=10"
    res = requests.get(url, headers=get_auth_header())
    return res.json()

# =========================
# UPDATE POST
# =========================
def update_post(post_id, content):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    data = {"content": content}
    res = requests.post(url, headers=get_auth_header(), json=data)
    return res.status_code

# =========================
# SEO OPTIMIZATION PROMPT
# =========================
def generate_seo(content, title):
    prompt = f"""
You are an expert SEO editor for a financial blog (USA & Canada newcomers).

GOALS:
- Improve SEO (rank on Google)
- Add internal linking placeholders
- Improve readability (human tone)
- Keep HTML structure
- Add FAQ section
- Add E-E-A-T trust signals
- Keep same length (important)

RULES:
- DO NOT remove HTML
- DO NOT shorten
- DO NOT add fluff
- Add 2-3 internal links like: /usa/... or /canada/...
- Add FAQ at end (3 questions)

ARTICLE:
TITLE: {title}
CONTENT:
{content}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}],
            timeout=60
        )
        return response.choices[0].message.content
    except Exception as e:
        print("❌ OpenAI Error:", e)
        return None

# =========================
# INTERNAL LINKING AUTO
# =========================
def add_internal_links(content):
    if "USA" in content:
        content += '<p>👉 Related: <a href="/usa/bank-account">Open a US Bank Account</a></p>'
    if "Canada" in content:
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
    print("===== 🚀 SAFE AUTO FIX V2 START =====")

    posts = get_posts()

    for post in posts:
        post_id = post["id"]
        title = post["title"]["rendered"]
        content = post["content"]["rendered"]

        print(f"\n===== ANALYSE =====")
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

    print("\n===== ✅ AUTO FIX COMPLETE =====")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    process_posts()
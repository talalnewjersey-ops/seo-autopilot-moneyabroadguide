import os
import requests
import time
import json
from datetime import date
from openai import OpenAI

# =========================
# CONFIG
# =========================
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# SECURITY
# =========================
if not WP_URL.startswith("http"):
    raise Exception("WP_URL must start with https://")

# =========================
# GET ALL POSTS (PAGINATION)
# =========================
def get_all_posts():
    posts = []
    page = 1

    while True:
        url = f"{WP_URL}/wp-json/wp/v2/posts?per_page=20&page={page}"
        res = requests.get(url, auth=(WP_USER, WP_PASSWORD))

        if res.status_code != 200:
            break

        data = res.json()
        if not data:
            break

        posts.extend(data)
        page += 1

    return posts

# =========================
# UPDATE POST
# =========================
def update_post(post_id, payload):
    if DRY_RUN:
        print("🧪 DRY RUN → No update sent")
        return 200

    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    res = requests.post(url, auth=(WP_USER, WP_PASSWORD), json=payload)
    return res.status_code

# =========================
# SAFE FIXES (NO RISK)
# =========================
def safe_fixes(content):

    # remove empty blocks
    content = content.replace('<div></div>', '')

    # add disclosure if missing
    if "Disclosure:" not in content:
        disclosure = """
<div style="background:#FFFBEB;padding:12px;border:1px solid #FDE68A;margin-bottom:20px;">
<strong>Disclosure:</strong> This article may contain affiliate links. We may earn a commission at no extra cost to you.
</div>
"""
        content = disclosure + content

    return content

# =========================
# AI SEO ENGINE (SAFE)
# =========================
def optimize_with_ai(content, title):

    prompt = f"""
You are a senior SEO expert.

STRICT RULES:
- DO NOT REMOVE content
- DO NOT REDUCE length
- KEEP full article (3000+ words)
- FIX HTML issues
- REMOVE empty spaces
- MAKE ALL LINKS CLICKABLE
- ADD rel="noopener sponsored"

SEO ADD:
- Add 2 CTA blocks (green buttons)
- Improve H2/H3
- Improve readability
- Add FAQ section if missing

RETURN ONLY VALID HTML

CONTENT:
{content}
"""

    for i in range(3):
        try:
            print(f"⏳ AI attempt {i+1}")

            res = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                timeout=60
            )

            new_content = res.choices[0].message.content

            # SAFETY CHECK (CRITICAL)
            if len(new_content) < len(content) * 0.6:
                print("⚠️ AI truncated content → skipped")
                return content

            return new_content

        except Exception as e:
            print(f"❌ Retry {i+1} failed:", e)
            time.sleep(5)

    return content

# =========================
# META GENERATOR (JSON SAFE)
# =========================
def generate_meta(title, content):

    prompt = f"""
Return JSON only:

{{
"title": "SEO title max 60 chars",
"description": "meta description max 155 chars"
}}

Article:
{title}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        data = json.loads(res.choices[0].message.content)

        return data["title"], data["description"]

    except:
        return title, ""

# =========================
# MAIN PROCESS
# =========================
def process_posts():
    print("🚀 AUTOPILOT SAFE + REVENUE START\n")

    posts = get_all_posts()

    for post in posts:

        post_id = post["id"]
        title = post["title"]["rendered"]
        content = post["content"]["rendered"]

        print("==== ARTICLE ====")
        print(title)

        # BACKUP
        original_content = content

        # STEP 1 SAFE FIX
        content = safe_fixes(content)

        # STEP 2 AI
        content = optimize_with_ai(content, title)

        # STEP 3 META
        seo_title, meta_desc = generate_meta(title, content)

        payload = {
            "content": content,
            "title": seo_title,
            "meta": {
                "_rank_math_description": meta_desc
            }
        }

        status = update_post(post_id, payload)

        if status == 200:
            print("✅ Updated\n")
        else:
            print("❌ Failed\n")

        time.sleep(2)

    print("✅ AUTOPILOT COMPLETE")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    process_posts()
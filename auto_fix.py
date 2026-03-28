import os
import requests
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
# VALIDATION
# =========================
if not WP_URL or not WP_URL.startswith("http"):
    raise Exception("❌ WP_URL must start with https://")

# =========================
# WORDPRESS API
# =========================
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts?per_page=20"
    try:
        response = requests.get(url, auth=(WP_USER, WP_PASSWORD), timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        return []

def update_post(post_id, data):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    try:
        response = requests.post(
            url,
            auth=(WP_USER, WP_PASSWORD),
            json=data,
            timeout=20
        )
        return response.status_code
    except Exception as e:
        print(f"❌ Update error: {e}")
        return 500

# =========================
# SAFE FIXES (NO AI)
# =========================
def safe_fixes(content):

    # Fix http → https
    content = content.replace('href="http://', 'href="https://')

    # Remove empty sections
    content = content.replace('<div></div>', '')
    content = content.replace('<p></p>', '')

    # Fix raw URLs
    content = content.replace('www.', 'https://www.')

    # Add affiliate disclosure
    if "Disclosure:" not in content:
        content = f"""
<div style="background:#FFFBEB;padding:10px;border:1px solid #FDE68A;margin-bottom:20px;">
<strong>Disclosure:</strong> This article may contain affiliate links. We may earn a commission at no extra cost to you.
</div>
""" + content

    return content

# =========================
# AI CONTENT OPTIMIZATION
# =========================
def optimize_with_ai(content, title):

    prompt = f"""
You are a senior SEO + CRO expert.

STRICT RULES:
- DO NOT reduce content length
- KEEP full article (3000+ words)
- DO NOT remove sections
- PRESERVE structure

TASK:
- Fix HTML issues
- Remove blank spaces/sections
- Ensure ALL links clickable <a>
- Add rel="noopener sponsored" target="_blank"
- Improve headings (H2/H3)
- Improve readability
- Add CTA button sections
- Add 3 FAQ at end

OUTPUT:
Return FULL HTML only

CONTENT:
{content}
"""

    for attempt in range(3):
        try:
            print(f"⏳ OpenAI attempt {attempt+1}")

            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                timeout=60
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ Retry {attempt+1} failed: {e}")
            time.sleep(5)

    print("⚠️ OpenAI failed — fallback applied")
    return content

# =========================
# META GENERATION
# =========================
def generate_meta(title):

    prompt = f"""
Generate SEO metadata:

Title (max 60 characters)
Meta description (max 155 characters)

Topic: {title}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )

        lines = response.choices[0].message.content.split("\n")

        seo_title = lines[0].strip()
        meta_desc = lines[1].strip() if len(lines) > 1 else ""

        return seo_title, meta_desc

    except:
        return title, ""

# =========================
# SCHEMA MARKUP
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
}},
"dateModified": "2026-03-27"
}}
</script>
"""

    return content + schema

# =========================
# MAIN PROCESS
# =========================
def process_posts():

    print("🚀 FULL SEO AUTOPILOT START\n")

    posts = get_posts()

    for post in posts:

        try:
            title = post["title"]["rendered"]
            content = post["content"]["rendered"]
            post_id = post["id"]

            print(f"===== ANALYSE =====")
            print(f"Article: {title}")

            # STEP 1: SAFE FIX
            content = safe_fixes(content)

            # STEP 2: AI
            content = optimize_with_ai(content, title)

            # STEP 3: SCHEMA
            content = add_schema(content, title)

            # STEP 4: META
            seo_title, meta_desc = generate_meta(title)

            # STEP 5: UPDATE
            status = update_post(post_id, {
                "title": seo_title,
                "content": content,
                "excerpt": meta_desc
            })

            if status == 200:
                print("✅ Updated successfully\n")
            else:
                print("❌ Update failed\n")

        except Exception as e:
            print(f"❌ Error processing post: {e}")

    print("🔥 AUTO FIX COMPLETE")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    process_posts()
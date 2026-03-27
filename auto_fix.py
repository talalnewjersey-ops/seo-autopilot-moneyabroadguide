import os
import requests
import json
from openai import OpenAI

print("DEBUG KEY:", os.getenv("OPENAI_API_KEY"))
print("WP_URL:", os.getenv("WP_URL"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

print("===== SAFE AUTO FIX START =====")


# 🤖 AI SEO OPTIMIZATION
def generate_ai_fix(title, content):
    try:
        prompt = f"""
prompt = f"""
You are a professional SEO expert specialized in finance (YMYL).

Your goal:
Improve this article to reach SEO score 95+ AND Google EEAT compliance.

IMPORTANT:
- Keep HTML structure
- Do NOT remove content
- Improve it

You MUST:

1. Optimize title (max 60 characters)
2. Add meta description (150–160 characters)
3. Improve readability (short paragraphs)
4. Add H2 and H3 structure
5. Add FAQ section (3 questions)
6. Add EEAT signals:
   - Author: Talal Eddaouahiri
   - Expertise mention
   - Disclaimer
7. Improve keyword usage naturally

Return ONLY JSON:

{{
"title": "...",
"meta": "...",
"content": "FULL OPTIMIZED HTML CONTENT"
}}

Title: {title}

Content:
{content}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("❌ OPENAI ERROR:", str(e))
        return None


# 📥 GET POSTS
def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    response = requests.get(url)
    return response.json()


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


# 🔍 SEO SCORE
def seo_score(content):
    score = 0

    if "<title" in content.lower():
        score += 25
    if 'meta name="description"' in content.lower():
        score += 25
    if "alt=" in content.lower():
        score += 25
    if len(content) > 3000:
        score += 25

    print(f"SEO SCORE: {score}/100")
    return score


# 🚀 MAIN
def run():
    posts = get_posts()

    for post in posts[:1]:
        print(f"\n===== ANALYZING =====")
        print(post["title"]["rendered"])

        # BEFORE
        before = seo_score(post["content"]["rendered"])

        ai_data = generate_ai_fix(
            post["title"]["rendered"],
            post["content"]["rendered"]
        )

        if ai_data:
            print("→ AI optimization OK")

            # AFTER
            after = seo_score(ai_data["content"])

            print(f"IMPROVEMENT: {before} → {after}")

            update_post(post["id"], ai_data)
        else:
            print("→ Skipped (AI error)")


if __name__ == "__main__":
    run()

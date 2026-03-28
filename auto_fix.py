import requests
import os
from requests.auth import HTTPBasicAuth
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

def get_posts():
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    response = requests.get(url, auth=HTTPBasicAuth(WP_USER, WP_PASSWORD))
    return response.json()

def clean_ai_response(text):
    return text.replace("```html", "").replace("```", "").strip()

def generate_patch(content):
    prompt = f"""
You are a SEO editor.

IMPORTANT RULES:
- DO NOT replace the article
- DO NOT shorten content
- KEEP full original content
- ONLY improve:
  - add FAQ at end
  - add internal links
  - improve readability

CONTENT:
{content}

Return FULL improved HTML.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        timeout=60
    )

    return clean_ai_response(response.choices[0].message.content)

def update_post(post_id, new_content):
    url = f"{WP_URL}/wp-json/wp/v2/posts/{post_id}"
    requests.post(
        url,
        auth=HTTPBasicAuth(WP_USER, WP_PASSWORD),
        json={"content": new_content}
    )

def process_posts():
    print("🚀 SAFE PATCH MODE START\n")

    posts = get_posts()

    for post in posts:
        print(f"Processing: {post['title']['rendered']}")

        original_content = post["content"]["rendered"]

        # 🔒 sécurité : skip si contenu trop court
        if len(original_content) < 2000:
            print("⚠️ Skipped (too short or broken)")
            continue

        try:
            new_content = generate_patch(original_content)

            # 🔒 sécurité : vérifier qu'on ne perd pas du contenu
            if len(new_content) < len(original_content) * 0.9:
                print("❌ Rejected (content shrink detected)")
                continue

            update_post(post["id"], new_content)

            print("✅ Updated safely\n")

        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    process_posts()
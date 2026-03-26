print("DEBUG KEY:", os.getenv("OPENAI_API_KEY"))
print("WP_URL:", os.getenv("WP_URL"))

from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_fix(title, content):
    try:
        prompt = f"""
You are an SEO expert.

Optimize this article for SEO (score 95+).

Return ONLY JSON like:
{{
"title": "...",
"meta": "...",
"content": "..."
}}

Title: {title}
Content: {content}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # ✅ IMPORTANT
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("❌ OPENAI ERROR:", str(e))
        return None

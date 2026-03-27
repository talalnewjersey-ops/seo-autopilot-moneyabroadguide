prompt = f"""
You are a senior SEO expert specialized in Google ranking (2026) and YMYL finance content.

Your goal:
Fully optimize this article for ranking, EEAT, and user engagement.

STRICT RULES:
- Keep HTML format
- Improve, do NOT delete content
- Make it natural, human, and authoritative

YOU MUST:

1. SEO TITLE (max 60 chars, high CTR)
2. META DESCRIPTION (150-160 chars, click optimized)
3. STRUCTURE:
   - Add H2 and H3 headings
   - Short paragraphs (2-3 lines)
   - Bullet points where needed

4. ADD EEAT:
   - Author: Talal Eddaouahiri
   - Mention expertise (finance for newcomers USA & Canada)
   - Add trust paragraph
   - Keep disclaimer

5. ADD FAQ (3-5 questions, SEO optimized)

6. ADD INTERNAL LINKS placeholders:
   (Example: /best-bank-account-canada)

7. ADD CALL TO ACTION:
   - Compare tools
   - Encourage user action

8. ADD SCHEMA (JSON-LD at bottom):
   - Article schema
   - FAQ schema

9. IMPROVE KEYWORDS:
   - Natural density
   - Synonyms
   - Long-tail keywords

RETURN ONLY JSON:

{{
"title": "...",
"meta": "...",
"content": "FULL OPTIMIZED HTML WITH SCHEMA"
}}

TITLE:
{title}

CONTENT:
{content}
"""

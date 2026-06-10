import os
import requests
import base64
import json
import time

# ============================================================
# CONFIGURATION
# ============================================================
WP_URL = os.getenv("WP_URL", "https://moneyabroadguide.com")
WP_USER = os.getenv("WP_USER", "")
WP_PASSWORD = os.getenv("WP_PASSWORD", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

password = WP_APP_PASSWORD if WP_APP_PASSWORD else WP_PASSWORD
credentials = f"{WP_USER}:{password}"
token = base64.b64encode(credentials.encode()).decode()
WP_HEADERS = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "User-Agent": "MAG-Content-Pipeline/2.0"
}

ARTICLES = [
    {
        "title": "Health Insurance for New Immigrants in the USA (2026)",
        "slug": "health-insurance-new-immigrants-usa-2026",
        "focus_keyword": "health insurance for new immigrants USA",
        "country": "USA",
        "category_slug": "usa",
    },
    {
        "title": "Car Insurance for New Immigrants in the USA (2026)",
        "slug": "car-insurance-new-immigrants-usa-2026",
        "focus_keyword": "car insurance for new immigrants USA",
        "country": "USA",
        "category_slug": "usa",
    },
    {
        "title": "How to Build Credit in Canada From Zero (2026)",
        "slug": "how-to-build-credit-canada-from-zero-2026",
        "focus_keyword": "how to build credit in Canada from zero",
        "country": "Canada",
        "category_slug": "canada",
    },
    {
        "title": "Health Insurance for Newcomers to Canada (2026)",
        "slug": "health-insurance-newcomers-canada-2026",
        "focus_keyword": "health insurance newcomers Canada",
        "country": "Canada",
        "category_slug": "canada",
    },
]

# ============================================================
# STEP 1: AUTHENTICATION PREFLIGHT
# ============================================================
print("=" * 70)
print("STEP 1: AUTHENTICATION PREFLIGHT")
print("=" * 70)

r = requests.get(
    f"{WP_URL}/wp-json/wp/v2/users/me?context=edit",
    headers=WP_HEADERS,
    timeout=30
)
print(f"GET /users/me: HTTP {r.status_code}")
if r.status_code != 200:
    print(f"PREFLIGHT FAILED: {r.text[:300]}")
    exit(1)

user = r.json()
print(f"Authenticated as: {user.get('name')}")
print(f"Username: {user.get('username')}")
print(f"Role: {user.get('roles')}")
print(f"User ID: {user.get('id')}")
print("PREFLIGHT: PASSED")

# ============================================================
# STEP 2: BACKUP AND DELETE EXISTING DRAFTS
# ============================================================
print()
print("=" * 70)
print("STEP 2: BACKUP AND DELETE EXISTING DRAFTS")
print("=" * 70)

def get_all_drafts():
    drafts = []
    page = 1
    while True:
        r = requests.get(
            f"{WP_URL}/wp-json/wp/v2/posts?status=draft&per_page=100&page={page}",
            headers=WP_HEADERS,
            timeout=30
        )
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        drafts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return drafts

existing_drafts = get_all_drafts()
print(f"Found {len(existing_drafts)} existing drafts")

backup = []
for d in existing_drafts:
    backup.append({
        "id": d.get("id"),
        "title": d.get("title", {}).get("rendered", ""),
        "status": d.get("status"),
        "date": d.get("date"),
        "slug": d.get("slug"),
    })

with open("drafts_backup.json", "w") as f:
    json.dump(backup, f, indent=2)

print(f"Backup saved: drafts_backup.json ({len(backup)} drafts)")

deleted_count = 0
for d in existing_drafts:
    did = d.get("id")
    dr = requests.delete(
        f"{WP_URL}/wp-json/wp/v2/posts/{did}?force=true",
        headers=WP_HEADERS,
        timeout=30
    )
    if dr.status_code in [200, 204, 410]:
        deleted_count += 1
        print(f"  Deleted draft ID {did}: {d.get('title',{}).get('rendered','')[:60]}")
    else:
        print(f"  Failed to delete {did}: HTTP {dr.status_code}")

print(f"Deleted {deleted_count}/{len(existing_drafts)} drafts")

# ============================================================
# STEP 3: GENERATE ARTICLES VIA OPENAI
# ============================================================
print()
print("=" * 70)
print("STEP 3: GENERATING 4 ARTICLES VIA OPENAI GPT-4o")
print("=" * 70)

def call_openai(prompt, model="gpt-4o", max_tokens=16000):
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set")
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": """You are the lead content strategist for MoneyAbroadGuide.com, a top-ranked personal finance website helping immigrants and newcomers navigate financial systems in the USA and Canada. You write authoritative, deeply researched, SEO-optimized articles in HTML format (WordPress-ready). Your writing style is warm, practical, and empathetic — you understand the challenges immigrants face. Articles must be 4000-5000+ words, comprehensive, and fully formatted for WordPress."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=300
    )
    
    if r.status_code != 200:
        print(f"OpenAI error: {r.status_code} - {r.text[:300]}")
        return None
    
    return r.json()["choices"][0]["message"]["content"]


def build_article_prompt(article):
    title = article["title"]
    keyword = article["focus_keyword"]
    country = article["country"]
    
    if country == "USA":
        country_context = "United States of America"
        internal_links = """
- /best-bank-account-immigrants-usa/
- /how-to-build-credit-usa-immigrants/
- /itin-number-immigrants-usa/
- /remittance-money-transfer-usa/"""
        authoritative_sources = """
- Healthcare.gov (official ACA marketplace)
- CMS.gov (Centers for Medicare & Medicaid Services)
- KFF.org (Kaiser Family Foundation health policy research)
- USCIS.gov
- Insurance Information Institute (iii.org)
- NAIC.org (National Association of Insurance Commissioners)"""
    else:
        country_context = "Canada"
        internal_links = """
- /best-bank-accounts-newcomers-canada/
- /how-to-build-credit-score-canada/
- /send-money-canada/
- /student-banking-canada/"""
        authoritative_sources = """
- Canada.ca (Government of Canada official website)
- CMHC.ca (Canada Mortgage and Housing Corporation)
- Financial Consumer Agency of Canada (FCAC)
- OHIP / Provincial health ministry websites
- Equifax Canada / TransUnion Canada
- Insurance Bureau of Canada (ibc.ca)"""

    prompt = f"""Write a comprehensive, SEO-optimized WordPress article for MoneyAbroadGuide.com with the following specifications:

TITLE: {title}
FOCUS KEYWORD: {keyword}
TARGET COUNTRY: {country_context}
MINIMUM WORD COUNT: 4,500 words
FORMAT: Full HTML (WordPress Gutenberg-compatible)

MANDATORY STRUCTURE (in this exact order):

1. **SEO META** (as HTML comment):
<!-- 
SEO Title: {title} | MoneyAbroadGuide
Meta Description: [150-160 char description with focus keyword]
Focus Keyword: {keyword}
-->

2. **KEY TAKEAWAYS BOX** (styled div):
<div class="key-takeaways-box" style="background:#f0f7ff;border-left:4px solid #0066cc;padding:20px;margin:20px 0;">
<h3>Key Takeaways</h3>
<ul>[5-7 critical takeaways for newcomers]</ul>
</div>

3. **INTRODUCTION** (300+ words):
- Hook with the immigrant experience struggle
- Address the exact pain point
- Promise what article covers
- Include focus keyword naturally in first 100 words

4. **TWO REALISTIC NEWCOMER STORIES** (400+ words total):
Create vivid, realistic stories of 2 immigrants (different backgrounds/countries of origin):
- Story 1: [Name], recently arrived, faces specific challenge
- Story 2: [Name], has been in {country} 6 months, overcame obstacle
Use <blockquote> tags with styling

5. **MAIN BODY SECTIONS** (8-12 H2 sections with H3 subsections):
Each section minimum 300 words. Cover:
- What newcomers need to know first
- Eligibility and requirements
- Step-by-step process
- Best options available (with specific names, companies, programs)
- Costs and what to expect
- Common mistakes to avoid
- Tips from experienced immigrants
- Recent changes for 2026

6. **COMPARISON TABLE** (HTML table with proper styling):
Compare at least 5 specific options with columns: Provider/Option | Best For | Cost | Requirements | Rating
Style: alternating row colors, professional appearance

7. **PROS AND CONS TABLE**:
Two-column table comparing pros vs cons

8. **FAQ SECTION** (8-10 questions):
Use schema-ready format:
<div class="faq-section">
<h2>Frequently Asked Questions</h2>
[Q&A format with <details>/<summary> or styled divs]
</div>
Focus on actual questions newcomers search for

9. **IMAGE PLACEHOLDERS** (8+ throughout article):
Format:
<!-- IMAGE PLACEHOLDER
Alt text: [descriptive alt text with keyword]
Caption: [caption]
Suggested image: [detailed AI image generation prompt - be specific about scene, people, setting]
Size: [recommended dimensions]
-->

10. **INFOGRAPHIC PLACEHOLDER**:
<!-- INFOGRAPHIC PLACEHOLDER
Title: [title]
Data to visualize: [list 5-7 data points]
Style: [description]
-->

11. **COMPARISON CHART PLACEHOLDER**:
<!-- COMPARISON CHART PLACEHOLDER
Type: [bar/line/pie]
Title: [title]
Data: [specific data points]
-->

12. **DATA VISUALIZATION PLACEHOLDER**:
<!-- DATA VISUALIZATION PLACEHOLDER
Title: [title]
Data: [specific statistics]
-->

13. **INTERNAL LINKS** (naturally integrated):
Use these paths:{internal_links}

14. **EXTERNAL AUTHORITATIVE SOURCES** (in-text citations + reference list):
Link to:{authoritative_sources}

15. **CONCLUSION** (200+ words):
- Summarize key points
- Call to action
- Encouragement for the newcomer journey

WRITING REQUIREMENTS:
- Empathetic, warm tone that speaks directly to immigrants
- Use "you" and "your" frequently
- Include specific dollar amounts, percentages, timelines
- Reference 2026 current information
- Use transition words for readability
- Short paragraphs (3-4 sentences max)
- Include statistics with sources
- Rank Math SEO score target: 95+
- Featured snippet optimized (answer questions in first 40-60 words of H2 sections)
- Natural keyword density: 1.5-2.5%

IMPORTANT: Output ONLY the complete HTML content. No preamble, no explanation. Start with the SEO meta comment and end with the conclusion."""

    return prompt


def post_to_wordpress(article, content):
    title = article["title"]
    slug = article["slug"]
    
    word_count = len(content.split())
    
    data = {
        "title": title,
        "slug": slug,
        "content": content,
        "status": "draft",
        "meta": {
            "rank_math_focus_keyword": article["focus_keyword"],
            "_yoast_wpseo_focuskw": article["focus_keyword"],
        }
    }
    
    r = requests.post(
        f"{WP_URL}/wp-json/wp/v2/posts",
        headers=WP_HEADERS,
        json=data,
        timeout=60
    )
    
    if r.status_code in [200, 201]:
        post = r.json()
        return {
            "success": True,
            "draft_id": post.get("id"),
            "draft_url": post.get("link"),
            "title": title,
            "word_count": word_count,
            "status": post.get("status"),
            "http_status": r.status_code,
        }
    else:
        return {
            "success": False,
            "title": title,
            "error": r.text[:500],
            "http_status": r.status_code,
        }


# ============================================================
# EXECUTE PIPELINE
# ============================================================
results = []

for i, article in enumerate(ARTICLES):
    print()
    print(f"--- ARTICLE {i+1}/4: {article['title']} ---")
    print(f"Generating with OpenAI GPT-4o...")
    
    prompt = build_article_prompt(article)
    
    content = call_openai(prompt)
    
    if not content:
        print(f"FAILED to generate content for: {article['title']}")
        results.append({
            "success": False,
            "title": article["title"],
            "error": "OpenAI generation failed",
        })
        continue
    
    word_count = len(content.split())
    print(f"Content generated: {word_count} words")
    
    print(f"Posting to WordPress as draft...")
    result = post_to_wordpress(article, content)
    results.append(result)
    
    if result["success"]:
        print(f"DRAFT SAVED:")
        print(f"  Title: {result['title']}")
        print(f"  Draft ID: {result['draft_id']}")
        print(f"  Draft URL: {result['draft_url']}")
        print(f"  Word Count: {result['word_count']}")
        print(f"  Status: {result['status']}")
        print(f"  HTTP: {result['http_status']}")
    else:
        print(f"FAILED: HTTP {result['http_status']}")
        print(f"Error: {result.get('error', 'unknown')[:200]}")
    
    if i < len(ARTICLES) - 1:
        print("Waiting 3s before next article...")
        time.sleep(3)

# ============================================================
# FINAL REPORT
# ============================================================
print()
print("=" * 70)
print("FINAL PIPELINE REPORT")
print("=" * 70)

success_count = sum(1 for r in results if r.get("success"))
print(f"Articles generated: {success_count}/{len(ARTICLES)}")
print()

for i, result in enumerate(results):
    print(f"ARTICLE {i+1}: {result.get('title', 'Unknown')[:60]}")
    if result.get("success"):
        print(f"  Status: SAVED AS DRAFT")
        print(f"  Draft ID: {result.get('draft_id')}")
        print(f"  Draft URL: {result.get('draft_url')}")
        print(f"  Word Count: {result.get('word_count')}")
        print(f"  HTTP Status: {result.get('http_status')}")
    else:
        print(f"  Status: FAILED")
        print(f"  Error: {result.get('error', 'unknown')[:100]}")
    print()

if success_count == len(ARTICLES):
    print("ALL 4 ARTICLES SUCCESSFULLY SAVED AS WORDPRESS DRAFTS")
else:
    print(f"WARNING: Only {success_count}/{len(ARTICLES)} articles saved")
    exit(1)

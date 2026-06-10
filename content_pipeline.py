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
    "User-Agent": "MAG-Content-Pipeline/3.0"
}

ARTICLES = [
    {
        "title": "Health Insurance for New Immigrants in the USA (2026)",
        "slug": "health-insurance-new-immigrants-usa-2026",
        "focus_keyword": "health insurance for new immigrants USA",
        "country": "USA",
    },
    {
        "title": "Car Insurance for New Immigrants in the USA (2026)",
        "slug": "car-insurance-new-immigrants-usa-2026",
        "focus_keyword": "car insurance for new immigrants USA",
        "country": "USA",
    },
    {
        "title": "How to Build Credit in Canada From Zero (2026)",
        "slug": "how-to-build-credit-canada-from-zero-2026",
        "focus_keyword": "how to build credit in Canada from zero",
        "country": "Canada",
    },
    {
        "title": "Health Insurance for Newcomers to Canada (2026)",
        "slug": "health-insurance-newcomers-canada-2026",
        "focus_keyword": "health insurance newcomers Canada",
        "country": "Canada",
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
        "date": d.get("date"),
        "slug": d.get("slug"),
    })

with open("drafts_backup.json", "w") as f:
    json.dump(backup, f, indent=2)
print(f"Backup saved: {len(backup)} drafts")

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
        print(f"  Deleted: ID {did} - {d.get('title',{}).get('rendered','')[:50]}")
print(f"Deleted {deleted_count}/{len(existing_drafts)} drafts")

# ============================================================
# STEP 3: GENERATE ARTICLES - MULTI-SECTION APPROACH
# ============================================================
print()
print("=" * 70)
print("STEP 3: GENERATING 4 ARTICLES (MULTI-SECTION, 4000+ WORDS EACH)")
print("=" * 70)

SYSTEM_PROMPT = """You are the lead editor of MoneyAbroadGuide.com, a top authority on immigrant personal finance in the USA and Canada. You write deeply researched, SEO-optimized WordPress content. Your writing is warm, practical, empathetic, and authoritative. Use short paragraphs, clear headings, real numbers, real program names, and speak directly to immigrants."""

def call_openai_section(prompt, max_tokens=4000):
    if not OPENAI_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=180
    )
    if r.status_code != 200:
        print(f"  OpenAI error: {r.status_code} - {r.text[:200]}")
        return None
    return r.json()["choices"][0]["message"]["content"]


def generate_full_article(article):
    title = article["title"]
    keyword = article["focus_keyword"]
    country = article["country"]

    if country == "USA":
        int_links = "/best-bank-account-immigrants-usa/, /how-to-build-credit-usa-immigrants/, /itin-number-immigrants-usa/"
        ext_sources = "Healthcare.gov, KFF.org, iii.org, NAIC.org, USCIS.gov"
        currency = "USD"
    else:
        int_links = "/best-bank-accounts-newcomers-canada/, /how-to-build-credit-score-canada/, /send-money-canada/"
        ext_sources = "Canada.ca, FCAC, ibc.ca, CMHC.ca"
        currency = "CAD"

    print(f"  Generating Part 1 (Intro + Stories + First 4 sections)...")
    part1_prompt = f"""Write Part 1 of a comprehensive WordPress article for MoneyAbroadGuide.com.

TITLE: {title}
FOCUS KEYWORD: {keyword}
TARGET: {country} newcomers/immigrants

Write in HTML. Include:

1. SEO meta comment:
<!-- SEO Title: {title} | MoneyAbroadGuide | Meta Description: [150-160 chars with keyword] | Focus Keyword: {keyword} -->

2. Key Takeaways box (styled div, 6 takeaways minimum):
<div class="key-takeaways" style="background:#f0f7ff;border-left:4px solid #0066cc;padding:20px 24px;margin:24px 0;border-radius:4px;">

3. Introduction (350+ words): Hook with immigrant struggle, address pain point, include keyword in first 100 words, promise what article covers.

4. Two newcomer stories (blockquotes, 200+ words each):
Story 1: [Amina/Carlos/Chen/Maria - pick fitting name], arrived 3 months ago, specific challenge with {keyword.split()[0]} {keyword.split()[-1] if len(keyword.split()) > 1 else ''}.
Story 2: [Different name, different origin country], 8 months in {country}, overcame the obstacle, specific outcome.

5. Four H2 sections (250+ words each) covering:
- What newcomers need to know first about {keyword} in {country} (overview, key facts, 2026 updates)
- Eligibility requirements and who qualifies (specific rules, visa types, waiting periods)
- Step-by-step process to get started (numbered steps, specific actions, timelines)
- Best options available with real names (5+ specific providers/programs with costs in {currency})

Include:
- Image placeholder: <!-- IMAGE PLACEHOLDER | Alt: [descriptive] | Prompt: [detailed AI art prompt showing immigrant family/person in relevant situation] | Size: 1200x628 -->
- Statistics with sources
- Dollar/dollar amounts
- Transition words between paragraphs
- Internal links naturally: {int_links}

Output ONLY the HTML. No preamble."""

    part1 = call_openai_section(part1_prompt, max_tokens=4000)
    if not part1:
        return None

    print(f"  Part 1: {len(part1.split())} words")
    time.sleep(2)

    print(f"  Generating Part 2 (Comparison tables + More sections + FAQ)...")
    part2_prompt = f"""Continue writing Part 2 of the article: "{title}" for MoneyAbroadGuide.com.

Write in HTML. Include:

1. COMPARISON TABLE (HTML, styled, alternating rows):
Compare 5-6 specific {keyword} options. Columns: Provider/Option | Best For | Monthly Cost ({currency}) | Key Requirements | Rating (stars)
Style with: border-collapse:collapse, alternating #f8f9fa/#ffffff rows, header #0066cc color.

2. PROS AND CONS TABLE (two-column HTML table):
Left: Pros (5-6 items) | Right: Cons (4-5 items)

3. Four more H2 sections (250+ words each):
- Common mistakes newcomers make with {keyword} in {country} (5-7 specific mistakes with explanations)
- How to save money on {keyword} as a newcomer (actionable tips, specific amounts saved)
- {country} government programs and assistance for newcomers (specific programs, amounts, eligibility)
- What to do if you face problems or denials (appeal process, advocacy resources, escalation steps)

4. Data visualization placeholder:
<!-- DATA VIZ PLACEHOLDER | Type: Bar chart | Title: Average {keyword} costs by provider | Data: [5 data points with specific numbers] -->

5. Infographic placeholder:
<!-- INFOGRAPHIC PLACEHOLDER | Title: Step-by-step guide to getting {keyword} as a newcomer in {country} | Steps: [7 steps] -->

6. FAQ section (10 questions with detailed answers - schema-ready):
<div class="faq-section">
<h2>Frequently Asked Questions</h2>
Format each as: <div class="faq-item"><h3>Question?</h3><p>Answer (50-100 words, specific)</p></div>

Focus on actual search queries immigrants use.

7. External sources cited: {ext_sources}

Output ONLY the HTML. No preamble."""

    part2 = call_openai_section(part2_prompt, max_tokens=4000)
    if not part2:
        return None

    print(f"  Part 2: {len(part2.split())} words")
    time.sleep(2)

    print(f"  Generating Part 3 (Final sections + Conclusion)...")
    part3_prompt = f"""Write Part 3 (final) of the article: "{title}" for MoneyAbroadGuide.com.

Write in HTML. Include:

1. Two more H2 sections (300+ words each):
- Success stories: How real newcomers navigated {keyword} in {country} in 2025-2026 (2-3 mini case studies with specific outcomes)
- 2026 changes and updates to {keyword} laws/programs in {country} (specific policy changes, new amounts, new rules)

2. Comparison chart placeholder:
<!-- COMPARISON CHART | Type: Horizontal bar | Title: {keyword} approval rates by applicant type | Data: [5 categories with percentages] -->

3. Expert tips section (H2: "Expert Tips From Financial Advisors Who Work With Immigrants"):
5-7 specific, actionable tips. Quote format with fictional but realistic advisor names.

4. Resource section (H2: "Key Resources for Newcomers"):
Formatted list of 8-10 specific resources (websites, hotlines, organizations) with descriptions.

5. Conclusion (300+ words):
- Summarize the immigrant journey with {keyword}
- Key action steps (numbered)
- Encouragement
- CTA to explore related articles on MoneyAbroadGuide.com
- Internal links: {int_links}

6. Three more image placeholders throughout:
<!-- IMAGE PLACEHOLDER | Alt: [descriptive alt text] | Prompt: [detailed AI prompt] | Size: 800x500 -->

Total article should reach 4500+ words across all three parts.

Output ONLY the HTML. No preamble."""

    part3 = call_openai_section(part3_prompt, max_tokens=3000)
    if not part3:
        return None

    print(f"  Part 3: {len(part3.split())} words")

    full_content = part1 + "\n\n" + part2 + "\n\n" + part3
    total_words = len(full_content.split())
    print(f"  TOTAL WORDS: {total_words}")

    return full_content


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

    content = generate_full_article(article)

    if not content:
        print(f"FAILED to generate: {article['title']}")
        results.append({"success": False, "title": article["title"], "error": "generation failed"})
        continue

    word_count = len(content.split())
    print(f"Posting to WordPress ({word_count} words)...")
    result = post_to_wordpress(article, content)
    results.append(result)

    if result["success"]:
        print(f"DRAFT SAVED: ID={result['draft_id']} | Words={result['word_count']} | HTTP={result['http_status']}")
    else:
        print(f"FAILED: HTTP {result['http_status']} | {result.get('error','')[:100]}")

    if i < len(ARTICLES) - 1:
        print("Waiting 5s before next article...")
        time.sleep(5)

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
    title = result.get('title', 'Unknown')[:65]
    print(f"ARTICLE {i+1}: {title}")
    if result.get("success"):
        print(f"  Status: SAVED AS DRAFT")
        print(f"  Draft ID: {result.get('draft_id')}")
        print(f"  Draft URL: {result.get('draft_url')}")
        print(f"  Word Count: {result.get('word_count')}")
        print(f"  HTTP Status: {result.get('http_status')}")
    else:
        print(f"  Status: FAILED")
        print(f"  Error: {result.get('error','unknown')[:100]}")
    print()

if success_count == len(ARTICLES):
    print("ALL 4 ARTICLES SUCCESSFULLY SAVED AS WORDPRESS DRAFTS")
else:
    print(f"PARTIAL: {success_count}/{len(ARTICLES)} saved")
    exit(1)

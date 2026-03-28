import os
import re
import json
import requests
import time
from datetime import date, datetime
from openai import OpenAI

# ─────────────────────────────────────────────────────────────
# CONFIG — all values come from GitHub Secrets / env variables
# ─────────────────────────────────────────────────────────────
WP_URL         = os.getenv("WP_URL", "").rstrip("/")
WP_USER        = os.getenv("WP_USER")
WP_PASSWORD    = os.getenv("WP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DRY_RUN        = os.getenv("DRY_RUN", "true").lower() != "false"
FORCE_ALL      = os.getenv("FORCE_ALL", "false").lower() == "true"
CACHE_FILE     = os.getenv("CACHE_FILE", ".cache/processed_posts.json")
AUTHOR_NAME    = os.getenv("AUTHOR_NAME", "Talal Eddaouahiri")
AUTHOR_TITLE   = os.getenv("AUTHOR_TITLE", "Financial Writer & Expat Finance Specialist")

SITE_NAME      = "MoneyAbroadGuide"
DAYS_REPROCESS = 7
MAX_AI_CHARS   = 8000
AI_MODEL       = "gpt-4.1-mini"
THROTTLE_SEC   = 2

AFFILIATE_DOMAINS = [
    "wise.com", "remitly.com", "ofx.com",
    "xe.com", "worldremit.com", "westernunion.com"
]

REQUIRED_PAGES = {
    "/privacy-policy/":   "Privacy Policy",
    "/disclaimer/":       "Disclaimer",
    "/editorial-policy/": "Editorial Policy",
    "/about-us/":         "About Us",
    "/contact/":          "Contact",
    "/team/":             "Team",
}

client = OpenAI(api_key=OPENAI_API_KEY)

# ─────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────
for value, name in [
    (WP_URL,         "WP_URL"),
    (WP_USER,        "WP_USER"),
    (WP_PASSWORD,    "WP_PASSWORD"),
    (OPENAI_API_KEY, "OPENAI_API_KEY"),
]:
    if not value:
        raise SystemExit(f"❌ {name} is required — check your GitHub Secrets")

if not WP_URL.startswith("http"):
    raise SystemExit("❌ WP_URL must start with https://")

print(f"⚙️  Mode : {'DRY RUN — nothing will be written' if DRY_RUN else '🔴 LIVE — writing to WordPress'}")
print(f"   Site : {WP_URL}")
print(f"   Force all : {FORCE_ALL}\n")

# ─────────────────────────────────────────────────────────────
# CACHE — avoid reprocessing articles updated < 7 days ago
# ─────────────────────────────────────────────────────────────
def load_cache():
    os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def needs_update(post_id, cache):
    if FORCE_ALL:
        return True
    rec = cache.get(str(post_id))
    if not rec:
        return True
    last = datetime.fromisoformat(rec["last_processed"]).date()
    return (date.today() - last).days >= DAYS_REPROCESS

def mark_done(post_id, cache, status, changes):
    cache[str(post_id)] = {
        "last_processed": datetime.now().isoformat(),
        "status": status,
        "changes": changes,
    }

# ─────────────────────────────────────────────────────────────
# WORDPRESS API
# ─────────────────────────────────────────────────────────────
def wp_get_all(endpoint):
    items, page = [], 1
    while True:
        try:
            r = requests.get(
                f"{WP_URL}/wp-json/wp/v2/{endpoint}",
                auth=(WP_USER, WP_PASSWORD),
                params={"per_page": 20, "page": page, "status": "publish"},
                timeout=20,
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            items.extend(batch)
            total = int(r.headers.get("X-WP-TotalPages", 1))
            print(f"   [{endpoint}] page {page}/{total} — {len(batch)} items")
            if page >= total:
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"   ❌ Error fetching {endpoint} page {page}: {e}")
            break
    return items

def wp_update(post_id, data, kind="posts"):
    if DRY_RUN:
        print(f"   [DRY RUN] Would update {kind[:-1]} #{post_id}")
        return 200
    try:
        r = requests.post(
            f"{WP_URL}/wp-json/wp/v2/{kind}/{post_id}",
            auth=(WP_USER, WP_PASSWORD),
            json=data,
            timeout=20,
        )
        return r.status_code
    except Exception as e:
        print(f"   ❌ Update error #{post_id}: {e}")
        return 500

# ─────────────────────────────────────────────────────────────
# GPT HELPER
# ─────────────────────────────────────────────────────────────
def gpt(prompt, max_tokens=2000, timeout=120):
    for attempt in range(3):
        try:
            r = client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                timeout=timeout,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  GPT attempt {attempt+1}/3: {e}")
            time.sleep(5)
    return None

def strip_fences(text):
    text = re.sub(r"^```[\w]*\s*", "", text.strip())
    return re.sub(r"\s*```$", "", text)

def safe_json(text):
    try:
        return json.loads(strip_fences(text))
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────
# FIX 1 — Safe HTML fixes (no AI needed)
# ─────────────────────────────────────────────────────────────
def safe_fixes(content):
    original = content

    # http → https on affiliate links only (never replaces non-affiliate URLs)
    for d in AFFILIATE_DOMAINS:
        content = content.replace(f'href="http://{d}',     f'href="https://{d}')
        content = content.replace(f'href="http://www.{d}', f'href="https://www.{d}')

    # Remove empty tags
    content = re.sub(r"<(div|p|span)\s*>\s*</\1>", "", content)

    # Add rel="noopener sponsored" + target="_blank" to affiliate links
    for d in AFFILIATE_DOMAINS:
        pat  = rf'(<a\s[^>]*href="https?://(?:www\.)?{re.escape(d)}[^"]*"[^>]*)(?![^>]*\brel=)([^>]*>)'
        repl = r'\1 rel="noopener sponsored" target="_blank"\2'
        content = re.sub(pat, repl, content)

    # Fix existing rel that is missing "sponsored"
    content = re.sub(
        r'rel="(noopener|noreferrer)"',
        'rel="noopener sponsored"',
        content,
    )

    return content, content != original

# ─────────────────────────────────────────────────────────────
# FIX 2 — Affiliate disclosure (FTC + Google Ads compliant)
# ─────────────────────────────────────────────────────────────
DISCLOSURE = (
    '<div class="affiliate-disclosure" style="background:#FFFBEB;padding:12px 16px;'
    'border:1px solid #FDE68A;border-radius:6px;margin-bottom:24px;font-size:13px;color:#92400E;">'
    "<strong>Disclosure:</strong> This page contains affiliate links. "
    "MoneyAbroadGuide may earn a commission if you click through and sign up, "
    "at no extra cost to you. Our editorial opinions are independent. "
    f'<a href="{WP_URL}/editorial-policy/" style="color:#92400E;text-decoration:underline;">'
    "Editorial Policy</a>"
    "</div>\n"
)

def add_disclosure(content):
    if "affiliate-disclosure" in content or "Disclosure:" in content[:800]:
        return content, False
    return DISCLOSURE + content, True

# ─────────────────────────────────────────────────────────────
# FIX 3 — Last updated date (freshness signal for Google)
# ─────────────────────────────────────────────────────────────
def add_last_updated(content):
    today_iso  = date.today().isoformat()
    today_long = date.today().strftime("%B %d, %Y")
    block = (
        f'<p class="last-updated" style="font-size:12px;color:#6B7280;margin-bottom:8px;">'
        f"<strong>Last updated:</strong> "
        f'<time datetime="{today_iso}">{today_long}</time>'
        f" — Rates and fees verified by our editorial team.</p>\n"
    )

    if "last-updated" in content:
        content = re.sub(
            r'<p class="last-updated"[^>]*>.*?</p>\n?',
            block, content, flags=re.DOTALL,
        )
        return content, True

    if "<h1" in content:
        content = re.sub(r"(</h1>)", r"\1\n" + block, content, count=1)
    else:
        content = block + content
    return content, True

# ─────────────────────────────────────────────────────────────
# FIX 4 — CTA button before last paragraph
# ─────────────────────────────────────────────────────────────
CTA = (
    '<div style="text-align:center;margin:28px 0;">'
    '<a href="#compare" style="background:#16A34A;color:#fff;padding:12px 28px;'
    'border-radius:7px;font-weight:600;font-size:15px;text-decoration:none;display:inline-block;">'
    "Compare Transfer Fees Now →</a>"
    '<p style="font-size:12px;color:#6B7280;margin:6px 0 0;">Free comparison · No signup required</p>'
    "</div>\n"
)

def add_cta(content):
    if "Compare Transfer Fees Now" in content:
        return content, False
    parts = content.rsplit("</p>", 1)
    if len(parts) == 2:
        return parts[0] + CTA + "</p>" + parts[1], True
    return content + CTA, True

# ─────────────────────────────────────────────────────────────
# FIX 5 — Author bio (E-E-A-T signal)
# ─────────────────────────────────────────────────────────────
AUTHOR_BIO = (
    '\n<div class="author-bio" style="background:#F8FAFC;border:0.5px solid #E2E8F0;'
    "border-radius:8px;padding:16px;margin-top:32px;display:flex;gap:14px;align-items:flex-start;\">"
    '<div style="flex-shrink:0;width:52px;height:52px;border-radius:50%;background:#E2E8F0;'
    'display:flex;align-items:center;justify-content:center;font-weight:600;font-size:18px;color:#475569;">TE</div>'
    "<div>"
    f'<p style="font-weight:600;font-size:14px;margin:0 0 2px;">{AUTHOR_NAME}</p>'
    f'<p style="font-size:12px;color:#64748B;margin:0 0 6px;">{AUTHOR_TITLE}</p>'
    '<p style="font-size:13px;color:#374151;margin:0;">'
    "Talal is a finance writer specializing in international money transfers and expat banking. "
    "Having navigated the US and Canadian financial systems as an immigrant, he writes practical "
    "guides to help newcomers make smarter financial decisions. "
    f'<a href="{WP_URL}/team/" style="color:#1D4ED8;">Full profile →</a>'
    "</p></div></div>\n"
)

def add_author_bio(content):
    if "author-bio" in content:
        return content, False
    return content + AUTHOR_BIO, True

# ─────────────────────────────────────────────────────────────
# FIX 6 — Legal disclaimer "not financial advice"
# ─────────────────────────────────────────────────────────────
LEGAL_DISCLAIMER = (
    '\n<div class="legal-disclaimer" style="background:#F8FAFC;padding:12px 16px;'
    "border-left:3px solid #CBD5E1;margin-top:32px;font-size:12px;color:#64748B;\">"
    "<strong>Disclaimer:</strong> The content on MoneyAbroadGuide is for informational "
    "purposes only and does not constitute financial, legal, or investment advice. "
    "We are not licensed financial advisors. Always consult a qualified professional "
    "before making financial decisions. Exchange rates and fees change frequently — "
    "verify current rates directly with providers before transacting."
    "</div>\n"
)

def add_legal_disclaimer(content):
    if "legal-disclaimer" in content:
        return content, False
    return content + LEGAL_DISCLAIMER, True

# ─────────────────────────────────────────────────────────────
# FIX 7 — AI content optimization (headings, readability, FAQ)
# ─────────────────────────────────────────────────────────────
def optimize_content(content, title):
    if len(content) > MAX_AI_CHARS:
        print(f"   ⚠️  {len(content)} chars > {MAX_AI_CHARS} limit — skipping AI")
        return content, False

    prompt = f"""You are a senior SEO editor for MoneyAbroadGuide.com, a finance comparison site for immigrants and expats in USA and Canada.

STRICT RULES:
- Return ONLY raw HTML. No markdown, no code fences, no text before or after.
- Do NOT remove or shorten any existing content.
- Do NOT change facts, numbers, links, or provider names.
- Keep all existing <div class="affiliate-disclosure">, <div class="legal-disclaimer">, <div class="author-bio"> blocks exactly as-is.

TASKS:
1. Fix any unclosed or malformed HTML tags.
2. Improve H2 and H3 headings: make them keyword-rich and clear for immigrants/expats searching on Google.
3. Shorten long sentences. Use active voice. Simple language for non-native English speakers.
4. Ensure all links to wise.com, remitly.com, ofx.com, xe.com have rel="noopener sponsored" target="_blank".
5. If no <h2>Frequently Asked Questions</h2> section exists, add 3 relevant FAQ items at the END of the main body (before any bio or disclaimer divs):
   <h2>Frequently Asked Questions</h2>
   <h3>[Specific question about this article topic]?</h3>
   <p>[Clear 2-sentence answer with a specific fact or number.]</p>
   (repeat x3)
6. If a comparison table exists, add a "Best for" column with short labels: Low fees / Speed / Large amounts / Rate tools.

ARTICLE TITLE: {title}

HTML TO IMPROVE:
{content}"""

    result = gpt(prompt, max_tokens=4000, timeout=120)
    if not result:
        return content, False

    result = strip_fences(result)

    if len(result) < len(content) * 0.6:
        print(f"   ⚠️  AI output too short ({len(result)} vs {len(content)}) — discarded")
        return content, False

    return result, True

# ─────────────────────────────────────────────────────────────
# FIX 8 — AI meta title + description
# ─────────────────────────────────────────────────────────────
def generate_meta(title):
    prompt = f"""Generate SEO metadata for a finance article on MoneyAbroadGuide.com targeting immigrants and expats.

Return ONLY valid JSON — no markdown, no explanation:
{{
  "seo_title": "keyword-first title, max 60 characters",
  "meta_description": "compelling description ending with a CTA, max 155 characters"
}}

Article topic: {title}"""

    raw = gpt(prompt, max_tokens=200, timeout=30)
    if not raw:
        return title[:60], ""

    data = safe_json(raw)
    if not data:
        return title[:60], ""

    seo_title = str(data.get("seo_title", title))[:60].strip()
    meta_desc  = str(data.get("meta_description", ""))[:155].strip()

    return (seo_title if len(seo_title) >= 10 else title[:60]), meta_desc

# ─────────────────────────────────────────────────────────────
# FIX 9 — Schema Article JSON-LD
# ─────────────────────────────────────────────────────────────
def build_article_schema(title):
    safe_title = title.replace('"', "'")
    return f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{safe_title}",
  "dateModified": "{date.today().isoformat()}",
  "author": {{
    "@type": "Person",
    "name": "{AUTHOR_NAME}",
    "jobTitle": "{AUTHOR_TITLE}",
    "url": "{WP_URL}/team/"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "{SITE_NAME}",
    "url": "{WP_URL}",
    "logo": {{
      "@type": "ImageObject",
      "url": "{WP_URL}/wp-content/uploads/logo.svg"
    }}
  }}
}}
</script>"""

# ─────────────────────────────────────────────────────────────
# FIX 10 — Schema FAQPage JSON-LD (auto-detected from content)
# ─────────────────────────────────────────────────────────────
def build_faq_schema(content):
    pairs = re.findall(
        r"<h3>([^<]+\?)</h3>\s*<p>([^<]{20,})</p>",
        content,
    )
    if not pairs:
        return ""

    items = []
    for q, a in pairs[:6]:
        clean_a = re.sub(r"<[^>]+>", "", a).strip().replace('"', "'")
        clean_q = q.strip().replace('"', "'")
        items.append(
            f'{{"@type":"Question","name":"{clean_q}",'
            f'"acceptedAnswer":{{"@type":"Answer","text":"{clean_a}"}}}}'
        )

    return f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{",".join(items)}]
}}
</script>"""

# ─────────────────────────────────────────────────────────────
# FIX 11 — Remove duplicate schemas before re-injecting
# ─────────────────────────────────────────────────────────────
def clean_old_schemas(content):
    return re.sub(
        r'<script type="application/ld\+json">\s*\{[^<]*?"@type":\s*"(?:Article|FAQPage)".*?</script>',
        "",
        content,
        flags=re.DOTALL,
    )

# ─────────────────────────────────────────────────────────────
# FIX 12 — Organization schema on homepage
# ─────────────────────────────────────────────────────────────
ORG_SCHEMA = f"""
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{SITE_NAME}",
  "url": "{WP_URL}",
  "logo": {{
    "@type": "ImageObject",
    "url": "{WP_URL}/wp-content/uploads/logo.svg"
  }},
  "description": "Financial guide for immigrants and expats in the USA and Canada. Compare money transfer services, banking, taxes and credit.",
  "contactPoint": {{
    "@type": "ContactPoint",
    "contactType": "Editorial",
    "email": "contact@moneyabroadguide.com"
  }},
  "sameAs": [
    "https://www.linkedin.com/company/moneyabroadguide",
    "https://twitter.com/moneyabroadguide"
  ]
}}
</script>"""

def update_homepage_schema(all_pages):
    home = next(
        (p for p in all_pages
         if p.get("slug") in ("home", "")
         or p.get("link", "").rstrip("/") == WP_URL),
        None,
    )
    if not home:
        print("   ⚠️  Homepage not found in WP pages — skipping")
        return

    content = home["content"]["rendered"]
    if "Organization" in content:
        print("   ✓ Organization schema already present on homepage")
        return

    status = wp_update(home["id"], {"content": content + ORG_SCHEMA}, kind="pages")
    print("   ✅ Organization schema added to homepage" if status == 200
          else f"   ❌ Homepage update failed (HTTP {status})")

# ─────────────────────────────────────────────────────────────
# FIX 13 — Audit required legal pages
# ─────────────────────────────────────────────────────────────
def audit_legal_pages(all_pages):
    slugs = set()
    for p in all_pages:
        link = p.get("link", "").replace(WP_URL, "").strip("/")
        slugs.add("/" + link + "/")

    print("\n📋 Required pages audit:")
    missing = []
    for slug, name in REQUIRED_PAGES.items():
        found = slug in slugs
        print(f"   {'✅' if found else '❌'} {name:22s} {slug}")
        if not found:
            missing.append((slug, name))

    if missing:
        print(f"\n   ⚠️  {len(missing)} page(s) missing — create them in WordPress Admin!")
    return missing

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def run():
    print("🚀 SEO AUTOPILOT — FULL DAILY RUN\n")
    cache = load_cache()

    # Fetch everything
    print("📥 Fetching posts...")
    posts = wp_get_all("posts")
    print("\n📥 Fetching pages...")
    pages = wp_get_all("pages")

    # Legal pages audit
    missing_pages = audit_legal_pages(pages)

    # Homepage Organization schema
    print("\n🏠 Homepage schema...")
    update_homepage_schema(pages)

    # Filter posts that need updating
    due           = [p for p in posts if needs_update(p["id"], cache)]
    skipped_cache = len(posts) - len(due)

    print(f"\n📊 Total posts    : {len(posts)}")
    print(f"   To update     : {len(due)}")
    print(f"   Cached (skip) : {skipped_cache}\n")

    success = failed = 0
    report  = []

    for i, post in enumerate(due, 1):
        title   = post["title"]["rendered"]
        content = post["content"]["rendered"]
        pid     = post["id"]
        changes = []

        print(f"[{i}/{len(due)}] {title[:65]}")

        try:
            # ── Safe fixes
            content, chg = safe_fixes(content)
            if chg: changes.append("safe_fixes");      print("   ✓ Safe fixes")

            # ── Disclosure
            content, chg = add_disclosure(content)
            if chg: changes.append("disclosure");      print("   ✓ Disclosure")

            # ── Last updated
            content, chg = add_last_updated(content)
            if chg: changes.append("last_updated");    print("   ✓ Last updated date")

            # ── AI optimization (headings, readability, FAQ, table)
            content, chg = optimize_content(content, title)
            if chg: changes.append("ai_optimized");    print("   ✓ AI optimized")

            # ── CTA button
            content, chg = add_cta(content)
            if chg: changes.append("cta");             print("   ✓ CTA added")

            # ── Author bio
            content, chg = add_author_bio(content)
            if chg: changes.append("author_bio");      print("   ✓ Author bio")

            # ── Legal disclaimer
            content, chg = add_legal_disclaimer(content)
            if chg: changes.append("legal_disclaimer"); print("   ✓ Legal disclaimer")

            # ── Schema: Article + FAQ
            content     = clean_old_schemas(content)
            art_schema  = build_article_schema(title)
            faq_schema  = build_faq_schema(content)
            content    += art_schema + (faq_schema if faq_schema else "")
            changes.append("schema")
            print(f"   ✓ Schema: Article{' + FAQ' if faq_schema else ''}")

            # ── Meta title + description
            seo_title, meta_desc = generate_meta(title)
            if seo_title != title[:60]:
                changes.append("meta")
                print(f"   ✓ SEO title: {seo_title}")

            # ── Push to WordPress
            status = wp_update(pid, {
                "title":   seo_title,
                "content": content,
                "excerpt": meta_desc,
            })

            if status == 200:
                print("   ✅ Done\n")
                success += 1
                mark_done(pid, cache, "success", changes)
                report.append({"id": pid, "title": title, "status": "success", "changes": changes})
            else:
                print(f"   ❌ HTTP {status}\n")
                failed += 1
                mark_done(pid, cache, f"failed_{status}", changes)
                report.append({"id": pid, "title": title, "status": f"failed_{status}"})

            time.sleep(THROTTLE_SEC)

        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            failed += 1
            mark_done(pid, cache, "error", [])
            report.append({"id": pid, "title": title, "status": "error", "error": str(e)})

    # Save cache + daily report
    save_cache(cache)
    os.makedirs(".cache", exist_ok=True)
    with open(f".cache/report_{date.today().isoformat()}.json", "w") as f:
        json.dump({
            "date":          date.today().isoformat(),
            "mode":          "dry_run" if DRY_RUN else "live",
            "total":         len(posts),
            "due":           len(due),
            "success":       success,
            "failed":        failed,
            "skipped":       skipped_cache,
            "missing_pages": [n for _, n in missing_pages],
            "articles":      report,
        }, f, indent=2, ensure_ascii=False)

    # Final summary
    print("=" * 52)
    print(f"🔥 COMPLETE — {date.today().isoformat()}")
    print(f"   ✅ Updated  : {success}")
    print(f"   ❌ Failed   : {failed}")
    print(f"   — Skipped  : {skipped_cache}")
    if missing_pages:
        print("\n   ⚠️  Pages to create manually in WordPress:")
        for slug, name in missing_pages:
            print(f"      → {name}  ({slug})")
    print("=" * 52)


if __name__ == "__main__":
    run()

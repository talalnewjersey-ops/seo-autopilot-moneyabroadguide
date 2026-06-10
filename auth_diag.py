import os
import requests
import base64
import json

WP_URL = os.getenv("WP_URL", "https://moneyabroadguide.com")
WP_USER = os.getenv("WP_USER", "")
WP_PASSWORD = os.getenv("WP_PASSWORD", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

print("=" * 60)
print("AUTH DIAGNOSTIC REPORT")
print("=" * 60)
print(f"WP_URL: {WP_URL}")
print(f"WP_USER set: {bool(WP_USER)}, value: {WP_USER[:3] + '***' if WP_USER else 'EMPTY'}")
print(f"WP_PASSWORD set: {bool(WP_PASSWORD)}")
print(f"WP_APP_PASSWORD set: {bool(WP_APP_PASSWORD)}")
print()


def test_auth(label, user, password):
    print(f"\n{'='*50}")
    print(f"TEST: {label}")
    print(f"{'='*50}")
    credentials = f"{user}:{password}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "User-Agent": "GitHub-Actions-Auth-Debug/1.0"
    }

    # Test with redirect following
    try:
        r = requests.get(
            f"{WP_URL}/wp-json/wp/v2/users/me?context=edit",
            headers=headers,
            timeout=30,
            allow_redirects=True
        )
        print(f"  WITH REDIRECTS: status={r.status_code}")
        print(f"  Final URL: {r.url}")
        try:
            data = r.json()
            print(f"  Response: {json.dumps(data, indent=2)[:800]}")
        except Exception:
            print(f"  Response text: {r.text[:500]}")
    except Exception as e:
        print(f"  ERROR (with redirects): {e}")

    # Test WITHOUT redirect following
    try:
        r2 = requests.get(
            f"{WP_URL}/wp-json/wp/v2/users/me?context=edit",
            headers=headers,
            timeout=30,
            allow_redirects=False
        )
        print(f"  NO-REDIRECT: status={r2.status_code}")
        if r2.status_code in [301, 302, 307, 308]:
            loc = r2.headers.get('Location', 'unknown')
            print(f"  REDIRECT DETECTED -> {loc}")
            if loc.startswith("http://") and WP_URL.startswith("https://"):
                print("  CRITICAL: HTTP->HTTPS redirect stripping Authorization header!")
            elif "?" not in loc:
                print("  Auth header stripped in redirect!")
    except Exception as e:
        print(f"  ERROR (no redirect): {e}")

    return r.status_code == 200 if 'r' in dir() else False


# Test 1: No auth baseline
print("\n--- BASELINE: No Auth ---")
try:
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts?per_page=1", timeout=15)
    print(f"  GET posts: {r.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

success = False

# Test 2: WP_PASSWORD
if WP_USER and WP_PASSWORD:
    ok = test_auth("WP_USER + WP_PASSWORD (Basic Auth)", WP_USER, WP_PASSWORD)
    success = success or ok

# Test 3: WP_APP_PASSWORD
if WP_USER and WP_APP_PASSWORD:
    ok = test_auth("WP_USER + WP_APP_PASSWORD", WP_USER, WP_APP_PASSWORD)
    success = success or ok

# Test 4: HTTP endpoint (without HTTPS)
print("\n--- TEST: HTTP endpoint (no SSL) ---")
http_url = WP_URL.replace("https://", "http://")
if http_url != WP_URL and WP_USER and (WP_PASSWORD or WP_APP_PASSWORD):
    pwd = WP_APP_PASSWORD or WP_PASSWORD
    credentials = f"{WP_USER}:{pwd}"
    token = base64.b64encode(credentials.encode()).decode()
    try:
        r = requests.get(
            f"{http_url}/wp-json/wp/v2/users/me?context=edit",
            headers={"Authorization": f"Basic {token}"},
            timeout=15,
            allow_redirects=False
        )
        print(f"  HTTP status: {r.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)
if success:
    print("AUTH STATUS: WORKING - HTTP 200 RECEIVED")
    print("WordPress authentication is functional.")
else:
    print("AUTH STATUS: FAILING - HTTP 401 PERSISTS")
    print()
    print("LIKELY ROOT CAUSES:")
    print("1. Authorization header stripped by LiteSpeed/Apache mod_rewrite")
    print("2. .htaccess missing CGIPassAuth On or SetEnvIf")
    print("3. HTTP->HTTPS redirect stripping auth header")
    print("4. Hostinger CDN or proxy stripping Authorization header")
    print("5. WordPress Application Password feature disabled")
    print("6. Wrong credentials in GitHub Secrets")
    print()
    print("REQUIRED FIX: Add to .htaccess ABOVE # BEGIN WordPress:")
    print("  CGIPassAuth On")
    print("  SetEnvIf Authorization .+ HTTP_AUTHORIZATION=$0")
    print()
    print("AND add to wp-config.php or a plugin:")
    print("  if (empty($_SERVER['HTTP_AUTHORIZATION']) &&")
    print("      !empty($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {")
    print("    $_SERVER['HTTP_AUTHORIZATION'] = $_SERVER['REDIRECT_HTTP_AUTHORIZATION'];")
    print("  }")

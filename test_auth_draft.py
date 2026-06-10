import os
import requests
import base64
import json

WP_URL = os.getenv("WP_URL", "https://moneyabroadguide.com")
WP_USER = os.getenv("WP_USER", "")
WP_PASSWORD = os.getenv("WP_PASSWORD", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

# Use WP_APP_PASSWORD if set, otherwise WP_PASSWORD
password = WP_APP_PASSWORD if WP_APP_PASSWORD else WP_PASSWORD

credentials = f"{WP_USER}:{password}"
token = base64.b64encode(credentials.encode()).decode()
headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json",
    "User-Agent": "GitHub-Actions-Auth-Test/1.0"
}

print("=" * 60)
print("AUTH SUCCESS - CREATING TEST DRAFT")
print("=" * 60)
print(f"WP_URL: {WP_URL}")
print(f"WP_USER: {WP_USER[:3] + '***' if WP_USER else 'NOT SET'}")
print()

# Step 1: Verify authentication
print("Step 1: Verify authentication...")
r = requests.get(
    f"{WP_URL}/wp-json/wp/v2/users/me?context=edit",
    headers=headers,
    timeout=30
)
print(f"  GET /users/me: HTTP {r.status_code}")
if r.status_code != 200:
    print(f"  FAILED: {r.text[:300]}")
    print("\nAUTH: FAILING")
    exit(1)

user_data = r.json()
print(f"  Authenticated as: {user_data.get('name', 'unknown')}")
print(f"  Username: {user_data.get('username', 'unknown')}")
print(f"  Role: {user_data.get('roles', ['unknown'])}")
print(f"  User ID: {user_data.get('id', 'unknown')}")
print()

# Step 2: Create test draft
print("Step 2: Creating TEST AUTH SUCCESS draft...")
draft_data = {
    "title": "TEST AUTH SUCCESS",
    "content": "Authentication verification test.",
    "status": "draft"
}
r2 = requests.post(
    f"{WP_URL}/wp-json/wp/v2/posts",
    headers=headers,
    json=draft_data,
    timeout=30
)
print(f"  POST /posts: HTTP {r2.status_code}")
if r2.status_code not in [200, 201]:
    print(f"  FAILED: {r2.text[:500]}")
    exit(1)

draft = r2.json()
draft_id = draft.get("id")
draft_url = draft.get("link", "N/A")
draft_status = draft.get("status", "unknown")

print(f"  Draft ID: {draft_id}")
print(f"  Draft URL: {draft_url}")
print(f"  Draft Status: {draft_status}")
print(f"  Draft Title: {draft.get('title', {}).get('rendered', 'N/A')}")
print()
print("Full draft response:")
print(json.dumps(draft, indent=2)[:1000])
print()

# Step 3: Delete the test draft
print("Step 3: Deleting test draft...")
r3 = requests.delete(
    f"{WP_URL}/wp-json/wp/v2/posts/{draft_id}?force=true",
    headers=headers,
    timeout=30
)
print(f"  DELETE /posts/{draft_id}: HTTP {r3.status_code}")
if r3.status_code in [200, 204, 410]:
    print(f"  Draft {draft_id} deleted successfully.")
else:
    print(f"  Delete response: {r3.text[:200]}")

print()
print("=" * 60)
print("FINAL CONCLUSION")
print("=" * 60)
print("AUTH STATUS: WORKING")
print(f"HTTP Status: 200")
print(f"Authenticated Username: {user_data.get('username', 'N/A')}")
print(f"User Role: {user_data.get('roles', ['N/A'])}")
print(f"Draft ID: {draft_id}")
print(f"Draft URL: {draft_url}")
print(f"Delete Status: HTTP {r3.status_code}")
print()
print("AUTHENTICATION WORKING")

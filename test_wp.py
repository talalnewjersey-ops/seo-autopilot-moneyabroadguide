import os
import requests
import base64

WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_PASSWORD = os.getenv("WP_PASSWORD")

print("===== WORDPRESS TEST =====")
print("URL:", WP_URL)
print("USER:", WP_USER)


# 🔐 AUTH
credentials = f"{WP_USER}:{WP_PASSWORD}"
token = base64.b64encode(credentials.encode()).decode()

headers = {
    "Authorization": f"Basic {token}",
    "Content-Type": "application/json"
}


# 🧪 TEST GET POSTS
print("\n--- TEST GET POSTS ---")
response = requests.get(f"{WP_URL}/wp-json/wp/v2/posts")

print("STATUS:", response.status_code)

if response.status_code == 200:
    print("✅ GET OK (WordPress API accessible)")
else:
    print("❌ GET FAILED")


# 🧪 TEST UPDATE (POST ID 7170)
print("\n--- TEST UPDATE POST ---")

payload = {
    "title": "TEST CONNECTION ✅",
}

response = requests.post(
    f"{WP_URL}/wp-json/wp/v2/posts/7170",
    headers=headers,
    json=payload
)

print("STATUS:", response.status_code)
print("RESPONSE:", response.text)


if response.status_code == 200:
    print("✅ UPDATE SUCCESS")
else:
    print("❌ UPDATE FAILED")

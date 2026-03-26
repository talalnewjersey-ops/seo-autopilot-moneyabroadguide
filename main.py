import requests
from bs4 import BeautifulSoup

print("START SCAN")

try:
    url = "https://moneyabroadguide.com"

    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        print("Website not reachable")
    else:
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "No title"
        h1 = [h.text.strip() for h in soup.find_all("h1")]

        print("TITLE:", title)
        print("H1:", h1)

except Exception as e:
    print("ERROR:", str(e))

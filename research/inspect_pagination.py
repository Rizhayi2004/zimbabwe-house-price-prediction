import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

for page in [99, 100, 101]:
    url = f"https://www.property.co.zw/houses-for-sale?page={page}"
    response = session.get(url, timeout=40)
    soup = BeautifulSoup(response.text, "lxml")

    print("\n" + "=" * 55)
    print("PAGE:", page)
    print("HTTP:", response.status_code)
    print("TITLE:", soup.title.get_text(strip=True) if soup.title else "No title")
    print("PAGE TEXT:", soup.get_text(" ", strip=True)[:700])

    print("PAGINATION LINKS:")
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a["href"]
        if "page=" in href or text in ["›", "»", "Next"]:
            print(repr(text), "->", href)

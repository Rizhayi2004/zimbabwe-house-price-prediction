import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html,application/xhtml+xml"
})

for page in [99, 100, 101, 102]:
    url = f"https://www.property.co.zw/houses-for-sale?page={page}"
    response = session.get(url, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select(".ResultCardItem")
    title = soup.title.get_text(strip=True) if soup.title else "No title"

    print("\n" + "=" * 60)
    print("PAGE:", page)
    print("STATUS:", response.status_code)
    print("FINAL URL:", response.url)
    print("TITLE:", title)
    print("HTML LENGTH:", len(response.text))
    print("LISTING CARD CONTAINERS:", len(cards))

    if cards:
        print("FIRST CARD:", cards[0].get_text(" ", strip=True)[:250])
    else:
        print("BODY PREVIEW:")
        print(soup.get_text(" ", strip=True)[:600])

    print("PAGINATION LINKS:")
    for a in soup.find_all("a", href=True):
        if "page=" in a["href"]:
            print(a.get_text(" ", strip=True), "->", a["href"])

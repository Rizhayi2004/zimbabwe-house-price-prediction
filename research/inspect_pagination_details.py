import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

for page in [1, 100]:
    url = f"https://www.property.co.zw/houses-for-sale?page={page}"
    response = session.get(url, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")

    print("\n" + "=" * 60)
    print("PAGE:", page)
    print("STATUS:", response.status_code)

    print("\nPAGINATION LINKS:")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "page=" in href or "page/" in href:
            print(a.get_text(" ", strip=True), "->", urljoin(url, href))

    print("\nLISTING CARD CONTAINERS:")
    for tag in soup.find_all(["article", "li", "div"]):
        links = tag.find_all(
            "a",
            href=lambda h: h and "/for-sale/houses-" in h
        )
        if links and len(links) <= 3:
            classes = tag.get("class", [])
            print(
                "Tag:", tag.name,
                "Classes:", classes,
                "House links:", len(links),
                "Text:", tag.get_text(" ", strip=True)[:180]
            )
            break

    print("\nPAGE SIZE / PAGINATION TEXT:")
    text = soup.get_text(" ", strip=True)
    for phrase in ["Showing", "of 2,634", "2,634 listings", "Next", "Last"]:
        if phrase.lower() in text.lower():
            position = text.lower().find(phrase.lower())
            print(text[max(0, position-100):position+180])

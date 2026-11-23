import requests
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

for page in [100, 101]:
    response = session.get(
        f"https://www.property.co.zw/houses-for-sale?page={page}",
        timeout=40
    )
    soup = BeautifulSoup(response.text, "lxml")

    print("\n" + "=" * 60)
    print("PAGE:", page)
    print("FINAL URL:", response.url)
    print("HTML SIZE:", len(response.text))
    print("FORMS:", len(soup.find_all("form")))
    print("SCRIPTS:")

    for script in soup.find_all("script", src=True):
        print(script.get("src"))

    print("\nPAGINATION / RESULT REFERENCES:")
    for element in soup.find_all(["a", "link", "input"]):
        text = element.get_text(" ", strip=True)
        href = element.get("href", "")
        value = element.get("value", "")

        if "page" in href.lower() or "page" in value.lower():
            print("Text:", text, "| URL:", href, "| Value:", value)

    print("\nRESULT CONTAINERS:")
    for tag in soup.find_all(True, class_=True):
        classes = " ".join(tag.get("class", []))
        if any(word in classes.lower() for word in ["pagination", "listing", "result"]):
            print(tag.name, classes[:120])

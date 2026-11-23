import requests
from bs4 import BeautifulSoup

url = "https://www.property.co.zw/houses-for-sale?page=1"
response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40
)

soup = BeautifulSoup(response.text, "lxml")

for number, form in enumerate(soup.find_all("form"), 1):
    print("\n" + "=" * 55)
    print("FORM:", number)
    print("ACTION:", form.get("action"))
    print("METHOD:", form.get("method"))

    for field in form.find_all(["input", "select", "button"]):
        name = field.get("name")
        field_id = field.get("id")
        field_type = field.get("type")
        value = field.get("value")

        print(
            "FIELD:",
            field.name,
            "| name:", name,
            "| id:", field_id,
            "| type:", field_type,
            "| value:", value
        )

        if field.name == "select":
            for option in field.find_all("option"):
                print(
                    "   OPTION:",
                    option.get("value"),
                    "|",
                    option.get_text(" ", strip=True)
                )

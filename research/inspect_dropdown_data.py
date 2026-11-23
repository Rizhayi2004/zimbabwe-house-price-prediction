import requests
import re

url = "https://www.property.co.zw/houses-for-sale?page=1"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40
)

html = response.text

terms = [
    "LOCATION_DATA",
    "AGENCY_DATA",
    "DEVELOPMENT_DATA",
    "NEIGHBORHOOD_DATA",
    "PRICE_TREND_LOCATIONS",
    "InitializeSelect2Ajax"
]

for term in terms:
    matches = list(re.finditer(re.escape(term), html, re.IGNORECASE))

    print("\n" + "=" * 60)
    print("TERM:", term, "| OCCURRENCES:", len(matches))

    for match in matches[:5]:
        start = max(0, match.start() - 500)
        end = min(len(html), match.end() + 1500)
        print(html[start:end])

import requests
import re

url = "https://www.property.co.zw/content/overhaul/js/portal.min.js?v=3.1.2.13579"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40
)

print("HTTP STATUS:", response.status_code)
print("JavaScript size:", len(response.text))

js = response.text

terms = [
    "searchResultForm",
    "neighborhood_ids",
    "development_ids",
    "Locations",
    "filterversion",
    "select2",
    "ajax",
    "/search"
]

for term in terms:
    print("\n" + "=" * 55)
    print("SEARCH TERM:", term)

    matches = list(re.finditer(re.escape(term), js, re.IGNORECASE))
    print("Occurrences:", len(matches))

    for match in matches[:3]:
        start = max(0, match.start() - 500)
        end = min(len(js), match.end() + 1000)
        print("\n", js[start:end])

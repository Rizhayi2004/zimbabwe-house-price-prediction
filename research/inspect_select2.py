import requests
import re

url = "https://www.property.co.zw/content/overhaul/js/ondemand/Select2.js?v=3.1.2.13579"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=40
)

print("HTTP STATUS:", response.status_code)
print("FILE SIZE:", len(response.text))

js = response.text

terms = [
    "InitializeSelect2Ajax",
    "LOCATION_DATA",
    "AGENCY_DATA",
    "DEVELOPMENT_DATA",
    "neighborhood_ids",
    "development_ids",
    "site_ids",
    "ajax",
    "url:",
    "Locations"
]

for term in terms:
    matches = list(re.finditer(re.escape(term), js, re.IGNORECASE))

    print("\n" + "=" * 55)
    print("TERM:", term, "| OCCURRENCES:", len(matches))

    for match in matches[:4]:
        start = max(0, match.start() - 400)
        end = min(len(js), match.end() + 900)
        print(js[start:end])

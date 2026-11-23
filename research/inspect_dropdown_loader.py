import requests
import re

url = "https://www.property.co.zw/content/overhaul/js/portal.min.js?v=3.1.2.13579"
js = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=40).text

terms = [
    "Select2:function",
    "Select2:",
    "Select2Setup",
    "LOCATION_DATA",
    "Load:{",
    "ajax-placeholder"
]

for term in terms:
    print("\n" + "=" * 65)
    print("TERM:", term)

    matches = list(re.finditer(re.escape(term), js, re.IGNORECASE))
    print("Occurrences:", len(matches))

    for match in matches[:8]:
        start = max(0, match.start() - 250)
        end = min(len(js), match.end() + 1800)
        print("\n" + js[start:end])

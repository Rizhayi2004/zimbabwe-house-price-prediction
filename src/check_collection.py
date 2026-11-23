
from datetime import date
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SETTINGS_FILE = PROJECT_ROOT / "data" / "collection_settings.json"

# Permission status must remain False until written permission is received.
SETTINGS = {
    "website": "Property.co.zw",
    "permission_status": "pending",
    "listing_data_permission": False,
    "photograph_permission": False,
    "collection_enabled": False,
    "last_checked": str(date.today())
}


def check_collection_readiness():

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(SETTINGS, file, indent=4)

    print("HOUSE PRICE PROJECT - COLLECTION CHECK")
    print("--------------------------------------")
    print("Website:", SETTINGS["website"])
    print("Permission status:", SETTINGS["permission_status"])
    print("Listing data permission:",
          SETTINGS["listing_data_permission"])
    print("Photograph permission:",
          SETTINGS["photograph_permission"])
    print("Collection enabled:",
          SETTINGS["collection_enabled"])

    if not SETTINGS["collection_enabled"]:
        print("\nCollection is DISABLED.")
        print("Wait for written permission before collecting data.")

    print("\nSettings saved to:", SETTINGS_FILE)


if __name__ == "__main__":
    check_collection_readiness()

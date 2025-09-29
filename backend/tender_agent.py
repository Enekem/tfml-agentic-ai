import json
from datetime import datetime
import random

TENDERS_FILE = "../logs/tenders.json"

def fetch_mock_tenders():
    return [
        {
            "title": "Building Maintenance – Zaria Campus",
            "score": random.randint(70, 95),
            "deadline": "2025-08-18",
            "link": "https://example.com/tenders/zaria-maintenance",
            "sector": "Education",
            "description": "Annual maintenance contract for classroom blocks, hostels, and offices.",
            "eoi": "",
            "status": "Pending"
        },
        {
            "title": "HVAC Upgrade Project – Enugu State",
            "score": random.randint(70, 95),
            "deadline": "2025-08-25",
            "link": "https://example.com/tenders/enugu-hvac",
            "sector": "Energy",
            "description": "Supply and installation of HVAC systems in state administrative buildings.",
            "eoi": "",
            "status": "Pending"
        }
    ]

def save_tenders(tenders):
    with open(TENDERS_FILE, "w") as f:
        json.dump(tenders, f, indent=2)

def run_agent():
    print("📡 Running TFML Tender Agent...")
    new_tenders = fetch_mock_tenders()

    try:
        with open(TENDERS_FILE, "r") as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    # Merge logic — avoid duplicates
    titles = {t["title"] for t in existing}
    for tender in new_tenders:
        if tender["title"] not in titles:
            existing.append(tender)

    save_tenders(existing)
    print(f"✅ {len(new_tenders)} new tenders added.")

if __name__ == "__main__":
    run_agent()

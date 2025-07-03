import requests
import os
from dotenv import load_dotenv

# --- Inputs ---
api_key = os.getenv('COMPANY_HOUSE_API_KEY')
company_number = '01471587'
headers = {"Accept": "application/json"}

# --- Get officers for the company ---
officers_url = f"https://api.company-information.service.gov.uk/company/{company_number}/officers"

try:
    response = requests.get(officers_url, auth=(api_key, ''), headers=headers)
    response.raise_for_status()
    officers_data = response.json()
    officers = officers_data.get("items", [])
    print(f"Found {len(officers)} officers for company {company_number}.")
    for officer in officers:
        print(officer)
        print(f"- {officer.get('name')}")
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch officers: {e}")

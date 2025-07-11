import requests
import os
from dotenv import load_dotenv
# --- Inputs ---
load_dotenv()
api_key = os.getenv('COMPANY_HOUSE_API_KEY')
company_number = '01471587'
headers = {"Accept": "application/json"}

# --- Get charges for the company ---
charges_url = f"https://api.company-information.service.gov.uk/company/{company_number}/charges"

try:
    response = requests.get(charges_url, auth=(api_key, ''), headers=headers)
    if response.status_code == 404:
        print(f"No charges found for company {company_number}.")
    else:
        response.raise_for_status()
        charges_data = response.json()
        print(f"Charges data for company {company_number}:")
        print(charges_data)
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch charges: {e}")
    

# --- Get a specific filing history item by ID ---
filing_history_id = "MDE0MDExMjM4N2FkaXF6a2N4"
filing_history_url = f"https://api.company-information.service.gov.uk/company/{company_number}/filing-history/{filing_history_id}"

try:
    filing_response = requests.get(filing_history_url, auth=(api_key, ''), headers=headers, allow_redirects=True)
    filing_response.raise_for_status()
    filing_data = filing_response.json()
    print(f"\nFiling history item {filing_history_id}:")
    print(filing_data)
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch filing history item: {e}")
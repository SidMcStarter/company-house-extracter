import requests
import os
from dotenv import load_dotenv
# --- Inputs ---
api_key = os.getenv('COMPANY_HOUSE_API_KEY')
company_number = '01471587'
headers = {"Accept": "application/json"}

# --- Get insolvency information for the company ---
insolvency_url = f"https://api.company-information.service.gov.uk/company/{company_number}/insolvency"

try:
    response = requests.get(insolvency_url, auth=(api_key, ''), headers=headers)
    if response.status_code == 404:
        print(f"No insolvency information found for company {company_number}.")
    else:
        response.raise_for_status()
        insolvency_data = response.json()
        print(f"Insolvency data for company {company_number}:")
        print(insolvency_data)
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch insolvency information: {e}")
import requests
import os
from dotenv import load_dotenv
# --- Inputs ---
load_dotenv()
api_key = os.getenv('COMPANY_HOUSE_API_KEY')
company_number = '01471587'
headers = {"Accept": "application/json"}

# --- Get exemptions information for the company ---
exemptions_url = f"https://api.company-information.service.gov.uk/company/{company_number}/exemptions"

try:
    response = requests.get(exemptions_url, auth=(api_key, ''), headers=headers)
    print(response)
    if response.status_code == 404:
        print(f"No exemptions information found for company {company_number}.")
    else:
        response.raise_for_status()
        exemptions_data = response.json()
        print(f"Exemptions data for company {company_number}:")
        print(exemptions_data)
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch exemptions information: {e}")
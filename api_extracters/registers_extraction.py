import requests
import os
from dotenv import load_dotenv

# --- Inputs ---
api_key = os.getenv('COMPANY_HOUSE_API_KEY')
company_number = '01471587'
headers = {"Accept": "application/json"}

# --- Get registers for the company ---
registers_url = f"https://api.company-information.service.gov.uk/company/{company_number}/registers"

try:
    response = requests.get(registers_url, auth=(api_key, ''), headers=headers)
    if response.status_code == 404:
        print(f"No registers found for company {company_number}.")
    else:
        response.raise_for_status()
        registers_data = response.json()
        print(f"Registers data for company {company_number}:")
        print(registers_data)
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to fetch registers: {e}")
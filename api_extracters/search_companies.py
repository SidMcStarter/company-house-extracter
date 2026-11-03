import requests
import os
from dotenv import load_dotenv

load_dotenv()
# api_key = os.getenv('COMPANY_HOUSE_API_KEY')
headers = {"Accept": "application/json"}

def search_companies(search_term, start_index=0, items_per_page=20, COMPANY_HOUSE_API_KEY=None):
    companies_url = (
        f"https://api.company-information.service.gov.uk/search/companies"
        f"?q={search_term}&items_per_page={items_per_page}&start_index={start_index}"
    )
    response = requests.get(companies_url, auth=(COMPANY_HOUSE_API_KEY, ''), headers=headers)
    response.raise_for_status()
    companies_data = response.json()
    results = [
        {"title": item.get("title"), "company_number": item.get("company_number")}
        for item in companies_data.get("items", [])
    ]
    return results

# Example usage:
if __name__ == "__main__":
    results = search_companies("vodafone")
    for company in results:
        print(company)
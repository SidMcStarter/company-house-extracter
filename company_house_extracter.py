import requests
import os
from dotenv import load_dotenv

# https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/filing-history/list

# --- Inputs ---
load_dotenv()
api_key = os.getenv('COMPANY_HOUSE_API_KEY') 
company_number = '01471587'  
headers = {"Accept": "application/json"}

# --- 1. Get ALL filing history using a pagination loop ---
print(f"📄 Fetching all filings for company {company_number}...")

all_filings = []
start_index = 0
# Use the max items_per_page to reduce the number of requests
items_per_page = 100 
total_count = None # We'll get this from the first API response

while True:
    filing_url = (
        f"https://api.company-information.service.gov.uk/company/{company_number}/filing-history"
        f"?items_per_page={items_per_page}&start_index={start_index}"
    )
    
    try:
        filing_response = requests.get(filing_url, auth=(api_key, ''), headers=headers)
        filing_response.raise_for_status() # This will raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch filing history: {e}")
        break # Exit the loop on a network or server error

    data = filing_response.json()
    items = data.get("items", [])
    
    if not items:
        # No more items to fetch, break the loop
        print("No more items found. Concluding fetch.")
        break
        
    all_filings.extend(items)
    
    # Get the total count from the first response, if we don't have it yet
    if total_count is None:
        total_count = data.get("total_count", 0)
        print(f"Total filings to retrieve: {total_count}")

    print(f"Retrieved {len(all_filings)} of {total_count} filings...")

    # Check if we have collected all the filings
    if len(all_filings) >= total_count:
        break
    
    # Prepare for the next iteration
    start_index += items_per_page

print(f"✅ Finished fetching. Found {len(all_filings)} total filings for company {company_number}.")

# --- 2. Process each filing ---
os.makedirs(f"{company_number}/filings", exist_ok=True)

# Now, loop through the 'all_filings' list which contains everything
for filing in all_filings:
    
    filing_type = filing.get("type")
    transaction_id = filing.get("transaction_id")
    metadata_url = filing.get("links", {}).get("document_metadata")
    
    if not metadata_url:
        print(f"⚠️ No document_metadata link for transaction {transaction_id}")
        continue
    
    # 3. Fetch document metadata
    try:
        meta_response = requests.get(metadata_url, auth=(api_key, ''), headers=headers)
        meta_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch metadata for {transaction_id}: {e}")
        continue

    doc_link = meta_response.json().get("links", {}).get("document")
    
    if not doc_link:
        print(f"⚠️ No 'document' download link found in metadata for {transaction_id}")
        continue

    # 4. Download the PDF
    pdf_headers = {"Accept": "application/pdf"}
    try:
        pdf_response = requests.get(doc_link, allow_redirects=True, auth=(api_key, ''), headers=pdf_headers)
        pdf_response.raise_for_status()
        
        # Check if the content is actually a PDF before saving
        if "application/pdf" in pdf_response.headers.get("Content-Type", ""):
            safe_filing_type = filing_type.replace("/", "_") if filing_type else "UNKNOWN"
            filename = f"{company_number}/filings/{safe_filing_type}_{transaction_id}.pdf"
            with open(filename, "wb") as f:
                f.write(pdf_response.content)
            print(f"✅ Downloaded: {filename}")
        else:
            print(f"❌ Failed to download PDF for {transaction_id}. Content-Type was not PDF.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download PDF for {transaction_id}: {e}")
import requests
import os

def download_company_filings(company_number, api_key, items_per_page=100):
    """
    Downloads all filings (PDFs) for a given company number using the Companies House API.
    Returns a list of downloaded PDF file paths.
    """
    headers = {"Accept": "application/json"}
    all_filings = []
    start_index = 0
    total_count = None

    # --- 1. Get ALL filing history using a pagination loop ---
    while True:
        filing_url = (
            f"https://api.company-information.service.gov.uk/company/{company_number}/filing-history"
            f"?items_per_page={items_per_page}&start_index={start_index}"
        )
        try:
            filing_response = requests.get(filing_url, auth=(api_key, ''), headers=headers)
            filing_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to fetch filing history: {e}")
            break

        data = filing_response.json()
        items = data.get("items", [])
        if not items:
            break
        all_filings.extend(items)
        if total_count is None:
            total_count = data.get("total_count", 0)
        if len(all_filings) >= total_count:
            break
        start_index += items_per_page

    print(f"✅ Finished fetching. Found {len(all_filings)} total filings for company {company_number}.")

    # --- 2. Download PDFs ---
    os.makedirs(f"{company_number}/filings", exist_ok=True)
    downloaded_files = []

    for filing in all_filings:
        filing_type = filing.get("type")
        transaction_id = filing.get("transaction_id")
        metadata_url = filing.get("links", {}).get("document_metadata")
        if not metadata_url:
            continue
        try:
            meta_response = requests.get(metadata_url, auth=(api_key, ''), headers=headers)
            meta_response.raise_for_status()
        except requests.exceptions.RequestException:
            continue
        doc_link = meta_response.json().get("links", {}).get("document")
        if not doc_link:
            continue
        pdf_headers = {"Accept": "application/pdf"}
        try:
            pdf_response = requests.get(doc_link, allow_redirects=True, auth=(api_key, ''), headers=pdf_headers)
            pdf_response.raise_for_status()
            if "application/pdf" in pdf_response.headers.get("Content-Type", ""):
                safe_filing_type = filing_type.replace("/", "_") if filing_type else "UNKNOWN"
                filename = f"{company_number}/filings/{safe_filing_type}_{transaction_id}.pdf"
                with open(filename, "wb") as f:
                    f.write(pdf_response.content)
                downloaded_files.append(filename)
            else:
                continue
        except requests.exceptions.RequestException:
            continue

    return downloaded_files

# Example usage:
# files = download_company_filings("01471587", "YOUR_API_KEY")
# print(files)
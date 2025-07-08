from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import requests
import time
import io
import os
import json
import fitz  # PyMuPDF
import pathlib

def load_azure_credentials():
    """
    Load Azure credentials from environment variables.
    
    Returns:
        tuple: (AZURE_KEY, AZURE_ENDPOINT)
    """
    load_dotenv()
    AZURE_KEY = os.getenv("AZURE_KEY")
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
    if not AZURE_KEY or not AZURE_ENDPOINT:
        raise ValueError("Azure credentials not found in environment variables.")
    return AZURE_KEY, AZURE_ENDPOINT

# takes a directroy and converts all pdfs in that directory to json files
def convert_pdf_to_json(client, from_directory, to_directory):
    
    files = os.listdir(from_directory)
    pdf_files = [f for f in files if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {from_directory}.")
        return []
    
    for file in pdf_files:
        doc = fitz.open(os.path.join(from_directory, file))
        total_pages = len(doc)
        print(f"[INFO] PDF {file} has {total_pages} pages.")
        
        json_path = os.path.join(to_directory, f"{file[:-4]}.json")
        os.makedirs(to_directory, exist_ok=True)
        print("CHECKING JSON PATH", json_path)            
        if os.path.exists(json_path):
            print(f"[CACHE] Found OCR JSON at {json_path}. Loading from cache...")
            to_directory2 = to_directory[:-5]  # Remove '-json' from the end
            to_directory2 += "-text"
            extract_text_from_json(json_path, to_directory2)
            continue
        
        ocr_results = []
        
        for page_num in range(total_pages):
            print("[INFO] Processing page", page_num + 1)
            
            # Render the page to an image
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            img_stream = io.BytesIO(img_bytes)
            
            # Submit to Azure Read API
            result = client.read_in_stream(img_stream, raw=True)
            operation_id = result.headers["Operation-Location"].split("/")[-1]
            
            # poll for Result
            while True:
                read_result = client.get_read_result(operation_id)
                if read_result.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)
                
            if read_result.status == OperationStatusCodes.succeeded:
                for page_result in read_result.analyze_result.read_results:
                    ocr_page = {
                        "page": page_result.page,
                        "lines": [{"text": line.text, "boundingBox": line.bounding_box} for line in page_result.lines]
                    }
                    ocr_results.append(ocr_page)
                print(f"[INFO] Successfully processed page {page_num + 1}.")
            else:
                print(f"[ERROR] Failed to process page {page_num + 1}. Status: {read_result.status}")
            # Rate limiting: stay under 10 calls/minute
            print("[INFO] Waiting to respect API rate limit...")
            time.sleep(6)

        # Save the OCR results to JSON
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(ocr_results, json_file, indent=2)
        doc.close()
        to_directory2 = to_directory[:-5]  # Remove '-json' from the end
        to_directory2 += "-text"
        extract_text_from_json(json_path, to_directory2)
    return True

def extract_text_from_json(json_path, to_directory):
    os.makedirs(to_directory, exist_ok=True)
    with open(json_path, "r", encoding="utf-8") as json_file:
        ocr_data = json.load(json_file)
        file_name = os.path.basename(json_path)
        file_name = file_name[:-5]  # Remove '.json' from the end
        file_name += ".txt"
    if os.path.exists(os.path.join(to_directory, file_name)):
        print(f"[CACHE] Text file {file_name} already exists in {to_directory}. Skipping extraction.")
        return
    
    
    flat_text = ""
    for page in ocr_data:
        # print("PAGE NUMBER:", page.get("page", "?"))
        for line in page["lines"]:
            # print("LINE:", line["text"])
            flat_text += line["text"] + "\n"
        flat_text += f"\n--- End of Page {page.get('page', '?')} ---\n\n"
    
    with open(os.path.join(to_directory, file_name), "w", encoding="utf-8") as text_file:
        text_file.write(flat_text)
    

if __name__ == "__main__":
    company_number = "01471587"
    directory = "shortened-filings"
    
    from_directory = f"{company_number}/{directory}"
    to_directory = f"{company_number}/{directory}-json"
    
    AZURE_KEY, AZURE_ENDPOINT = load_azure_credentials()
    client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))
    
    print(convert_pdf_to_json(client, from_directory, to_directory))

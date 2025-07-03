# pdf_qa_with_ollama_final.py

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import requests, time, io
from dotenv import load_dotenv
import os
import fitz  # PyMuPDF

# Azure OCR Setup
load_dotenv()
AZURE_KEY = os.getenv("AZURE_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

client = ComputerVisionClient(
    AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY)
)

# --- MODIFIED FUNCTION WITH RATE LIMITING ---
def extract_text_from_pdf_pagewise(pdf_path):
    """
    Extracts text by sending one page at a time to the Azure API,
    with a delay to respect the free tier rate limit (10 calls/min).
    """
    print(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"PDF has {total_pages} pages. Starting extraction...")

    full_text_output = ""

    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        
        # Convert the page to an image in memory (as before)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        img_stream = io.BytesIO(img_bytes)

        print(f"  Processing page {page_num + 1}/{total_pages}...")

        # Send the single page to the API (as before)
        result = client.read_in_stream(img_stream, raw=True)
        operation_id = result.headers["Operation-Location"].split("/")[-1]

        # Poll for the result of this single page (as before)
        while True:
            read_result = client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            time.sleep(1)

        # Append the extracted text (as before)
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    full_text_output += line.text + "\n"
        else:
            print(f"  [ERROR] Failed to process page {page_num + 1}. Status: {read_result.status}")

        full_text_output += "\n--- End of Page " + str(page_num + 1) + " ---\n\n"

        # !!!!! --- RATE LIMITING FIX --- !!!!!
        # To stay under the 10 calls/minute limit, wait for ~7 seconds after each call.
        # The polling loop already waits for ~1-2 seconds, so we add 6 more.
        print("    Waiting to avoid rate limit...")
        time.sleep(6) 
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    print("Extraction complete.")
    doc.close()
    return full_text_output

# --- YOUR SCRIPT CONTINUES (NO CHANGES NEEDED BELOW) ---

pdf_path = "/Users/siddharthdileep/extracter/OC353214/filings/AA_MzA1NTY1NzAxNWFkaXF6a2N4.pdf"
pdf_text = extract_text_from_pdf_pagewise(pdf_path)

output_file_path = "./documents/extracted_text.txt"
print(f"Saving extracted text to {output_file_path}")
with open(output_file_path, "w", encoding="utf-8") as out_file:
    out_file.write(pdf_text)

print("Text saved. Ready for Q&A.")

user_question = input("Enter your question: ")

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma:2b",
        "prompt": f"Based on the following document content, answer the user's question.\n\nDocument Content:\n{pdf_text}\n\nQuestion: {user_question}\nAnswer:",
        "stream": False
    }
)

if response.status_code == 200:
    answer = response.json().get("response", "No 'response' field in output.")
    print("\nAnswer:\n" + answer)
else:
    print(f"\n[ERROR] Ollama server responded with status {response.status_code}")
    print("Raw response:", response.text)
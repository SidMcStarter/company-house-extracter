"""
pdf_qa_with_ollama_final.py

This script:
1. Performs OCR on a scanned or image-based PDF using Azure's Read API (one page at a time).
2. Caches the structured OCR output (.json) by filename to avoid repeated API calls.
3. Extracts and flattens text from OCR output.
4. Lets the user ask multiple questions using a local Ollama model.
"""

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

# -------------------- Azure OCR Setup --------------------
load_dotenv()
AZURE_KEY = os.getenv("AZURE_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

client = ComputerVisionClient(
    AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY)
)

# -------------------- Rate-Limited OCR Function --------------------
def extract_text_pagewise_with_cache(pdf_path, ocr_json_path):
    """
    Extracts text from each page of a PDF using Azure Read API with caching.

    Args:
        pdf_path (str): Path to the input PDF.
        ocr_json_path (str): Path to save the structured OCR JSON.

    Returns:
        str: Flattened plain text extracted from the OCR result.
    """
    if os.path.exists(ocr_json_path):
        print(f"[CACHE] Found OCR JSON at {ocr_json_path}. Loading from cache...")
        with open(ocr_json_path, "r", encoding="utf-8") as f:
            ocr_data = json.load(f)
            # print("PRINTING OCR DATA:")

        # Reconstruct flattened text from cached JSON
        read_results = ocr_data.get("analyze_result", {}).get("read_results", [])
        print(f"[CACHE] Loaded {len(read_results)} pages from cache.")
        flat_text = ""
        for page in read_results:
            print("PAGE NUMBER:", page.get("page", "?"))
            for line in page["lines"]:
                print("LINE:", line["text"])
                flat_text += line["text"] + "\n"
            flat_text += f"\n--- End of Page {page.get('page', '?')} ---\n\n"

        return flat_text

    # If cache not found, proceed with Azure OCR
    print(f"[INFO] Running Azure OCR page-by-page on {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"[INFO] PDF has {total_pages} pages.")

    ocr_results = []
    full_text_output = ""

    for page_num in range(total_pages):
        print(f"\n[PAGE {page_num + 1}/{total_pages}] Processing...")

        # Render page to image
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        img_stream = io.BytesIO(img_bytes)

        # Submit to Azure Read API
        result = client.read_in_stream(img_stream, raw=True)
        operation_id = result.headers["Operation-Location"].split("/")[-1]

        # Poll for result
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

                for line in page_result.lines:
                    full_text_output += line.text + "\n"
        else:
            print(f"[ERROR] Failed to process page {page_num + 1}. Status: {read_result.status}")

        full_text_output += f"\n--- End of Page {page_num + 1} ---\n\n"

        # Rate limiting: stay under 10 calls/minute
        print("[INFO] Waiting to respect API rate limit...")
        time.sleep(6)

    doc.close()

    # Save the structured OCR result
    with open(ocr_json_path, "w", encoding="utf-8") as f:
        json.dump(ocr_results, f, indent=2)

    print("\n[INFO] OCR extraction complete and saved to JSON.")
    return full_text_output

# -------------------- Main Execution --------------------

# Define file paths
pdf_path = "/Users/siddharthdileep/extracter/01471587/AA_MzA0MTYzNDYxN2FkaXF6a2N4-pages.pdf"
pdf_stem = pathlib.Path(pdf_path).stem

ocr_json_path = f"./documents/{pdf_stem}.json"
extracted_text_path = f"./documents/{pdf_stem}.txt"

# Extract text (with caching)
pdf_text = extract_text_pagewise_with_cache(pdf_path, ocr_json_path)

# Save flattened text
print(f"[INFO] Saving flattened text to: {extracted_text_path}")
with open(extracted_text_path, "w", encoding="utf-8") as f:
    f.write(pdf_text)

print("\n[INFO] Text ready. You can now ask questions about the document.")
print("Type 'exit' to quit.\n")

# -------------------- Interactive Q&A Loop --------------------
while True:
    user_question = input("Enter your question: ").strip()
    if user_question.lower() in ["exit", "quit"]:
        print("[INFO] Exiting question loop. Goodbye!")
        break

    print("[INFO] Sending question to Ollama model...")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:latest",  # Adjust based on available models
            "prompt": (
                "Based on the following document content, answer the user's question.\n\n"
                f"Document Content:\n{pdf_text}\n\n"
                f"Question: {user_question}\nAnswer:"
            ),
            "stream": False
        }
    )

    if response.status_code == 200:
        answer = response.json().get("response", "No 'response' field in response.")
        print("\nAnswer:\n" + answer + "\n")
    else:
        print(f"\n[ERROR] Ollama server responded with status {response.status_code}")
        print("Raw response:", response.text)

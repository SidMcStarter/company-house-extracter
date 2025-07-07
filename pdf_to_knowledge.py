"""
pdf_qa_with_ollama.py

This script:
1. Uses Azure's Read API to extract text from scanned/image PDFs.
2. Caches the OCR result in a JSON file named after the PDF file.
3. Saves flattened plain text from the OCR.
4. Sends the text and user question to a local Ollama model and prints the answer.
"""

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import requests
import json
import time
import os
import pathlib

# -------------------- Azure Setup --------------------
load_dotenv()
AZURE_KEY = os.getenv("AZURE_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

client = ComputerVisionClient(
    AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY)
)

# -------------------- OCR Extraction Function --------------------
def extract_text_and_json_from_pdf(pdf_path, json_output_path):
    """
    Extracts text and stores OCR JSON from PDF using Azure Read API.

    Args:
        pdf_path (str): Path to PDF file.
        json_output_path (str): Output path for OCR JSON.

    Returns:
        str: Flattened plain text extracted from OCR result.
    """
    with open(pdf_path, "rb") as f:
        result = client.read_in_stream(f, raw=True)

    operation_id = result.headers["Operation-Location"].split("/")[-1]
    print(f"[Azure OCR] Operation ID: {operation_id}")

    while True:
        read_result = client.get_read_result(operation_id)
        print(f"[Azure OCR] Current status: {read_result.status}")
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    if read_result.status == OperationStatusCodes.succeeded:
        # Save JSON
        with open(json_output_path, "w", encoding="utf-8") as json_file:
            json.dump(read_result.as_dict(), json_file, indent=2)

        # Extract plain text
        text_output = ""
        for page in read_result.analyze_result.read_results:
            for line in page.lines:
                text_output += line.text + "\n"
        return text_output
    else:
        raise RuntimeError(f"[Azure OCR] Extraction failed. Status: {read_result.status}")

# -------------------- File Setup --------------------
# PDF input path
pdf_path = "/Users/siddharthdileep/extracter/OC353214/filings/LLAP01_MzA0NTIzMzQzNGFkaXF6a2N4.pdf"
pdf_stem = pathlib.Path(pdf_path).stem  # "AA_MzA1NTY1NzAxNWFkaXF6a2N4"
print(f"[INFO] Processing PDF: {pdf_stem}")
# Output paths
ocr_json_output_path = f"./documents/{pdf_stem}.json"
extracted_text_path = f"./documents/{pdf_stem}.txt"

# -------------------- Use Cached OCR if Available --------------------
if os.path.exists(ocr_json_output_path):
    print(f"[CACHE] OCR JSON found for '{pdf_stem}'. Loading from cache...")
    with open(ocr_json_output_path, "r", encoding="utf-8") as json_file:
        ocr_data = json.load(json_file)

    # Reconstruct plain text
    pdf_text = ""
    for page in ocr_data["analyzeResult"]["readResults"]:
        for line in page["lines"]:
            pdf_text += line["text"] + "\n"

else:
    print("[INFO] No cache found. Running OCR via Azure...")
    pdf_text = extract_text_and_json_from_pdf(pdf_path, ocr_json_output_path)

    # Save plain text output
    with open(extracted_text_path, "w", encoding="utf-8") as out_file:
        out_file.write(pdf_text)

# -------------------- Ask User Question --------------------
user_question = input("\nEnter your question: ")

# -------------------- Query Ollama Model --------------------
print("[INFO] Sending question to Ollama model...")

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.2:latest",  # Replace with your pulled Ollama model
        "prompt": f"The following is the content of a PDF:\n\n{pdf_text}\n\nQuestion: {user_question}\nAnswer:",
        "stream": False
    }
)

# -------------------- Handle Response --------------------
if response.status_code == 200:
    answer = response.json().get("response", "No 'response' field in output.")
    print("\nAnswer:\n" + answer)
else:
    print(f"\n[ERROR] Ollama server responded with status {response.status_code}")
    print("Raw response:", response.text)
